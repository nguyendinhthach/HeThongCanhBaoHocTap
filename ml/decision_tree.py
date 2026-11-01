"""
Decision Tree cho 3 mục tiêu cảnh báo — cũng là file MẪU cho các phương pháp khác.

Mỗi file phương pháp chỉ cần:
1. tao_mo_hinh(**tham_so): trả về một mô hình MỚI, chưa huấn luyện, có
   fit(X, y) và predict_proba(X); tham_so ghi đè THAM_SO mặc định. Không tự
   đọc form, tự chia dữ liệu hay tự tính chỉ số: dữ liệu lấy từ dac_trung.py,
   đánh giá (kể cả chọn tham số và ngưỡng) do danh_gia.py lo.
2. LUOI_THAM_SO: các giá trị thử cho tham số chính, ~6 cấu hình.
3. Phần __main__ gọi danh_gia.chay_thu(tao_mo_hinh, "Tên phương pháp", LUOI_THAM_SO).

DecisionTreeClassifier của scikit-learn (từ bản 1.3) nhận NaN trực tiếp nên
không cần điền ô trống; class_weight="balanced" bù cho việc chỉ ~6% ca dương.

Chạy:  python ml/decision_tree.py
"""

from sklearn.tree import DecisionTreeClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"max_depth": 5, "min_samples_leaf": 20, "class_weight": "balanced",
           "random_state": SEED}

# Độ sâu và cỡ lá điều khiển độ phức tạp của cây (cây sâu, lá nhỏ = dễ học thuộc)
LUOI_THAM_SO = {"max_depth": [3, 5, 8], "min_samples_leaf": [10, 40]}


def tao_mo_hinh(**tham_so):
    return DecisionTreeClassifier(**{**THAM_SO, **tham_so})


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "Decision Tree", LUOI_THAM_SO)
