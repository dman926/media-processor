import shlex

from db import get_conn

def yn(say: str) -> bool:
	yn = input(say + 'Continue? (y/n)').lower()
	return yn == 'y' or yn == 'e' or yn == 's'

def command(commands: list[str]) -> bool:
	conn = get_conn()
	if not conn:
		return False
	cur = conn.cursor()
	for c in commands:
		split: list[str] = [a.strip() for a in shlex.split(c)]
		if split[0] == 'commit':
			print('Committing to DB.')
			conn.commit()
		elif split[0] == 'vacuum':
			print('Clearing space in DB.')
			conn.execute('''VACUUM;''')
		elif split[0] == 'add' or split[0] == '':
			if split[1] == 'property':
				property = split[2]
				pattern = split[3]
				print(f'Adding property "{property}" with pattern "{pattern}"')
				cur.execute('''INSERT INTO properties (property, pattern) VALUES (?, ?) ON DUPLICATE KEY UPDATE pattern = ?;''', (property, pattern, pattern))
			elif split[1] == 'setting':
				property = split[2]
				ffmpeg_args = split[3]
				output_container = split[4]
				folder = split[5]
				print(f'Adding settings (ffmpeg_args: "{ffmpeg_args}") (output_container: "{output_container}") (folder: "{folder}") to property {property}')
				cur.execute('''INSERT INTO property_settings (property, ffmpeg_args, output_container, folder) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE ffmpeg_args = ?, output_container = ?, folder = ?;''', (property, ffmpeg_args, output_container, folder, ffmpeg_args, output_container, folder))
			else:
				if not yn(f'[{split[1]}] is not a valid `add` command and it will be ignored. '):
					break
		elif split[0] == 'remove':
			if split[1] == 'property':
				property = split[2]
				print(f'Removing property {property}')
				cur.execute('''DELETE FROM properties WHERE property = ?;''', (property,))
			elif c[:15] == 'setting':
				property = split[2]
				print(f'Removing settings from {property}')
				cur.execute('''DELETE FROM property_settings WHERE property = ?;''', (property,))
			else:
				if not yn(f'[{split[1]}] is not a valid `remove` command and it will be ignored. '):
					break
		elif split[0] == 'reset':
			if split[1] == 'db':
				print('Removing all data.')
				cur.execute('''DELETE FROM property_settings;''')
				cur.execute('''DELETE FROM properties;''')
			elif split[1] == 'properties':
				print('Removing all data in `properties`.')
				cur.execute('''DELETE FROM properties;''')
			elif split[1] == 'patterns':
				print('Removing all data in `settings`.')
				cur.execute('''DELETE FROM property_settings;''')
		else:
			if not yn(f'[{c}] is not a valid command and it will be ignored. '):
				break
	cur.close()
	return True

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