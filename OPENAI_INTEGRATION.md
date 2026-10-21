# AUREVA – AI đọc chứng từ qua OpenAI Responses API

> Đặc tả chính thức cập nhật 20/10/2026: sử dụng OpenAI API thay cho Google Gemini. Codex là agent hỗ trợ lập trình; tính năng đọc ảnh hóa đơn/PDF cần một model API hỗ trợ đầu vào hình ảnh và file.

## 1. Cấu hình

Thiết lập secrets trong môi trường chạy **backend** (ví dụ Vercel / Railway hoặc file `.env` local, tuyệt đối không commit):

```env
OPENAI_API_KEY=...  # chỉ nhập trong môi trường server, không gửi qua chat
OPENAI_MODEL=gpt-5-mini
```

- `OPENAI_API_KEY`: API key từ nền tảng OpenAI, có project billing/quota phù hợp.
- `OPENAI_MODEL`: tên model có khả năng đọc ảnh/PDF và Structured Outputs. Mặc định `gpt-5-mini`. Kiểm tra hạn mức và quyền truy cập model của project.
- Không dùng `GEMINI_API_KEY`/`GEMINI_MODEL` nữa. Chúng không kích hoạt chức năng AI trong AUREVA.
- Nếu người dùng chỉ có **tài khoản ChatGPT/Codex**, điều này **không thay thế** API key OpenAI dành cho backend.

## 2. Luồng thực hiện

1. Manager tải file JPG/PNG/PDF tối đa 2 MB, PDF tối đa 5 trang; file được kiểm tra và lưu trong database có phân quyền.
2. Khi Manager nhấn **Phân tích bằng OpenAI**, backend gọi `https://api.openai.com/v1/responses` bằng bearer key server-side.
3. File được gửi dưới dạng data URL (`input_image` với ảnh, `input_file` với PDF). Không có kết quả hardcode.
4. Model trả kết quả `json_schema` dạng strict cho nhà cung cấp, mã hóa đơn, ngày, loại tiền, tổng VND, trạng thái đọc được và ghi chú. Backend kiểm tra bằng Pydantic.
5. Backend lưu JSON thật và `model` thực tế; rules trong `backend/evidence.py` đối chiếu số tiền, tên nhà cung cấp, SHA-256 file và số hóa đơn trùng.
6. Approver xem kết quả AI, chứng từ và **tự duyệt/từ chối** kèm lý do. Blockchain chỉ ghi dấu khi giao dịch Sepolia thật được xác nhận. PDF được tạo từ dữ liệu đã chốt.

Nếu chưa có key, server trả HTTP **503**; nếu AI lỗi/quota/mạng/JSON sai, trả lỗi **502**, không tự giả kết quả. Mã lỗi không tiết lộ key hay nội dung bí mật của nhà cung cấp.

## 3. Kiểm thử

```sh
python -m pytest tests/test_openai_invoice.py -q
python -m pytest tests -q
cd frontend && npm ci && npm run build
```

Các unit test mock **chỉ ở ranh giới HTTP của OpenAI**, không tốn tiền API, kiểm tra payload ảnh/PDF, schema, handling khi thiếu key/quota/timeout. Bản chạy thật vẫn phải được test một lần bằng hóa đơn thử (đã che thông tin nhạy cảm) trên môi trường staging có key.

## 4. Lưu ý về an toàn và chất lượng

- Hóa đơn có thể chứa thông tin cá nhân. Tải lên và gọi API chỉ cho người có quyền; người quản lý phải thông báo việc gửi chứng từ cho nhà cung cấp AI, che những phần không cần thiết.
- Nội dung file là dữ liệu không đáng tin cậy: cấm làm theo chỉ dẫn bên trong file, không bật công cụ hay truy cập đường dẫn ngoài.
- `store:false` được gửi trong request AI; lưu ý điều này không phải là cam kết xóa ngay mọi dữ liệu phía nhà cung cấp.
- Không coi AI là công cụ xác định gian lận; chỉ cảnh báo để con người kiểm tra.
- Khóa OpenAI độc lập với ví ký Sepolia. Không đặt bất kỳ private key hoặc API key nào ở frontend hoặc GitHub source.

## 5. Tài liệu

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [File inputs & PDF](https://platform.openai.com/docs/guides/pdf-files)
- [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [GPT-5 mini](https://platform.openai.com/docs/models/gpt-5-mini)
