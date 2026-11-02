"""
Mô hình cuối: chọn, huấn luyện, lưu và dùng để dự đoán.

1. Chọn phương pháp: với mỗi mục tiêu, lấy phương pháp có PR-AUC trung bình
   cao nhất trong results/so_sanh_tom_tat.csv (kết quả của so_sanh.py) — quy
   tắc cố định, không chọn tay.
2. Huấn luyện: chọn cấu hình tham số và ngưỡng F2 bằng đúng cách của
   danh_gia.py (3 fold trong theo sinh viên) nhưng trên TOÀN BỘ dữ liệu, rồi
   train lại trên toàn bộ dữ liệu.
3. Lưu models/<muc_tieu>.joblib: mô hình, ngưỡng, danh sách cột, phương pháp,
   cấu hình, PR-AUC lúc so sánh... (models/ không commit: chạy lại file này).
4. du_doan(): đọc file form (thật hoặc mô phỏng), trả về xác suất, có báo
   động không và lý do (SHAP) cho từng sinh viên / môn. Web app chỉ gọi hàm
   này với mô hình đã lưu, không train lúc mở trang.

Mục tiêu có mô hình riêng: "canh_bao" và "truot_mon". "thoi_hoc" suy từ mô
hình cảnh báo (dac_trung.nguy_co_thoi_hoc, Điều 18.2a) như đã chốt.

Chạy:  python ml/mo_hinh_cuoi.py            # train + lưu + vẽ SHAP
       python ml/mo_hinh_cuoi.py --du-doan "đường/dẫn/file.xlsx"
"""

import argparse
import os
import sys
from datetime import datetime

import joblib
import pandas as pd

import dac_trung
import danh_gia
import decision_tree
import giai_thich
import lightgbm_model
import random_forest
import svm
import xgboost_model


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_MO_HINH = os.path.join(THU_MUC_GOC, "models")
DUONG_DAN_TOM_TAT = os.path.join(THU_MUC_GOC, "results", "so_sanh_tom_tat.csv")

# Thứ tự cố định (so_sanh.py dùng chung danh sách này)
PHUONG_PHAP = {
    "Decision Tree": decision_tree,
    "SVM": svm,
    "XGBoost": xgboost_model,
    "Random Forest": random_forest,
    "LightGBM": lightgbm_model,
}
MUC_TIEU_CO_MO_HINH = ("canh_bao", "truot_mon")
TEN_MUC_TIEU = {"canh_bao": "cảnh báo học tập kỳ sau", "truot_mon": "trượt môn"}


def chon_phuong_phap(muc_tieu, duong_dan_tom_tat=DUONG_DAN_TOM_TAT):
    """Tên phương pháp có PR-AUC trung bình cao nhất cho mục tiêu (bỏ baseline)."""
    tom = pd.read_csv(duong_dan_tom_tat)
    tom = tom[(tom["muc_tieu"] == muc_tieu) & tom["phuong_phap"].isin(PHUONG_PHAP)]
    if tom.empty:
        raise ValueError(f"{duong_dan_tom_tat} chưa có kết quả cho {muc_tieu!r}: chạy so_sanh.py trước")
    dong = tom.loc[tom["pr_auc_tb"].idxmax()]
    return dong["phuong_phap"], float(dong["pr_auc_tb"])


def _duong_dan(muc_tieu, thu_muc):
    return os.path.join(thu_muc, f"{muc_tieu}.joblib")


def huan_luyen(muc_tieu, duong_dan=None, thu_muc=THU_MUC_MO_HINH,
               duong_dan_tom_tat=DUONG_DAN_TOM_TAT):
    """Chọn phương pháp, cấu hình, ngưỡng; train trên toàn bộ dữ liệu; lưu file."""
    if muc_tieu not in MUC_TIEU_CO_MO_HINH:
        raise ValueError(f"muc_tieu phải là một trong {MUC_TIEU_CO_MO_HINH}")
    ten, pr_auc = chon_phuong_phap(muc_tieu, duong_dan_tom_tat)
    mod = PHUONG_PHAP[ten]

    X, y, nhom = dac_trung.tao_du_lieu(muc_tieu, duong_dan)
    cau_hinh, nguong = danh_gia.chon_cau_hinh(mod.tao_mo_hinh, getattr(mod, "LUOI_THAM_SO", None),
                                              X, y, nhom)
    mo_hinh = mod.tao_mo_hinh(**cau_hinh).fit(X, y)

    goi = {
        "muc_tieu": muc_tieu, "phuong_phap": ten, "cau_hinh": cau_hinh,
        "nguong": nguong, "cot": list(X.columns), "mo_hinh": mo_hinh,
        "pr_auc_so_sanh": pr_auc, "so_dong": len(X), "ti_le_duong": float(y.mean()),
        "du_lieu": os.path.basename(duong_dan or dac_trung.DUONG_DAN_MAC_DINH),
        "thoi_diem": datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(thu_muc, exist_ok=True)
    joblib.dump(goi, _duong_dan(muc_tieu, thu_muc))
    return goi


def tai(muc_tieu, thu_muc=THU_MUC_MO_HINH):
    """Đọc gói mô hình đã lưu; báo rõ cách tạo nếu chưa có."""
    duong_dan = _duong_dan(muc_tieu, thu_muc)
    if not os.path.exists(duong_dan):
        raise FileNotFoundError(f"Chưa có {duong_dan}: chạy python ml/mo_hinh_cuoi.py để train và lưu")
    return joblib.load(duong_dan)


def du_doan(duong_dan, muc_tieu, thu_muc=THU_MUC_MO_HINH, so_ly_do=3):
    """Dự đoán cho file form `duong_dan`.

    - "canh_bao" / "thoi_hoc": mỗi sinh viên hợp lệ một dòng, dự đoán cho học
      kỳ kế tiếp học kỳ gần nhất đã học xong.
    - "truot_mon": mỗi môn của học kỳ gần nhất một dòng.

    Trả về DataFrame: thông tin (ma_sv, hoc_ky, ...), xac_suat, bao_dong
    (xac_suat >= ngưỡng F2 đã chọn), ly_do (list chuỗi; rỗng khi không báo
    động — đặc trưng đẩy nguy cơ 1% lên 2% không phải "lý do" để nói).

    xac_suat dùng để XẾP HẠNG và so với ngưỡng; nó chưa được hiệu chỉnh nên
    không nên hiển thị như "x% khả năng" (LightGBM cho giá trị rất sát 0 / 1).
    """
    if muc_tieu not in dac_trung.MUC_TIEU:
        raise ValueError(f"muc_tieu phải là một trong {dac_trung.MUC_TIEU}")
    goi = tai("truot_mon" if muc_tieu == "truot_mon" else "canh_bao", thu_muc)
    X, thong_tin = dac_trung.dac_trung_du_doan(muc_tieu, duong_dan)
    X = X[goi["cot"]]            # đúng thứ tự cột lúc train

    xac_suat = pd.Series(goi["mo_hinh"].predict_proba(X)[:, 1], index=X.index)
    if muc_tieu == "thoi_hoc":
        xac_suat = dac_trung.nguy_co_thoi_hoc(xac_suat, X["so_lan_canh_bao_lien_tiep"])

    ket_qua = thong_tin.copy()
    ket_qua["xac_suat"] = xac_suat.round(4)
    ket_qua["bao_dong"] = xac_suat >= goi["nguong"]
    ly_do = giai_thich.ly_do(goi["mo_hinh"], X, so_ly_do) if len(X) else []
    ket_qua["ly_do"] = [ld if bd else [] for ld, bd in zip(ly_do, ket_qua["bao_dong"])]
    return ket_qua


def ve_shap(muc_tieu, thu_muc=THU_MUC_MO_HINH, duong_dan=None):
    """Vẽ biểu đồ SHAP của mô hình đã lưu trên dữ liệu huấn luyện."""
    goi = tai(muc_tieu, thu_muc)
    X, _, _ = dac_trung.tao_du_lieu(muc_tieu, duong_dan)
    return giai_thich.ve_bieu_do(
        goi["mo_hinh"], X[goi["cot"]],
        f"Ảnh hưởng tới nguy cơ {TEN_MUC_TIEU[muc_tieu]} ({goi['phuong_phap']})",
        os.path.join(giai_thich.THU_MUC_KET_QUA, f"shap_{muc_tieu}.png"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 120)

    tham_so = argparse.ArgumentParser(description="Train / dự đoán với mô hình cuối")
    tham_so.add_argument("--du-doan", metavar="FILE_XLSX", help="chỉ dự đoán file này (không train)")
    tham_so.add_argument("--du-lieu", default=None, help="file train (mặc định data/mo_phong.xlsx)")
    a = tham_so.parse_args()

    if a.du_doan:
        for muc_tieu in dac_trung.MUC_TIEU:
            kq = du_doan(a.du_doan, muc_tieu)
            print(f"\n=== {muc_tieu}: {int(kq['bao_dong'].sum())}/{len(kq)} báo động ===")
            print(kq.sort_values("xac_suat", ascending=False).head(10).to_string(index=False))
    else:
        for muc_tieu in MUC_TIEU_CO_MO_HINH:
            goi = huan_luyen(muc_tieu, a.du_lieu)
            print(f"{muc_tieu}: {goi['phuong_phap']} {goi['cau_hinh']}, ngưỡng F2 = {goi['nguong']:.3f}, "
                  f"PR-AUC lúc so sánh = {goi['pr_auc_so_sanh']:.3f}, {goi['so_dong']} dòng "
                  f"→ {_duong_dan(muc_tieu, THU_MUC_MO_HINH)}")
            print(f"  SHAP → {ve_shap(muc_tieu, duong_dan=a.du_lieu)}")
