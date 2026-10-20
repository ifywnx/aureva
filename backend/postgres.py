"""Small DB-API adapter; application queries remain parameterized on both databases."""
from decimal import Decimal
import psycopg
from psycopg.rows import dict_row
class Row(dict):
    def __init__(self,row):
        super().__init__((k,int(v) if isinstance(v,Decimal) and v==v.to_integral_value() else v) for k,v in row.items())
    def __getitem__(self,key):
        return list(self.values())[key] if isinstance(key,int) else super().__getitem__(key)
class Cursor:
    def __init__(self,cursor):self.cursor=cursor
    def fetchone(self):
        row=self.cursor.fetchone();return Row(row) if row is not None else None
    def fetchall(self):return [Row(row) for row in self.cursor.fetchall()]
    def __iter__(self):return iter(self.fetchall())
class Connection:
    def __init__(self,url,write=False):
        self.conn=psycopg.connect(url,connect_timeout=15,prepare_threshold=None,row_factory=dict_row)
        self.conn.execute('SET LOCAL search_path TO aureva')
        if write:self.conn.execute('SELECT pg_advisory_xact_lock(724201028)')
    def execute(self,sql,args=()):return Cursor(self.conn.execute(sql.replace('?','%s'),args))
    def commit(self):self.conn.commit()
    def rollback(self):self.conn.rollback()
    def close(self):self.conn.close()
