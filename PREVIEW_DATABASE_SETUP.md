# AUREVA – Preview database riêng trong cùng dự án Supabase

Cập nhật: 20/10/2026

## Đã triển khai

- Supabase project: `aureva` (`epwojwlsibjmxhdbtsqu`), khu vực Singapore.
- Schema ứng dụng production: `aureva` — giữ nguyên.
- Schema môi trường thử: `aureva_preview` — được tạo riêng, đầy đủ 11 bảng (users, sessions, attempts, campaigns, campaign_covers, donations, expenses, audit, documents, attestations, reports).
- Vai trò `aureva_preview_app` chỉ được cấp quyền truy cập vào schema `aureva_preview`, không có USAGE hoặc SELECT trên schema `aureva`. RLS bật cho toàn bộ bảng, có policy dành riêng cho role preview.
- `backend/postgres.py` dùng `AUREVA_DB_SCHEMA`: mặc định `aureva`, chỉ cho phép giá trị `aureva` hoặc `aureva_preview`. Advisory write lock cho Preview khác với production.
- Vercel preview-only env: `AUREVA_DB_SCHEMA=aureva_preview`, `AUREVA_SECURE_COOKIE=1`; biến production không bị sửa.
- `backend/app.py` chấp nhận Origin cùng hostname HTTPS thuộc `.vercel.app` **chỉ khi** schema preview được kích hoạt.

## Bước thủ công bắt buộc còn thiếu: cấp mật khẩu kết nối database

Bước cấu hình thông tin đăng nhập tự động giữa Supabase và Vercel bị hệ thống bảo vệ secrets từ chối; **không sử dụng lại DATABASE_URL production**. Role `aureva_preview_app` hiện chưa bật LOGIN nên không thể đăng nhập cho đến khi thiết lập mật khẩu.

### A. Trong Supabase SQL Editor của dự án `aureva`

Chọn một mật khẩu dài, ngẫu nhiên, **không gửi cho AI/chat và không commit**. Chạy trong SQL Editor:

```sql
ALTER ROLE aureva_preview_app WITH LOGIN PASSWORD 'THAY_BANG_MAT_KHAU_NGAU_NHIEN_RIENG';
```

Kiểm tra role `aureva_preview_app` có LOGIN, schema `aureva_preview` có 11 bảng.

### B. Trong Vercel – Settings → Environment Variables

Tạo biến `DATABASE_URL` cho **Preview**, loại `Sensitive` hoặc `Encrypted`, KHÔNG chọn Production.

Lấy **connection string Session pooler** trực tiếp từ Supabase Dashboard → Connect của dự án `aureva`. Thay username trong chuỗi kết nối bằng role `aureva_preview_app` (trong pooler thường là `aureva_preview_app.<project-ref>`) và password riêng ở bước A. Không dùng URL chứa role `postgres` hoặc production app user cho Preview.

Có thể dùng direct connection nếu runtime hỗ trợ IPv6, nhưng Vercel thường phù hợp hơn với Session pooler. Chỉ lấy pooler hostname và port từ **dashboard thực tế**, không đoán hostname.

Không cần tạo biến `OPENAI_API_KEY`/Sepolia để xác nhận DB; bổ sung sau.

### C. Redeploy và kiểm thử

Deploy lại feature branch `feat/premium-motion-ui-20261020` lên Preview để Vercel nạp biến môi trường vừa thêm.

Kiểm tra:

- `GET /api/health`: HTTP 200, `database=postgresql`.
- `GET /api/public/dashboard`: HTTP 200, `campaigns=[]` nếu chưa có chiến dịch thử.
- Đăng ký donor thử, đăng nhập, logout, tải lại trang: trạng thái phiên phản ánh dữ liệu bền vững.
- Tạo manager/approver thử qua công cụ cấp tài khoản backend chỉ chạy trong môi trường staging; KHÔNG chèn trực tiếp dữ liệu tài chính giả vào production.
- Tạo một chiến dịch thử có nhãn rõ ràng trên Preview, xác nhận dữ liệu tồn tại sau redeploy.

## Ranh giới dữ liệu quan trọng

Dù dùng cùng máy chủ Supabase (miễn phí theo báo giá hiện tại), dữ liệu hai schema được tách biệt về quyền database. Cả hai cùng chia tài nguyên/quota, tính sẵn sàng và sao lưu cấp project. Đây **không** phải một Postgres instance độc lập.

Không bao giờ trỏ DATABASE_URL Preview vào role production. Nếu sau này dùng Supabase Branch/project riêng, đổi URI và schema theo migration tương ứng trước khi triển khai.

## Xác minh quyền database

```sql
SELECT
 has_schema_privilege('aureva_preview_app','aureva_preview','USAGE') AS preview_access,
 has_schema_privilege('aureva_preview_app','aureva','USAGE') AS production_schema_access,
 has_table_privilege('aureva_preview_app','aureva.users','SELECT') AS production_table_access;
```

Kết quả dự kiến: `true, false, false`.

## An toàn

- Không chia sẻ hoặc hiển thị `DATABASE_URL`, mật khẩu PostgreSQL, khóa OpenAI hoặc ví Sepolia trong hội thoại.
- Không tắt Vercel Deployment Protection chỉ để kiểm thử dễ hơn.
- Không seed dữ liệu cứu trợ không có thật và không gán giao dịch testnet là chuyển tiền thật.
