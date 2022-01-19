import sqlite3
from typing import Optional

conn = None

def get_conn() -> Optional[sqlite3.Connection]:
	return conn

def connect_to_db() -> bool:
	'''Connect to `db.sqlite3`. Returns `True` on success and `False` otherwise'''
	global conn
	if not conn:
		conn = sqlite3.connect('db.sqlite3')
		return True
	return False

def create_tables() -> bool:
	if not conn:
		return False
	cur = conn.cursor()
	cur.execute('''CREATE TABLE IF NOT EXISTS properties (
		property TEXT,
		pattern TEXT,
		PRIMARY KEY (property)
	);''')
	cur.execute('''CREATE TABLE IF NOT EXISTS property_settings (
		property TEXT,
		ffmpeg_args TEXT,
		PRIMARY KEY (property),
		FOREIGN KEY (property) REFERENCES properties(property)		
	);''')
	conn.commit()
	return True

def disconnect_from_db() -> bool:
	'''Disconnect from `db.sqlite3`. Returns `True` on success, `False` otherwise'''
	global conn
	if conn:
		conn.close()
		conn = None
		return True
	return False