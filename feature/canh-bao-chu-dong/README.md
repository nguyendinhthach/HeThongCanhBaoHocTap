# Kế hoạch và nội dung báo cáo — `feature/canh-bao-chu-dong`

Nhánh này triển khai gửi email cảnh báo theo hàng đợi, nhắc sinh viên theo các mốc học kỳ và chạy dự đoán lại khi có phiên bản mô hình mới. Thiết kế bám theo `docs/SPEC.md` §12.5–§12.6; các tệp trong danh sách cấm sửa được giữ nguyên.

## Các task

- [Task 1 — Gửi email SMTP và xử lý hàng đợi](./task-01-email-smtp.md)
- [Task 2 — Nhắc cập nhật theo mốc học kỳ](./task-02-nhac-theo-moc.md)
- [Task 3 — Dự đoán lại khi có mô hình mới](./task-03-mo-hinh-moi.md)
- [Task 4 — Tích hợp scheduler, Postman và kiểm thử](./task-04-api-postman.md)

## Cách chạy và kiểm thử

- Cài thư viện: `pip install -r requirements.txt`.
- Khởi động API bằng một worker: `python -m uvicorn api.main:app --port 8000`.
- Kiểm tra SMTP bằng tài khoản Gmail nhóm và mật khẩu ứng dụng; không dùng mật khẩu Gmail thật.
- Điền ngày học kỳ thực tế vào `config/moc_hoc_ky.json`. Ngày chưa biết được để `null` và mốc đó không xếp email.
- Chạy test riêng: `python -m unittest dich_vu.test_gui_email dich_vu.test_tac_vu_canh_bao`.
- Collection Postman: `docs/CanhBaoHocTap.postman_collection.json`.

## Kịch bản báo cáo tổng quan

- **Mục đích:** Tự động gửi các email đã xếp hàng, chủ động nhắc cập nhật dữ liệu học tập và cập nhật dự đoán sau khi thay mô hình.
- **Kết quả:** Email chỉ gửi ở job nền; lỗi SMTP được ghi nhận vào hàng đợi để thử lại. Lịch nhắc chống trùng theo khóa mốc/lần nhắc. Scheduler chạy cùng FastAPI và được dừng khi ứng dụng tắt.
- **Điểm cần lưu ý:** Phải chạy một worker; cần cấu hình SMTP và điền lịch đào tạo chính thức. Máy chạy ứng dụng phải có SQL Server/schema và các mô hình đã train để kiểm tra đầy đủ.
- **Công cụ:** Python, FastAPI, APScheduler, SQL Server, Gmail SMTP app password, Postman.
