"""
Giải thích dự đoán bằng SHAP cho các mô hình cây (Decision Tree, Random Forest,
XGBoost, LightGBM).

- ly_do(): với từng dòng, các đặc trưng đẩy nguy cơ LÊN nhiều nhất — dùng cho
  mục "Lý do chính" hiển thị cho sinh viên. Đặc trưng làm giảm nguy cơ, ô
  trống và cột đánh dấu thiếu ("_thieu") không phải lý do nên bị bỏ qua.
- ve_bieu_do(): biểu đồ mức ảnh hưởng trung bình của từng đặc trưng.

Mô hình lấy từ mo_hinh_cuoi.py (đã train và lưu ở models/).

Chạy:  python ml/giai_thich.py     # vẽ lại biểu đồ SHAP từ mô hình đã lưu
"""

import os
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_KET_QUA = os.path.join(THU_MUC_GOC, "results")

TEN_DAC_TRUNG = {
    # Học kỳ (mục tiêu cảnh báo / thôi học)
    "hoc_ky": "Số thứ tự học kỳ",
    "tc_dat_hk": "Tín chỉ đạt trong học kỳ",
    "dtb_hk": "Điểm trung bình học kỳ (thang 4)",
    "tctl": "Tín chỉ tích lũy",
    "no_tc": "Tín chỉ còn nợ",
    "dtb_tl": "Điểm trung bình tích lũy (thang 4)",
    "trinh_do": "Trình độ năm theo tín chỉ tích lũy",
    "drl": "Điểm rèn luyện",
    "canh_bao": "Đang bị cảnh báo học tập",
    "so_lan_canh_bao_lien_tiep": "Số học kỳ bị cảnh báo liên tiếp",
    "ky_su": "Hệ đào tạo kỹ sư",
    "muc_vang": "Mức vắng học (0–3)",
    "dtb_hk_thay_doi": "Điểm trung bình học kỳ tăng / giảm so với kỳ trước",
    "hoc_phi_dung_han": "Học phí đóng đúng hạn",
    "hoc_phi_tre_han": "Học phí đóng trễ hạn",
    "hoc_phi_chua_du": "Học phí chưa đóng đủ",
    "hoc_phi_mien": "Được miễn học phí",
    "hoc_phi_khong_tra_loi": "Tình trạng học phí không rõ",
    # Môn học (mục tiêu trượt môn)
    "so_tc": "Số tín chỉ của môn",
    "diem_gk": "Điểm giữa kỳ (thang 10)",
    "ti_trong_gk": "Tỉ trọng điểm giữa kỳ",
    "vang_lt": "Vắng lý thuyết (0–2)",
    "co_thuc_hanh": "Môn có thực hành",
    "vang_th": "Có vắng buổi thực hành",
    "truoc_dtb_hk": "Điểm trung bình học kỳ trước",
    "truoc_dtb_tl": "Điểm trung bình tích lũy đến kỳ trước",
    "truoc_tctl": "Tín chỉ tích lũy đến kỳ trước",
    "truoc_no_tc": "Tín chỉ còn nợ đến kỳ trước",
    "truoc_trinh_do": "Trình độ năm ở kỳ trước",
    "truoc_drl": "Điểm rèn luyện kỳ trước",
    "truoc_muc_vang": "Mức vắng học kỳ trước (0–3)",
    "truoc_canh_bao": "Kỳ trước bị cảnh báo học tập",
    "truoc_so_lan_canh_bao_lien_tiep": "Số học kỳ bị cảnh báo liên tiếp đến kỳ trước",
    "lich_su_thieu": "Chưa có học kỳ trước",
}


def ten_dac_trung(cot):
    """Tên tiếng Việt của một cột; cột "_thieu" thành "Thiếu ..."."""
    if cot.endswith("_thieu") and cot != "lich_su_thieu":
        goc = cot[: -len("_thieu")]
        return f"Thiếu: {TEN_DAC_TRUNG.get(goc, goc)}"
    return TEN_DAC_TRUNG.get(cot, cot)


def gia_tri_shap(mo_hinh, X):
    """SHAP values của lớp nguy cơ (nhãn 1), shape = X.shape.

    Chỉ dành cho mô hình cây (TreeExplainer); SVM / pipeline thì báo lỗi rõ.
    Mỗi thư viện trả shape khác nhau (list theo lớp, mảng 3 chiều...) nên
    chuẩn hoá về một dạng.
    """
    try:
        giai_thich = shap.TreeExplainer(mo_hinh)
    except Exception as loi:
        raise ValueError(f"SHAP TreeExplainer không hỗ trợ {type(mo_hinh).__name__}") from loi
    with warnings.catch_warnings():
        # LightGBM + SHAP mới báo đổi định dạng kết quả; bên dưới đã chuẩn hoá mọi dạng
        warnings.simplefilter("ignore", UserWarning)
        gia_tri = giai_thich.shap_values(X)
    if isinstance(gia_tri, list):
        gia_tri = gia_tri[1]
    gia_tri = np.asarray(gia_tri)
    if gia_tri.shape == X.shape:
        return gia_tri
    if gia_tri.ndim == 3 and gia_tri.shape[:2] == X.shape:   # (dòng, cột, lớp)
        return gia_tri[:, :, -1]
    if gia_tri.ndim == 3 and gia_tri.shape[1:] == X.shape:   # (lớp, dòng, cột)
        return gia_tri[-1]
    raise ValueError(f"SHAP values có shape {gia_tri.shape}, không khớp dữ liệu {X.shape}")


def _dinh_dang(gia_tri):
    return f"{gia_tri:g}" if float(gia_tri) != int(gia_tri) else f"{int(gia_tri)}"


def ly_do(mo_hinh, X, so_ly_do=3):
    """Tối đa `so_ly_do` đặc trưng làm TĂNG nguy cơ nhiều nhất, cho từng dòng X.

    Trả về list (mỗi dòng X một list chuỗi, có thể rỗng nếu không có đặc
    trưng nào đẩy nguy cơ lên). Bỏ qua: đặc trưng làm giảm nguy cơ, ô trống
    và cột "_thieu" — "thiếu dữ liệu" không phải lý do để nói với sinh viên.
    """
    if so_ly_do < 1:
        raise ValueError("so_ly_do phải lớn hơn 0")
    shap_values = gia_tri_shap(mo_hinh, X)
    cot_thieu = np.array([c.endswith("_thieu") for c in X.columns])

    ket_qua = []
    for i, dong in enumerate(shap_values):
        gia_tri = X.iloc[i].to_numpy(dtype=float)
        hop_le = (dong > 0) & ~cot_thieu & ~np.isnan(gia_tri)
        thu_tu = [j for j in np.argsort(-dong) if hop_le[j]][:so_ly_do]
        ket_qua.append([f"{ten_dac_trung(X.columns[j])} = {_dinh_dang(gia_tri[j])}"
                        for j in thu_tu])
    return ket_qua


def ve_bieu_do(mo_hinh, X, tieu_de, duong_dan, so_dac_trung=15):
    """Biểu đồ mức ảnh hưởng trung bình |SHAP| của từng đặc trưng."""
    shap_values = gia_tri_shap(mo_hinh, X)
    X_ten = X.rename(columns=ten_dac_trung)
    shap.summary_plot(shap_values, X_ten, plot_type="bar", show=False, max_display=so_dac_trung)
    plt.title(tieu_de)
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(duong_dan)), exist_ok=True)
    plt.savefig(duong_dan, dpi=150, bbox_inches="tight")
    plt.close()
    return duong_dan


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import mo_hinh_cuoi
    for muc_tieu in mo_hinh_cuoi.MUC_TIEU_CO_MO_HINH:
        print(mo_hinh_cuoi.ve_shap(muc_tieu))
