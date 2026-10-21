# AUREVA – Chế độ thuyết trình dùng API, AI và Sepolia thật

Trong thời gian bật DEMO công khai, **mọi người chỉ cần mở https://aureva-sigma.vercel.app/** để vào bản AUREVA thật với ba vai trò.
Có thể mở trực tiếp **https://aureva-sigma.vercel.app/?demo=1**. Không cần mã khi bật `AUREVA_PUBLIC_DEMO=1`.
Vào xong, website tự tải giao diện AUREVA gốc, có thanh chuyển 3 tài khoản DEMO:
**Donor → Manager → Approver**. Đây là **tài khoản backend thử nghiệm thật**
trong schema PostgreSQL `aureva_presentation`, **không phải tài khoản Production**.

## Luồng trình diễn trên cùng website

1. Chuyển **Manager**; tạo chiến dịch, tên tự thêm `[DEMO]`.
2. Chuyển **Donor**; vào chiến dịch DEMO và khai báo số tiền **giả định**.
3. Chuyển **Manager**; đối soát xác nhận giả định, rồi đề xuất khoản chi.
4. Manager tải ảnh/PDF hóa đơn **thử nghiệm**; bấm **Phân tích AI**.
   Dữ liệu chứng từ được gửi tới nhà cung cấp AI phía server. Không có kết quả hardcode
   nếu khóa hết hạn, model không được cấp quyền, lỗi 403 hoặc AI trả dữ liệu sai.
5. Chuyển **Approver**; đọc kết quả và cảnh báo, nhập lý do, quyết định.
   Không được phê duyệt khoản chi vượt số tiền đã đối soát; cảnh báo bắt buộc xác nhận.
6. Tạo báo cáo PDF và dùng **MetaMask ví chủ hợp đồng** trên mạng Sepolia
   để ghi SHA-256 lên smart contract. Đợi xác nhận thực rồi kiểm tra ở Etherscan.

**Lưu ý quan trọng:** Sepolia là testnet. Chỉ TX và gas ETH thử nghiệm là có thật;
tiền đóng góp cứu trợ không được chuyển qua blockchain. Trong luồng này
khoản đóng góp và đối soát là dữ liệu DEMO do nhóm nhập, không phải chuyển tiền thật.

## Bảo mật và cô lập

- Website chính `/` không có đặc quyền 3 vai trò cho khách truy cập.
- Khách cùng nguồn được tự mở DEMO bằng `POST /api/demo/enter`. Server cấp cookie HttpOnly, Secure, SameSite=Strict có chữ ký
  HMAC, hết hạn sau **6 giờ**.
- Với cookie hợp lệ, *toàn bộ request* được route sang schema
  `aureva_presentation` bằng `ContextVar` + transaction-local
  PostgreSQL `search_path`. Không thay đổi `AUREVA_DB_SCHEMA` theo toàn tiến trình.
- Schema `aureva_presentation` có 11 bảng riêng, FK riêng, policy RLS dành
  cho backend. Schema chính `aureva` và schema Preview `aureva_preview`
  không bị dùng làm nơi lưu dữ liệu lớp học.
- **Thoát chế độ thuyết trình** xóa cookie quyền DEMO và cookie đăng nhập.
- PIN vẫn là cách truy cập dự phòng khi chế độ công khai tắt.
- Rate limit chuyển vai trò theo IP: 60 lần / 15 phút. Trần AI dùng chung trên DEMO: 24 lượt phân tích hóa đơn và 120 lượt chatbot / ngày UTC.
- Các tài khoản và hồ sơ trong chế độ thuyết trình **dùng chung** giữa những người xem: hãy sử dụng dữ liệu giả, không nhập thông tin nhạy cảm.
- Endpoint `/api/attestations/{id}/anchor` (ký bằng ví server) bị chặn trong DEMO công khai. Chỉ ký Sepolia qua MetaMask của ví chủ hợp đồng.
- Thanh chuyển nhanh tạo session chỉ cho 3 người dùng DEMO; không biến tài khoản
  thường thành Manager/Approver trên Production.
- Không ghi khóa API/DB/ví vào code hoặc `README`.

## Biến môi trường Vercel (chỉ Production)

| Biến | Mục đích |
|---|---|
| `DATABASE_URL` | Vẫn là chuỗi kết nối Production, được server route sang schema `aureva_presentation` khi xác thực DEMO |
| `AUREVA_PUBLIC_DEMO` | `1` khi thuyết trình công khai, `0` hoặc xóa khi tắt; **phải redeploy** để cấu hình hiệu lực |
| `AUREVA_PRESENTATION_CODE` | PIN dự phòng, Sensitive; không cần chia mã cho khán giả |
| `AUREVA_PRESENTATION_SIGNING_KEY` | Secret ít nhất 32 ký tự để ký cookie, Sensitive, **không chia cho nhóm** |
| `OPENAI_API_KEY`, `AI_BASE_URL`, `OPENAI_MODEL` | Nhà cung cấp AI thật, có quota/model đúng |
| `SEPOLIA_RPC_URL`, `AUREVA_CONTRACT_ADDRESS` | RPC và hợp đồng Sepolia thật |

Không tạo các biến PIN/signing key cho Preview. Preview vẫn có DEMO bảo vệ
bằng Deployment Protection như trước, dùng schema riêng `aureva_preview`.

**Tắt khi triển khai thật:** xóa hoặc đổi `AUREVA_PUBLIC_DEMO=0` trên Production rồi **redeploy**. Các cookie DEMO được cấp theo chế độ công khai sẽ tự mất hiệu lực do backend kiểm tra cờ này trên từng request. Nếu cần tắt cả chế độ PIN, xóa thêm `AUREVA_PRESENTATION_CODE` và `AUREVA_PRESENTATION_SIGNING_KEY` rồi redeploy. Chỉ ẩn nút bằng CSS là không đủ.

**Lưu ý:** Khách truy cập tên miền gốc được đưa thẳng vào DEMO khi bật public flag. Người quản trị muốn xem luồng Production bình thường có thể thoát chế độ DEMO hoặc dùng `/?site=1` (nhớ thoát chế độ để hủy cookie DEMO).

## Thiết lập database

SQL: `supabase/presentation_schema.sql`. Chạy một lần trên database dự án,
không copy dữ liệu Production. Verifying SQL:
```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='aureva_presentation';
SELECT has_schema_privilege('anon','aureva_presentation','USAGE');
SELECT has_schema_privilege('aureva_backend','aureva_presentation','USAGE');
```
Kết quả dự kiến: 11 bảng; false; true.

## Giới hạn và trách nhiệm thuyết trình

- Mỗi thành viên cần tự thử một quy trình qua API; tài khoản đổi chung theo vai trò,
  nên **mọi người có mã** đều có thể thay đổi dữ liệu của **chế độ thử nghiệm**.
- Không ghi thông tin cá nhân thật vào hóa đơn và yêu cầu AI.
- AI/Blockchain chỉ được coi là đã hoạt động khi API trả kết quả thành công /
  Sepolia có receipt + transaction hash thực; cấu hình key/RPC chưa đủ làm bằng chứng.
- Ký Sepolia cần ví chủ contract trên máy người trình bày và test ETH làm gas.
- Website có sandbox không dùng API ở `/?sandbox=1` (giữ để học offline).
  **Không dùng sandbox này làm bằng chứng AI hoặc Blockchain thật.**
