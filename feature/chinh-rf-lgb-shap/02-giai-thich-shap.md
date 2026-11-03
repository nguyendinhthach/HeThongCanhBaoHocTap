# Task 2 — Giải thích mô hình bằng SHAP

## Yêu cầu đã chốt với leader

- Mục tiêu chính là cảnh báo sớm cho **học kỳ kế tiếp**: dùng dữ liệu đã có ở học kỳ `k` để dự đoán nguy cơ ở học kỳ `k+1`.
- Giữ phần mô hình học máy và SHAP; không thay việc học máy bằng các luật `if/else`.
- Không tính lại GPA/điểm trên website. Đầu vào phải dùng điểm và số liệu tổng kết do nguồn dữ liệu cung cấp.
- Có hai luồng dữ liệu cần hỗ trợ khi làm giao diện ở giai đoạn sau:
  1. **Giảng viên:** tải Excel có nhiều sinh viên; hệ thống nhận diện/ghép cột dữ liệu để dự đoán cho từng sinh viên.
  2. **Sinh viên:** cung cấp kết quả các học kỳ đã qua, theo cách nhập liệu phù hợp với bộ dữ liệu khảo sát.
- Chưa làm giao diện trong task này. Giao diện hiện có chưa đại diện cho hai luồng trên và cần được thiết kế lại ở giai đoạn cuối.

## Phạm vi hiện tại

- Giữ phần so sánh/tinh chỉnh Random Forest và LightGBM của Task 1, phần giải thích SHAP, dependency và ba biểu đồ đã tạo.
- Không giữ phần tích hợp dự đoán trực tiếp vào ứng dụng hoặc các thay đổi giao diện của Task 2.
- Hợp đồng dữ liệu huấn luyện trong `ml/dac_trung.py` đã định nghĩa `canh_bao` và `thoi_hoc` bằng dữ liệu cuối kỳ `k` với nhãn ở `k+1`. Mục tiêu `truot_mon` là bài toán riêng, dự đoán kết quả môn sau giữa kỳ, không phải cảnh báo học kỳ kế tiếp.

## File liên quan

- `ml/random_forest.py`, `ml/lightgbm_model.py`: các mô hình và cấu hình được tinh chỉnh ở Task 1.
- `ml/dac_trung.py`: hợp đồng đặc trưng/nhãn; xác định mốc dữ liệu `k` và nhãn kỳ sau `k+1`.
- `ml/giai_thich.py`: chọn mô hình/cấu hình, tạo giải thích SHAP và biểu đồ cho ba mục tiêu.
- `requirements.txt`: khai báo SHAP.
- `results/shap_<muc_tieu>.png`: biểu đồ SHAP cho từng mục tiêu.

## Cách triển khai

1. Dùng các kết quả so sánh mô hình hiện có để chọn cấu hình cho phần giải thích; không thay đổi các mô hình đã được leader chấp thuận.
2. Huấn luyện mô hình trên dữ liệu theo hợp đồng `(X, y, nhom)` của `dac_trung.tao_du_lieu(...)`.
3. Với cảnh báo học kỳ tiếp theo, đặc trưng chỉ lấy từ học kỳ `k`; nhãn kiểm tra là kết quả cảnh báo ở `k+1`, không phải kết quả của chính kỳ `k`.
4. Dùng `shap.TreeExplainer` để tạo biểu đồ và nêu các đặc trưng ảnh hưởng mạnh nhất.
5. Khi triển khai hai luồng nhập liệu sau này, ghép dữ liệu Excel của giảng viên hoặc dữ liệu các kỳ trước do sinh viên cung cấp vào đúng hợp đồng đặc trưng. Dùng điểm/GPA đã có từ nguồn; không tự tính lại điểm.
6. Hoãn màn hình, upload Excel và nhập liệu sinh viên đến giai đoạn làm giao diện; không gắn dự đoán live vào `ui/` trong task này.

## Kiểm tra

- Chạy `python ml/test_danh_gia.py` để kiểm tra các phép đo và đánh giá mô hình.
- Chạy `python ml/giai_thich.py`, xác nhận có đủ ba biểu đồ SHAP.
- Kiểm tra nhãn cảnh báo trong `ml/dac_trung.py`: dữ liệu kỳ `k` được ghép với nhãn kỳ `k+1`.
- Kết quả hiện có: 8/8 kiểm thử đánh giá đạt; ba biểu đồ SHAP đã được tạo. Không triển khai hoặc kiểm tra giao diện trong task này.

## Kịch bản báo cáo

- **File / folder:** `ml/dac_trung.py` quy định dữ liệu đầu vào và mốc dự đoán; `ml/giai_thich.py` tạo phần giải thích; `results/` lưu biểu đồ; `ml/random_forest.py` và `ml/lightgbm_model.py` là các mô hình được tinh chỉnh ở Task 1.
- **Mục đích:** cảnh báo phải dự đoán trước một kỳ để người dùng có thời gian chủ động; SHAP giúp giải thích những đặc trưng đã ảnh hưởng đến kết quả mô hình.
- **Kết quả:** phần mô hình và SHAP được giữ nguyên; mục tiêu `canh_bao`/`thoi_hoc` dùng dữ liệu kỳ `k` để dự đoán kỳ `k+1`. Giao diện và hai luồng nhập dữ liệu chưa được triển khai.
- **Hai luồng sẽ làm ở giai đoạn giao diện:** giảng viên tải Excel nhiều sinh viên để nhận diện/ghép cột; sinh viên cung cấp kết quả các kỳ trước. Cả hai phải dùng cùng hợp đồng đặc trưng và kết quả điểm do nguồn cung cấp.
- **Lưu ý:** `truot_mon` là mục tiêu riêng ở cấp môn học, dự đoán sau giữa kỳ; không nên nhầm với cảnh báo học vụ cho kỳ tiếp theo. Dữ liệu đánh giá hiện tại là dữ liệu mô phỏng, nên cần kiểm tra lại chất lượng khi có dữ liệu Excel/sinh viên thực tế. Mô hình là công cụ hỗ trợ tham khảo, không thay thế quy chế học vụ.
- **Công cụ:** Python, scikit-learn, LightGBM, XGBoost, SHAP, pandas và matplotlib.
