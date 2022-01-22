import argparse
import os
import signal

from configure import shell
from db import LockableSqliteConn
import processor

threads = []

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

class ServiceExit(Exception):
	pass

if __name__ == '__main__':
	def service_shutdown(signum, frame):
		print(f'\nCaught signal {signum}')
		raise ServiceExit

	# Attach interrupt handler to shutdown threads gracefully
	signal.signal(signal.SIGINT, service_shutdown)

	parser = argparse.ArgumentParser()
	parser.add_argument('-w', '--watch', dest='watch_folder', help='the directory to watch for changes (required)', type=dir_path, required=True)
	parser.add_argument('-p', '--process', dest='process_folder', help='the directory to process media in (required)', type=dir_path, required=True)
	parser.add_argument('-pt', '--processer-threads', dest='processor_threads', help='the number of processor threads. should be equal to the number of max transcodes at a time', type=int, default=1)
	parser.add_argument('-t', '--time-to-sleep', dest='sleep_time', help='how many minutes the watcher should wait before scanning again', type=float, default=0.5)
	parser.add_argument('-kh', '--known-hosts', dest='known_hosts', help='location of an ssh known_hosts file. required if using sftp and you care about security', type=dir_file)
	parser.add_argument('-pkl', '--private-key_loc', dest='private_key_loc', help='location of a ssh private key to use for sftp', type=dir_file)
	parser.add_argument('-pkp', '--private-key-pass', dest='private_key_pass', help='the ssh private key password')
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	parser.add_argument('-r', '--clean-regex',
		dest='clean_regex',
		help='''the regex used to match and remove substrings from the filename before processing.
			by default, any characters between parenthesis and brackets (including) and any characters after 1080p (p optional), 720p (p optional), and bluray (case insensitive) are removed.''',
		default='\[.+?\]|\(.+?\)|(1080p?.*)|(720p?.*)|(bluray.*)/i'
	)
	try:
		args: argparse.Namespace = parser.parse_args()
	except NotADirectoryError:
		print('One of the supplied directories is malformed or does not exist. Exiting. (Error 1)')
		exit(1)
	except FileNotFoundError:
		print('The supplied known hosts file or private key location does not exist. Exiting. (Error 2)')
		exit(2)
	lconn = LockableSqliteConn('db.sqlite3')
	try:
		with lconn:
			lconn.cur.execute('''CREATE TABLE IF NOT EXISTS properties (
				property TEXT,
				pattern TEXT NOT NULL,
				partial INT(1),
				PRIMARY KEY (property)
			);''')
			lconn.cur.execute('''CREATE TABLE IF NOT EXISTS property_settings (
				property TEXT,
				ffmpeg_args TEXT NOT NULL,
				output_container TEXT NOT NULL,
				user_at_ip TEXT,
				folder TEXT NOT NULL,
				PRIMARY KEY (property),
				FOREIGN KEY (property) REFERENCES properties(property),
				FOREIGN KEY (user_at_ip) REFERENCES destination_servers(user_at_ip)
			);''')
			lconn.cur.execute('''CREATE TABLE IF NOT EXISTS destination_servers (
				user_at_ip TEXT,
				password TEXT,
				PRIMARY KEY (user_at_ip)	
			);''')
			lconn.conn.commit()
	except Exception:
		print('There was an error connecting to `db.sqlite3` or creating tables. Exiting. (Error 3)')
		exit(3)
	del lconn
	print('Tables created if not exist.')
	try:
		# Spin up watcher and processor threads
		watcherThread = processor.WatcherThread(args.watch_folder, args.sleep_time)
		watcherThread.start()
		threads.append(watcherThread)
		for i in range(args.processor_threads):
			processorThread = processor.ProcessorThread(args.process_folder, args.clean_regex, args.known_hosts, args.private_key_loc, args.private_key_pass, i + 1)
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
		print('Exiting')