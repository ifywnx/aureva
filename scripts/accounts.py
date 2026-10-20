"""Local administration; never exposed as an HTTP endpoint."""
import sys, argparse, getpass
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import init_db,connect,password_hash,uid
p=argparse.ArgumentParser()
p.add_argument('--email',required=True)
p.add_argument('--name',required=True)
p.add_argument('--role',choices=['donor','manager','approver'],required=True)
a=p.parse_args()
password=getpass.getpass('Mật khẩu (ít nhất 10 ký tự): ')
if len(password)<10: raise SystemExit('Mật khẩu quá ngắn')
init_db()
with connect(write=True) as db:
    db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid(),a.name,a.email.lower(),password_hash(password),a.role))
print('Đã tạo tài khoản:',a.email,a.role)
