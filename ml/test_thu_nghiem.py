"""
Kiểm tra giao diện thử nghiệm thu_nghiem.py bằng streamlit.testing.

Chạy:  python ml/test_thu_nghiem.py     (hoặc pytest ml/ nếu đã cài pytest)

Cần models/ đã train. Bảng data_editor không gõ được qua AppTest nên phần sửa ô
kiểm bằng cách thay bảng trong phiên làm việc.
"""

import os

import pandas as pd
from streamlit.testing.v1 import AppTest

import doc_cong_thong_tin as cong


THU_MUC = os.path.dirname(os.path.abspath(__file__))
FILE_APP = os.path.join(os.path.dirname(THU_MUC), "thu_nghiem.py")
FILE_MAU = os.path.join(THU_MUC, "du_lieu_mau", "cong_thong_tin_mau.txt")


def van_ban_mau():
    with open(FILE_MAU, encoding="utf-8") as f:
        return f.read()


def mo_app():
    at = AppTest.from_file(FILE_APP, default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def bam(at, nhan):
    next(b for b in at.button if b.label == nhan).click()
    at.run()
    assert not at.exception, at.exception


def den_ket_qua():
    at = mo_app()
    at.text_area[0].set_value(van_ban_mau())
    bam(at, "Đọc dữ liệu")
    bam(at, "Dữ liệu đúng, xem kết quả")
    return at


def toan_bo_chu(at):
    phan = list(at.title) + list(at.subheader) + list(at.markdown) + list(at.success) \
        + list(at.info) + list(at.warning) + list(at.error) + list(at.caption)
    return " ".join(p.value for p in phan)


def test_ba_buoc_dung_ten():
    at = mo_app()
    assert list(at.radio[0].options) == ["1. Dữ liệu", "2. Kiểm tra", "3. Kết quả"]


def test_khong_dung_tu_dan():
    at = mo_app()
    chu = toan_bo_chu(at) + at.text_area[0].label + (at.text_area[0].placeholder or "")
    assert "dán" not in chu.lower(), chu


def test_chua_co_du_lieu_thi_nhac():
    at = mo_app()
    at.radio[0].set_value("3. Kết quả").run()
    assert not at.exception, at.exception
    assert "Chưa có dữ liệu" in at.info[0].value


def test_doc_du_lieu_sang_buoc_kiem_tra():
    at = mo_app()
    at.text_area[0].set_value(van_ban_mau())
    bam(at, "Đọc dữ liệu")
    assert at.radio[0].value == "2. Kiểm tra"
    assert at.metric[0].value == "6"
    assert "Không phát hiện lỗi" in at.success[0].value


def test_van_ban_sai_bao_loi():
    at = mo_app()
    at.text_area[0].set_value("Trang chủ\nThông báo")
    bam(at, "Đọc dữ liệu")
    assert at.radio[0].value == "1. Dữ liệu"
    assert "Xem điểm" in at.error[0].value


def test_nut_du_lieu_mau():
    at = mo_app()
    bam(at, "Dùng dữ liệu mẫu")
    assert at.radio[0].value == "2. Kiểm tra"


def test_ket_qua_dung_ky_va_nguy_co_thap():
    at = den_ket_qua()
    assert at.title[0].value == "Dự đoán cho HK1 2026–2027"
    chu = toan_bo_chu(at)
    assert "Dựa trên dữ liệu đến HK2 2025–2026" in chu
    assert "Nguy cơ thấp" in chu and "Chưa thể xảy ra ở kỳ này" in chu


def test_nhap_diem_giua_ky_thi_du_doan_duoc_mon():
    at = den_ket_qua()
    mon = at.session_state["mon_sua"].copy()
    mon.loc[0, ["diem_gk", "ti_trong_gk"]] = [1.5, 0.5]
    mon["vang_lt"] = mon["vang_lt"].astype(object)
    mon["vang_th"] = mon["vang_th"].astype(object)
    mon.loc[0, "vang_lt"] = "Ít hoặc không vắng"
    mon.loc[0, "vang_th"] = "Không vắng buổi nào"
    at.session_state["mon_sua"] = mon
    at.run()
    assert not at.exception, at.exception
    bang = at.dataframe[0].value
    assert not str(bang.loc[0, "Kết quả"]).startswith("Chưa có")
    assert str(bang.loc[1, "Kết quả"]).startswith("Chưa có")


def test_sua_so_lieu_kem_bao_nguy_co_cao():
    at = den_ket_qua()
    hk = at.session_state["hk_sua"].copy()
    cuoi = hk.index[-1]
    hk.loc[cuoi, ["dtb_hk", "dtb_tl", "tc_dang_ky"]] = [0.3, 1.2, 125.0]
    at.session_state["hk_sua"] = hk
    at.run()
    assert not at.exception, at.exception
    assert "Nguy cơ cao" in toan_bo_chu(at)


def test_du_lieu_sua_sai_khong_doan():
    at = den_ket_qua()
    hk = at.session_state["hk_sua"].copy()
    hk.loc[hk.index[-1], "tc_dang_ky"] = 10.0     # TC đăng ký < TCTL
    at.session_state["hk_sua"] = hk
    at.run()
    assert not at.exception, at.exception
    assert "chưa hợp lệ" in at.error[0].value


def test_canh_bao_khi_mat_dong_hoc_ky():
    """Xoá một dòng 'Học kỳ: HK02' -> báo thiếu học kỳ, không im lặng."""
    van_ban = van_ban_mau()
    vi_tri = van_ban.index("Học kỳ: HK02")
    con_lai = van_ban[:vi_tri] + van_ban[vi_tri + len("Học kỳ: HK02"):]
    assert any("thiếu một học kỳ" in c for c in cong.canh_bao_du_lieu(con_lai))


def test_canh_bao_khi_mat_dong_tong_ket():
    van_ban = van_ban_mau().replace("- Điểm rèn luyện: 85\n", "", 1)
    assert any("Điểm rèn luyện" in c for c in cong.canh_bao_du_lieu(van_ban))


def test_van_ban_day_du_khong_canh_bao():
    assert cong.canh_bao_du_lieu(van_ban_mau()) == []


if __name__ == "__main__":
    cac_test = [(ten, ham) for ten, ham in globals().items() if ten.startswith("test_")]
    loi = 0
    for ten, ham in cac_test:
        try:
            ham()
            print(f"OK    {ten}")
        except AssertionError as e:
            loi += 1
            print(f"LỖI   {ten}: {str(e)[:300]}")
    print(f"\n{len(cac_test) - loi}/{len(cac_test)} test đạt")
    raise SystemExit(1 if loi else 0)
