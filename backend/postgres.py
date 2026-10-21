"""Small DB-API adapter; application queries remain parameterized on both databases."""
import os
from decimal import Decimal
import psycopg
from backend.presentation import selected_schema
from psycopg.rows import dict_row
def bind_sqlite_parameters(sql: str) -> str:
    """Replace positional SQLite ? bind markers only outside SQL literals/comments.

    Our public campaign SELECT embeds a literal '/cover?v=' URL. Blindly
    replacing all '?' turns that URL into a fake psycopg %s placeholder and
    makes every dashboard request fail even when Postgres is healthy.
    """
    out = []
    i = 0
    state = "code"
    while i < len(sql):
        ch = sql[i]
        pair = sql[i:i+2]
        if state == "code":
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif pair == "--":
                state = "line_comment"
                out.append(pair)
                i += 2
                continue
            elif pair == "/*":
                state = "block_comment"
                out.append(pair)
                i += 2
                continue
            elif ch == "?":
                out.append("%s")
                i += 1
                continue
        elif state in ("single", "double"):
            closing = "'" if state == "single" else '"'
            if ch == closing:
                if sql[i+1:i+2] == closing:
                    out.append(ch + closing)
                    i += 2
                    continue
                state = "code"
        elif state == "line_comment":
            if ch == "\n":
                state = "code"
        elif state == "block_comment" and pair == "*/":
            out.append(pair)
            i += 2
            state = "code"
            continue
        out.append(ch)
        i += 1
    return "".join(out)

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
        schema=selected_schema() or os.getenv('AUREVA_DB_SCHEMA','aureva')
        if schema not in ('aureva','aureva_preview','aureva_presentation'):
            self.conn.close()
            raise ValueError('Unsupported AUREVA database schema')
        # Transaction-local search path: no cross-request schema leakage with a pooler.
        self.conn.execute("SELECT pg_catalog.set_config('search_path', %s, true)", (schema,))
        if write:
            lock_id={'aureva':724201028,'aureva_preview':724201029,'aureva_presentation':724201030}[schema]
            self.conn.execute('SELECT pg_advisory_xact_lock(%s)',(lock_id,))
    def execute(self,sql,args=()):return Cursor(self.conn.execute(bind_sqlite_parameters(sql),args))
    def commit(self):self.conn.commit()
    def rollback(self):self.conn.rollback()
    def close(self):self.conn.close()
