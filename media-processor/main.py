import asyncio
import argparse
import os
import signal
import threading

from configure import shell
from db import connect_to_db, create_tables, disconnect_from_db
import processor

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

if __name__ == '__main__':
	def service_shutdown(signum, frame):
		print(f'\nCaught signal {signum}')
		raise ServiceExit

	parser = argparse.ArgumentParser()
	parser.add_argument('-w', '--watch', dest='watch_folder', help='the directory to watch for changes (required)', type=dir_path, required=True)
	parser.add_argument('-p', '--process', dest='process_folder', help='the directory to process media in (required)', type=dir_path, required=True)
	parser.add_argument('-t', '--time-to-sleep', dest='sleep_time', help='how many minutes the watcher should wait before scanning again', type=float, default=0.5)
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	parser.add_argument('-r', '--clean-regex',
		dest='clean_regex',
		help='''the regex used to match and remove substrings from the filename before processing.
			by default, any characters between parenthesis and brackets (including), 1080p (p optional), 720p (p optional), and bluray (case insensitive) are removed.''',
		default='\[.+?\]|\(.+?\)|(1080p?.*)|(720p?.*)|(bluray.*)/i'
	)
	try:
		args: argparse.Namespace = parser.parse_args()
	except NotADirectoryError:
		print('One of the supplied directories is malformed or does not exist. Exiting. (Error 1)')
		exit(1)
	# Attach interrupt handler to shutdown threads gracefully
	signal.signal(signal.SIGINT, service_shutdown)
	if not connect_to_db():
		print('Something went wrong connecting to the DB. Exiting. (Error 2)')
		exit(2)
	print('Connected to DB.')
	if not create_tables():
		print('Something went wrong creating DB tables. Exiting. (Error 3)')
		exit(3)
	print('Tables created if not exist.')
	try:
		# Spin up watcher and processor threads
		watcherThread = processor.WatcherThread(args.watch_folder, args.sleep_time)
		watcherThread.start()
		threads.append(watcherThread)
		processorThread = processor.ProcessorThread(args.process_folder, args.clean_regex)
		processorThread.start()
		threads.append(processorThread)

		# Keep alive and collect user input
		shell(args.shell)
	except ServiceExit:
		pass
	finally:
		print('Shutting down threads.')
		# Shutdown
		processor.kill()
		for thread in threads:
			thread.join()
		if disconnect_from_db():
			print("Successfully disconnected from DB.")
		else:
			print("Error disconnecting from DB. Perhaps it is already disconnected?")
		print('Exiting')