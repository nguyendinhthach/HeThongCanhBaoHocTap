# Task 1 — Gửi email SMTP và xử lý hàng đợi

## Mục tiêu

Gửi các dòng email đến hạn bằng Gmail SMTP; cập nhật trạng thái đã gửi hoặc ghi nhận lỗi để repository thử lại theo giới hạn có sẵn.

## File và vị trí

- `dich_vu/gui_email.py`: kết nối SMTP STARTTLS, xác thực bằng app password và gửi email văn bản thuần.
- `dich_vu/tac_vu_canh_bao.py`: hàm `gui_hang_doi_email()` đọc hàng đợi và cập nhật trạng thái.
- `requirements.txt`: thêm APScheduler 3.x cho tác vụ định kỳ.
- `dich_vu/test_gui_email.py`, `dich_vu/test_tac_vu_canh_bao.py`: test SMTP giả lập và luồng thành công/thất bại.

## Cách triển khai

- Đọc thông tin SMTP qua `dich_vu.cau_hinh.smtp()`, không ghi thông tin bí mật vào code.
- Báo lỗi nếu thiếu user, app password hoặc địa chỉ gửi.
- Với từng email đến hạn: gửi trước, sau đó gọi `danh_dau_da_gui`; nếu SMTP lỗi thì gọi `danh_dau_loi`.
- Mỗi email lỗi được ghi log theo ID; không gửi thư thật trong unit test.

## Kịch bản báo cáo

- **File/folder để làm gì?** `gui_email.py` gom phần kết nối SMTP; scheduler điều phối hàng đợi; test kiểm tra mà không cần Gmail thật.
- **Vì sao cần?** API chỉ xếp thư, không nên bị chặn bởi độ trễ hoặc lỗi SMTP.
- **Kết quả:** Email được gửi từ cấu hình `.env`; lỗi được trả về trạng thái hàng đợi để thử lại theo chính sách database.
- **Lưu ý:** Gmail cần app password; SMTP chưa được kiểm chứng với tài khoản thật trong test.
- **Công cụ:** Python `smtplib`/`EmailMessage`, Gmail SMTP, unittest/mock.
