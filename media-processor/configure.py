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
		split: list[str] = [c.strip() for c in shlex.split(c)]
		if split[0] == 'commit':
			print('Committing to DB.')
			conn.commit()
		elif split[0] == 'vacuum':
			print('Clearing space in DB.')
			conn.execute('''VACUUM;''')
		elif split[0] == 'add':
			if split[1] == 'property':
				property = split[2]
				print(f'Adding property {property}')
				cur.execute('''INSERT INTO properties (property) VALUES (?);''', (property,))
			elif split[1] == 'pattern':
				property = split[2]
				pattern = split[3]
				print(f'Adding pattern {pattern} to property {property}')
				cur.execute('''INSERT INTO patterns (property) VALUES (?, ?) ON DUPLICATE KEY UPDATE pattern = ?;''', (property, pattern, pattern))
			else:
				if not yn(f'[{split[1]}] is not a valid `add` command and it will be ignored. '):
					break
		elif split[0] == 'remove':
			if split[1] == 'property':
				property = split[2]
				print(f'Removing property {property}')
				cur.execute('''DELETE FROM properties WHERE property = ?;''', (property,))
			elif c[:15] == 'pattern':
				property = split[2]
				print(f'Removing pattern from {property}')
				cur.execute('''DELETE FROM patterns WHERE property = ?;''', (property,))
			else:
				if not yn(f'[{split[1]}] is not a valid `remove` command and it will be ignored. '):
					break
		elif split[0] == 'reset':
			if split[1] == 'db':
				print('Removing all data.')
				cur.execute('''DELETE FROM patterns;''')
				cur.execute('''DELETE FROM properties;''')
			elif split[1] == 'properties':
				print('Removing all data in `properties`.')
				cur.execute('''DELETE FROM properties;''')
			elif split[1] == 'patterns':
				print('Removing all data in `patterns`.')
				cur.execute('''DELETE FROM patterns;''')
		else:
			if not yn(f'[{c}] is not a valid command and it will be ignored. '):
				break
	return True

if __name__ == '__main__':
	import argparse
	from db import connect_to_db, create_tables, disconnect_from_db
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--shell', dest='shell', help='the shell symbol to use', default='$ ')
	args: argparse.Namespace = parser.parse_args()
	commands: list[str] = []
	if not connect_to_db():
		print('Something went wrong connecting to the DB. Exiting. (Error 2)')
		exit(2)
	print('Connected to DB.')
	if not create_tables():
		print('Something went wrong creating DB tables. Exiting. (Error 3)')
		exit(3)
	print('Tables created if not exist.')
	print('Starting shell.')
	while True:
		# Shell
		c = input(args.shell)
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
	if disconnect_from_db():
		print("Successfully disconnected from DB.")
	else:
		print("Error disconnecting from DB. Perhaps it is already disconnected?")
	print('Exiting')