import os
from queue import Queue
from subprocess import Popen, PIPE, SubprocessError
import threading
import time
from typing import Iterable

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
		self.last_files: set[tuple] = set()

	def run(self):
		print('Watcher thread started.')
		first_pass = True
		while not e.is_set():
			if not os.path.exists(self.watch_folder):
				os.makedirs(self.watch_folder)
			new_scan: set[tuple] = set()
			for entry in full_scan_dir(self.watch_folder):
				stat = os.stat(entry)
				ctime=stat.st_ctime
				new_scan.add((entry, ctime))
			if first_pass:
				first_pass = False
				self.last_files = new_scan
			new_files = new_scan - self.last_files
			for f in new_files:
				processingQueue.put(f[0])
			self.last_files = new_scan
			e.wait(timeout=self.sleep_time)


class ProcessorThread(threading.Thread):
	def __init__(self, process_folder: str):
		threading.Thread.__init__(self)
		self.process_folder: str = process_folder

	def run(self):
		print('Processor thread started.')
		while not e.is_set():
			if not os.path.exists(self.process_folder):
				os.makedirs(self.process_folder)
			if processingQueue.empty():
				e.wait(timeout=5.0)
			else:
				item = processingQueue.get()
				filename = os.path.basename(item)
				ext = filename.rsplit('.', 1)[1]
				filename = filename.rsplit('.', 1)[0]
				print(item + ' | ' + filename + ' | ' + ext)
