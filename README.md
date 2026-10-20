# AUREVA

**Xây dựng nền tảng minh bạch hóa hoạt động quyên góp cứu trợ ứng dụng AI và Blockchain.**

Trao gửi yêu thương, rõ từng đóng góp.

Ứng dụng độc lập, không phụ thuộc Sites/hosting ChatGPT. Frontend React + TypeScript + Vite; API FastAPI; dữ liệu SQLite lưu tại `data/aureva.db`. Khung công nghệ tham khảo ReliefChain/AapdaSetu; nghiệp vụ và giao diện AUREVA được viết riêng. Repo tham khảo không được nhúng vào dự án này.

## Chạy trên Mac

```sh
cd /Users/macm1/Documents/Codex/AUREVA
./scripts/start.sh
```

Mở http://127.0.0.1:8001 — API docs: http://127.0.0.1:8001/docs.

Tài khoản local đã tạo nằm trong `data/local-accounts.txt` (chỉ chủ máy được đọc, đã ignore khỏi Git). Có 3 vai trò; không có số tiền, chiến dịch hay giao dịch mẫu được nạp sẵn. Mật khẩu được hash bằng scrypt; cookie phiên HttpOnly, SameSite=Strict, hết hạn sau 8 giờ. Phiên lưu trong database, logout thu hồi phiên.

Tạo thêm tài khoản do người quản trị cấp:

```sh
.venv/bin/python scripts/accounts.py --email manager@example.com --name 'Người phụ trách' --role manager
```

Công cụ hỏi mật khẩu tương tác. Người dùng đăng ký qua website chỉ nhận quyền donor; không thể tự chọn manager/approver.

## Luồng sử dụng

1. Đăng nhập manager, tạo chiến dịch và mục tiêu VND.
2. Đăng nhập donor, mở chiến dịch, ghi nhận khoản đóng góp và mã tham chiếu. Đây không phải cổng thanh toán; tiền chưa được tính vào tổng.
3. Manager vào Không gian làm việc, kiểm tra tiền thực nhận rồi xác nhận đóng góp. Chỉ người phụ trách đúng chiến dịch được đối soát.
4. Manager đề xuất khoản chi, người nhận tiền và mục đích.
5. Approver xem khoản chi, ghi lý do và duyệt/từ chối. Server cấm tự duyệt, quyết định lặp lại và chi vượt số dư.
6. Trang công khai tự tính tổng đóng góp đã đối soát, chi đã duyệt và số dư từ SQLite. Không hiển thị email người đóng góp hay mã chuyển khoản.

Hiện tại “chi đã duyệt” là quyết định phân bổ tiền, chưa chứng minh đã thực chi/chuyển tiền. Việc xác nhận đóng góp là thủ công. Không dùng các tổng này để tuyên bố đã giải ngân ngân hàng.

## Kiểm tra và build

```sh
.venv/bin/python -m pytest -q
cd frontend
npm ci
npm run build
```

Sau build, khởi động lại backend để phục vụ frontend. Khi cài mới: `uv venv --python 3.12 .venv`, rồi `uv pip install --python .venv/bin/python -r requirements.lock.txt`.

## Đã có / còn thiếu

Đã có: auth, phân quyền server, phạm vi chiến dịch theo người phụ trách, ledger đóng góp/chi VND nguyên, audit log, dashboard database, kiểm tra số dư trong transaction SQLite, kiểm thử quyền và persistence ở tiến trình Python mới.

Chưa có: upload hóa đơn; AI trích xuất và phát hiện bất thường; giao dịch testnet, hash báo cáo; PDF; phục hồi mật khẩu/email verification; đóng chiến dịch; điều chỉnh giao dịch; phân quyền reviewer theo tổ chức. Tích hợp AI và Blockchain trả trạng thái `not_configured`, không tạo kết quả/hashes giả.

Chỉ chạy loopback để phát triển. Trước deploy: HTTPS + `AUREVA_SECURE_COOKIE=1`, cấu hình `AUREVA_ORIGIN`, giới hạn request toàn hệ thống, backup, nâng cấp dependency, kiểm thử đồng thời và chính sách dữ liệu cá nhân. SQLite cần ổ đĩa persistent, không dùng filesystem tạm của serverless. Schema v1 được init idempotent; các thay đổi schema sau này cần migration versioned.

Không commit `data/`, `.env`, khóa API hoặc private key. AI sẽ cần API đọc ảnh/PDF; Blockchain cần RPC Sepolia và ví testnet riêng khi triển khai giai đoạn sau.

## Production (16/10/2026)

URL: https://aureva-sigma.vercel.app

Vercel project `aureva` (prj_UANELTCR2vVS32Vsl9yXpBFlz3WK). Supabase project `aureva` (epwojwlsibjmxhdbtsqu), hoàn toàn tách khỏi các project khác. PostgreSQL schema `aureva` không công khai qua Data API; backend dùng role riêng, không dùng superuser. File hóa đơn và PDF hiện lưu BYTEA trong database, tối đa 2 MB mỗi chứng từ.

Phiên bản này đã bổ sung upload chứng từ riêng tư, gọi OpenAI Responses API qua khóa API server-side, cảnh báo chênh lệch số tiền/trùng file/trùng số hóa đơn, yêu cầu phân tích trước khi duyệt, snapshot quyết định, báo cáo PDF tiếng Việt bất biến, kiểm tra SHA-256 trên trình duyệt, outbox giao dịch Sepolia và smart contract registry. Các mô tả “chưa có” ở mục phiên bản 0.1 bên trên được thay thế bởi mục này.

AI và Blockchain CHƯA được kiểm chứng với dịch vụ thật khi chưa có cấu hình. Điền `.env`: OPENAI_API_KEY, OPENAI_MODEL (mặc định gpt-5-mini), SEPOLIA_RPC_URL, BLOCKCHAIN_PRIVATE_KEY (ví riêng chỉ dùng testnet), AUREVA_CONTRACT_ADDRESS. Sau đó cấu hình tương ứng lên Vercel bằng stdin; không commit hoặc in secrets. Compile contract: `npm --prefix blockchain ci && npm --prefix blockchain run build`; triển khai bằng `.venv/bin/python scripts/deploy_contract.py` sau khi có test ETH. Backend chỉ cho chain ID 11155111.

Các tài khoản đã tạo tại `data/local-accounts.txt` dùng được trên production. Không chia sẻ file này công khai. `.env.deploy` chứa credential PostgreSQL riêng và bị ignore. Chưa có dữ liệu tài chính giả được seed lên production.

Deploy: `npx vercel@64.3.1 deploy --prod --scope team_0RXiQnJ9tD3DZBTSLMAiFShM`. Phải giữ AUREVA_ORIGIN=https://aureva-sigma.vercel.app, AUREVA_SECURE_COOKIE=1 và DATABASE_URL trong production. SQLite fallback bị cấm trên Vercel.
