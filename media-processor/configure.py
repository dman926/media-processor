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
			if split[1] == 'propery':
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