"""Browser smoke tests against a local SQLite instance; NEVER use production credentials."""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # Invoked as tests/ui_smoke.py from the repository root.
BASE = "http://127.0.0.1:8001"
PASSWORD = "test-password-123"


def wait_until_ready(proc):
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError(f"Web server quit: {proc.returncode}")
        try:
            with urllib.request.urlopen(BASE + "/api/health", timeout=1) as r:
                if r.status == 200 and b'"status":"ok"' in r.read():
                    return
        except Exception:
            time.sleep(.2)
    raise TimeoutError("Local web server never became healthy")


def login(page, email, password=PASSWORD):
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    dialog = page.get_by_role("dialog")
    dialog.locator('input[name="email"]').fill(email)
    dialog.locator('input[name="password"]').fill(password)
    dialog.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.locator("header .site-user strong")).to_be_visible(timeout=15000)


def register_donor(page):
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    page.get_by_role("button", name="Chưa có tài khoản? Đăng ký đóng góp").click()
    dialog=page.get_by_role("dialog")
    dialog.locator('input[name="name"]').fill("Người góp thử nghiệm")
    dialog.locator('input[name="email"]').fill("donor-smoke@test.vn")
    dialog.locator('input[name="password"]').fill(PASSWORD)
    dialog.get_by_role("button", name="Tạo tài khoản", exact=True).click()
    expect(dialog.get_by_role("button", name="Đăng nhập", exact=True)).to_be_visible(timeout=15000)
    dialog.locator('input[name="email"]').fill("donor-smoke@test.vn")
    dialog.locator('input[name="password"]').fill(PASSWORD)
    dialog.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.locator("header .site-user strong")).to_contain_text("Người góp", timeout=15000)


def run():
    # Isolated database and trusted sample accounts. Never seed Supabase.
    with tempfile.TemporaryDirectory(prefix="aureva-browser-") as data_dir:
        env={**os.environ,"AUREVA_DB":str(Path(data_dir)/"test.db"),
             "AUREVA_ORIGIN":BASE,"AUREVA_SECURE_COOKIE":"0"}
        env.pop("DATABASE_URL",None)
        os.environ.update({"AUREVA_DB":env["AUREVA_DB"],"AUREVA_ORIGIN":BASE})
        os.environ.pop("DATABASE_URL",None)
        from backend import app as backend
        backend.DB_PATH=Path(env["AUREVA_DB"])
        backend.init_db()
        with backend.connect(write=True) as db:
            for role in ("manager","approver"):
                db.execute("INSERT INTO users VALUES(?,?,?,?,?)",
                           (role,role,role+"@test.vn",backend.password_hash(PASSWORD),role))
        proc=subprocess.Popen([sys.executable,"-m","uvicorn","backend.app:app",
                               "--host","127.0.0.1","--port","8001"],
                              cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        try:
            wait_until_ready(proc)
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                try:
                    manager=browser.new_context(viewport={"width":1440,"height":900},accept_downloads=True)
                    page=manager.new_page()
                    page.goto(BASE,wait_until="networkidle")
                    Path("work").mkdir(exist_ok=True)
                    page.screenshot(path="work/aureva-desktop.png",full_page=True)
                    expect(page.get_by_role("heading",name="Điều đẹp nhất là lòng tốt được đi đúng nơi.")).to_be_visible()
                    expect(page.get_by_role("heading",name="Cho đi bằng cả tấm lòng. Minh bạch bằng sự thật.")).to_be_visible()
                    page.get_by_role("navigation").get_by_role("button",name="Minh bạch").click()
                    expect(page.get_by_role("heading",name="Minh bạch không chỉ là một lời hứa.")).to_be_visible()
                    page.get_by_role("navigation").get_by_role("button",name="Chiến dịch").click()
                    expect(page.locator(".hero")).to_have_count(0)
                    page.get_by_role("navigation").get_by_role("button",name="Tổng quan công khai").click()
                    expect(page.locator(".hero")).to_be_visible()
                    login(page,"manager@test.vn")
                    page.get_by_role("navigation").get_by_role("button",name="Chiến dịch").click()
                    page.get_by_role("button",name="Tạo chiến dịch",exact=True).click()
                    dialog=page.get_by_role("dialog")
                    dialog.locator('input[name="title"]').fill("Cứu trợ Quảng Trị minh bạch")
                    dialog.locator('input[name="location"]').fill("Quảng Trị")
                    dialog.locator('textarea[name="description"]').fill("Góp sức hỗ trợ người dân bằng nhu yếu phẩm")
                    dialog.locator('input[name="amount"]').fill("1000000")
                    dialog.get_by_role("button",name="Lưu thông tin").click()
                    expect(page.get_by_role("heading",name="Cứu trợ Quảng Trị minh bạch")).to_be_visible(timeout=15000)
                    page.get_by_role("button",name="Xem chi tiết chiến dịch").click()
                    expect(page.get_by_role("heading",name="Lịch sử đóng góp công khai")).to_be_visible()
                    page.get_by_role("navigation").get_by_role("button",name="Không gian làm việc").click()
                    expect(page.get_by_role("heading",name="Bảng điều hành cứu trợ")).to_be_visible()
                    page.screenshot(path="work/aureva-workspace.png",full_page=True)
                    manager.close()
                    donor=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
                    mobile=donor.new_page()
                    mobile.goto(BASE,wait_until="networkidle")
                    expect(mobile.locator(".hero")).to_be_visible()
                    proof=mobile.evaluate("""() => {
                        const hero=document.querySelector('.hero').getBoundingClientRect();
                        const sheet=document.querySelector('.proof-visual-sheet').getBoundingClientRect();
                        return {heroBottom:hero.bottom,sheetBottom:sheet.bottom};
                    }""")
                    assert proof["sheetBottom"] <= proof["heroBottom"]+3, "Mobile proofboard is clipped by hero"
                    mobile.screenshot(path="work/aureva-mobile.png",full_page=True)
                    expect(mobile.get_by_role("navigation").get_by_role("button",name="Chiến dịch")).to_be_visible()
                    assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),"Horizontal overflow on mobile"
                    register_donor(mobile)
                    mobile.get_by_role("navigation").get_by_role("button",name="Chiến dịch").click()
                    expect(mobile.locator(".campaign").first).to_be_visible()
                    assert mobile.locator(".campaign").first.evaluate("(el) => getComputedStyle(el).opacity") == "1", "Campaign card should not be invisible before scroll"
                    mobile.get_by_role("button",name="Xem chi tiết chiến dịch").click()
                    mobile.get_by_role("button",name="Ghi nhận đóng góp").click()
                    dialog=mobile.get_by_role("dialog")
                    dialog.locator('input[name="amount"]').fill("200000")
                    dialog.locator('input[name="reference"]').fill("browser-test-001")
                    dialog.get_by_role("button",name="Lưu thông tin").click()
                    expect(mobile.get_by_text("chờ người phụ trách đối soát",exact=False)).to_be_visible(timeout=15000)
                    mobile.get_by_role("navigation").get_by_role("button",name="Không gian làm việc").click()
                    expect(mobile.get_by_role("heading",name="Hành trình đóng góp của bạn")).to_be_visible()
                    expect(mobile.get_by_role("button",name="Mở thu chi của chiến dịch")).to_be_visible()
                    donor.close()
                    print("Browser smoke: desktop navigation, manager login/create/detail, mobile layout, donor registration/login/donation PASSED")
                finally:
                    browser.close()
        finally:
            proc.terminate()
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:proc.kill()


if __name__=="__main__":
    run()
