"""
Đánh giá mô hình dùng chung cho cả 5 phương pháp.

- Chia dữ liệu bằng StratifiedGroupKFold theo mã sinh viên: một sinh viên chỉ
  nằm trọn ở train hoặc ở test (các học kỳ của cùng một người rất giống nhau,
  chia ngẫu nhiên theo dòng sẽ cho điểm đẹp giả), đồng thời giữ tỉ lệ ca
  dương gần đều giữa các fold.
- Chỉ số chính là PR-AUC (average precision): dữ liệu chỉ ~6% ca dương nên
  accuracy vô nghĩa (đoán "không" hết cũng được 94%). Kèm ROC-AUC và
  precision / recall / F1 tại một ngưỡng.
- Baseline là luật đơn giản (LuatDonGian); mô hình phải vượt baseline mới có ý nghĩa.

Mỗi file phương pháp chỉ cần một hàm tao_mo_hinh() trả về mô hình MỚI, chưa
huấn luyện, có fit(X, y) và predict_proba(X) như scikit-learn.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold


SO_FOLD = 5
SEED = 42
NGUONG_MAC_DINH = 0.5
CAC_CHI_SO = ["pr_auc", "roc_auc", "precision", "recall", "f1"]


def tinh_chi_so(y, xac_suat, nguong=NGUONG_MAC_DINH):
    """Các chỉ số cho lớp dương (nhãn 1) từ xác suất dự đoán."""
    y = np.asarray(y)
    xac_suat = np.asarray(xac_suat, dtype=float)
    du_doan = (xac_suat >= nguong).astype(int)
    return {
        "pr_auc": average_precision_score(y, xac_suat),
        "roc_auc": roc_auc_score(y, xac_suat),
        "precision": precision_score(y, du_doan, zero_division=0),
        "recall": recall_score(y, du_doan, zero_division=0),
        "f1": f1_score(y, du_doan, zero_division=0),
    }


def chia_fold(y, nhom, so_fold=SO_FOLD, seed=SEED):
    """Số thứ tự fold (0..so_fold−1) của từng dòng; cùng sinh viên cùng fold."""
    chia = StratifiedGroupKFold(n_splits=so_fold, shuffle=True, random_state=seed)
    fold = np.empty(len(y), dtype=int)
    for i, (_, chi_so_test) in enumerate(chia.split(np.zeros(len(y)), y, groups=nhom)):
        fold[chi_so_test] = i
    return pd.Series(fold, index=y.index, name="fold")


def danh_gia_cheo(tao_mo_hinh, X, y, nhom, so_fold=SO_FOLD, seed=SEED, nguong=NGUONG_MAC_DINH):
    """Cross-validation theo nhóm sinh viên.

    Trả về:
        bang:     DataFrame mỗi fold một dòng, cột là CAC_CHI_SO.
        xac_suat: Series xác suất dự đoán "ngoài fold" cho từng dòng của X
                  (mỗi dòng được dự đoán đúng một lần, bởi mô hình không thấy
                  nó lúc huấn luyện); dùng để chọn ngưỡng, suy nguy cơ thôi học...
    """
    fold = chia_fold(y, nhom, so_fold, seed)
    xac_suat = pd.Series(np.nan, index=X.index, name="xac_suat")
    cac_dong = []
    for i in range(so_fold):
        train, test = fold != i, fold == i
        mo_hinh = tao_mo_hinh().fit(X[train], y[train])
        xac_suat[test] = mo_hinh.predict_proba(X[test])[:, 1]
        cac_dong.append(tinh_chi_so(y[test], xac_suat[test], nguong))
    return pd.DataFrame(cac_dong)[CAC_CHI_SO], xac_suat


def tom_tat(bang):
    """Trung bình ± độ lệch chuẩn qua các fold, dạng chuỗi để in."""
    return {cot: f"{bang[cot].mean():.3f} ± {bang[cot].std():.3f}" for cot in CAC_CHI_SO}


class LuatDonGian:
    """Baseline: một luật if-else biến X thành điểm nguy cơ, không học gì.

    `ham_diem(X)` trả về mảng điểm trong [0, 1] (luật có / không thì 0 hoặc 1).
    Có fit / predict_proba để đánh giá y như một mô hình.
    """

    def __init__(self, ham_diem):
        self.ham_diem = ham_diem

    def fit(self, X, y):
        return self

    def predict_proba(self, X):
        diem = np.asarray(self.ham_diem(X), dtype=float)
        return np.column_stack([1 - diem, diem])


# Luật baseline cho từng mục tiêu (dùng tên cột của dac_trung.py)
BASELINE = {
    # Kỳ này đã bị cảnh báo hoặc ĐTB học kỳ thấp -> kỳ sau bị cảnh báo
    "canh_bao": lambda X: ((X["canh_bao"] == 1) | (X["dtb_hk"] < 1.5)).astype(float),
    # Đã bị cảnh báo 2 kỳ liên tiếp -> kỳ sau bị buộc thôi học
    "thoi_hoc": lambda X: (X["so_lan_canh_bao_lien_tiep"] >= 2).astype(float),
    # Điểm giữa kỳ dưới 4 hoặc vắng lý thuyết trên 20% -> trượt
    "truot_mon": lambda X: ((X["diem_gk"] < 4) | (X["vang_lt"] == 2)).astype(float),
}


def tao_baseline_tu(ham_diem):
    """Hàm tạo mô hình từ một luật bất kỳ, cùng kiểu với tao_mo_hinh()."""
    return lambda: LuatDonGian(ham_diem)


def tao_baseline(muc_tieu):
    """Hàm tạo mô hình baseline của một mục tiêu."""
    return tao_baseline_tu(BASELINE[muc_tieu])
