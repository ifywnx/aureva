# AUREVA – Bản đồ code & ôn hỏi đáp cá nhân

> Cập nhật cho bài báo cáo Web Nâng Cao 28/10/2026. Học theo **code chạy thật**,
> không học thuộc các câu trả lời khi chưa hiểu. Mỗi thành viên phải thực sự
> kiểm tra/chỉnh sửa/kiểm thử phần nhận trong bảng phân công của nhóm.

## 1. Luồng chạy từ trình duyệt đến database

```text
Người dùng bấm trên React (frontend/src/main.tsx)
       ↓ fetch('/api/...') kèm cookie phiên & X-Aureva-Request
FastAPI (backend/app.py) → xác thực + kiểm tra quyền
       ↓
PostgreSQL/Supabase (backend/postgres.py) hoặc SQLite local
       ↓
JSON cho React → màn hình cập nhật
```

- **React:** cập nhật giao diện, gọi API, hiển thị trạng thái.
- **FastAPI:** validation, xác thực, phân quyền, quy tắc nghiệp vụ và lưu dữ liệu.
- **PostgreSQL:** giữ dữ liệu bền vững (không phải MongoDB).
- **Cookie phiên:** dùng cookie HttpOnly, SameSite=Strict, Secure khi HTTPS.
  Token phiên được băm trước khi lưu DB; frontend không lưu bearer token.
- **AI:** `frontend/src/AurevaChat.tsx` → `backend/assistant.py`;
  đọc chứng từ ở `backend/evidence.py`. Nhà cung cấp cấu hình qua backend
  `AI_BASE_URL`, `OPENAI_MODEL` và `OPENAI_API_KEY`.
- **Blockchain:** `frontend/src/Evidence.tsx` + `backend/chain.py`;
  chỉ ghi SHA-256 lên Ethereum Sepolia. Không chuyển tiền cứu trợ.

## 2. Bảng phân công *để nhóm tự ghi người chịu trách nhiệm*

| Người phụ trách | Nên nhận module | File phải biết | Demo có thể thực hiện |
|---|---|---|---|
| [Điền tên 1] | Giao diện và giao tiếp API | `frontend/src/main.tsx`, `frontend/src/AurevaChat.tsx` | Đăng nhập, tìm chiến dịch, giải thích `fetch` |
| [Điền tên 2] | Tài khoản, vai trò và quyên góp | `backend/app.py`, `backend/demo.py` | Donor gửi khai báo; Manager đối soát |
| [Điền tên 3] | Khoản chi, cân đối và kiểm thử | `backend/app.py`, `backend/finance.py`, `tests/test_finance_viva.py` | Khoản chi vượt số dư bị từ chối |
| [Điền tên 4] | AI đọc hóa đơn/chứng từ | `backend/evidence.py`, `backend/assistant.py`, `frontend/src/Evidence.tsx` | AI đọc hóa đơn và giải thích cảnh báo |
| [Điền tên 5] | Blockchain, báo cáo PDF | `backend/chain.py`, `backend/evidence.py`, `frontend/src/Evidence.tsx` | Hash → ký MetaMask → kiểm tra TX và PDF |

Bảng này chỉ là **gợi ý chia để học và kiểm thử**, không phải chứng nhận
thành viên nào đã tự viết phần đó. Nhóm cần điều chỉnh theo đóng góp thực tế,
đưa tên, phần việc và commit tương ứng vào bản báo cáo.

## 3. Phải giải thích được những hàm này

### `api<T>(path, body)` – frontend/src/main.tsx
1. Nhận đường dẫn API và dữ liệu cần gửi.
2. Có `body` → POST, không có → GET.
3. Gửi cookie phiên và header `X-Aureva-Request`.
4. Đọc JSON; nếu server trả lỗi thì hiện thông báo, không âm thầm giả thành công.
5. Trả dữ liệu cho giao diện.

**Câu hỏi:** Tại sao không kiểm tra quyền bằng React thôi?
**Trả lời:** Nút ẩn trong React vẫn có thể bị gọi API trực tiếp, nên
`backend/app.py` dùng `current_user` và `require` kiểm tra trên máy chủ.

### `DonationInput` – backend/app.py
- `amount` phải là **số nguyên** từ 1 đến 1.000.000.000.000.
- `reference` dài 3–100 ký tự.
- Validation do **Pydantic** xử lý trước khi ghi database.
- Chỉ tài khoản Donor được tạo khai báo và khoản đó ban đầu là `pending`.
- Chỉ Manager mới xác nhận `confirmed` sau khi đối soát thủ công.

**Câu hỏi:** Tại sao ghi nhận 1 triệu mà tổng chưa tăng?
**Trả lời:** Hệ thống chỉ cộng khoản có `status='confirmed'`, không cộng
khai báo chưa có bằng chứng nhận tiền.

### `confirmed_totals(campaigns)` – backend/finance.py
- Nhận các chiến dịch đã được SQL tổng hợp.
- Cộng các trường `raised` (đã đối soát), `spent` (đã duyệt),
  `contribution_count` (lượt đóng góp xác nhận).
- Trả dictionary tổng; dữ liệu không tồn tại → 0.

### `available_to_approve(db, campaign_id)` – backend/finance.py
- Query số thu **đã đối soát** trừ số chi **đã duyệt**.
- Dùng dấu `?` và tuple tham số, tránh ghép ID vào câu SQL.
- Được gọi trong transaction khi `/api/expenses/{id}/decision` duyệt.
- Nếu khoản chi lớn hơn số dư này → trả **HTTP 409**.

### `extract_invoice(raw, mime)` – backend/evidence.py
- Chỉ Manager tải chứng từ, tối đa 2 MB; JPG/PNG/PDF hợp lệ.
- Gửi tới nhà cung cấp AI theo `AI_BASE_URL`; nội dung có thể lỗi/không đọc được.
- Kiểm tra JSON với mô hình `Invoice`, sau đó phát hiện lệch tổng tiền,
  nhà cung cấp, hóa đơn trùng và SHA-256 file.
- AI **không tự duyệt** và **không chứng nhận hóa đơn thật**.
- MiraiAPI có thể đọc ảnh hoặc PDF trích được văn bản; PDF scan cần ảnh.

### `prepare_wallet` / `verify` – backend/chain.py
- Chuẩn bị dữ liệu giao dịch hợp đồng chứa SHA-256 đã chốt.
- MetaMask dùng mạng **Sepolia (chain ID 11155111)**; giao dịch có thể cần
  testnet ETH làm gas nhưng không chuyển tiền cứu trợ.
- Xác minh `tx_hash`, giao dịch đúng contract/hàm/digest và số xác nhận.
- `pending` không có nghĩa là đã ghi blockchain.

## 4. Bài sửa code nhỏ trong 3 phút – luyện trong nhánh thử

**Bài A – thêm validation:** trong `backend/app.py`, đổi
`Field(min_length=5, max_length=1000)` của `ExpenseInput.purpose`
thành `max_length=200`; thêm case chuỗi 201 ký tự vào test. Giải thích
input dài sẽ bị Pydantic từ chối **422**.

**Bài B – thêm test:** mở `tests/test_finance_viva.py`, thêm test
`confirmed_totals([])` trả toàn số 0. Không cần đụng database thật.

**Bài C – đổi thông báo:** chỉ sửa câu thông báo lỗi khi nhập mã tham chiếu
không hợp lệ, không đổi rule bảo mật hoặc trạng thái database.

Sau khi thay: `python -m pytest tests/test_finance_viva.py -q`
và `python -m pytest tests -q`. Không sửa trực tiếp Production trong giờ thi.

## 5. Câu hỏi phản biện rất dễ gặp

**Vì sao React?** Dùng component giao diện và state, cập nhật không cần
tải lại cả trang; dùng TypeScript để kiểm tra kiểu khi build.

**Vì sao FastAPI?** Python dễ viết API, Pydantic giúp kiểm tra dữ liệu đầu
vào, dễ tích hợp xử lý hóa đơn AI.

**Vì sao PostgreSQL mà không MongoDB?** Dữ liệu thu–chi có quan hệ giữa
users, campaigns, donations, expenses, và cần transaction/constraint;
PostgreSQL phù hợp cho tính toàn vẹn.

**Vì sao dùng cookie?** Phiên được giữ bằng HttpOnly cookie, JavaScript
trong trang không thể đọc trực tiếp giá trị cookie. Server vẫn phải bảo vệ
CSRF bằng quy tắc origin/header và kiểm tra quyền.

**Nếu 1.000 người dùng đồng thời?** Bottleneck có thể ở database, giới hạn
pool kết nối, truy vấn tổng hợp và số request AI; cần đo tải trước khi khẳng
định khả năng mở rộng, dùng pooler/caching nơi phù hợp.

**Nếu AI lỗi 403?** Kiểm tra key/model/quyền của provider. Không giả kết
quả AI thành công, không cho Approver duyệt thiếu bước kiểm tra bắt buộc.

**Nếu Sepolia lỗi?** Không đánh dấu `confirmed`; giữ TX hash nếu đã gửi
để đồng bộ sau, tránh ký gửi trùng.

**Nếu server chết sau khi tạo chiến dịch?** PostgreSQL lưu bền vững,
ứng dụng kết nối lại và truy vấn. Cần thử nghiệm thực tế, không coi unit
test là bằng chứng uptime.

## 6. Quy định dùng công cụ AI – khai báo đúng thực tế

Giảng viên cho dùng công cụ AI để học, gợi ý code và tìm lỗi nhưng yêu cầu
kê khai cụ thể. Không tuyên bố mọi code đều được tự viết nếu nhóm dùng AI.

**Mẫu nhóm phải tự hoàn thiện trong báo cáo:**

> Nhóm có sử dụng: [ChatGPT/Codex/Claude/... – ghi đúng công cụ đã dùng].
> Phần việc AI hỗ trợ: [đề xuất kiến trúc/giao diện/gợi ý code/sửa lỗi/tạo test/...].
> Phần tự kiểm chứng: [thành viên, commit/PR, test đã chạy và thao tác thật].
> Trách nhiệm: mỗi thành viên đọc hiểu và kiểm thử module mình báo cáo;
> không dùng AI thay thế câu trả lời khi được hỏi cá nhân.

**Không dán API key, mật khẩu database, khóa ví hay seed phrase vào báo cáo.**

## 7. Checklist trước buổi bảo vệ

- [ ] Mỗi bạn chỉ được *ít nhất 2 hàm* trong phần đã nhận: input → xử lý → output.
- [ ] Mỗi bạn đã mở file được trong VS Code và giải thích một dòng bất kỳ.
- [ ] Mỗi bạn tự thêm 1 test hoặc validation trên branch thử, rồi chạy test.
- [ ] Nhóm kiểm tra đăng nhập 3 vai trò: Production cần tài khoản thật;
      chuyển vai trò 1 chạm **chỉ dành cho protected Preview** có DB tách biệt.
- [ ] Chỉ tạo dữ liệu demo, không bấm xác nhận tiền thật khi chưa đối soát.
- [ ] AI và Sepolia phải có kết quả thực tế mới nói là đã chạy thành công.
- [ ] Kê khai công cụ AI đúng thực tế và nêu đóng góp của từng thành viên.
- [ ] Chốt URL, commit và tài liệu trước buổi báo cáo.
