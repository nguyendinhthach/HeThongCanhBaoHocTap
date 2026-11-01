"""
Đánh giá mô hình dùng chung cho cả 5 phương pháp.

- Chia dữ liệu bằng StratifiedGroupKFold theo mã sinh viên: một sinh viên chỉ
  nằm trọn ở train hoặc ở test (các học kỳ của cùng một người rất giống nhau,
  chia ngẫu nhiên theo dòng sẽ cho điểm đẹp giả), đồng thời giữ tỉ lệ ca
  dương gần đều giữa các fold.
- So sánh mô hình bằng PR-AUC (average precision): dữ liệu chỉ ~6% ca dương
  nên accuracy vô nghĩa (đoán "không" hết cũng được 94%).
- Ngưỡng báo động chọn theo F2-score: đề cương ưu tiên Recall/F1 vì bỏ sót
  sinh viên có nguy cơ nặng hơn báo nhầm; F2 coi recall nặng gấp đôi
  precision nhưng không bỏ mặc precision (ép recall cao thì báo động cả lớp).
- Cross-validation lồng nhau: ở mỗi fold ngoài, chỉ dùng phần train để chọn
  cấu hình tham số (PR-AUC qua 3 fold trong, cũng chia theo sinh viên) và
  chọn ngưỡng (F2 trên xác suất ngoài fold trong), rồi huấn luyện lại trên
  toàn phần train và đo trên phần test. Phần test không ảnh hưởng tới lựa
  chọn nào nên điểm không bị đẹp giả.
- Baseline là luật đơn giản (LuatDonGian); mô hình phải vượt baseline mới có ý nghĩa.

Mỗi file phương pháp cần:
- tao_mo_hinh(**tham_so): trả về mô hình MỚI, chưa huấn luyện, có fit(X, y)
  và predict_proba(X) như scikit-learn; tham_so ghi đè tham số mặc định.
- LUOI_THAM_SO: dict {tên tham số: [các giá trị thử]} (~6 cấu hình để các
  phương pháp được chỉnh công bằng như nhau); None = không chỉnh.
- __main__: chay_thu(tao_mo_hinh, "Tên phương pháp", LUOI_THAM_SO).
"""

import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import (average_precision_score, f1_score, fbeta_score,
                             precision_recall_curve, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import ParameterGrid, StratifiedGroupKFold

import dac_trung


SO_FOLD = 5
SO_FOLD_TRONG = 3
SEED = 42
BETA = 2                     # F2: recall nặng gấp đôi precision
SO_LUONG_SONG_SONG = -1      # số tiến trình chạy song song (-1 = mọi nhân CPU)
CAC_CHI_SO = ["pr_auc", "roc_auc", "precision", "recall", "f1", "f2", "nguong"]


def tinh_chi_so(y, xac_suat, nguong):
    """Các chỉ số cho lớp dương (nhãn 1) từ xác suất dự đoán và ngưỡng."""
    y = np.asarray(y)
    xac_suat = np.asarray(xac_suat, dtype=float)
    du_doan = (xac_suat >= nguong).astype(int)
    return {
        "pr_auc": average_precision_score(y, xac_suat),
        "roc_auc": roc_auc_score(y, xac_suat),
        "precision": precision_score(y, du_doan, zero_division=0),
        "recall": recall_score(y, du_doan, zero_division=0),
        "f1": f1_score(y, du_doan, zero_division=0),
        "f2": fbeta_score(y, du_doan, beta=BETA, zero_division=0),
        "nguong": float(nguong),
    }


def chon_nguong(y, xac_suat, beta=BETA):
    """Ngưỡng cho F-beta lớn nhất trên (y, xac_suat)."""
    precision, recall, cac_nguong = precision_recall_curve(y, xac_suat)
    precision, recall = precision[:-1], recall[:-1]   # điểm cuối không ứng với ngưỡng nào
    f_beta = (1 + beta ** 2) * precision * recall / np.maximum(beta ** 2 * precision + recall, 1e-12)
    return float(cac_nguong[np.argmax(f_beta)])


def chia_fold(y, nhom, so_fold=SO_FOLD, seed=SEED):
    """Số thứ tự fold (0..so_fold−1) của từng dòng; cùng sinh viên cùng fold."""
    chia = StratifiedGroupKFold(n_splits=so_fold, shuffle=True, random_state=seed)
    fold = np.empty(len(y), dtype=int)
    for i, (_, chi_so_test) in enumerate(chia.split(np.zeros(len(y)), y, groups=nhom)):
        fold[chi_so_test] = i
    return pd.Series(fold, index=y.index, name="fold")


def _du_doan_mot_fold(tao_mo_hinh, cau_hinh, X, y, train, test):
    mo_hinh = tao_mo_hinh(**cau_hinh).fit(X[train], y[train])
    return mo_hinh.predict_proba(X[test])[:, 1]


def chon_cau_hinh(tao_mo_hinh, luoi, X, y, nhom, seed=SEED):
    """Chọn cấu hình tham số và ngưỡng chỉ từ (X, y) — phần train của fold ngoài.

    Mỗi cấu hình chạy SO_FOLD_TRONG fold trong theo sinh viên; giữ cấu hình có
    PR-AUC (trên xác suất ngoài fold trong) cao nhất, ngưỡng = F2 lớn nhất trên
    chính các xác suất đó. Trả về (cấu hình, ngưỡng).
    """
    cac_cau_hinh = list(ParameterGrid(luoi)) if luoi else [{}]
    fold = chia_fold(y, nhom, SO_FOLD_TRONG, seed)
    cong_viec = [(c, i) for c in range(len(cac_cau_hinh)) for i in range(SO_FOLD_TRONG)]
    ket_qua = Parallel(n_jobs=SO_LUONG_SONG_SONG)(
        delayed(_du_doan_mot_fold)(tao_mo_hinh, cac_cau_hinh[c], X, y, fold != i, fold == i)
        for c, i in cong_viec)

    xac_suat = {c: pd.Series(np.nan, index=y.index) for c in range(len(cac_cau_hinh))}
    for (c, i), du_doan in zip(cong_viec, ket_qua):
        xac_suat[c][fold == i] = du_doan
    diem = [average_precision_score(y, xac_suat[c]) for c in range(len(cac_cau_hinh))]
    tot_nhat = int(np.argmax(diem))
    return cac_cau_hinh[tot_nhat], chon_nguong(y, xac_suat[tot_nhat])


def danh_gia_cheo(tao_mo_hinh, X, y, nhom, luoi=None, so_fold=SO_FOLD, seed=SEED):
    """Cross-validation lồng nhau theo nhóm sinh viên.

    Trả về:
        bang:     DataFrame mỗi fold ngoài một dòng: CAC_CHI_SO + "cau_hinh"
                  (cấu hình được chọn ở fold đó).
        xac_suat: Series xác suất ngoài fold của từng dòng X (mỗi dòng được
                  dự đoán đúng một lần, bởi mô hình không thấy nó lúc huấn luyện).
        nguong:   Series ngưỡng đã dùng cho từng dòng (ngưỡng của fold chứa nó).
    """
    fold = chia_fold(y, nhom, so_fold, seed)
    xac_suat = pd.Series(np.nan, index=X.index, name="xac_suat")
    nguong = pd.Series(np.nan, index=X.index, name="nguong")
    cac_dong = []
    for i in range(so_fold):
        train, test = fold != i, fold == i
        cau_hinh, nguong_fold = chon_cau_hinh(tao_mo_hinh, luoi, X[train], y[train],
                                             nhom[train], seed)
        mo_hinh = tao_mo_hinh(**cau_hinh).fit(X[train], y[train])
        xac_suat[test] = mo_hinh.predict_proba(X[test])[:, 1]
        nguong[test] = nguong_fold
        cac_dong.append({**tinh_chi_so(y[test], xac_suat[test], nguong_fold),
                         "cau_hinh": str(cau_hinh)})
    return pd.DataFrame(cac_dong), xac_suat, nguong


def tom_tat(bang):
    """Trung bình ± độ lệch chuẩn qua các fold, dạng chuỗi để in."""
    return {cot: f"{bang[cot].mean():.3f} ± {bang[cot].std():.3f}" for cot in CAC_CHI_SO}


def danh_gia_thoi_hoc_suy_ra(xac_suat_canh_bao, nguong, X_canh_bao, y_thoi_hoc, fold):
    """Chỉ số thôi học suy từ nguy cơ cảnh báo (cách chính, Điều 18.2a), theo fold.

    Dùng đúng xác suất và ngưỡng ngoài fold của mô hình cảnh báo, nên không
    cần huấn luyện thêm gì.
    """
    nguy_co = dac_trung.nguy_co_thoi_hoc(xac_suat_canh_bao, X_canh_bao["so_lan_canh_bao_lien_tiep"])
    cac_dong = []
    for i in sorted(fold.unique()):
        o = fold == i
        cac_dong.append(tinh_chi_so(y_thoi_hoc[o], nguy_co[o], nguong[o].iloc[0]))
    return pd.DataFrame(cac_dong)


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


def chay_thu(tao_mo_hinh, ten_phuong_phap, luoi=None, duong_dan=None):
    """Đánh giá chéo lồng nhau một phương pháp trên 3 mục tiêu, in bảng so với baseline.

    Dùng chung cho mọi file phương pháp. Với "canh_bao" in thêm dòng thôi học
    suy từ nguy cơ cảnh báo (cách chính cho mục tiêu buộc thôi học).
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pd.set_option("display.width", 220)
    so_cau_hinh = len(ParameterGrid(luoi)) if luoi else 1
    print(f"{ten_phuong_phap}: {SO_FOLD}-fold theo sinh viên, mỗi fold chọn 1/{so_cau_hinh} "
          f"cấu hình và ngưỡng F{BETA} bằng {SO_FOLD_TRONG}-fold trong; "
          "số liệu: trung bình ± độ lệch chuẩn qua các fold")

    for muc_tieu in dac_trung.MUC_TIEU:
        X, y, nhom = dac_trung.tao_du_lieu(muc_tieu, duong_dan)
        print(f"\n=== {muc_tieu}: {len(X)} dòng, {int(y.sum())} ca dương ({y.mean():.1%}), "
              f"{nhom.nunique()} sinh viên ===")

        dong, cau_hinh = {}, None
        for ten, tao, luoi_ in [("Baseline luật", tao_baseline(muc_tieu), None),
                                (ten_phuong_phap, tao_mo_hinh, luoi)]:
            bang, xac_suat, nguong = danh_gia_cheo(tao, X, y, nhom, luoi_)
            dong[ten] = tom_tat(bang)
            cau_hinh = bang["cau_hinh"]
            if muc_tieu == "canh_bao":
                _, y_thoi_hoc, _ = dac_trung.tao_du_lieu("thoi_hoc", duong_dan)
                suy_ra = danh_gia_thoi_hoc_suy_ra(xac_suat, nguong, X, y_thoi_hoc,
                                                  chia_fold(y, nhom))
                dong[f"{ten} → thôi học (suy từ cảnh báo)"] = tom_tat(suy_ra)
        print(pd.DataFrame(dong).T.to_string())
        if luoi:
            print("Cấu hình được chọn ở từng fold:", "; ".join(cau_hinh))
