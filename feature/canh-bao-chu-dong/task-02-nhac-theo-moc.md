# Task 2 — Nhắc cập nhật theo mốc học kỳ

## Mục tiêu

Mỗi ngày lúc 07:00, xếp email nhắc lần đầu vào ngày bắt đầu mốc và lần hai sau 7 ngày cho sinh viên chưa cập nhật dữ liệu kể từ mốc đó.

## File và vị trí

- `config/moc_hoc_ky.json`: danh sách mốc, loại nhắc và ngày bắt đầu.
- `dich_vu/tac_vu_canh_bao.py`: đọc cấu hình, kiểm tra ngày, gọi repository để xếp thư.
- `dich_vu/test_tac_vu_canh_bao.py`: kiểm tra lịch, lần nhắc thứ hai, và dữ liệu ngày sai.

## Cách triển khai

- Đọc mốc theo đường dẫn `HT_MOC_HOC_KY` hoặc mặc định cấu hình trong `dich_vu.cau_hinh`.
- Chỉ xét người chưa cập nhật từ ngày mốc; repository tự lọc người tắt email.
- Dùng `them_email(..., moc=..., lan_nhac=...)`; nếu bản ghi bị trùng, repository tự trả `None`.
- Chưa có ngày chính thức thì để `bat_dau: null`; mốc đó được cảnh báo trong log và không xếp thư.

## Kịch bản báo cáo

- **File/folder để làm gì?** JSON là lịch mốc; hàm tác vụ biến lịch thành email xếp hàng.
- **Vì sao cần?** Sinh viên cần được nhắc cập nhật trước/sau các đợt giữa kỳ, cuối kỳ.
- **Kết quả:** Mỗi mốc có tối đa hai lần nhắc; gửi thực tế vẫn do tác vụ hàng đợi thực hiện.
- **Lưu ý:** Cần thay `null` bằng ngày chính thức `YYYY-MM-DD` theo kế hoạch đào tạo của trường; không nên tự suy đoán ngày thi.
- **Công cụ:** JSON, Python `datetime`, SQL Server repository.
