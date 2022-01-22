import shlex
try:
	import readline # Naked import. Used to extend `input()` to allow for better UX (arrow key navigation, history, etc.)
except ImportError:
	pass # Just ignore it. Not critical. I read that some python environments don't support readline

from db import LockableSqliteConn

def yn(say: str) -> bool:
	yn = input(say + 'Continue? (y/n)').lower()
	return yn == 'y' or yn == 'e' or yn == 's'

def command(commands: list[str]) -> None:
	lconn = LockableSqliteConn('db.sqlite3')
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
					if len(split) > 6:
						destination_server = split[6]
					else:
						destination_server = None
					print(f'Adding settings (ffmpeg_args: "{ffmpeg_args}") (output_container: "{output_container}") (destination folder: "{folder}") (destination server "{destination_server}") to property "{property}."')
					lconn.cur.execute('''INSERT INTO property_settings (property, ffmpeg_args, output_container, user_at_ip, folder) VALUES (?, ?, ?, ?, ?) ON CONFLICT(property) DO UPDATE SET ffmpeg_args = ?, output_container = ?, user_at_ip = ?, folder = ?;''', (property, ffmpeg_args, output_container, destination_server, folder, ffmpeg_args, output_container, destination_server, folder))
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


def shell(symbol: str):
	print('Starting shell.')
	commands: list[str] = []
	while True:
		# Shell
		c = input(symbol)
		if len(c) > 0:
			commands.append(c)
			if c == 'exit':
				break
			elif c == 'exec':
				print('Executing commands.')
				try:
					if command(commands[:-1]):
						print('All commands executed successfully.')
					else:
						print('Some commands did not execute successfully.')
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
	import signal

	from db import connect_to_db, create_tables, disconnect_from_db

	# Attach interrupt handler to shutdown gracefully
	signal.signal(signal.SIGINT, service_shutdown)
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	args: argparse.Namespace = parser.parse_args()
	if not connect_to_db():
		print('Something went wrong connecting to the DB. Exiting. (Error 2)')
		exit(2)
	print('Connected to DB.')
	if not create_tables():
		print('Something went wrong creating DB tables. Exiting. (Error 3)')
		exit(3)
	print('Tables created if not exist.')
	try:
		shell(args.shell)
	except ServiceExit:
		pass
	finally:
		if disconnect_from_db():
			print("Successfully disconnected from DB.")
		else:
			print("Error disconnecting from DB. Perhaps it is already disconnected?")
		print('Exiting')