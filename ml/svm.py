"""
SVM cho 3 mục tiêu cảnh báo (theo mẫu decision_tree.py).

SVM khác các phương pháp cây ở hai điểm, nên tao_mo_hinh() trả về một Pipeline:
- Không nhận NaN: điền trung vị (SimpleImputer). Cột "<tên>_thieu" của
  dac_trung.py vẫn giữ thông tin "ô này từng trống".
- Nhạy với thang đo (TCTL tới 150, ĐTB chỉ 0–4): chuẩn hoá (StandardScaler).
Đặt cả hai trong pipeline để mỗi fold chỉ học trung vị / trung bình / độ lệch
từ phần train, không rò thông tin của phần test.

SVC chỉ cho điểm khoảng cách tới mặt phân cách, không cho xác suất; bọc trong
CalibratedClassifierCV (Platt scaling, cách scikit-learn 1.9 khuyên dùng thay
cho SVC(probability=True) đã bị bỏ) để có predict_proba. Xác suất sau hiệu
chỉnh bám tỉ lệ ca dương thật (~6%) nên hiếm khi vượt 0,5: recall ở ngưỡng 0,5
thấp, cần chọn ngưỡng riêng; PR-AUC không phụ thuộc ngưỡng nên vẫn so được.

Chạy:  python ml/svm.py
"""

from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from danh_gia import SEED, chay_thu


THAM_SO = {"kernel": "rbf", "C": 1.0, "gamma": "scale", "class_weight": "balanced",
           "random_state": SEED}


def tao_mo_hinh():
    return make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        CalibratedClassifierCV(SVC(**THAM_SO), method="sigmoid", ensemble=False),
    )


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "SVM")
