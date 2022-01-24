import shlex
try:
	import readline # Naked import. Used to extend `input()` to allow for better UX (arrow key navigation, history, etc.)
except ImportError:
	pass # Just ignore it. Not critical. I read that some python environments don't support readline

from db import LockableSqliteConn

def yn(say: str) -> bool:
	yn = input(say + 'Continue? (y/n)').lower()
	return yn == 'y' or yn == 'e' or yn == 's'

def command(lconn: LockableSqliteConn, commands: list[str]) -> None:
	with lconn:
		for c in commands:
			split: list[str] = [a.strip() for a in shlex.split(c)]
			if split[0] == 'commit':
				print('Committing to DB.')
				lconn.conn.commit()
			elif split[0] == 'vacuum':
				print('Clearing space in DB.')
				lconn.conn.execute('''VACUUM;''')
			elif split[0] == 'add' or split[0] == '':
				if split[1] == 'property':
					property = split[2]
					pattern = split[3]
					if len(split) > 4:
						partial = 1
					else:
						partial = 0
					print(f'Adding property "{property}" with pattern "{pattern}" and partial "{partial != 0}".')
					lconn.cur.execute('''INSERT INTO properties (property, pattern, partial) VALUES (?, ?, ?) ON CONFLICT(property) DO UPDATE SET pattern = ?, partial = ?;''', (property, pattern, partial, pattern, partial))
				elif split[1] == 'setting':
					property = split[2]
					ffmpeg_args = split[3]
					output_container = split[4]
					folder = split[5]
					destination_server = None
					is_show = 0
					season_override = None
					if len(split) > 6:
						for i in range(6, len(split)):
							if i == 6:
								if len(split[i]) > 0:
									destination_server = split[i]
							elif i == 7:
								if len(split[i]) > 0:
									is_show = 1
							elif i == 8:
								if len(split[i]) > 0:
									season_override = split[i]
					print(f'Adding settings (ffmpeg_args: "{ffmpeg_args}") (output_container: "{output_container}") (destination folder: "{folder}") (destination server "{destination_server}") to property "{property}."')
					lconn.cur.execute('''INSERT INTO property_settings (property, ffmpeg_args, output_container, user_at_ip, folder, is_show, season_override) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(property) DO UPDATE SET ffmpeg_args = ?, output_container = ?, user_at_ip = ?, folder = ?, is_show = ?, season_override = ?;''', (property, ffmpeg_args, output_container, destination_server, folder, is_show, season_override, ffmpeg_args, output_container, destination_server, folder, is_show, season_override))
				elif split[1] == 'destination':
					user_at_ip = split[2]
					if len(split) > 3:
						password = split[3]
					else:
						password = None
					print(f'Adding destination server at {user_at_ip} with password {password}.')
					lconn.cur.execute('''INSERT INTO destination_servers (user_at_ip, password) VALUES (?, ?) ON CONFLICT(user_at_ip) DO UPDATE SET password = ?;''', (user_at_ip, password, password))
				else:
					if not yn(f'[{split[1]}] is not a valid `add` command and it will be ignored. '):
						break
			elif split[0] == 'remove':
				if split[1] == 'property':
					property = split[2]
					print(f'Removing property {property}.')
					lconn.cur.execute('''DELETE FROM properties WHERE property = ?;''', (property,))
				elif split[1] == 'setting':
					property = split[2]
					print(f'Removing settings from {property}.')
					lconn.cur.execute('''DELETE FROM property_settings WHERE property = ?;''', (property,))
				elif split[1] == 'destination':
					user_at_ip = split[2]
					print(f'Removing destination server at {user_at_ip}.')
					lconn.cur.execute('''DELETE FROM destination_servers WHERE user_at_ip = ?;''', (user_at_ip,))
				else:
					if not yn(f'[{split[1]}] is not a valid `remove` command and it will be ignored. '):
						break
			elif split[0] == 'reset':
				if split[1] == 'db':
					print('Removing all data.')
					lconn.cur.execute('''DELETE FROM property_settings;''')
					lconn.cur.execute('''DELETE FROM properties;''')
				elif split[1] == 'properties':
					print('Removing all data in `properties`.')
					lconn.cur.execute('''DELETE FROM properties;''')
				elif split[1] == 'settings':
					print('Removing all data in `property_settings`.')
					lconn.cur.execute('''DELETE FROM property_settings;''')
				elif split[1] == 'destination':
					print('Removing all data in `destination_servers`.')
					lconn.cur.execute('''DELETE FROM destination_servers;''')
			else:
				if not yn(f'[{c}] is not a valid command and it will be ignored. '):
					break

def shell(lconn: LockableSqliteConn, symbol: str):
	print('Starting shell.')
	commands: list[str] = []
	while True:
		# Shell
		c = input(symbol)
		if len(c) > 0:
			commands.append(c)
			if c == 'exit':
				break
			elif c == 'wipe':
				print('Wiping transaction.')
				commands: list[str] = []
			elif c == 'exec':
				print('Executing commands.')
				try:
					command(lconn, commands[:-1])
				except Exception as e:
					print(f'Some commands did not execute successfully. [{e}] error occured')
				commands: list[str] = []

if __name__ == '__main__':
	class ServiceExit(Exception):
		pass

	def service_shutdown(signum, frame):
		print(f'Caught signal {signum}')
		raise ServiceExit

	import argparse
	import logging
	import signal

	from db import create_tables

	# Attach interrupt handler to shutdown gracefully
	signal.signal(signal.SIGINT, service_shutdown)

	logger = logging.getLogger(__name__)

	parser = argparse.ArgumentParser()
	parser.add_argument('-g', '--gui', dest='use_gui', help='use the gui instead of the shell', action='store_true')
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	args: argparse.Namespace = parser.parse_args()
	lconn = LockableSqliteConn('db.sqlite3')
	try:
		create_tables(lconn)
	except Exception:
		print('There was an error creating tables. Exiting. (Error 3)')
		logger.error('Exiting with code 3')
		exit(3)
	print('Tables created if not exist.')
	try:
		if args.use_gui:
			from gui import driver
			print('Shell disabled. Launching GUI...')
			driver(lconn)
		else:
			shell(lconn, args.shell)
	except ServiceExit:
		pass
	finally:
		print('Exiting')