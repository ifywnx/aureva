"""Safe administrative smoke checks and account provisioning for AUREVA Preview.

Never accepts or reuses a production PostgreSQL role. No simulated financial data.
Run only after setting DATABASE_URL in your local shell and AUREVA_DB_SCHEMA=aureva_preview.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def assert_preview_configuration():
    """Fail closed BEFORE connecting, even if someone mistakenly supplied production DSN."""
    from psycopg.conninfo import conninfo_to_dict

    if os.getenv("AUREVA_DB_SCHEMA") != "aureva_preview":
        raise RuntimeError("AUREVA_DB_SCHEMA phải bằng aureva_preview.")
    if os.getenv("AUREVA_DB"):
        raise RuntimeError("AUREVA_DB SQLite không được dùng trong công cụ Preview.")
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("Chưa có DATABASE_URL riêng cho Preview.")
    config = conninfo_to_dict(url)
    pg_user = (config.get("user") or "").split(".")[0]
    if pg_user != "aureva_preview_app":
        raise RuntimeError("Chỉ chấp nhận database role aureva_preview_app. Từ chối production.")
    if config.get("dbname", "postgres") != "postgres":
        raise RuntimeError("Database name phải là postgres của Supabase.")
    return url


def inspect_live_preview():
    assert_preview_configuration()
    from backend.app import connect

    with connect() as db:
        state = db.execute(
            "SELECT current_user AS username, current_schema() AS active_schema"
        ).fetchone()
        if state["username"] != "aureva_preview_app":
            raise RuntimeError("Kết nối không sử dụng tài khoản Preview được cấp riêng.")
        if state["active_schema"] != "aureva_preview":
            raise RuntimeError("Không được kết nối sang schema ngoài Preview.")
        count = db.execute(
            "SELECT count(*) AS count FROM information_schema.tables "
            "WHERE table_schema='aureva_preview' AND table_type='BASE TABLE'"
        ).fetchone()["count"]
        if count != 11:
            raise RuntimeError(f"Preview phải có 11 bảng; thực tế: {count}.")
        # An actual table query tests permissions and search_path without writing rows.
        db.execute("SELECT count(*) AS count FROM users").fetchone()
    return True


def create_preview_user(email, name, role):
    if role not in ("manager", "approver"):
        raise ValueError("Chỉ cho phép tạo manager hoặc approver trong công cụ này.")
    email = email.strip().lower()
    name = name.strip()
    if "@" not in email or "." not in email.split("@")[-1] or not 3 <= len(email) <= 254:
        raise ValueError("Email không hợp lệ.")
    if not 2 <= len(name) <= 100:
        raise ValueError("Tên cần 2–100 ký tự.")
    inspect_live_preview()
    password = getpass.getpass("Mật khẩu đăng nhập website (>= 10 ký tự): ")
    if not 10 <= len(password) <= 128:
        raise ValueError("Mật khẩu phải có 10–128 ký tự.")
    from backend.app import connect, password_hash, uid
    with connect(write=True) as db:
        db.execute("INSERT INTO users(id,name,email,password,role) VALUES(?,?,?,?,?)",
                   (uid(), name, email, password_hash(password), role))
    print(f"Đã tạo tài khoản Preview: {email} ({role}). Không lưu mật khẩu vào file.")


def main():
    parser = argparse.ArgumentParser(description="AUREVA Preview tools. Never accesses production.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Kiểm tra quyền Preview + kết nối PostgreSQL + 11 bảng")
    create = sub.add_parser("create-user", help="Cấp tài khoản quản lý/phê duyệt cho nhóm")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", required=True, choices=("manager", "approver"))
    args = parser.parse_args()
    try:
        if args.command == "check":
            inspect_live_preview()
            print("Preview PostgreSQL: CONNECTED, schema cô lập và 11 bảng đều truy cập được.")
        else:
            create_preview_user(args.email, args.name, args.role)
    except Exception as error:
        print(f"Preview không sẵn sàng: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
