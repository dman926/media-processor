import asyncio
import argparse
import os
import signal
import threading
import time

from db import disconnect_from_db
from processor import WatcherThread, ProcessorThread, kill

threads = []

def dir_path(path: str) -> str:
	'''Return the full path if it is a directory. Raise a `NotADirectoryError` otherwise'''
	if len(path) > 0 and os.path.isdir(path):
		if path[0] != '/':
			path = os.path.join(os.getcwd(), path)
		return path
	raise NotADirectoryError(path)

class ServiceExit(Exception):
	pass

def service_shutdown(signum, frame):
	print(f'Caught signal {signum}')
	raise ServiceExit

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-w', '--watch', dest='watch_folder', help='the directory to watch for changes (required)', type=dir_path, required=True)
	parser.add_argument('-p', '--process', dest='process_folder', help='the directory to process media in (required)', type=dir_path, required=True)
	parser.add_argument('-t', '--time-to-sleep', dest='sleep_time', help='how many minutes the watcher should wait before scanning again', type=float, default=0.5)
	try:
		args = parser.parse_args()
	except NotADirectoryError:
		print('One of the supplied directories is malformed or does not exist. (Error 1)')
		exit(1)
	# Attach interrupt handler to shutdown threads gracefully
	signal.signal(signal.SIGINT, service_shutdown)
	try:
		# Spin up watcher and processor threads
		watcher = WatcherThread(args.watch_folder, args.sleep_time)
		watcher.start()
		threads.append(watcher)
		processor = ProcessorThread(args.process_folder)
		processor.start()
		threads.append(processor)

		# Keep alive
		while True:
			time.sleep(5)
	except ServiceExit:
		print('Shutting down threads.')
		# Shutdown
		kill()
		for thread in threads:
			thread.join()
		print('Disconnected from DB.')
		if disconnect_from_db():
			print("Successfully disconnected from DB.")
		else:
			print("Error disconnecting from DB. Perhaps it is already disconnected.")
		print('Exitting')