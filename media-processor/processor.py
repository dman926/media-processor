import os
from queue import Queue
import re
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
				if not os.path.exists(self.process_folder):
					os.makedirs(self.process_folder)
				item = processingQueue.get()
				filename = os.path.basename(item)
				ext = filename.rsplit('.', 1)[1]
				filename = self.clean_filename(filename.rsplit('.', 1)[0])
				cur = get_conn()
				if not cur:
					continue
				cur = cur.cursor()
				cur.execute('''SELECT * FROM properties;''')
				rows = cur.fetchall()
				topMatch = None
				for row in rows:
					pass
				if topMatch:
					cur.execute('''SELECT ffmpeg_args FROM property_settings WHERE property = ?;''', (topMatch,))
					args = cur.fetchone()['ffmpeg_args']
				cur.close()
