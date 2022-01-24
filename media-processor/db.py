from sqlite3 import connect
from threading import Lock


class LockableSqliteConn(object):
	def __init__(self, db: str):
		self.lock = Lock()
		self.conn = connect(db, check_same_thread=False)
		self.cur = None

	def __del__(self):
		self.conn.close()
	
	def __enter__(self):
		self.lock.acquire()
		self.cur = self.conn.cursor()
		return self
	
	def __exit__(self, type, value, traceback):
		if self.cur is not None:
			self.cur.close()
			self.cur = None
		self.lock.release()

def create_tables(lconn: LockableSqliteConn) -> None:
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
			is_show INT(1),
			season_override INT(2),
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