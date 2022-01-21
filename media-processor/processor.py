import os
from queue import Queue
import re
import shlex
from subprocess import Popen, PIPE, SubprocessError
import threading
from typing import Iterable

from db import get_conn

processingQueue = Queue(0)
e = threading.Event()

def kill() -> None:
	'''Set flag to kill all threads'''
	e.set()

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
			'webm' '264', 'mpeg', 'mpv', 'm2ts', '3gp2', 'flv' , 'mp4v',
			'm4v', 'mts', 'mov', 'h264', 'hevc', 'h265', 'wmv']

	def run(self) -> None:
		'''Watcher thread main function.'''
		print('Watcher thread started.')
		while not e.is_set():
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
					processingQueue.put(f[0])
			self.last_files = new_scan
			e.wait(timeout=self.sleep_time)


class ProcessorThread(threading.Thread):
	def __init__(self, process_folder: str, clean_regex: str):
		threading.Thread.__init__(self)
		self.process_folder: str = process_folder
		self.clean_regex = clean_regex

	def clean_filename(self, filename: str) -> str:
		'''
		Remove substrings according to clean_regex.
		Replace `.` with ` `.
		Strip leading or trailing spaces.
		'''
		return re.sub(self.clean_regex, '', filename).replace('.', ' ').strip()

	def run(self) -> None:
		'''Processor thread main function'''
		print('Processor thread started.')
		while not e.is_set():
			if processingQueue.empty():
				e.wait(timeout=5.0)
			else:
				cur = get_conn()
				if not cur:
					print('\nCan\'t process pending queue: not connected to DB.')
					continue
				if not os.path.exists(self.process_folder):
					os.makedirs(self.process_folder)
				item = processingQueue.get()
				filename = os.path.basename(item).rsplit('.', 1)
				ext = filename[1]
				filename = self.clean_filename(filename[0])

				cur = cur.cursor()
				cur.execute('''SELECT * FROM properties;''')
				rows = cur.fetchall()
				topMatch = None
				for row in rows:
					pass
				if topMatch:
					cur.execute('''SELECT ffmpeg_args, output_container, folder FROM property_settings WHERE property = ?;''', (topMatch,))
					row = cur.fetchone()
					if row:
						try:
							args = [a.strip() for a in shlex.split(row['ffmpeg_args'])]
							modifiers = ''
							tmp_output_path = os.path.join(self.process_folder, filename + modifiers + '.' + row['output_container'])
							s_args = ['ffmpeg', '-i', item, *args, f'{tmp_output_path}']
							p = Popen(s_args)
							if p.wait() != 0:
								raise SubprocessError
							os.replace(tmp_output_path, os.path.join(row['folder'], filename + modifiers + '.' + row["output_container"]))
						except SubprocessError as e:
							print(f'\nError executing command {s_args}: {e}')
					else:
						print(f'\nTried procesing {filename}.{ext}, but failed due to missing settings. Logging...')
				cur.close()
