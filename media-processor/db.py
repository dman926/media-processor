import sqlite3

conn = None

def connect_to_db() -> bool:
	'''Connect to `db.sqlite3`. Returns `True` on success and `False` otherwise'''
	global conn
	if not conn:
		conn = sqlite3.connect('db.sqlite3')
		return True
	return False

def disconnect_from_db() -> bool:
	'''Disconnect from `db.sqlite3`. Returns `True` on success, `False` otherwise'''
	global conn
	if conn:
		conn.close()
		conn = None
		return True
	return False