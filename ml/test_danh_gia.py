"""
Kiểm tra danh_gia.py.

Chạy:  python ml/test_danh_gia.py     (hoặc pytest ml/ nếu đã cài pytest)
"""

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

import danh_gia


def du_lieu_gia(so_sv=60, so_ky=4, seed=0):
    """Dữ liệu giả: mỗi sinh viên vài dòng, nhãn phụ thuộc cột 'x'."""
    rng = np.random.default_rng(seed)
    n = so_sv * so_ky
    nhom = pd.Series([f"SV{i // so_ky + 1}" for i in range(n)])
    X = pd.DataFrame({"x": rng.normal(size=n)})
    y = pd.Series((X["x"] + rng.normal(0, 0.5, n) > 1.2).astype(int))
    return X, y, nhom


def test_tinh_chi_so_tinh_tay():
    y = [1, 1, 0, 0, 0]
    xac_suat = [0.9, 0.4, 0.6, 0.2, 0.1]
    kq = danh_gia.tinh_chi_so(y, xac_suat, nguong=0.5)
    # Ngưỡng 0.5: đoán dương 2 dòng (0.9 đúng, 0.6 sai) -> P = 1/2, R = 1/2
    assert np.isclose(kq["precision"], 0.5) and np.isclose(kq["recall"], 0.5)
    assert np.isclose(kq["f1"], 0.5)
    # Xếp hạng: 0.9 (1) > 0.6 (0) > 0.4 (1) -> AP = (1/1 + 2/3) / 2
    assert np.isclose(kq["pr_auc"], (1 + 2 / 3) / 2)


def test_chia_fold_khong_tach_sinh_vien():
    X, y, nhom = du_lieu_gia()
    fold = danh_gia.chia_fold(y, nhom)
    assert set(fold) == set(range(danh_gia.SO_FOLD))
    assert (fold.groupby(nhom).nunique() == 1).all()


def test_danh_gia_cheo_moi_dong_du_doan_mot_lan():
    X, y, nhom = du_lieu_gia()
    bang, xac_suat = danh_gia.danh_gia_cheo(
        lambda: DummyClassifier(strategy="prior"), X, y, nhom)
    assert len(bang) == danh_gia.SO_FOLD and list(bang.columns) == danh_gia.CAC_CHI_SO
    assert xac_suat.notna().all() and xac_suat.index.equals(X.index)
    # Mô hình đoán hằng số thì không xếp hạng được: ROC-AUC = 0.5
    assert np.allclose(bang["roc_auc"], 0.5)


def test_cung_seed_cung_ket_qua():
    X, y, nhom = du_lieu_gia()
    a, _ = danh_gia.danh_gia_cheo(danh_gia.tao_baseline_tu(lambda X: X["x"] > 1), X, y, nhom)
    b, _ = danh_gia.danh_gia_cheo(danh_gia.tao_baseline_tu(lambda X: X["x"] > 1), X, y, nhom)
    pd.testing.assert_frame_equal(a, b)


def test_baseline_la_luat_khong_hoc():
    X = pd.DataFrame({"canh_bao": [1, 0, 0], "dtb_hk": [3.0, 1.0, 3.0],
                      "so_lan_canh_bao_lien_tiep": [2, 1, 0],
                      "diem_gk": [3.0, 6.0, 8.0], "vang_lt": [0, 2, 0]})
    du_kien = {"canh_bao": [1, 1, 0], "thoi_hoc": [1, 0, 0], "truot_mon": [1, 1, 0]}
    for muc_tieu, mong_doi in du_kien.items():
        mo_hinh = danh_gia.tao_baseline(muc_tieu)().fit(X, None)
        assert mo_hinh.predict_proba(X)[:, 1].tolist() == mong_doi, muc_tieu


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
