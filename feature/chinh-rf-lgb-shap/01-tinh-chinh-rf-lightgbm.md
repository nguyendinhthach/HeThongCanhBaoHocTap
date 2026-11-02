# Task 1 — Tinh chỉnh Random Forest và LightGBM

## Mục tiêu

- Cho Random Forest và LightGBM thử sáu cấu hình tham số trong quá trình đánh giá chéo lồng nhau.
- Giữ cách đánh giá và số lượng cấu hình tương đương các phương pháp còn lại.
- Giới hạn mỗi mô hình dùng một luồng CPU để tránh tranh chấp với các tiến trình đánh giá song song.

## File liên quan

- `ml/random_forest.py`: tham số mặc định, lưới sáu cấu hình và hàm tạo mô hình.
- `ml/lightgbm_model.py`: tham số mặc định, sáu bộ tham số LightGBM và hàm tạo mô hình.
- `ml/danh_gia.py`: thành phần dùng lưới tham số để chọn cấu hình; không cần sửa.
- `ml/so_sanh.py`: chạy đánh giá tổng hợp và ghi kết quả vào `results/`; không cần sửa.
- `results/`: kết quả so sánh sau khi chạy lệnh theo yêu cầu.

## Cách triển khai

1. Dùng `tao_mo_hinh(**tham_so)` để cho phép cấu hình đang được đánh giá ghi đè giá trị mặc định.
2. Thử `max_depth` và `min_samples_leaf` theo tích Descartes 2 × 3 cho Random Forest.
3. Thử sáu bộ kết hợp `num_leaves`, `learning_rate` và `min_child_samples` cho LightGBM.
4. Đặt `n_jobs=1` ở cả hai mô hình; phần đánh giá bên ngoài vốn đã chạy nhiều mô hình song song.
5. Chạy `python ml/so_sanh.py --so-lan-lap 3` để sinh lại các bảng và biểu đồ trong `results/`.

## Kiểm tra

- Xác nhận mỗi lưới tạo đúng sáu cấu hình.
- Xác nhận hàm tạo mô hình áp dụng được tham số ghi đè.
- Chạy phép so sánh ba lần lặp và kiểm tra đủ các file kết quả trong `results/`.
- Kết quả thực tế: 360 dòng chi tiết, 24 dòng tổng hợp, ba seed `42`, `43`, `44`; biên dịch Python và `git diff --check` đều đạt.
- Lần chạy hoàn tất mất 751 giây. Giới hạn tạm thời số worker Joblib ở 4 giúp tránh lỗi truy cập bộ nhớ XGBoost trên Python 3.14; cấu hình này không được ghi vào code dự án.
- PR-AUC trung bình nổi bật: Random Forest đạt `0.615` cho `canh_bao`; LightGBM đạt `0.839` cho `truot_mon`. Đây là kết quả trên dữ liệu mô phỏng, không phải kết luận tổng quát.

## Kịch bản báo cáo

- **File / folder:** `ml/random_forest.py` và `ml/lightgbm_model.py` khai báo cách tạo hai mô hình; `results/` lưu kết quả đánh giá. Tài liệu này ghi lại phạm vi và cách kiểm tra task.
- **Mục đích:** trước đây hai mô hình chưa khai báo lưới tham số nên chưa được tối ưu trong quy trình so sánh chung. `n_jobs=1` tránh mỗi mô hình lại chiếm nhiều luồng khi đánh giá đã chạy song song.
- **Kết quả:** mỗi thuật toán có sáu cấu hình; CSV và biểu đồ đã ghi nhận ba lần lặp với 5 fold. Lần chạy mất khoảng 12 phút 31 giây trong môi trường này.
- **Lưu ý:** kết quả phụ thuộc dữ liệu mô phỏng và cách chia fold; sáu cấu hình là phạm vi thử nghiệm gọn, chưa khẳng định là tối ưu toàn cục. Python toàn cục dùng để chạy vì `.venv` thiếu scikit-learn và LightGBM; cần cài đủ requirements vào môi trường dự án để tái lập thuận tiện. Giới hạn worker đã dùng chỉ cho lệnh chạy này.
- **Công cụ:** Python trong môi trường dự án, scikit-learn, LightGBM, pandas và matplotlib.
