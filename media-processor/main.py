import argparse
import logging
import os
import re
import signal
from typing import Pattern

from configure import shell
from db import LockableSqliteConn, create_tables
import processor

threads = []

logging.basicConfig(filename='log.log', encoding='utf-8', format='%(levelname)s | %(asctime)s | %(threadName)s | %(message)s', level=logging.INFO)

def dir_path(path: str) -> str:
	'''Return the full path if it is a directory. Raise a `NotADirectoryError` otherwise'''
	if len(path) > 0 and os.path.isdir(path):
		if path[0] != '/':
			path = os.path.join(os.getcwd(), path)
		return path
	raise NotADirectoryError(path)

def dir_file(path: str) -> str:
	'''Return the full path if it is a file. Raise a `FileNotFoundError` otherwise'''
	if len(path) > 0 and os.path.isfile(path):
		if path[0] != '/':
			path = os.path.join(os.getcwd(), path)
		return path
	raise FileNotFoundError(path)

def compile_regex(regex: str) -> Pattern[str]:
	flags = 0
	reversed_regex = regex[::-1]
	end = None
	for i in range(0, len(reversed_regex), 2):
		if reversed_regex[i + 1] != '/':
			if i > 0:
				end = i * -1
			break
		if reversed_regex[i] == 'a':
			flags |= re.A
		elif reversed_regex[i] == 'i':
			flags |= re.I
		elif reversed_regex[i] == 'm':
			flags |= re.M
		elif reversed_regex[i] == 's':
			flags |= re.S
		elif reversed_regex[i] == 'x':
			flags |= re.X
		elif reversed_regex[i] == 'l':
			flags |= re.L
	if end == None:
		return re.compile(regex, flags=0)
	else:
		return re.compile(regex[:end], flags=flags)

class ServiceExit(Exception):
	pass

if __name__ == '__main__':
	def service_shutdown(signum, frame):
		print(f'\nCaught signal {signum}')
		raise ServiceExit

	# Attach interrupt handler to shutdown threads gracefully
	signal.signal(signal.SIGINT, service_shutdown)

	logger = logging.getLogger(__name__)

	parser = argparse.ArgumentParser()
	parser.add_argument('-w', '--watch', dest='watch_folder', help='the directory to watch for changes (required)', type=dir_path, required=True)
	parser.add_argument('-p', '--process', dest='process_folder', help='the directory to process media in (required)', type=dir_path, required=True)
	parser.add_argument('-pt', '--processer-threads', dest='processor_threads', help='the number of processor threads. should be equal to the number of max transcodes at a time', type=int, default=1)
	parser.add_argument('-t', '--time-to-sleep', dest='sleep_time', help='how many minutes the watcher should wait before scanning again', type=float, default=0.5)
	parser.add_argument('-kh', '--known-hosts', dest='known_hosts', help='location of an ssh known_hosts file. required if using sftp and you care about security', type=dir_file)
	parser.add_argument('-pkl', '--private-key_loc', dest='private_key_loc', help='location of a ssh private key to use for sftp', type=dir_file)
	parser.add_argument('-pkp', '--private-key-pass', dest='private_key_pass', help='the ssh private key password')
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	parser.add_argument('-ds', '--disable-shell', dest='disable_shell', help='use to disable the shell', action='store_true')
	parser.add_argument('-cr', '--clean-regex',
		dest='clean_regex',
		help='''the regex used to match and remove substrings from the filename before processing.
			by default, any characters between parenthesis and brackets (including) and any characters after 1080p (p optional), 720p (p optional), and bluray (case insensitive) are removed.''',
		default='\[.+?\]|\(.+?\)|(1080p?.*)|(720p?.*)|(bluray.*)/i',
		type=compile_regex
	)
	parser.add_argument('-ser', '--season-episode-regex',
		dest='season_episode_regex',
		help='''the regex used to get substrings from the filename to figure out season and episode number.
			by default, s<SEASON NUMBER>e<EPISODE NUMBER>, season <SEASON NUMBER> (space optional), and episode <EPISODE NUMBER> (space optional) (case insensitive) are matched.''',
		default='(s(\d+)e(\d+))|(season ?(\d+))|(episode ?(\d+))',
		type=compile_regex
	)
	parser.add_argument('-er', '--episode-regex',
		dest='episode_regex',
		help='''the regex used to get substrings from the filename to figure episode number. Used if `-ser` fails.
			by default, "- <EPISODE NUMBER>" (space optional) and e<EPISODE NUMBER (at least two characters)> (case insensitive) are matched.''',
		default='((- ?)(\d+))|(e(\d{2,}))/i',
		type=compile_regex
	)
	try:
		args: argparse.Namespace = parser.parse_args()
	except NotADirectoryError:
		print('One of the supplied directories is malformed or does not exist. Exiting. (Error 1)')
		logger.error('Exiting with code 1')
		exit(1)
	except FileNotFoundError:
		print('The supplied known hosts file or private key location does not exist. Exiting. (Error 2)')
		logger.error('Exiting with code 2')
		exit(2)
	lconn = LockableSqliteConn('db.sqlite3')
	try:
		create_tables(lconn)
	except Exception:
		print('There was an error creating tables. Exiting. (Error 3)')
		logger.error('Exiting with code 3')
		exit(3)
	print('Tables created if not exist.')
	try:
		# Spin up watcher and processor threads
		watcherThread = processor.WatcherThread(args.watch_folder, args.sleep_time)
		watcherThread.start()
		threads.append(watcherThread)
		for i in range(args.processor_threads):
			processorThread = processor.ProcessorThread(args.process_folder, args.clean_regex, args.season_episode_regex, args.episode_regex, args.known_hosts, args.private_key_loc, args.private_key_pass, i + 1)
			processorThread.start()
			threads.append(processorThread)

		# Keep alive and maybe collect user input
		if args.disable_shell:
			print('Shell disabled. Waiting.')
			watcherThread.join()
		else:
			shell(lconn, args.shell)
	except ServiceExit:
		pass
	finally:
		print('Shutting down threads.')
		# Shutdown
		processor.kill()
		for thread in threads:
			thread.join()
		print('Exiting')