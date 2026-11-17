# Task 4 — Tích hợp scheduler, Postman và kiểm thử

## Mục tiêu

Khởi động/tắt APScheduler cùng vòng đời FastAPI, cung cấp bộ request Postman và đảm bảo các tác vụ được kiểm thử độc lập.

## File và vị trí

- `api/main.py`: khởi động scheduler khi ứng dụng lên và dừng scheduler khi ứng dụng kết thúc.
- `dich_vu/tac_vu_canh_bao.py`: lịch 5 phút, 07:00 và 02:00; mỗi job chỉ có một phiên chạy đồng thời.
- `docs/CanhBaoHocTap.postman_collection.json`: luồng đăng ký, lấy token, lưu dữ liệu học kỳ và gọi API.
- `dich_vu/test_gui_email.py`, `dich_vu/test_tac_vu_canh_bao.py`: test độc lập với SMTP/DB giả lập.

## Cách triển khai

- Dùng một `BackgroundScheduler` theo múi giờ `Asia/Ho_Chi_Minh`; tắt scheduler trong `finally` của lifespan.
- Cấu hình `max_instances=1`, tránh một job bị chạy chồng.
- Postman lưu token sau khi đăng nhập; request đọc trước dữ liệu đưa kết quả sang biến để request lưu sử dụng.
- Không tạo hoặc ghi `.env` với thông tin xác thực thật.

## Kịch bản báo cáo

- **File/folder để làm gì?** `api/main.py` quản lý vòng đời; Postman collection giúp gọi lần lượt các API.
- **Vì sao cần?** Job nền phải được khởi động/dừng đúng vòng đời ứng dụng; Postman giúp kiểm tra luồng sử dụng bằng giao diện.
- **Kết quả:** Có ba lịch định kỳ và một bộ request cho các API đăng nhập, học tập, dự đoán, email, sức khỏe.
- **Lưu ý:** Chạy đúng một worker như hướng dẫn; cần thay nội dung mẫu trong `vanBanHocTap` và điền SMTP/ngày học kỳ trước khi kiểm tra end-to-end.
- **Công cụ:** FastAPI, APScheduler, Postman, Python unittest.
