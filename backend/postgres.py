"""Small DB-API adapter; application queries remain parameterized on both databases."""
import os
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
        schema=os.getenv('AUREVA_DB_SCHEMA','aureva')
        if schema not in ('aureva','aureva_preview'):
            self.conn.close()
            raise ValueError('AUREVA_DB_SCHEMA must be aureva or aureva_preview')
        # Transaction-local search path: no cross-request schema leakage with a pooler.
        self.conn.execute("SELECT pg_catalog.set_config('search_path', %s, true)", (schema,))
        if write:
            lock_id=724201029 if schema=='aureva_preview' else 724201028
            self.conn.execute('SELECT pg_advisory_xact_lock(%s)',(lock_id,))
    def execute(self,sql,args=()):return Cursor(self.conn.execute(sql.replace('?','%s'),args))
    def commit(self):self.conn.commit()
    def rollback(self):self.conn.rollback()
    def close(self):self.conn.close()
