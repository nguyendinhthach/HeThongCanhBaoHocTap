"""
Decision Tree cho 3 mục tiêu cảnh báo — cũng là file MẪU cho các phương pháp khác.

Mỗi file phương pháp chỉ cần:
1. tao_mo_hinh(): trả về một mô hình MỚI, chưa huấn luyện, có fit(X, y) và
   predict_proba(X). Phần dữ liệu lấy từ dac_trung.tao_du_lieu(), phần đánh
   giá dùng danh_gia.danh_gia_cheo() — không tự đọc form hay tự chia dữ liệu.
2. Phần chạy thử (__main__) giống file này: in bảng so với baseline luật.

DecisionTreeClassifier của scikit-learn (từ bản 1.3) nhận NaN trực tiếp nên
không cần điền ô trống; class_weight="balanced" bù cho việc chỉ ~6% ca dương.

Chạy:  python ml/decision_tree.py
"""

import sys

import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import dac_trung
import danh_gia


# Cây nông + lá đủ lớn để không học thuộc từng sinh viên; chỉnh ở bước so sánh sau
THAM_SO = {"max_depth": 5, "min_samples_leaf": 20, "class_weight": "balanced",
           "random_state": danh_gia.SEED}


def tao_mo_hinh():
    return DecisionTreeClassifier(**THAM_SO)


def chay_thu(tao_mo_hinh, ten_phuong_phap):
    """Đánh giá chéo một phương pháp trên 3 mục tiêu, in bảng so với baseline.

    Dùng chung được cho mọi file phương pháp: chỉ cần truyền tao_mo_hinh của file đó.
    """
    pd.set_option("display.width", 200)
    for muc_tieu in dac_trung.MUC_TIEU:
        X, y, nhom = dac_trung.tao_du_lieu(muc_tieu)
        print(f"\n=== {muc_tieu}: {len(X)} dòng, {int(y.sum())} ca dương ({y.mean():.1%}), "
              f"{nhom.nunique()} sinh viên ===")

        dong = {}
        for ten, tao in [("Baseline luật", danh_gia.tao_baseline(muc_tieu)),
                         (ten_phuong_phap, tao_mo_hinh)]:
            bang, xac_suat = danh_gia.danh_gia_cheo(tao, X, y, nhom)
            dong[ten] = danh_gia.tom_tat(bang)
            if muc_tieu == "canh_bao":
                # Cách chính cho buộc thôi học: suy từ nguy cơ cảnh báo kỳ sau
                _, y_thoi_hoc, _ = dac_trung.tao_du_lieu("thoi_hoc")
                nguy_co = dac_trung.nguy_co_thoi_hoc(xac_suat, X["so_lan_canh_bao_lien_tiep"])
                suy_ra = danh_gia.tinh_chi_so(y_thoi_hoc, nguy_co)
                dong[f"{ten} → thôi học (suy từ cảnh báo)"] = {
                    k: f"{v:.3f}" for k, v in suy_ra.items()}
        print(pd.DataFrame(dong).T.to_string())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("Decision Tree, 5-fold theo sinh viên; số liệu: trung bình ± độ lệch chuẩn qua các fold")
    chay_thu(tao_mo_hinh, "Decision Tree")
