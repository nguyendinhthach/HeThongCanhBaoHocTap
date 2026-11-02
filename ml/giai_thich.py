"""SHAP explanations for the three student-risk prediction targets.

Run: python ml/giai_thich.py
"""

import os
import sys
from functools import lru_cache

THU_MUC_ML = os.path.dirname(os.path.abspath(__file__))
if THU_MUC_ML not in sys.path:
    sys.path.insert(0, THU_MUC_ML)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

import dac_trung
import lightgbm_model
import xgboost_model


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_KET_QUA = os.path.join(THU_MUC_GOC, "results")

# Best XGBoost/LightGBM model and most frequent CV configuration per target
# from results/so_sanh_tom_tat.csv and results/so_sanh_chi_tiet.csv.
MO_HINH_THEO_MUC_TIEU = {
    "canh_bao": (xgboost_model.tao_mo_hinh,
                 {"max_depth": 2, "learning_rate": 0.05}),
    "thoi_hoc": (lightgbm_model.tao_mo_hinh,
                 {"num_leaves": 31, "learning_rate": 0.1,
                  "min_child_samples": 30}),
    "truot_mon": (lightgbm_model.tao_mo_hinh,
                  {"num_leaves": 15, "learning_rate": 0.05,
                   "min_child_samples": 10}),
}

TEN_DAC_TRUNG = {
    "hoc_ky": "Số thứ tự học kỳ",
    "tc_dat_hk": "Tín chỉ đạt trong học kỳ",
    "dtb_hk": "Điểm trung bình học kỳ (thang 4)",
    "tctl": "Tín chỉ tích lũy",
    "no_tc": "Tín chỉ còn nợ",
    "dtb_tl": "Điểm trung bình tích lũy (thang 4)",
    "trinh_do": "Trình độ năm theo tín chỉ tích lũy",
    "drl": "Điểm rèn luyện",
    "canh_bao": "Cảnh báo học vụ trong học kỳ",
    "so_lan_canh_bao_lien_tiep": "Số học kỳ bị cảnh báo liên tiếp",
    "ky_su": "Hệ đào tạo kỹ sư",
    "muc_vang": "Mức vắng học",
    "dtb_hk_thay_doi": "Thay đổi điểm trung bình học kỳ",
    "drl_thieu": "Thiếu điểm rèn luyện",
    "muc_vang_thieu": "Thiếu thông tin mức vắng",
    "dtb_hk_thay_doi_thieu": "Thiếu dữ liệu điểm kỳ trước",
    "hoc_phi_dung_han": "Học phí đóng đúng hạn",
    "hoc_phi_tre_han": "Học phí đóng trễ hạn",
    "hoc_phi_chua_du": "Học phí chưa đóng đủ",
    "hoc_phi_mien": "Được miễn học phí",
    "hoc_phi_khong_tra_loi": "Tình trạng học phí không rõ",
}


def _gia_tri_shap(mo_hinh: object, X: pd.DataFrame) -> np.ndarray:
    """Lấy SHAP values của lớp nguy cơ (nhãn 1), chuẩn hoá các shape phổ biến."""
    gia_tri = shap.TreeExplainer(mo_hinh).shap_values(X)
    if isinstance(gia_tri, list):
        if len(gia_tri) < 2:
            raise ValueError("SHAP không trả về giá trị cho lớp nguy cơ.")
        gia_tri = gia_tri[1]

    gia_tri = np.asarray(gia_tri)
    if gia_tri.shape == X.shape:
        return gia_tri
    if gia_tri.ndim == 3:
        if gia_tri.shape[:2] == X.shape:
            return gia_tri[:, :, -1]
        if gia_tri.shape[1:] == X.shape:
            return gia_tri[-1]
    raise ValueError(
        f"SHAP values có shape {gia_tri.shape}, không khớp dữ liệu {X.shape}."
    )


def ly_do(mo_hinh, X: pd.DataFrame, so_ly_do: int = 3) -> list[list[str]]:
    """Trả về các đặc trưng ảnh hưởng mạnh nhất cho từng dòng, kèm chiều tác động.

    Mỗi dòng là một danh sách tối đa `so_ly_do` chuỗi; giá trị SHAP dương làm
    tăng nguy cơ, giá trị âm làm giảm nguy cơ. Giao diện hiển thị danh sách này
    cùng dự đoán hiện tại, không ghi vào lịch sử SQL.
    """
    if so_ly_do < 1:
        raise ValueError("so_ly_do phải lớn hơn 0.")

    gia_tri_shap = _gia_tri_shap(mo_hinh, X)
    ket_qua = []
    for vi_tri, dong_shap in enumerate(gia_tri_shap):
        muc = np.argsort(np.abs(dong_shap))[::-1][:so_ly_do]
        ly_do_dong = []
        for i in muc:
            gia_tri = X.iat[vi_tri, i]
            gia_tri_text = "thiếu" if pd.isna(gia_tri) else f"{float(gia_tri):g}"
            if dong_shap[i] > 0:
                huong = "tăng nguy cơ"
            elif dong_shap[i] < 0:
                huong = "giảm nguy cơ"
            else:
                huong = "ít ảnh hưởng"
            ten = TEN_DAC_TRUNG.get(X.columns[i], X.columns[i])
            ly_do_dong.append(f"{ten} = {gia_tri_text} ({huong})")
        ket_qua.append(ly_do_dong)
    return ket_qua


@lru_cache(maxsize=len(MO_HINH_THEO_MUC_TIEU))
def mo_hinh_tai(muc_tieu: str) -> tuple[object, tuple[str, ...]]:
    """Huấn luyện và giữ mô hình trong bộ nhớ để giao diện tái sử dụng."""
    if muc_tieu not in MO_HINH_THEO_MUC_TIEU:
        raise ValueError(f"Mục tiêu không hợp lệ: {muc_tieu!r}")

    X, y, _ = dac_trung.tao_du_lieu(muc_tieu)
    tao_mo_hinh, tham_so = MO_HINH_THEO_MUC_TIEU[muc_tieu]
    mo_hinh = tao_mo_hinh(**tham_so).fit(X, y)
    return mo_hinh, tuple(X.columns)


def _ve_bieu_do(gia_tri_shap: np.ndarray, X: pd.DataFrame,
                muc_tieu: str) -> str:
    os.makedirs(THU_MUC_KET_QUA, exist_ok=True)
    shap.summary_plot(gia_tri_shap, X, plot_type="bar", show=False, max_display=20)
    plt.title(f"Đặc trưng ảnh hưởng đến nguy cơ: {muc_tieu}")
    plt.tight_layout()
    duong_dan = os.path.join(THU_MUC_KET_QUA, f"shap_{muc_tieu}.png")
    plt.savefig(duong_dan, dpi=150, bbox_inches="tight")
    plt.close()
    return duong_dan


def tao_bieu_do(muc_tieu: str) -> tuple[object, pd.DataFrame, str]:
    """Huấn luyện cấu hình đã chọn trên toàn bộ dữ liệu và lưu biểu đồ SHAP."""
    if muc_tieu not in MO_HINH_THEO_MUC_TIEU:
        raise ValueError(f"Mục tiêu không hợp lệ: {muc_tieu!r}")

    X, _, _ = dac_trung.tao_du_lieu(muc_tieu)
    mo_hinh, _ = mo_hinh_tai(muc_tieu)
    duong_dan = _ve_bieu_do(_gia_tri_shap(mo_hinh, X), X, muc_tieu)
    return mo_hinh, X, duong_dan


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for muc_tieu in dac_trung.MUC_TIEU:
        _, _, duong_dan = tao_bieu_do(muc_tieu)
        print(f"{muc_tieu}: đã lưu {duong_dan}")
