"""
Kiểm tra goi_y.py (gợi ý cải thiện).

Chạy:  python ml/test_goi_y.py     (hoặc pytest ml/ nếu đã cài pytest)
"""

import os

import pandas as pd

import doc_cong_thong_tin as cong
import doc_form as form
import goi_y


FILE_MAU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu_mau", "cong_thong_tin_mau.txt")


def bang(*hoc_ky):
    """Bảng học kỳ của một sinh viên từ các bộ (tc_dat_hk, dtb_hk, tctl, tc_dang_ky, dtb_tl)."""
    return pd.DataFrame([{"ma_sv": "SV1", "hoc_ky": i + 1, "tc_dat_hk": a, "dtb_hk": b, "tctl": c,
                          "tc_dang_ky": d, "dtb_tl": e, "drl": 80.0}
                         for i, (a, b, c, d, e) in enumerate(hoc_ky)])


# --- Điểm thi cuối kỳ cần đạt ------------------------------------------------------
def test_diem_cuoi_ky_can_dat_tinh_tay():
    # 0,4 × 3,5 + 0,6 × CK >= 4  ->  CK >= 4,333  -> làm tròn LÊN 4,4
    assert goi_y.diem_cuoi_ky_can_dat(3.5, 0.4) == 4.4
    # 0,5 × 0,5 + 0,5 × CK >= 4  ->  CK >= 7,5 (đúng 7,5, không bị đẩy lên 7,6)
    assert goi_y.diem_cuoi_ky_can_dat(0.5, 0.5) == 7.5
    # Giữa kỳ 8,5 chiếm 50% đã đủ 4,25 -> không cần thêm
    assert goi_y.diem_cuoi_ky_can_dat(8.5, 0.5) == 0
    # 0,7 × 1 + 0,3 × CK >= 4 -> CK >= 11: không thể
    assert goi_y.diem_cuoi_ky_can_dat(1.0, 0.7) > 10
    # Mục tiêu C (5,5): 0,4 × 6 + 0,6 × CK >= 5,5 -> CK >= 5,1667 -> 5,2
    assert goi_y.diem_cuoi_ky_can_dat(6.0, 0.4, goi_y.DIEM_C) == 5.2


def test_diem_cuoi_ky_thieu_so_lieu():
    assert goi_y.diem_cuoi_ky_can_dat(None, 0.4) is None
    assert goi_y.diem_cuoi_ky_can_dat(5.0, float("nan")) is None
    assert goi_y.diem_cuoi_ky_can_dat(5.0, 1.0) is None          # 100% giữa kỳ: không có thi cuối kỳ


# --- Gợi ý từng môn ---------------------------------------------------------------
def test_goi_y_mon_diem_thap():
    ls = goi_y.goi_y_mon(3.5, 0.4)
    assert any("4,4 điểm thi cuối kỳ để qua môn" in g for g in ls), ls
    assert any("điểm C" in g for g in ls)


def test_goi_y_mon_khong_the_qua():
    ls = goi_y.goi_y_mon(1.0, 0.7)
    assert len(ls) == 1 and "học lại" in ls[0]


def test_goi_y_mon_vang():
    ls = goi_y.goi_y_mon(None, None, form.VANG_LY_THUYET[2], form.VANG_THUC_HANH[2])
    assert any("cấm thi" in g for g in ls) and any("thực hành" in g for g in ls)


def test_goi_y_mon_tot_va_chua_co_diem_thi_khong_noi_gi():
    assert goi_y.goi_y_mon(9.0, 0.5, form.VANG_LY_THUYET[0], form.VANG_THUC_HANH[1]) == []
    assert goi_y.goi_y_mon(None, None) == []


# --- Gợi ý học kỳ ----------------------------------------------------------------
def test_sinh_vien_hoc_tot_khong_co_goi_y():
    _, hk, _ = cong.doc_van_ban(open(FILE_MAU, encoding="utf-8").read())
    assert goi_y.goi_y_hoc_ky(hk) == []


def test_dtb_tich_luy_sat_nguong():
    # TCTL 60 (năm hai), kỳ tới 15 TC -> 75 TC (năm ba, ngưỡng 1,6); ĐTB TL 1,5
    # cần g: (1,6 × 75 − 1,5 × 60) / 15 = 2,0
    ls = goi_y.goi_y_hoc_ky(bang((20, 1.6, 40, 40, 1.6), (20, 1.4, 60, 60, 1.5)), tc_ky_toi=15)
    assert any("từ 2 (thang 4)" in g and "ngưỡng cảnh báo 1,6" in g for g in ls), ls


def test_no_tin_chi():
    gan = goi_y.goi_y_hoc_ky(bang((18, 2.5, 18, 36, 2.5)))
    assert any("nợ 18 tín chỉ" in g for g in gan)
    qua = goi_y.goi_y_hoc_ky(bang((18, 2.5, 18, 45, 2.5)))
    assert any("quá mức 24" in g for g in qua)


def test_dtb_hoc_ky_thap_va_giam():
    thap = goi_y.goi_y_hoc_ky(bang((18, 3.0, 18, 18, 3.0), (18, 1.2, 36, 36, 2.2)))
    assert any("ĐTB học kỳ vừa rồi chỉ 1,2" in g for g in thap)
    giam = goi_y.goi_y_hoc_ky(bang((18, 3.0, 18, 18, 3.0), (18, 2.2, 36, 36, 2.6)))
    assert any("giảm 0,8" in g for g in giam)
    # Giảm nhưng vẫn loại Khá (2,6): chưa đáng lo, không nhắc
    van_kha = goi_y.goi_y_hoc_ky(bang((18, 3.4, 18, 18, 3.4), (18, 2.6, 36, 36, 3.0)))
    assert not any("giảm" in g for g in van_kha)


def test_canh_bao_lien_tiep_sat_thoi_hoc():
    # Hai kỳ ĐTB học kỳ dưới 1,0 -> bị cảnh báo 2 kỳ liên tiếp
    ls = goi_y.goi_y_hoc_ky(bang((10, 0.7, 10, 18, 2.0), (8, 0.8, 18, 36, 2.0)))
    assert any("2 kỳ liên tiếp" in g and "buộc thôi học" in g for g in ls), ls


def test_bang_rong():
    assert goi_y.goi_y_hoc_ky(bang()) == []


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
