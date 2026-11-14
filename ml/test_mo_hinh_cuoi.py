"""
Kiểm tra mo_hinh_cuoi.py, giai_thich.ly_do và dac_trung.dac_trung_du_doan.

Chạy:  python ml/test_mo_hinh_cuoi.py     (hoặc pytest ml/ nếu đã cài pytest)

Dữ liệu và mô hình đều ghi ra thư mục tạm (không đụng data/, models/, results/);
bảng so sánh giả để chọn Decision Tree cho nhanh.
"""

import os
import tempfile

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import dac_trung
import giai_thich
import mo_hinh_cuoi
import mo_phong


DUONG_DAN_KHAO_SAT = os.environ.get(
    "KHAO_SAT_THAT", os.path.expanduser(r"~\Downloads\Kết quả khảo sát học tập (ẩn danh).xlsx"))
_cache = {}


def chuan_bi():
    """Dữ liệu mô phỏng 300 SV + bảng so sánh giả + mô hình đã train, ghi ra thư mục tạm."""
    if not _cache:
        tam = tempfile.mkdtemp()
        du_lieu = os.path.join(tam, "mo_phong.xlsx")
        mo_phong.ghi_xlsx(*mo_phong.mo_phong(300, 7), du_lieu)
        tom_tat = os.path.join(tam, "tom_tat.csv")
        pd.DataFrame({
            "muc_tieu": ["canh_bao"] * 3 + ["truot_mon"] * 2,
            "phuong_phap": ["Baseline luật", "Decision Tree", "SVM", "Decision Tree", "SVM"],
            "pr_auc_tb": [0.99, 0.60, 0.50, 0.70, 0.40],
        }).to_csv(tom_tat, index=False)
        mo_hinh = os.path.join(tam, "models")
        goi = {m: mo_hinh_cuoi.huan_luyen(m, du_lieu, mo_hinh, tom_tat)
               for m in mo_hinh_cuoi.MUC_TIEU_CO_MO_HINH}
        _cache.update(du_lieu=du_lieu, tom_tat=tom_tat, mo_hinh=mo_hinh, goi=goi)
    return _cache


def test_chon_phuong_phap_cao_nhat_bo_baseline():
    c = chuan_bi()
    # Baseline 0.99 phải bị bỏ qua
    assert mo_hinh_cuoi.chon_phuong_phap("canh_bao", c["tom_tat"]) == ("Decision Tree", 0.60)
    assert mo_hinh_cuoi.chon_phuong_phap("truot_mon", c["tom_tat"])[0] == "Decision Tree"


def test_luu_va_tai_lai_cho_cung_ket_qua():
    c = chuan_bi()
    for muc_tieu, goi in c["goi"].items():
        tai = mo_hinh_cuoi.tai(muc_tieu, c["mo_hinh"])
        assert tai["phuong_phap"] == "Decision Tree" and tai["cot"] == goi["cot"]
        assert 0 < tai["nguong"] <= 1
        X, _, _ = dac_trung.tao_du_lieu(muc_tieu, c["du_lieu"])
        assert np.array_equal(tai["mo_hinh"].predict_proba(X), goi["mo_hinh"].predict_proba(X))


def test_tai_bao_ro_khi_chua_train():
    try:
        mo_hinh_cuoi.tai("canh_bao", tempfile.mkdtemp())
    except FileNotFoundError as loi:
        assert "mo_hinh_cuoi.py" in str(loi)
        return
    raise AssertionError("phải báo FileNotFoundError")


def test_dac_trung_du_doan_cung_cot_voi_luc_train():
    c = chuan_bi()
    for muc_tieu in dac_trung.MUC_TIEU:
        X, thong_tin = dac_trung.dac_trung_du_doan(muc_tieu, c["du_lieu"])
        X_train, _, _ = dac_trung.tao_du_lieu(muc_tieu, c["du_lieu"])
        assert list(X.columns) == list(X_train.columns), muc_tieu
        assert X.index.equals(thong_tin.index)


def test_du_doan_canh_bao_moi_sinh_vien_ky_gan_nhat():
    c = chuan_bi()
    kq = mo_hinh_cuoi.du_doan(c["du_lieu"], "canh_bao", c["mo_hinh"])
    bang = dac_trung.doc_bang_hoc_ky(c["du_lieu"])
    ky_cuoi = bang.groupby("ma_sv")["hoc_ky"].max()
    assert kq["ma_sv"].is_unique and set(kq["ma_sv"]) == set(ky_cuoi.index)
    # Dữ liệu kỳ cuối đã học xong, dự đoán cho kỳ kế tiếp
    assert (kq["dua_tren_hk"].to_numpy() == ky_cuoi[kq["ma_sv"]].to_numpy()).all()
    assert (kq["du_doan_cho_hk"] == kq["dua_tren_hk"] + 1).all()
    assert kq["xac_suat"].between(0, 1).all()
    assert (kq["bao_dong"] == (kq["xac_suat"] >= c["goi"]["canh_bao"]["nguong"] - 1e-4)).all()
    # Lý do chỉ có khi báo động, tối đa 3, không có "Thiếu: ..."
    assert all(ld == [] for ld in kq.loc[~kq["bao_dong"], "ly_do"])
    assert all(len(ld) <= 3 and not any(l.startswith("Thiếu") for l in ld) for ld in kq["ly_do"])


def test_du_doan_thoi_hoc_suy_tu_canh_bao():
    c = chuan_bi()
    cb = mo_hinh_cuoi.du_doan(c["du_lieu"], "canh_bao", c["mo_hinh"])
    th = mo_hinh_cuoi.du_doan(c["du_lieu"], "thoi_hoc", c["mo_hinh"])
    assert (th["xac_suat"] <= cb["xac_suat"]).all()
    assert not (th["bao_dong"] & ~cb["bao_dong"]).any()
    X, _ = dac_trung.dac_trung_du_doan("thoi_hoc", c["du_lieu"])
    assert (th.loc[X["so_lan_canh_bao_lien_tiep"] < 2, "xac_suat"] == 0).all()


def test_du_doan_truot_mon_moi_mon():
    c = chuan_bi()
    kq = mo_hinh_cuoi.du_doan(c["du_lieu"], "truot_mon", c["mo_hinh"])
    _, mon = dac_trung.doc_du_lieu(c["du_lieu"])
    assert len(kq) == len(mon) and kq["xac_suat"].between(0, 1).all()


def test_ly_do_chi_lay_dac_trung_tang_nguy_co():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"diem_gk": rng.uniform(0, 10, 400), "so_tc": rng.integers(2, 5, 400).astype(float)})
    X["diem_gk_thieu"] = 0.0
    y = (X["diem_gk"] < 4).astype(int)
    mo_hinh = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X, y)
    ld = giai_thich.ly_do(mo_hinh, X.iloc[:20])
    for i, cac_ly_do in enumerate(ld):
        if X["diem_gk"].iloc[i] < 4:     # điểm thấp: lý do chính là điểm giữa kỳ
            assert cac_ly_do[0].startswith("Điểm giữa kỳ"), cac_ly_do
        else:                            # điểm cao làm GIẢM nguy cơ: không phải lý do
            assert not any(l.startswith("Điểm giữa kỳ") for l in cac_ly_do), cac_ly_do
        assert not any("Thiếu" in l for l in cac_ly_do)


def test_du_doan_tu_cong_thong_tin_khong_doan_mon_chua_co_diem_gk():
    c = chuan_bi()
    file_mau = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "du_lieu_mau", "cong_thong_tin_mau.txt")
    cb = mo_hinh_cuoi.du_doan(file_mau, "canh_bao", c["mo_hinh"])
    assert len(cb) == 1 and cb["xac_suat"].between(0, 1).all()
    tm = mo_hinh_cuoi.du_doan(file_mau, "truot_mon", c["mo_hinh"])
    # Kỳ đang học chưa có điểm giữa kỳ: không đoán bừa
    assert len(tm) == 6 and tm["xac_suat"].isna().all() and not tm["bao_dong"].any()
    assert (tm["ghi_chu"] != "").all()
    # Cả 3 mục tiêu cùng dự đoán cho học kỳ đang học (HK thứ 7), dựa trên HK thứ 6
    assert (cb["du_doan_cho_hk"] == 7).all() and (tm["du_doan_cho_hk"] == 7).all()
    assert (cb["dua_tren_hk"] == 6).all() and (tm["dua_tren_hk"] == 6).all()


def test_du_doan_file_that():
    if not os.path.exists(DUONG_DAN_KHAO_SAT):
        print("  (bỏ qua: không có file khảo sát thật)")
        return
    c = chuan_bi()
    for muc_tieu in dac_trung.MUC_TIEU:
        kq = mo_hinh_cuoi.du_doan(DUONG_DAN_KHAO_SAT, muc_tieu, c["mo_hinh"])
        assert set(kq["ma_sv"]) <= {"SV1", "SV2", "SV4", "SV6", "SV7"}
        print(f"  file thật {muc_tieu}: {len(kq)} dòng, {int(kq['bao_dong'].sum())} báo động")


if __name__ == "__main__":
    cac_test = [(ten, ham) for ten, ham in globals().items() if ten.startswith("test_")]
    loi = 0
    for ten, ham in cac_test:
        try:
            ham()
            print(f"OK    {ten}")
        except AssertionError as e:
            loi += 1
            print(f"LỖI   {ten}: {e}")
    print(f"\n{len(cac_test) - loi}/{len(cac_test)} test đạt")
    raise SystemExit(1 if loi else 0)
