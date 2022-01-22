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
