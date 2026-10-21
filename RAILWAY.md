# Deploy AUREVA trên Railway (bản thử nghiệm riêng)

Railway build đầy đủ React/Vite (Node 22) + FastAPI (Python 3.12) từ `Dockerfile` ở thư mục gốc. FastAPI phục vụ `frontend/dist` và API cùng domain; `railway.toml` kiểm tra `/api/health`.

## Thiết lập

1. Kết nối GitHub repo `ifywnx/aureva` tại Railway; chọn branch `feat/premium-motion-ui-20261020` để thử giao diện trước khi merge.
2. Chọn root directory `/`, builder Dockerfile với path `Dockerfile`. Không đặt root thành `frontend` vì API nằm ở `backend/`.
3. Chọn **một trong hai** cách lưu dữ liệu:
   - **Test độc lập / SQLite**: tạo và gắn một **persistent volume** ở `/data`. Thêm biến dịch vụ `AUREVA_DB=/data/aureva.db`. Không đặt `DATABASE_URL`. SQLite tự khởi tạo bảng khi FastAPI chạy lần đầu. Dữ liệu này **hoàn toàn tách biệt** với Supabase/Vercel; không có tài khoản người phụ trách/phê duyệt sẵn. Hãy dùng `scripts/accounts.py` trên môi trường được cấu hình **chỉ cho hệ thống test**, theo hướng dẫn README.
   - **Sử dụng PostgreSQL hiện có**: cấu hình `DATABASE_URL` bí mật ngay trong Railway, **không** đặt `AUREVA_DB`. Database phải có schema `aureva` như `backend/schema.postgres.sql` và role có quyền trong schema. Không chia sẻ database production hoặc copy credentials vào Git.
4. Tạo Railway domain HTTPS, sau đó đặt `AUREVA_ORIGIN=https://<railway-domain>` (không có slash cuối) và `AUREVA_SECURE_COOKIE=1`.
5. Các biến tích hợp `OPENAI_API_KEY`, `OPENAI_MODEL`, `SEPOLIA_RPC_URL`, `BLOCKCHAIN_PRIVATE_KEY`, `AUREVA_CONTRACT_ADDRESS` chỉ thêm khi thực sự cần AI/testnet. Nếu thiếu, ứng dụng hiển thị trạng thái chưa cấu hình; không tạo dữ liệu AI/Blockchain giả.
6. Deploy, kiểm tra `GET /api/health` trả `status: ok`, sau đó thử dashboard, đăng nhập, tạo chiến dịch, tải chứng từ. **Không báo triển khai thành công chỉ vì Railway trả trạng thái queued/building.**

## Lưu ý

- Dùng **dịch vụ và volume mới riêng**; không ghi đè `locket-gold-ywnx`, `an-store` hay volume của các dự án khác.
- Railway có giới hạn tài nguyên tùy gói. Nếu báo `Free plan resource provision limit exceeded`, cần giải phóng hạn mức một cách chủ động hoặc nâng gói trước khi tạo tài nguyên mới; không tự xóa dịch vụ/volume đang có.
- SQLite chỉ phù hợp một instance chạy thử; để mở rộng nhiều replica hoặc triển khai lâu dài, dùng PostgreSQL với migration/backup phù hợp.
- Không thiết lập `PORT` cố định; start command đọc biến `PORT` do Railway cấp.
- Chưa xác thực build Railway trong phiên này vì tài khoản hiện tại bị giới hạn provision tài nguyên.
