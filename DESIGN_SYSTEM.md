# AUREVA — Civic Impact Design System v3

**Tên đề tài:** AUREVA – Xây dựng nền tảng minh bạch hóa hoạt động quyên góp cứu trợ ứng dụng AI và Blockchain.  
**Slogan:** Trao gửi yêu thương, rõ từng đóng góp.  
**Giai đoạn:** Preview để duyệt giao diện trước buổi báo cáo 28/10/2026.

## Ý tưởng độc lập

Thiết kế được xây dựng **riêng cho nghiệp vụ cứu trợ**, không sao chép trang bán hàng hay dùng bố cục thương mại điện tử. Tinh thần là *humanitarian editorial × financial operations*: trang công khai có chiều sâu và dễ hiểu; khu vực làm việc có cấu trúc kiểm soát, trạng thái, minh chứng cụ thể.

Ba nguyên tắc:

1. **Niềm tin qua dữ liệu, không qua khẩu hiệu:** số tiền, số đóng góp, trạng thái được đọc từ API; khi không có dữ liệu không được đưa số mẫu lên màn hình public.
2. **Người dùng nhận biết được việc kế tiếp:** CTA rõ, vai trò khác nhau có không gian khác nhau, không để form chuyên môn chen vào trang giới thiệu.
3. **Chứng cứ trước hiệu ứng:** AI trích xuất và cảnh báo; người xét duyệt quyết định; Blockchain ghi dấu kiểm chứng, không tuyên bố tiền đã được ngân hàng chuyển đi.

## Bảng màu

| Token | Mã hex | Vai trò |
| --- | --- | --- |
| Paper | `#F7F8F6` | Background mềm, giảm chói |
| Surface | `#FFFFFF` | Bề mặt card, bảng, form |
| Ink | `#1B313B` | Văn bản chính |
| Navy | `#152E38` | Heading, tín nhiệm |
| Primary | `#1C5B5C` | Hành động chính, liên kết chức năng |
| Primary hover | `#174B4C` | Hover CTA |
| Sage | `#E7F1E9` | Thông tin đã đối soát, nền phụ |
| Line | `#E6EBE8` | Viền trung tính |
| Quiet | `#6D8287` | Metadata, chú thích |
| Peach | `#D58369` | Điểm nhấn nhân văn; không dùng tràn lan |
| Warning | `#A75B3F` | Cảnh báo chênh lệch chứng từ |
| Danger | `#AE504B` | Từ chối/lỗi |

Font: **DM Sans / Be Vietnam Pro** cho văn bản giao diện, **Newsreader** cho một vài câu nhấn mang sắc thái biên tập. Heading không phụ thuộc font serif để tránh lỗi hiển thị tiếng Việt. Không dùng gradient rực rỡ, 3D bóng bẩy hoặc nhiều bóng đổ cạnh nhau.

## Information architecture

### Khu vực công khai
1. **Tổng quan:** thương hiệu, thông điệp, giải thích quy trình, con số đã đối soát, danh sách chiến dịch và cách sử dụng chứng từ.
2. **Chiến dịch:** tìm theo tên/khu vực, xem tiến độ và chi tiết. Trong mục chi tiết có lịch sử công khai, báo cáo PDF và dấu xác thực.
3. **Minh bạch:** thu đã đối soát, chi đã phê duyệt, số dư. Chỉ số liệu có trong database; các cảnh báo về giới hạn của bằng chứng phải xuất hiện sát số liệu.

### Không gian làm việc
- **Donor:** xem khoản đã khai báo, chờ/đã đối soát; xem chi tiết chiến dịch.
- **Manager:** danh sách chiến dịch phụ trách, đối soát đóng góp; đề xuất khoản chi và tải chứng từ.
- **Approver:** hồ sơ khoản chi, cảnh báo AI và quyết định duyệt/từ chối có ghi lý do.

## Thành phần UI

- **Hero:** canvas off-white, nội dung và hành động bên trái; thẻ quy trình gồm 3 bước minh họa bên phải. Chỉ nói đây là sơ đồ, không phải giao dịch thật.
- **Campaign cards:** nhấn tên, địa điểm, tổng tiền thực nhận; phần nền đồ họa do CSS dựng, không ngụy tạo ảnh cứu trợ thật.
- **Workspace sidebar:** chỉ ở khu vực làm việc; màn công khai dùng thanh menu ngang.
- **AI review:** file preview có kiểm tra quyền, tổng tiền khai báo so với tổng tiền trích xuất, mã hóa đơn, tên nhà cung cấp và cảnh báo khác biệt.
- **Chain evidence:** trạng thái `pending / signed / submitted / confirmed / failed`, SHA-256 và URL Etherscan khi đã có transaction hash. Không tô nhãn `confirmed` chỉ vì có cấu hình.
- **PDF report:** bản PDF bất biến theo snapshot, nút tải, người dùng có thể chọn file PDF trên máy để so sánh SHA-256 cục bộ.

## Quy tắc UX

- Khi API lỗi hoặc trả dữ liệu sai cấu trúc: thông báo tiếng Việt dễ hiểu; **không đóng dialog thất bại**.
- Khi thiếu kết nối Gemini/Sepolia: hiển thị lý do cấu hình thiếu từ server; không sinh dữ liệu placeholder.
- Phím Tab/Enter hoạt động, focus visible; `prefers-reduced-motion` tắt animation không cần thiết.
- Trên mobile: menu cuộn ngang nếu thiếu chỗ, không ẩn các mục quan trọng; tách khối đối chiếu hóa đơn thành một cột.
- File xem trước chứng từ lấy bằng fetch có cookie sau hành động người dùng; blob URL được thu hồi khi đóng. Chứng từ vẫn do backend phân quyền.
- Không dùng số liệu demo hoặc con dấu Blockchain giả trong trang public.

## Kiểm thử

- `npm --prefix frontend run build` (TypeScript + Vite).
- `python -m pytest tests -q` (FastAPI, phân quyền, ledger, chứng từ/PDF dùng AI stub **chỉ trong unit tests**).
- `python tests/ui_smoke.py` (Chromium desktop/mobile, DB SQLite tạm độc lập, không chạm production).
- Vercel Preview phải READY; **READY không chứng minh API runtime đã hoạt động** nếu Preview thiếu `DATABASE_URL`.

## Những phần chưa mở cho người dùng thật

Gemini API live, Sepolia on-chain transaction, đối soát ngân hàng tự động, môi trường preview database độc lập, quyền truy cập Vercel Protected Preview và bản ghi sức khỏe production vẫn là các điểm cần kiểm chứng riêng. Chưa merge nhánh UI vào production trước khi duyệt.
