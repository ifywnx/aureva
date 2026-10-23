# AUREVA — Đăng nhập nhanh vào tài khoản thật

Các nút đăng nhập nhanh dùng **chung PostgreSQL Production** và đăng nhập vào các tài khoản đã được cấp sẵn. Không tạo người dùng demo, không thay thế mật khẩu của tài khoản, không dùng cookie thuyết trình.

## Cấu hình Vercel Production

Trong Vercel → Project → Settings → Environment Variables, tạo các biến **server-side**, không đặt tiền tố VITE_:

- `AUREVA_TEAM_ACCESS_CODE`: mã ngẫu nhiên dài tối thiểu 16 ký tự, chỉ gửi riêng cho thành viên nhóm. Không commit mã vào GitHub.
- `AUREVA_QUICK_DONOR_EMAIL`: email tài khoản thật có role `donor`.
- `AUREVA_QUICK_MANAGER_EMAIL`: email tài khoản thật có role `manager`.
- `AUREVA_QUICK_APPROVER_EMAIL`: email tài khoản thật có role `approver`.
- `AUREVA_SECURE_COOKIE=1` (trên HTTPS).

Tài khoản phải tồn tại trong bảng `users`, với role tương ứng. Người dùng mới đăng ký chỉ có role `donor`; quản lý/phê duyệt cần được quản trị viên cấp theo quy trình của dự án. Không sử dụng các địa chỉ `@aureva.invalid` hoặc ID `aureva_demo_*`.

**Tắt** `AUREVA_PUBLIC_DEMO`, `AUREVA_PRESENTATION_CODE`, `AUREVA_DEMO_SWITCH` trên Production, sau khi xác nhận không còn phiên thuyết trình cần dùng. Triển khai lại Production để áp dụng biến môi trường.

## Kiểm thử bắt buộc trước khi phát hành

1. Khách chưa đăng nhập vẫn xem được dashboard và chiến dịch.
2. Khách không biết mã nhóm không thể đăng nhập nhanh; nhập sai liên tục bị giới hạn.
3. Từng nút tạo session đúng role và dữ liệu từ cùng DB Production.
4. Manager tạo chiến dịch; Approver duyệt; Donor không thể gọi API đặc quyền.
5. Đăng xuất xóa phiên, session cookie dùng HttpOnly/SameSite/HTTPS.
6. AI gửi chứng từ thật qua OpenAI API, xử lý lỗi quota; Blockchain chỉ báo thành công khi giao dịch Sepolia được xác nhận.
7. Không được hiển thị giao dịch thử như khoản quyên góp tiền thật.

**Lưu ý:** nút đăng nhập nhanh là tài khoản dùng chung trong nhóm, không có audit danh tính từng thành viên. Với vận hành cứu trợ thật lâu dài, nên cấp mỗi thành viên một tài khoản riêng và dùng MFA.
