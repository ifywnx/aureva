"""Browser smoke tests against a local SQLite instance; NEVER use production credentials."""
import os
import json
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
                    # The public three-role sandbox must work without API access
                    # or writing a single record to the production database.
                    demo_requests = []
                    demo_tab = manager.new_page()
                    demo_tab.on("request", lambda req: demo_requests.append(req.url)
                                if "/api/" in req.url else None)
                    demo_tab.goto(BASE + "/?sandbox=1", wait_until="networkidle")
                    expect(demo_tab.get_by_role("heading", name="Thử đủ 3 vai trò. Hiểu trọn một quy trình.")).to_be_visible()
                    assert demo_tab.locator(".pd-role").count() == 3
                    demo_tab.locator(".pd-role").filter(has_text="Người đóng góp").click()
                    demo_tab.locator('.pd-inline input[name="amount"]').fill("500000")
                    demo_tab.get_by_role("button", name="Ghi nhận DEMO").click()
                    expect(demo_tab.locator(".pd-status.pending")).to_be_visible()
                    demo_tab.locator(".pd-role").filter(has_text="Người quản lý").click()
                    demo_tab.get_by_role("button", name="Xác nhận DEMO").click()
                    demo_tab.locator('input[name="purpose"]').fill("Mua gạo và mì gói")
                    demo_tab.locator('input[name="vendor"]').fill("Đơn vị mẫu")
                    demo_tab.locator('input[name="amount"]').last.fill("200000")
                    demo_tab.get_by_role("button", name="Gửi chờ phê duyệt").click()
                    demo_tab.get_by_role("button", name="Thêm chứng từ và đối chiếu").click()
                    demo_tab.locator('input[name="receipt"]').set_input_files({
                        "name": "hoa-don-demo.png", "mimeType": "image/png",
                        "buffer": b"local-test-only-image",
                    })
                    demo_tab.locator('input[name="invoiceTotal"]').fill("200000")
                    demo_tab.get_by_role("button", name="Đối chiếu mô phỏng").click()
                    demo_tab.locator(".pd-role").filter(has_text="Người phê duyệt").click()
                    demo_tab.locator(".pd-decision textarea").fill("Đã đối chiếu chứng từ mẫu; đồng ý phê duyệt.")
                    demo_tab.get_by_role("button", name="Phê duyệt DEMO").click()
                    expect(demo_tab.locator(".pd-status.approved")).to_be_visible(timeout=10000)
                    digest = demo_tab.locator(".pd-hash code").inner_text()
                    assert len(digest) == 64, "Local-only SHA-256 should have 64 hex characters"
                    assert not demo_requests, f"Public sandbox unexpectedly contacted API: {demo_requests}"
                    demo_tab.reload(wait_until="networkidle")
                    expect(demo_tab.locator(".pd-status.approved")).to_be_visible()
                    demo_tab.close()
                    # Public demo=1 now prompts for a server-issued classroom access
                    # cookie; it must NOT grant roles merely from a query parameter.
                    gate_tab=manager.new_page()
                    gate_tab.goto(BASE + "/?demo=1", wait_until="networkidle")
                    expect(gate_tab.get_by_label("Mã truy cập thuyết trình")).to_be_visible()
                    assert gate_tab.locator(".aureva-demo-bar").count()==0
                    gate_tab.close()
                    page.goto(BASE+'/?utm_source=external&ref=preserved#intro',wait_until="networkidle")
                    assert 'utm_source=' not in page.url, "Referral query should be removed from address bar"
                    assert '?ref=preserved#intro' in page.url, "Unrelated query and hash must remain untouched"
                    Path("work").mkdir(exist_ok=True)
                    page.screenshot(path="work/aureva-desktop.png",full_page=True)
                    # Assistive chatbot is prominent, accessible and driven by a genuine API contract.
                    page.route("**/api/public/assistant/chat",lambda route: route.fulfill(
                        status=200,content_type="application/json",body='{"reply":"Dữ liệu thật từ bảng công khai, không tự suy đoán.","model":"test-only","data_status":"connected","campaign_count":0}'))
                    page.get_by_role("button",name="Mở trợ lý AI AUREVA").click()
                    chat=page.get_by_role("dialog",name="Trợ lý AI AUREVA")
                    expect(chat.get_by_role("heading",name="AUREVA AI")).to_be_visible()
                    chat.get_by_role("button",name="Hiện có chiến dịch cứu trợ nào?").click()
                    expect(chat.get_by_text("Dữ liệu thật từ bảng công khai, không tự suy đoán.")).to_be_visible(timeout=15000)
                    expect(chat.get_by_text("Đã đọc dữ liệu công khai")).to_be_visible()
                    bubble_size=chat.locator(".aureva-chat-bubble").first.evaluate(
                        "(el)=>parseFloat(getComputedStyle(el).fontSize)")
                    assert bubble_size>=12, f"AI assistant text too small: {bubble_size}px"
                    chat.get_by_role("button",name="Thu nhỏ trợ lý").click()
                    expect(chat).to_have_count(0)
                    expect(page.get_by_role("heading",name="Lòng tốt xứng đáng được đặt đúng niềm tin.")).to_be_visible()
                    expect(page.get_by_role("heading",name="Một hành động tử tế. Một hành trình rõ ràng.")).to_be_visible()
                    assert page.locator(".journey-step").count()==6, "Expected six connected business stages"
                    page.get_by_role("button",name="Bước 04: AI kiểm tra").click()
                    expect(page.locator(".journey-focus h3")).to_have_text("AI kiểm tra")
                    expect(page.locator(".journey-focus .journey-proof-content")).to_contain_text("Mô tả nghiệp vụ")
                    page.get_by_role("button",name="Bước tiếp theo").click()
                    expect(page.locator(".journey-focus h3")).to_have_text("Duyệt hoặc từ chối")
                    page.get_by_role("button",name="Bước 01: Tạo chiến dịch").click()

                    expect(page.get_by_role("heading",name="Trao đi yêu thương. Rõ từng đóng góp.")).to_be_visible()
                    # Regression: old layers mixed DM Sans / Manrope / Newsreader.
                    # The current brand and Vietnamese UI must render with one family.
                    sample_selectors=[
                        ".brand-wordmark", ".brand-wordmark small",
                        ".site-nav button", ".site-user strong",
                        ".v5-hero h1", ".v5-hero h1 em",
                        ".journey-flow-heading h2", ".journey-step strong",
                        ".v5-stat strong", ".aureva-chat-toggle-copy strong",
                    ]
                    for selector in sample_selectors:
                        element=page.locator(selector).first
                        if element.count()==0:
                            # account label exists only after sign-in
                            assert selector==".site-user strong", f"Missing typography sample: {selector}"
                            continue
                        family=element.evaluate("(el)=>getComputedStyle(el).fontFamily").lower()
                        assert "be vietnam pro" in family, f"{selector} font mismatch: {family}"
                        assert not any(old in family for old in ("manrope","dm sans","newsreader")), (
                            f"{selector} still includes old legacy fonts: {family}"
                        )
                    nav_size=page.locator(".site-nav button").first.evaluate("(el)=>parseFloat(getComputedStyle(el).fontSize)")
                    assert nav_size>=11.0, f"Navigation font too small: {nav_size}px"
                    # Real Vietnam imagery rotates; active photo credits follow their scene.
                    photo=page.locator(".v5-hero-photo")
                    expect(photo.locator(".v5-hero-slide")).to_have_count(1)
                    expect(photo.locator(".v5-photo-country strong")).to_have_text("Trao đi sự tử tế.")
                    expect(photo.get_by_text("Duy Nguyen / Pexels",exact=False)).to_be_visible()
                    photo.get_by_role("button",name="Ảnh tiếp theo").click()
                    expect(photo.locator(".v5-photo-country strong")).to_have_text("Gắn kết cộng đồng.")
                    expect(photo.get_by_text("Ninh Tien Dat / Pexels",exact=False)).to_be_visible()
                    photo.get_by_role("button",name="Chọn ảnh 3: Từ những hành động nhỏ.").click()
                    expect(photo.locator(".v5-photo-country strong")).to_have_text("Từ những hành động nhỏ.")
                    photo.get_by_role("button",name="Tạm dừng tự chuyển ảnh").click()
                    expect(photo.get_by_role("button",name="Tiếp tục tự chuyển ảnh")).to_be_visible()
                    photo.get_by_role("button",name="Ảnh trước").click()
                    expect(photo.locator(".v5-photo-country strong")).to_have_text("Gắn kết cộng đồng.")
                    assert "không thuộc chiến dịch AUREVA" in photo.locator(".v5-photo-credit").inner_text()
                    primary_color=page.locator(".v5-hero-actions .btn.primary").evaluate("(el)=>getComputedStyle(el).backgroundColor")
                    assert primary_color=="rgb(255, 199, 131)", f"Primary CTA must use warm accent, got {primary_color}"
                    assert page.evaluate("""() => {
                        const tech=document.querySelector('.v5-tech-section');
                        const campaigns=document.querySelector('.campaign-section');
                        return tech && campaigns && !!(tech.compareDocumentPosition(campaigns) & Node.DOCUMENT_POSITION_FOLLOWING);
                    }"""), "When no campaigns exist, show the technology story before the empty campaign list"
                    expect(page.get_by_role("heading",name="Một luồng cứu trợ. Hai lớp kiểm chứng.")).to_be_visible()
                    expect(page.locator(".v5-proof-core")).to_be_visible()
                    assert page.locator(".v5-tech-features article").count()==3
                    assert page.locator(".v5-tech-features article").evaluate_all(
                        "(els)=>els.every(el=>getComputedStyle(el).opacity==='1')"
                    ), "AI, Blockchain and PDF cards must be visible before scrolling"
                    assert page.locator(".v5-proof-status").inner_text().find("Chưa cấu hình") >= 0, "CI must not fabricate live AI/chain configuration"
                    page.get_by_role("navigation").get_by_role("button",name="Minh bạch").click()
                    expect(page.get_by_role("heading",name="Minh bạch từ mỗi quyết định.")).to_be_visible()
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
                    # Confirm the standalone MetaMask deploy screen has no auto-sign.
                    wallet=browser.new_context(viewport={"width":1060,"height":860})
                    wallet.add_init_script("""(() => {
                        const listeners={};
                        window.ethereum={
                            request:async ({method,params})=>{
                                if(method==='eth_requestAccounts')return ['0x1111111111111111111111111111111111111111'];
                                if(method==='wallet_switchEthereumChain')return null;
                                if(method==='eth_chainId')return '0xaa36a7';
                                if(method==='eth_getBalance')return '0xb1a2bc2ec50000';
                                if(method==='eth_sendTransaction'){window.__walletSent=true;return '0x'+'a'.repeat(64)}
                                if(method==='eth_getTransactionReceipt')return {status:'0x1',contractAddress:'0x'+'b'.repeat(40)};
                                throw Error('Unexpected wallet request: '+method);
                            },
                            on:(name,cb)=>{listeners[name]=cb}
                        };
                    })()""")
                    wallet_page=wallet.new_page()
                    wallet_page.goto(BASE+'/deploy-sepolia.html?utm_source=external&keep=1#contract',wait_until='networkidle')
                    assert 'utm_source=' not in wallet_page.url
                    assert '?keep=1#contract' in wallet_page.url
                    expect(wallet_page.get_by_role('heading',name='Triển khai Blockchain. Không cần chia sẻ khóa ví.')).to_be_visible()
                    assert wallet_page.get_by_role('button',name='2. Deploy smart contract').is_disabled()
                    assert wallet_page.evaluate("!window.__walletSent"), 'Wallet signing must never start automatically'
                    wallet_page.get_by_role('button',name='1. Kết nối MetaMask').click()
                    expect(wallet_page.get_by_text('Ethereum Sepolia (11155111)')).to_be_visible()
                    assert wallet_page.get_by_role('button',name='2. Deploy smart contract').is_enabled()
                    wallet_page.get_by_role('button',name='2. Deploy smart contract').click()
                    expect(wallet_page.locator('#contract')).to_have_text('0x'+'b'*40,timeout=12000)
                    assert wallet_page.evaluate("window.__walletSent") is True
                    assert not ('alch_' in wallet_page.content()), 'Alchemy RPC key must not appear in browser HTML'
                    wallet.close()
                    manager.close()
                    # Demo switcher should be usable in one tap without credentials;
                    # provider/network responses are mocked only in the browser UI
                    # test, with server-side switching tested separately in SQLite.
                    demo_browser=browser.new_context(viewport={"width":1250,"height":850})
                    demonstration=demo_browser.new_page()
                    demonstration.route("**/api/demo/status",lambda route: route.fulfill(
                        status=200,content_type="application/json",body='{"enabled":true}'))
                    demonstration.route("**/api/workspace",lambda route: route.fulfill(
                        status=200,content_type="application/json",body='{"donations":[],"expenses":[]}'))
                    def fake_demo_switch(route):
                        role=route.request.post_data_json['role']
                        route.fulfill(status=200,content_type="application/json",
                            body=json.dumps({"id":"aureva_demo_"+role+"_v1","name":"DEMO · "+role,
                                             "email":"preview-"+role+"@aureva.invalid",
                                             "role":role,"demo":True}))
                    demonstration.route("**/api/demo/switch",fake_demo_switch)
                    demonstration.goto(BASE,wait_until="networkidle")
                    expect(demonstration.get_by_role("button",name="Đăng nhập",exact=True)).to_be_visible()
                    expect(demonstration.get_by_role("button",name="Đổi sang tài khoản demo Người phụ trách")).to_be_visible()
                    demo_family=demonstration.locator(".aureva-demo-role").first.evaluate("(el)=>getComputedStyle(el).fontFamily").lower()
                    assert "be vietnam pro" in demo_family and "manrope" not in demo_family, (
                        f"Demo bar still has mismatched typography: {demo_family}"
                    )
                    assert demonstration.locator(".aureva-demo-bar").evaluate(
                        "(el)=>{const r=el.getBoundingClientRect();return r.width<680 && r.height<105 && r.left>=0 && r.top>=0}"
                    ), "Demo toolbar must be compact, not a 246px-wide full-height sidebar"
                    demonstration.get_by_role("button",name="Đổi sang tài khoản demo Người phụ trách").click()
                    expect(demonstration.locator("header .site-user strong")).to_have_text("DEMO · manager")
                    expect(demonstration.get_by_role("heading",name="Bảng điều hành cứu trợ")).to_be_visible()
                    demonstration.get_by_role("button",name="Đổi sang tài khoản demo Người đóng góp").click()
                    expect(demonstration.locator("header .site-user strong")).to_have_text("DEMO · donor")
                    demonstration.get_by_role("button",name="Đổi sang tài khoản demo Người phê duyệt").click()
                    expect(demonstration.locator("header .site-user strong")).to_have_text("DEMO · approver")
                    demo_browser.close()
                    offline=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
                    unavailable=offline.new_page()
                    unavailable.route("**/api/public/dashboard",lambda route: route.fulfill(
                        status=503,content_type="application/json",
                        body='{"detail":"Không thể kết nối database thử nghiệm"}'))
                    unavailable.goto(BASE,wait_until="networkidle")
                    expect(unavailable.get_by_role("heading",name="Chưa kết nối được dữ liệu công khai")).to_be_visible()
                    expect(unavailable.get_by_role("button",name="Thử kết nối lại")).to_be_visible()
                    expect(unavailable.get_by_role("heading",name="Một hành động tử tế. Một hành trình rõ ràng.")).to_be_visible()
                    offline.close()
                    donor=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
                    mobile=donor.new_page()
                    mobile.route("**/api/demo/status",lambda route: route.fulfill(
                        status=200,content_type="application/json",body='{"enabled":true}'))
                    mobile.goto(BASE,wait_until="networkidle")
                    expect(mobile.get_by_role("button",name="Đổi sang tài khoản demo Người phê duyệt")).to_be_visible()
                    assert mobile.locator(".aureva-demo-bar").evaluate("(el)=>el.getBoundingClientRect().right <= window.innerWidth + 2 && el.getBoundingClientRect().left >= -2"), "Mobile demo switcher must fit viewport"
                    mobile.get_by_role("button",name="Mở trợ lý AI AUREVA").click()
                    mobile_chat=mobile.get_by_role("dialog",name="Trợ lý AI AUREVA")
                    expect(mobile_chat).to_be_visible()
                    assert mobile_chat.evaluate("(el) => el.getBoundingClientRect().right <= window.innerWidth + 2 && el.getBoundingClientRect().left >= -2"), "Chat window must fit a mobile viewport"
                    mobile_chat.get_by_role("button",name="Thu nhỏ trợ lý").click()
                    expect(mobile.locator(".hero")).to_be_visible()
                    expect(mobile.locator(".v5-hero-photo")).to_be_visible()
                    photo_mobile=mobile.locator(".v5-hero-photo")
                    assert photo_mobile.get_by_role("button",name="Ảnh tiếp theo").evaluate(
                        "(el)=>el.getBoundingClientRect().right <= window.innerWidth + 2"
                    ), "Hero carousel controls must fit within the mobile viewport"
                    photo_mobile.get_by_role("button",name="Ảnh tiếp theo").click()
                    expect(photo_mobile.locator(".v5-photo-country strong")).to_have_text("Gắn kết cộng đồng.")
                    expect(mobile.locator(".journey-flow")).to_be_visible()
                    mobile.get_by_role("button",name="Bước 06: Công khai & xác thực").click()
                    expect(mobile.locator(".journey-focus h3")).to_have_text("Công khai & xác thực")
                    assert mobile.locator(".journey-line").evaluate("(el)=>el.scrollWidth>el.clientWidth"), "Mobile journey should be swipeable"

                    assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"), "Homepage has horizontal overflow"
                    mobile.screenshot(path="work/aureva-mobile.png",full_page=True)
                    assert mobile.locator(".v5-hero-actions .btn").count()==2
                    assert mobile.locator(".v5-hero-actions .btn").first.evaluate("""el => {
                        const buttons=el.parentElement.querySelectorAll('button');
                        const b1=buttons[0].getBoundingClientRect(), b2=buttons[1].getBoundingClientRect();
                        return b2.top>b1.bottom && Math.abs(b1.width-b2.width)<3;
                    }"""), "Mobile hero CTAs should be stacked with equal widths"
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
