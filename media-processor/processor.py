import logging
import os
from queue import Queue
import re
import shlex
from subprocess import Popen, PIPE, SubprocessError
from thefuzz import fuzz
import threading
from typing import Iterable, Optional, Pattern

try:
	from paramiko import SSHClient, AutoAddPolicy
	from paramiko.ssh_exception import SSHException
	sftp_ok = True
except ImportError:
	sftp_ok = False

from db import LockableSqliteConn

logger = logging.getLogger(__name__)

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
		self.name = 'Watcher Thread'
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
	def __init__(self, process_folder: str, clean_regex: Pattern[str], season_episode_regex: Pattern[str], episode_regex: Pattern[str], known_hosts: Optional[str], private_key_loc: Optional[str], private_key_pass: Optional[str], tid: int):
		threading.Thread.__init__(self)
		self.process_folder: str = process_folder
		self.clean_regex: Pattern[str] = clean_regex
		self.season_episode_regex: Pattern[str] = season_episode_regex
		self.episode_regex: Pattern[str] = episode_regex
		self.known_hosts: Optional[str] = known_hosts
		self.private_key_loc: Optional[str] = private_key_loc
		self.private_key_pass: Optional[str] = private_key_pass
		self.tid = tid
		self.name = f'Processor Thread {tid}'
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

				logger.info(f'Starting processing of {item}')

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
						logger.info(f'Matched {item} to {topMatch}')
						self.lconn.cur.execute('''SELECT ps.ffmpeg_input_args, ps.ffmpeg_output_args, ps.output_container, ps.folder, ds.user_at_ip, ds.password, ps.is_show, ps.season_override FROM property_settings ps JOIN destination_servers ds ON ps.user_at_ip = ds.user_at_ip WHERE property = ?;''', (topMatch,))
						row = self.lconn.cur.fetchone()
						if not row:
							self.lconn.cur.execute('''SELECT ps.ffmpeg_input_args, ps.ffmpeg_output_args, ps.output_container, ps.folder, ps.is_show, ps.season_override FROM property_settings ps WHERE property = ?;''', (topMatch,))
							row = self.lconn.cur.fetchone()
							if row:
								# hacky way to get around not having a destination server
								row = list(row)
								row.insert(4, None)
								row.insert(5, None)
								row = tuple(row)
					else:
						logger.warning(f'Can\'t process {item}. No properties that are close enough.')
				if row:
					try:
						input_args = [a.strip() for a in shlex.split(row[0])]
						output_args = [a.strip() for a in shlex.split(row[1])]
						modifiers = ''
						if row[6]:
							# is show
							season_episode = re.search(self.season_episode_regex, filename)
							if season_episode:
								modifiers = f' {season_episode.group().upper()}'
							elif row[7]:
								season_episode = re.search(self.episode_regex, filename)
								if season_episode:
									modifiers = f' S{int(row[7]):02}E{int(season_episode.group().replace(" ", "").replace("-", "").replace("e", "")):02}'
						tmp_output_path = os.path.join(self.process_folder, topMatch + modifiers + '.' + row[2])
						s_args = ['ffmpeg', '-y', *input_args, '-i', item, *output_args, '-v', 'quiet', f'{tmp_output_path}']
						p = Popen(s_args)
						if p.wait() != 0:
							raise SubprocessError
						if not row[4]:
							os.replace(tmp_output_path, os.path.join(row[3], topMatch + modifiers + '.' + row[2]))
						elif sftp_ok:
							sftp_user = row[4].split('@', 1)
							sftp_host = sftp_user[1].split(':', 1)
							if len(sftp_host) > 1:
								sftp_port = int(sftp_host[1])
							else:
								sftp_port = 22
							sftp_host = sftp_host[0]
							sftp_user = sftp_user[0]
							try:
								cpass = True
								if not row[5] and self.private_key_loc:
									self.ssh_client.connect(hostname=sftp_host, username=sftp_user, port=sftp_port, key_filename=self.private_key_loc, passphrase=self.private_key_pass)
								elif row[5]:
									self.ssh_client.connect(hostname=sftp_host, username=sftp_user, password=row[4], port=sftp_port)
								else:
									cpass = False
								if cpass:
									sftp = self.ssh_client.open_sftp()
									sftp.put(tmp_output_path, os.path.join(row[3], topMatch + modifiers + '.' + row[2]))
									os.remove(tmp_output_path)
								else:
									logger.warn(f'Can\'t SFTP {item} to remote server. No ssh key or password given. File is processed, but will not be moved.')
							except SSHException:
								logger.warn(f'Can\'t SFTP {item} to remote server. Invalid host. Perhaps it isn\'t in the `known_hosts` file?. File is processed, but will not be moved.')
							self.ssh_client.close()
						else:
							logger.warn(f'Can\'t SFTP {item} to remote server. `paramiko` not installed. File is processed, but will not be moved.')
					except SubprocessError as e:
						logger.error(f'\nError executing command {s_args} for {item}: {e}')
				else:
					logger.warn(f'\nTried procesing {item}, but failed due to missing settings.')
