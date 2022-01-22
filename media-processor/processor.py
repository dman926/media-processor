from thefuzz import fuzz
import os
from queue import Queue
import re
import shlex
from subprocess import Popen, PIPE, SubprocessError
import threading
from typing import Iterable, Optional

try:
	from paramiko import SSHClient, AutoAddPolicy
	from paramiko.ssh_exception import SSHException
	sftp_ok = True
except ImportError:
	sftp_ok = False

from db import LockableSqliteConn

processing_queue = Queue(0)
event = threading.Event()
processing_lock = threading.Lock()

def kill() -> None:
	'''Set flag to kill all threads'''
	event.set()

def full_scan_dir(baseDir: str) -> Iterable[str]:
	'''Recursively scan a dir to get all file absolute paths'''
	for entry in os.scandir(baseDir):
		if entry.is_file():
			yield os.path.join(baseDir, entry.name)
		else:
			yield from full_scan_dir(entry.path)


class WatcherThread(threading.Thread):
	def __init__(self, watch_folder: str, sleep_time: float):
		threading.Thread.__init__(self)
		self.watch_folder: str = watch_folder
		self.sleep_time: float = sleep_time * 60
		# Initialize last_files.
		self.last_files: set[tuple] = set()
		for entry in full_scan_dir(self.watch_folder):
			stat = os.stat(entry)
			ctime=stat.st_ctime
			self.last_files.add((entry, ctime))

	def is_video(self, filename: str) -> bool:
		'''Returns `True` if this is a video file. `False` otherwise.'''
		return filename.rsplit('.', 1)[1].lower() in ['mp4', 'mkv', 'avi',
			'webm', '264', 'mpeg', 'mpv', 'm2ts', '3gp2', 'flv', 'mp4v',
			'm4v', 'mts', 'mov', 'h264', 'hevc', 'h265', 'wmv']

	def run(self) -> None:
		'''Watcher thread main function.'''
		print('Watcher thread started.')
		while not event.is_set():
			if not os.path.exists(self.watch_folder):
				os.makedirs(self.watch_folder)
			new_scan: set[tuple] = set()
			for entry in full_scan_dir(self.watch_folder):
				stat = os.stat(entry)
				ctime=stat.st_ctime
				new_scan.add((entry, ctime))
			new_files = new_scan - self.last_files
			for f in new_files:
				if self.is_video(f[0]):
					processing_queue.put(f[0])
			self.last_files = new_scan
			event.wait(timeout=self.sleep_time)


class ProcessorThread(threading.Thread):
	def __init__(self, process_folder: str, clean_regex: str, known_hosts: Optional[str], private_key_loc: Optional[str], private_key_pass: Optional[str], tid: int):
		threading.Thread.__init__(self)
		self.process_folder: str = process_folder
		self.clean_regex: str = clean_regex
		self.known_hosts: Optional[str] = known_hosts
		self.private_key_loc: Optional[str] = private_key_loc
		self.private_key_pass: Optional[str] = private_key_pass
		self.tid = tid
		self.lconn = LockableSqliteConn('db.sqlite3')
		self.ssh_client = SSHClient()
		if self.known_hosts:
			self.ssh_client.load_host_keys(self.known_hosts)
		else:
			self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

	def clean_filename(self, filename: str) -> str:
		'''
		Remove substrings according to clean_regex.
		Replace `.` and `_` with ` `.
		Strip leading or trailing spaces.
		'''
		return re.sub(self.clean_regex, '', filename).replace('.', ' ').replace('_', ' ').strip()

	def run(self) -> None:
		'''Processor thread main function'''
		print(f'Processor thread {self.tid} started.')
		while not event.is_set():
			if processing_queue.empty():
				event.wait(timeout=5.0)
			else:
				if not os.path.exists(self.process_folder):
					os.makedirs(self.process_folder)
				with processing_lock:
					item = processing_queue.get()
				filename = os.path.basename(item).rsplit('.', 1)
				ext = filename[1]
				filename = self.clean_filename(filename[0])

				row = None
				with self.lconn:
					self.lconn.cur.execute('''SELECT property, pattern, partial FROM properties;''')
					rows = self.lconn.cur.fetchall()
					topMatch = None
					topScore = -1
					for prow in rows:
						if prow[2]:
							score = fuzz.partial_ratio(filename, prow[1])
						else:
							score = fuzz.ratio(filename, prow[1])
						if score > 40 and score > topScore:
							topMatch = prow[0]
					if topMatch:
						self.lconn.cur.execute('''SELECT ps.ffmpeg_args, ps.output_container, ps.folder, ds.user_at_ip, ds.password FROM property_settings ps JOIN destination_servers ds ON ps.user_at_ip = ds.user_at_ip WHERE property = ?;''', (topMatch,))
						row = self.lconn.cur.fetchone()
				if row:
					try:
						args = [a.strip() for a in shlex.split(row[0])]
						tmp_output_path = os.path.join(self.process_folder, topMatch + '.' + row[1])
						s_args = ['ffmpeg', '-y', '-i', item, *args, f'{tmp_output_path}']
						p = Popen(s_args)
						if p.wait() != 0:
							raise SubprocessError
						if not row[3]:
							os.replace(tmp_output_path, os.path.join(row[2], topMatch + '.' + row[1]))
						elif sftp_ok:
							sftp_user = row[3].split('@', 1)
							sftp_host = sftp_user[1].split(':', 1)
							if len(sftp_host) > 1:
								sftp_port = int(sftp_host[1])
							else:
								sftp_port = 22
							sftp_host = sftp_host[0]
							sftp_user = sftp_user[0]
							try:
								cpass = True
								if not row[4] and self.private_key_loc:
									self.ssh_client.connect(hostname=sftp_host, username=sftp_user, port=sftp_port, key_filename=self.private_key_loc, passphrase=self.private_key_pass)
								elif row[4]:
									self.ssh_client.connect(hostname=sftp_host, username=sftp_user, password=row[4], port=sftp_port)
								else:
									cpass = False
								if cpass:
									sftp = self.ssh_client.open_sftp()
									sftp.put(tmp_output_path, os.path.join(row[2], topMatch + '.' + row[1]))
									os.remove(tmp_output_path)
								else:
									print('Can\'t SFtp file to remote server. No ssh key or password given. File is processed, but will not be moved.')
							except SSHException:
								print('Can\'t SFTP file to remote server. Invalid host. Perhaps it isn\'t in the `known_hosts` file?. File is processed, but will not be moved.')
							self.ssh_client.close()
						else:
							print('Can\'t SFTP file to remote server. `pysftp` not installed. File is processed, but will not be moved.')
					except SubprocessError as e:
						# TODO: replace with logging
						print(f'\nError executing command {s_args}: {e}')
				else:
					# TODO: replace with logging
					print(f'\nTried procesing {filename}.{ext}, but failed due to missing settings. Logging...')
