# Task 2 — Giải thích mô hình bằng SHAP

## Mục tiêu

- Huấn luyện mô hình tốt nhất trong nhóm XGBoost/LightGBM theo kết quả so sánh, dùng toàn bộ dữ liệu của từng mục tiêu.
- Tạo biểu đồ SHAP cho từng mục tiêu và một hàm trả lời ba đặc trưng ảnh hưởng mạnh nhất cho mỗi dòng.
- Dự đoán trực tiếp trong ứng dụng từ điểm môn học đã lưu, hiển thị lý do SHAP và không ghi lịch sử dự đoán vào SQL.

## File liên quan

- `ml/giai_thich.py`: chọn mô hình/cấu hình, huấn luyện, tạo `TreeExplainer`, lưu biểu đồ và cung cấp `ly_do(...)`.
- `requirements.txt`: thêm SHAP làm dependency.
- `ui/data.py`: suy ra các đặc trưng học tập từ lịch sử môn học và gọi mô hình để dự đoán trực tiếp.
- `ui/screens/risk.py`, `ui/screens/dashboard.py`: hiển thị cùng một dự đoán live; trang cảnh báo có thêm lý do SHAP.
- `app.py`: mô tả đúng luồng dự đoán, không lưu kết quả vào SQL.
- `results/shap_<muc_tieu>.png`: biểu đồ độ quan trọng theo SHAP.

## Cách triển khai

1. Dựa trên `results/so_sanh_tom_tat.csv`, chọn XGBoost cho `canh_bao`, LightGBM cho `thoi_hoc` và `truot_mon`; dùng cấu hình được chọn thường xuyên nhất trong các fold.
2. Huấn luyện từng mô hình trên toàn bộ `(X, y)` từ `dac_trung.tao_du_lieu(...)`.
3. Dùng `shap.TreeExplainer` để tạo biểu đồ tầm quan trọng và lưu theo tên mục tiêu.
4. `mo_hinh_tai("canh_bao")` huấn luyện mô hình một lần trong tiến trình ứng dụng và giữ lại để tái sử dụng.
5. `ui.data.dac_trung_canh_bao(...)` tính các đặc trưng từ học kỳ đã nhập đủ điểm. Những dữ liệu không lưu trong SQL (điểm rèn luyện, mức vắng, hệ đào tạo) được đánh dấu thiếu; học phí dùng nhóm “không muốn trả lời”.
6. `ui.data.du_doan_canh_bao(...)` căn chỉnh đúng thứ tự cột huấn luyện, tính xác suất và gọi `ly_do(...)`. Dashboard và trang cảnh báo dùng cùng luồng; không ghi dự đoán vào SQL.

## Kiểm tra

- Chạy `python ml/test_danh_gia.py` để kiểm tra đánh giá mô hình; biên dịch các file Python liên quan.
- Chạy `python ml/giai_thich.py`, xác nhận có đủ ba biểu đồ SHAP.
- Smoke test bộ chuyển đặc trưng với dữ liệu đủ điểm, học kỳ thiếu điểm và dự đoán live: xác suất nằm trong 0–100%, có ba lý do SHAP, không cần ghi SQL.
- Kết quả thực tế: đã tạo đủ ba PNG; `ly_do` trả ba lý do cho mỗi dòng với cả XGBoost và LightGBM; smoke test live prediction với dữ liệu môn mẫu đã đạt.
- Tám kiểm thử đánh giá mô hình hiện có đều đạt; các file Python liên quan biên dịch được.

## Kịch bản báo cáo

- **File / folder:** `ml/giai_thich.py` tạo phần giải thích và giữ mô hình trong bộ nhớ; `ui/data.py` chuyển môn học thành đặc trưng; thư mục `results/` lưu biểu đồ; dashboard và màn hình `ui/screens/risk.py` hiển thị dự đoán trực tiếp.
- **Mục đích:** mô hình cần giải thích được để người dùng hiểu yếu tố nào ảnh hưởng tới nguy cơ, thay vì chỉ thấy một tỷ lệ.
- **Kết quả:** mỗi mục tiêu có biểu đồ SHAP; với tài khoản có ít nhất một học kỳ đủ điểm, ứng dụng hiển thị xác suất và ba lý do SHAP được tính từ dữ liệu môn học. Nếu chưa đủ dữ liệu, màn hình báo rõ thay vì dùng số liệu mẫu.
- **Lưu ý:** dữ liệu huấn luyện vẫn là dữ liệu mô phỏng. SQL Server không lưu điểm rèn luyện, mức vắng, hệ đào tạo và học phí; các trường này được để thiếu/không rõ, nên dự đoán chỉ mang tính tham khảo. Không có bản ghi dự đoán nào được ghi vào SQL. LightGBM có cảnh báo về định dạng SHAP mới; hàm chuẩn hoá đã xử lý định dạng này.
- **Công cụ:** Python, SHAP, XGBoost/LightGBM, pandas, matplotlib, Streamlit và SQL Server hiện có.
