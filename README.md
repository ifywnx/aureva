# AUREVA — Trao gửi yêu thương, rõ từng đóng góp.

**Tên đề tài:** AUREVA – Xây dựng nền tảng minh bạch hóa hoạt động quyên góp cứu trợ ứng dụng AI và Blockchain.

Đồ án cuối kỳ **Web Nâng Cao**, báo cáo **28/10/2026** (5–7 phút), với giao diện tiếng Việt, nghiệp vụ cứu trợ và dấu xác minh dữ liệu công khai.

> **Giới hạn trung thực:** Đây là nền tảng ghi nhận/đối soát khoản quyên góp và chứng thực *quyết định, báo cáo*. AUREVA hiện **không** chuyển tiền qua blockchain, không xác nhận giao dịch ngân hàng tự động, không xác nhận hóa đơn là hợp pháp. AI chỉ gợi ý cảnh báo; người có thẩm quyền ra quyết định. Tên chiến dịch và số tiền demo phải được ghi rõ là dữ liệu thử.

## Công nghệ

- Frontend: React 18, TypeScript, Vite, Framer Motion, Lucide.
- Backend: FastAPI, Pydantic, Python 3.12.
- Persistence: PostgreSQL (Supabase ở bản hosted) hoặc SQLite trên volume bền vững khi phát triển.
- AI: **OpenAI Responses API**, đọc JPG/PNG/PDF và trả JSON có cấu trúc; không dùng kết quả lập sẵn khi thiếu key.
- Blockchain: smart contract `AurevaRegistry.sol` trên **Ethereum Sepolia** (chain ID 11155111), ghi SHA-256 của bản chốt; có thể ký bằng MetaMask.
- PDF: ReportLab; báo cáo chốt cố định và kiểm tra SHA-256 trong trình duyệt.

## Nghiệp vụ đã được lập trình

1. Donor đăng ký, đăng nhập, ghi nhận thông tin đóng góp. Khoản tiền chỉ tính vào quỹ sau khi manager **đối soát thủ công**.
2. Manager tạo chiến dịch, thay ảnh bìa, xem số liệu, đối soát đóng góp, đề xuất khoản chi và tải chứng từ.
3. Manager nhấn phân tích AI: hệ thống đọc chứng từ và đối chiếu tổng tiền, nhà cung cấp, số hóa đơn, hash file/trùng lặp.
4. Approver duyệt hoặc từ chối với lý do. Khi **duyệt một hồ sơ có cảnh báo**, backend bắt buộc xác nhận đã kiểm tra cảnh báo và giải trình đủ dài; nội dung được đưa vào bản ghi SHA-256.
5. Quyết định sinh ra bản ghi `attestation` ở trạng thái `pending`. Chỉ sau khi giao dịch Sepolia hợp lệ và đủ xác nhận mới mang trạng thái `confirmed`. Người xem có thể kiểm tra trực tiếp hợp đồng.
6. Dashboard đọc tổng từ database. PDF tạo từ snapshot cố định; người xem tải file và kiểm tra SHA-256.
7. Manager có thể **kết thúc chiến dịch** khi không còn đóng góp/khoản chi chờ xử lý. Sự kiện đóng được lưu trong audit log. Không mở nhận tiền hoặc khoản chi mới sau khi đóng; báo cáo cũ vẫn truy cập được.

Các vai trò `donor`, `manager`, `approver` được kiểm tra tại server. Đăng ký tự phục vụ luôn tạo `donor`. Không có số tiền quyên góp mẫu nào được tự động seed thành dữ liệu thật.

## Chạy trên MacBook / local

```bash
git clone https://github.com/ifywnx/aureva.git
cd aureva
git switch feat/premium-motion-ui-20261020
# Cài Python 3.12, Node 22+ và uv nếu máy chưa có.
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
cp .env.example .env
npm --prefix frontend ci
npm --prefix frontend run build
./scripts/start.sh
```

Mở **http://127.0.0.1:8001** và API docs **http://127.0.0.1:8001/docs**. Trong local, SQLite mặc định được lưu tại `data/aureva.db` (không commit).

Tài khoản manager/approver phải được cấp thủ công (không cho người dùng tự nhận quyền):

```bash
.venv/bin/python scripts/accounts.py --email manager@example.com --name 'Người phụ trách' --role manager
.venv/bin/python scripts/accounts.py --email reviewer@example.com --name 'Người phê duyệt' --role approver
```

**Không dùng mật khẩu ví dụ làm mật khẩu thật.** Script hỏi mật khẩu qua terminal. Các file trong `data/` được bỏ qua khỏi Git.

## Cấu hình tích hợp

Sử dụng `.env.example` làm mẫu, nhưng chỉ đặt secrets trong `.env` local hoặc trong **encrypted environment variables** của Vercel/Railway:

| Tên biến | Mục đích |
|---|---|
| `OPENAI_API_KEY` | Đọc hóa đơn bằng OpenAI và chatbot |
| `OPENAI_MODEL` | Model thị giác/Structured Outputs, mặc định `gpt-5-mini` |
| `DATABASE_URL` | PostgreSQL bền vững, bắt buộc trên Vercel |
| `AUREVA_DB_SCHEMA` | `aureva` hoặc `aureva_preview` |
| `AUREVA_ORIGIN` | HTTPS origin khớp chính xác môi trường chạy |
| `AUREVA_SECURE_COOKIE` | `1` khi dùng HTTPS |
| `SEPOLIA_RPC_URL` | Ethereum Sepolia RPC |
| `AUREVA_CONTRACT_ADDRESS` | Hợp đồng đã triển khai |
| `BLOCKCHAIN_PRIVATE_KEY` | **Không bắt buộc** khi ký qua MetaMask |
| `AUREVA_DEMO_SWITCH` | Chỉ bật trong protected Preview có DB cô lập |

Tuyệt đối không đưa API key, password kết nối database, private key, seed phrase lên GitHub, frontend hoặc trong báo cáo.

Chi tiết: [OPENAI_INTEGRATION.md](OPENAI_INTEGRATION.md), [PREVIEW_DATABASE_SETUP.md](PREVIEW_DATABASE_SETUP.md), [RAILWAY.md](RAILWAY.md).

## Kiểm thử

```bash
.venv/bin/python -m pytest tests -q
npm --prefix frontend run build
# Tùy chọn: yêu cầu Playwright + Chromium
.venv/bin/python tests/ui_smoke.py
```

Workflow GitHub Actions: `.github/workflows/aureva-quality.yml` tự chạy test backend, build frontend và browser smoke trên **SQLite độc lập**. Kết quả CI tốt **không chứng minh** Vercel/Railway, OpenAI billable hay Sepolia thật đã chạy. Với release, bắt buộc kiểm tra thêm luồng live trên domain preview.

## Triển khai và demo 28/10

- **Preview an toàn:** cấu hình schema PostgreSQL `aureva_preview`, database role riêng, cookie secure, Vercel Deployment Protection, và (nếu cần) nút đổi vai trò demo chỉ trên Preview.
- **OpenAI thật:** dùng chứng từ thử đã che thông tin cá nhân, ví dụ số khai báo khác số trên hóa đơn; kiểm tra API response và cảnh báo không phải kết quả hardcode.
- **Blockchain thật:** deploy `AurevaRegistry.sol` bằng MetaMask testnet, cấu hình RPC/address, ghi một mã băm rồi đối chiếu TX ở [Sepolia Etherscan](https://sepolia.etherscan.io/).
- **Data bền vững:** tạo chiến dịch preview, tải lại, đăng nhập lại và kiểm tra sau redeploy.
- **Xuất báo cáo:** tạo PDF trên API, tải xuống, kiểm tra hash của PDF, ghi dấu báo cáo qua ví và xác minh trực tiếp.

Luồng chạy kiểm thử và trạng thái tích hợp được mô tả trong các mục trên; toàn bộ hoạt động live phải được xác minh trên domain staging trước khi đưa lên production.

## Trạng thái xác minh

Các tính năng lõi đã có unit/browser tests. Các bước **chưa thể tuyên bố hoàn thành** khi chưa có bằng chứng E2E: API OpenAI với hóa đơn thật, Sepolia transaction/receipt thật và bản deploy có PostgreSQL persistent kiểm tra sau restart.

PR đang phát triển: [#1](https://github.com/ifywnx/aureva/pull/1). Không merge hoặc promote lên production chỉ vì build thành công. Đồ án có tham khảo ý tưởng ReliefChain/AapdaSetu, nhưng thiết kế UX và nghiệp vụ AUREVA được phát triển riêng.
