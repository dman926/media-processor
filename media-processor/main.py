import asyncio
import argparse
import os
import signal
import threading

from configure import command
from db import connect_to_db, create_tables, disconnect_from_db
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
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
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
		watcher = WatcherThread(args.watch_folder, args.sleep_time)
		watcher.start()
		threads.append(watcher)
		processor = ProcessorThread(args.process_folder)
		processor.start()
		threads.append(processor)

		# Keep alive and collect user input
		commands: list[str] = []
		print('Starting shell.')
		while True:
			# Shell
			c = input(args.shell)
			commands.append(c)
			if c == 'exec':
				print('Executing commands.')
				try:
					if command(commands[:-1]):
						print('All commands executed successfully.')
					else:
						print('Some commands did not execute successfully.')
				except Exception as e:
					print(f'Some commands did not execute successfully. [{e}] error occured')
				commands: list[str] = []
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
		print('Exiting')