"""
Kiểm tra dac_trung.py.

Chạy:  python ml/test_dac_trung.py     (hoặc pytest ml/ nếu đã cài pytest)

Dữ liệu thử sinh bằng mo_phong.py ra file tạm; test với file khảo sát thật chỉ
chạy khi có file đó (biến môi trường KHAO_SAT_THAT, mặc định ở Downloads).
"""

import os
import tempfile

import pandas as pd

import dac_trung
import mo_phong


DUONG_DAN_KHAO_SAT = os.environ.get(
    "KHAO_SAT_THAT", os.path.expanduser(r"~\Downloads\Kết quả khảo sát học tập (ẩn danh).xlsx"))

SO_SV, SEED = 300, 7
_cache = {}


def du_lieu(muc_tieu="canh_bao"):
    """Sinh dữ liệu mô phỏng một lần, tạo (X, y, nhom) cho từng mục tiêu."""
    if "duong_dan" not in _cache:
        bang_form, bang_nhan = mo_phong.mo_phong(SO_SV, SEED)
        duong_dan = os.path.join(tempfile.mkdtemp(), "mo_phong.xlsx")
        mo_phong.ghi_xlsx(bang_form, bang_nhan, duong_dan)
        _cache.update(duong_dan=duong_dan, bang_nhan=bang_nhan,
                      bang=dac_trung.doc_bang_hoc_ky(duong_dan))
    if muc_tieu not in _cache:
        _cache[muc_tieu] = dac_trung.tao_du_lieu(muc_tieu, _cache["duong_dan"])
    return _cache[muc_tieu]


def test_ten_muc_tieu_sai():
    try:
        dac_trung.tao_du_lieu("abc")
    except ValueError:
        return
    raise AssertionError("phải báo ValueError")


# --- canh_bao -------------------------------------------------------------------

def test_canh_bao_dung_hop_dong():
    X, y, nhom = du_lieu()
    assert len(X) == len(y) == len(nhom) > 0
    assert X.index.equals(y.index) and X.index.equals(nhom.index)
    assert set(y.unique()) <= {0, 1}
    assert nhom.str.startswith("SV").all()
    # Toàn cột số để mọi mô hình nhận được
    assert all(pd.api.types.is_numeric_dtype(t) for t in X.dtypes), X.dtypes[X.dtypes == object]


def test_canh_bao_khong_dung_nganh_hoc_he():
    X, _, _ = du_lieu()
    assert not any("nganh" in c or "hoc_he" in c for c in X.columns)


def test_canh_bao_dac_trung_ky_k_nhan_ky_sau():
    """Đặc trưng lấy đúng học kỳ k, nhãn lấy đúng học kỳ k+1 của cùng sinh viên."""
    X, y, nhom = du_lieu()
    bang = _cache["bang"].set_index(["ma_sv", "hoc_ky"])
    khoa_k = list(zip(nhom, X["hoc_ky"].astype(int)))
    khoa_sau = [(sv, k + 1) for sv, k in khoa_k]
    for cot in ["dtb_hk", "dtb_tl", "tctl", "no_tc", "canh_bao"]:
        assert (X[cot].to_numpy() == bang.loc[khoa_k, cot].astype(float).to_numpy()).all(), cot
    assert (y.to_numpy() == bang.loc[khoa_sau, "canh_bao"].astype(int).to_numpy()).all()


def test_canh_bao_bo_hoc_ky_cuoi():
    X, _, nhom = du_lieu()
    bang = _cache["bang"]
    so_ky = bang.groupby("ma_sv")["hoc_ky"].count()
    assert len(X) == (so_ky - 1).sum()
    ky_cuoi = bang.groupby("ma_sv")["hoc_ky"].max()
    assert (X["hoc_ky"].to_numpy() < ky_cuoi[nhom].to_numpy()).all()


def test_canh_bao_cot_thieu():
    X, _, _ = du_lieu()
    for cot in dac_trung.COT_CO_THE_THIEU:
        assert (X[f"{cot}_thieu"] == X[cot].isna()).all(), cot
    assert X["dtb_hk_thay_doi"][X["hoc_ky"] == 1].isna().all()
    assert X["dtb_hk_thay_doi"][X["hoc_ky"] > 1].notna().all()
    # Mỗi dòng có đúng một lựa chọn học phí
    hoc_phi = X[[c for c in X.columns if c.startswith("hoc_phi_")]]
    assert (hoc_phi.sum(axis=1) == 1).all()


def test_canh_bao_ti_le_duong():
    _, y, _ = du_lieu()
    assert 0.02 < y.mean() < 0.15, y.mean()


def test_canh_bao_khop_nhan_that():
    """Nhãn gán từ form (không có số TC rớt trong kỳ) gần trùng nhãn thật."""
    X, y, nhom = du_lieu()
    that = _cache["bang_nhan"].set_index(["ma_sv", "hoc_ky"])["canh_bao"]
    y_that = that.loc[list(zip(nhom, X["hoc_ky"].astype(int) + 1))].to_numpy()
    khop = (y.to_numpy() == y_that).mean()
    print(f"  nhãn kỳ sau từ form khớp nhãn thật: {khop:.1%}")
    assert khop > 0.95


def test_canh_bao_file_that():
    if not os.path.exists(DUONG_DAN_KHAO_SAT):
        print("  (bỏ qua: không có file khảo sát thật)")
        return
    X, y, nhom = dac_trung.tao_du_lieu("canh_bao", DUONG_DAN_KHAO_SAT)
    # Chỉ sinh viên hợp lệ; cùng bộ cột với dữ liệu mô phỏng
    assert set(nhom) <= {"SV1", "SV2", "SV4", "SV6", "SV7"}
    assert list(X.columns) == list(du_lieu()[0].columns)
    print(f"  file thật: {len(X)} dòng, {int(y.sum())} ca dương")


# --- thoi_hoc -------------------------------------------------------------------

def test_thoi_hoc_cung_dong_voi_canh_bao():
    X_cb, _, nhom_cb = du_lieu("canh_bao")
    X, y, nhom = du_lieu("thoi_hoc")
    pd.testing.assert_frame_equal(X, X_cb)
    assert nhom.equals(nhom_cb)
    assert set(y.unique()) <= {0, 1} and y.sum() > 0


def test_thoi_hoc_dung_luat():
    # Điều 18.2a: chỉ bị buộc thôi học ở kỳ k+1 khi kỳ k đã có 2 cảnh báo liên tiếp
    X, y, _ = du_lieu("thoi_hoc")
    assert (X.loc[y == 1, "so_lan_canh_bao_lien_tiep"] == 2).all()


def test_nguy_co_thoi_hoc():
    nguy_co = pd.Series([0.9, 0.9, 0.9, 0.2])
    lien_tiep = pd.Series([0, 1, 2, 2])
    assert dac_trung.nguy_co_thoi_hoc(nguy_co, lien_tiep).tolist() == [0.0, 0.0, 0.9, 0.2]


# --- truot_mon ------------------------------------------------------------------

def test_truot_mon_dung_hop_dong():
    X, y, nhom = du_lieu("truot_mon")
    assert len(X) == len(y) == len(nhom) > 0
    assert X.index.equals(y.index) and X.index.equals(nhom.index)
    assert set(y.unique()) == {0, 1}
    assert all(pd.api.types.is_numeric_dtype(t) for t in X.dtypes)


def test_truot_mon_khong_dung_tong_ket_ky_k():
    """Cột lịch sử phải là của học kỳ k−1; không có cột tổng kết học kỳ k."""
    X, _, nhom = du_lieu("truot_mon")
    cot_cam = {"dtb_hk", "tc_dat_hk", "dtb_tl", "tctl", "no_tc", "canh_bao", "drl", "muc_vang"}
    assert not cot_cam & set(X.columns)

    bang = _cache["bang"].set_index(["ma_sv", "hoc_ky"])
    co_ls = X["hoc_ky"] > 1
    khoa_truoc = list(zip(nhom[co_ls], X.loc[co_ls, "hoc_ky"].astype(int) - 1))
    for cot in ["dtb_hk", "dtb_tl", "tctl", "no_tc"]:
        assert (X.loc[co_ls, f"truoc_{cot}"].to_numpy()
                == bang.loc[khoa_truoc, cot].astype(float).to_numpy()).all(), cot
    # Học kỳ 1: không có lịch sử
    assert X.loc[~co_ls, "truoc_dtb_hk"].isna().all()
    assert (X["lich_su_thieu"] == (~co_ls)).all()


def test_truot_mon_nhan_va_ma_hoa():
    X, y, _ = du_lieu("truot_mon")
    assert 0.02 < y.mean() < 0.2, y.mean()
    # Vắng lý thuyết trên 20% -> cấm thi -> trượt
    assert (y[X["vang_lt"] == 2] == 1).all()
    # Môn không có thực hành thì không vắng thực hành
    assert (X.loc[X["co_thuc_hanh"] == 0, "vang_th"] == 0).all()
    for cot in dac_trung.COT_MON_CO_THE_THIEU:
        assert (X[f"{cot}_thieu"] == X[cot].isna()).all(), cot


def test_ba_muc_tieu_file_that():
    if not os.path.exists(DUONG_DAN_KHAO_SAT):
        print("  (bỏ qua: không có file khảo sát thật)")
        return
    for muc_tieu in ["thoi_hoc", "truot_mon"]:
        X, y, nhom = dac_trung.tao_du_lieu(muc_tieu, DUONG_DAN_KHAO_SAT)
        assert set(nhom) <= {"SV1", "SV2", "SV4", "SV6", "SV7"}
        assert list(X.columns) == list(du_lieu(muc_tieu)[0].columns), muc_tieu
        print(f"  file thật {muc_tieu}: {len(X)} dòng, {int(y.sum())} ca dương")


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
