# Task 3 — Dự đoán lại khi có mô hình mới

## Mục tiêu

Mỗi ngày lúc 02:00, nhận biết mô hình cảnh báo đã đổi và chạy dự đoán lại trên lần cập nhật mới nhất của từng sinh viên.

## File và vị trí

- `dich_vu/tac_vu_canh_bao.py`: so phiên bản mô hình với repository và điều phối việc dự đoán.
- `dich_vu/test_tac_vu_canh_bao.py`: kiểm tra dự đoán cho toàn bộ người dùng và bù người còn phiên bản cũ.
- `dich_vu/du_doan.py` và `db/repo_canh_bao.py`: chỉ sử dụng giao diện hiện có, không sửa.

## Cách triển khai

- Lấy thời điểm của cả hai model đang dùng từ `du_doan.goi_mo_hinh()`.
- Vì repository trả phiên bản của dòng dự đoán mới nhất (có thể là model trượt môn), nhận diện phiên bản trong bộ model hiện tại; nếu đã đồng bộ thì chỉ chạy lại người còn kết quả cũ.
- Khi có model mới, gọi `du_doan.chay(user_id)` cho từng user có cập nhật.
- Nếu một user lỗi, ghi log và báo job thất bại; lần chạy kế tiếp kiểm tra phiên bản từng user để thử bù.
- `du_doan.chay()` vẫn chịu trách nhiệm xếp email nếu xuất hiện nguy cơ cao mới.

## Kịch bản báo cáo

- **File/folder để làm gì?** Tác vụ định kỳ kiểm tra phiên bản và gọi lại dịch vụ dự đoán hiện hữu.
- **Vì sao cần?** Sau khi train mô hình mới, kết quả cũ không còn phản ánh mô hình đang dùng.
- **Kết quả:** Kết quả được lưu qua dịch vụ dự đoán, email cảnh báo mới vẫn theo quy tắc hiện tại.
- **Lưu ý:** Ảnh nêu `du_doan_hang_loat_moi()` nhưng hàm này chưa có và file `du_doan.py` bị cấm sửa; vì vậy dùng `goi_mo_hinh()` hiện có. Đối chiếu cả hai model tránh chạy lại toàn bộ mỗi ngày khi thời điểm train của chúng khác nhau.
- **Công cụ:** Python, mô hình `.joblib`, SQL Server repository.
