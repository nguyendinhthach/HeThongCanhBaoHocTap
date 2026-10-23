"""
Decision Tree cho 3 mục tiêu cảnh báo — cũng là file MẪU cho các phương pháp khác.

Mỗi file phương pháp chỉ cần:
1. tao_mo_hinh(): trả về một mô hình MỚI, chưa huấn luyện, có fit(X, y) và
   predict_proba(X). Không tự đọc form, tự chia dữ liệu hay tự tính chỉ số:
   dữ liệu lấy từ dac_trung.py, đánh giá do danh_gia.py lo.
2. Phần __main__ gọi danh_gia.chay_thu(tao_mo_hinh, "Tên phương pháp").

DecisionTreeClassifier của scikit-learn (từ bản 1.3) nhận NaN trực tiếp nên
không cần điền ô trống; class_weight="balanced" bù cho việc chỉ ~6% ca dương.

Chạy:  python ml/decision_tree.py
"""

from sklearn.tree import DecisionTreeClassifier

from danh_gia import SEED, chay_thu


# Cây nông + lá đủ lớn để không học thuộc từng sinh viên; chỉnh ở bước so sánh sau
THAM_SO = {"max_depth": 5, "min_samples_leaf": 20, "class_weight": "balanced",
           "random_state": SEED}


def tao_mo_hinh():
    return DecisionTreeClassifier(**THAM_SO)


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "Decision Tree")
