"""
Kiểm tra doc_cong_thong_tin.py (đọc văn bản dán từ cổng thông tin sinh viên).

Chạy:  python ml/test_doc_cong_thong_tin.py     (hoặc pytest ml/ nếu đã cài pytest)

File mẫu ml/du_lieu_mau/cong_thong_tin_mau.txt là trang "Xem điểm" thật đã
che họ tên, mã sinh viên.
"""

import os

import numpy as np

import dac_trung
import doc_cong_thong_tin as cong
import doc_form as form


THU_MUC = os.path.dirname(os.path.abspath(__file__))
FILE_MAU = os.path.join(THU_MUC, "du_lieu_mau", "cong_thong_tin_mau.txt")


def van_ban_mau():
    with open(FILE_MAU, encoding="utf-8") as f:
        return f.read()


def test_doc_du_6_hoc_ky_dung_so_cua_truong():
    sinh_vien, hk, _ = cong.doc_van_ban(van_ban_mau())
    assert len(hk) == 6 and list(hk["hoc_ky"]) == [1, 2, 3, 4, 5, 6]
    dau = hk.iloc[0]
    assert (dau["tc_dat_hk"], dau["dtb_hk"], dau["tctl"], dau["tc_dang_ky"], dau["dtb_tl"], dau["drl"]) \
        == (13, 2.46, 13, 13, 2.46, 80)
    cuoi = hk.iloc[-1]
    assert (cuoi["tctl"], cuoi["tc_dang_ky"], cuoi["dtb_tl"]) == (98, 98, 2.87)
    assert sinh_vien.loc["SV1", "hop_le"], sinh_vien.loc["SV1", "loi"]


def test_cung_dang_voi_doc_form():
    sinh_vien, hk, mon = cong.doc_van_ban(van_ban_mau())
    assert list(hk.columns) == ["ma_sv", "hoc_ky", *form.CAU_HOC_KY.values()]
    assert list(mon.columns) == ["ma_sv", "hoc_ky", "stt_mon", *form.CAU_MON.values()]
    assert {"nam_nhap_hoc", "he_dao_tao", "hop_le", "loi"} <= set(sinh_vien.columns)
    # Trang không có mức vắng, học phí: ghi lựa chọn "không trả lời" của form
    assert (hk["muc_vang"] == form.MUC_VANG[4]).all() and (hk["hoc_phi"] == form.HOC_PHI[4]).all()


def test_he_dao_tao_va_nam_nhap_hoc_tu_ma_chuong_trinh():
    sinh_vien, _, _ = cong.doc_van_ban(van_ban_mau())
    sv = sinh_vien.loc["SV1"]
    assert sv["nam_nhap_hoc"] == 2023 and sv["nganh"] == "Công nghệ thông tin"
    assert sv["he_dao_tao"] == "Kỹ sư (4,5 năm)"


def test_ky_dang_hoc_vao_bang_mon_bo_mon_sao_va_0_tc():
    _, hk, mon = cong.doc_van_ban(van_ban_mau())
    # 2026-2027 HK01 đang học: 6 môn 3 TC + 2 môn Sinh hoạt công dân 0 TC (bị bỏ)
    assert len(mon) == 6 and (mon["hoc_ky"] == len(hk) + 1).all()
    assert mon["ket_qua"].isna().all() and (mon["so_tc"] == 3).all()


def test_khong_doc_thong_tin_ca_nhan():
    sinh_vien, hk, mon = cong.doc_van_ban(van_ban_mau().replace("Nguyễn Văn A", "Trần Thị B"))
    tat_ca = " ".join(map(str, [sinh_vien.to_dict(), hk.to_dict(), mon.to_dict()]))
    assert "Trần Thị B" not in tat_ca and "2300000" not in tat_ca
    assert list(sinh_vien.index) == ["SV1"]


VAN_BAN_CO_CHI_TIET = "\n".join([
    "Năm học:2023-2024", "Học kỳ: HK01",
    "1\tAA101\tMôn A\t3\t5.8\t2.0\tC\t\t\t",
    "- Số TC đạt học kỳ: 3", "- Điểm TB học kỳ (hệ 4): 2.00", "- Điểm rèn luyện: 75",
    "- Tổng số TC tích lũy/ Số TC đăng ký: 3/3", "- Điểm TB tích lũy toàn khóa (hệ 4): 2.00",
    "Học kỳ: HK02",
    "2\tAA102\tMôn B\t4\t\t\t\t\t\t",
    "Chi tiết học phần: AA102 - Môn B",
    "STT\tTên thành phần\tTrọng số\tĐiểm lần 1\tĐiểm lần 2\tĐiểm lần 3",
    "1\tĐiểm Thi giữa học phần\tHS1\t3.5\t\t",
    "2\tĐiểm thi lý thuyết\t60%\t\t\t",
    "3\tAA103\tMôn C\t3\t\t\t\t\t\t",
    "Chi tiết học phần: AA103 - Môn C",
    "1\tĐiểm Thi giữa học phần\t30%\t6.0\t7.5\t",
    "2\tĐiểm thi lý thuyết\t70%\t\t\t",
    "- Số TC đạt học kỳ:", "- Điểm TB học kỳ (hệ 4):",
])


def test_diem_giua_ky_va_ti_trong_tu_chi_tiet():
    _, hk, mon = cong.doc_van_ban(VAN_BAN_CO_CHI_TIET)
    assert len(hk) == 1 and list(mon["ten_mon"]) == ["Môn B", "Môn C"]
    # "HS1" + thi 60% -> giữa kỳ chiếm 40%
    assert mon.loc[0, "diem_gk"] == 3.5 and np.isclose(mon.loc[0, "ti_trong_gk"], 0.4)
    # Ghi thẳng 30%; thi lại nhiều lần thì lấy điểm cao nhất
    assert mon.loc[1, "diem_gk"] == 7.5 and np.isclose(mon.loc[1, "ti_trong_gk"], 0.3)


def test_dong_xuong_dong_kieu_windows():
    _, hk, _ = cong.doc_van_ban(van_ban_mau().replace("\n", "\r\n"))
    assert len(hk) == 6


def test_van_ban_sai_bao_loi_de_hieu():
    try:
        cong.doc_van_ban("Trang chủ\nĐăng nhập\nThông báo")
    except ValueError as loi:
        assert "Xem điểm" in str(loi)
        return
    raise AssertionError("phải báo ValueError")


def test_dac_trung_doc_duoc_file_txt_cung_bo_cot():
    """dac_trung nhận .txt như .xlsx và ra đúng bộ cột mô hình đã học."""
    X_mo_phong, _, _ = dac_trung.tao_du_lieu("canh_bao")
    for muc_tieu in dac_trung.MUC_TIEU:
        X, thong_tin = dac_trung.dac_trung_du_doan(muc_tieu, FILE_MAU)
        X_train, _, _ = dac_trung.tao_du_lieu(muc_tieu)
        assert list(X.columns) == list(X_train.columns), muc_tieu
    X, _ = dac_trung.dac_trung_du_doan("canh_bao", FILE_MAU)
    assert len(X) == 1 and X.loc[0, "hoc_ky"] == 6 and X.loc[0, "ky_su"] == 1
    assert list(X_mo_phong.columns) == list(X.columns)


# --- Học kỳ hè và học kỳ đang học (văn bản dựng tay, đúng định dạng trang) -------
def _ky(nam, ky, mon, tong_ket=None):
    """Một học kỳ trên trang. mon: [(mã, TC, điểm 10 hoặc None, điểm 4)];
    tong_ket: (TC đạt, ĐTB HK, ĐRL hoặc "", TCTL, TC ĐK, ĐTB TL) hoặc None (trống)."""
    dong = [f"Năm học:{nam}-{nam + 1}", f"Học kỳ: HK0{ky}"]
    for stt, (ma, tc, d10, d4) in enumerate(mon, start=1):
        diem = ("\t\t" if d10 is None else "VT\tVT\tVT" if d10 == "VT"      # VT: vắng thi
                else f"{d10}\t{d4}\tB")
        dong.append(f"{stt}\t{ma}\tMôn {ma}\t{tc}\t{diem}\t\t\t")
    tk = tong_ket or ("", "", "", "", "", "")
    dong += [f"- Số TC đạt học kỳ: {tk[0]}", f"- Điểm TB học kỳ (hệ 4): {tk[1]}",
             f"- Điểm rèn luyện: {tk[2]}", f"- Tổng số TC tích lũy/ Số TC đăng ký: "
             + (f"{tk[3]}/{tk[4]}" if tong_ket else ""),
             f"- Điểm TB tích lũy toàn khóa (hệ 4): {tk[5]}"]
    return dong


def _van_ban(*cac_ky):
    return "\n".join(["Chương trình đào tạo", "CQ23CT-PM"] + sum(cac_ky, []))


VAN_BAN_HE = _van_ban(
    _ky(2023, 1, [("A1", 4, 7.0, 3.0), ("A2", 4, 7.0, 3.0)], (8, 3.00, 64, 8, 8, 3.00)),
    _ky(2023, 2, [("B1", 4, 5.0, 1.0), ("B2", 4, 3.0, 0.0), ("B3", 4, "VT", None)],
        (4, 0.33, 58, 12, 20, 2.33)),                       # trường tính VT là 0: 4/12
    _ky(2023, 3, [("B2", 4, 6.0, 2.0)], (4, 2.00, "", 16, 20, 2.25)),     # hè học lại B2
    _ky(2024, 1, [("C1", 3, 8.5, 4.0), ("C2", 3, 7.0, 3.0)], (6, 3.50, 80, 22, 26, 2.59)),
    # HK2 2024–2025 đang học: 1 môn đã có điểm nên trang có tổng kết dở dang
    _ky(2024, 2, [("D1", 3, 6.5, 2.0), ("D2", 3, None, None), ("D3", 2, None, None)],
        (3, 2.00, "", 25, 29, 2.52)),
    _ky(2025, 1, [("E1", 5, None, None)]),                                 # mới đăng ký học phần
)


def test_hoc_ky_he_gop_vao_ky_chinh_truoc():
    _, hk, _ = cong.doc_van_ban(VAN_BAN_HE)
    assert len(hk) == 3                                       # HK1, HK2 (gộp hè), HK1 năm sau
    hk2 = hk.iloc[1]
    assert hk2["tc_dat_hk"] == 8                              # 4 + 4 TC đạt hè
    assert hk2["dtb_hk"] == round((0.33 * 12 + 2.0 * 4) / 16, 2)  # theo TC có kết quả, kể cả VT
    assert (hk2["tctl"], hk2["tc_dang_ky"], hk2["dtb_tl"]) == (16, 20, 2.25)   # số sau hè
    assert hk2["drl"] == 58                                   # ĐRL của kỳ chính
    ten = cong.ten_hoc_ky(VAN_BAN_HE)
    assert ten[2] == "HK2 2023–2024 (gộp học kỳ hè)" and ten[3] == "HK1 2024–2025"


def test_ky_dang_hoc_la_ky_dau_sau_ky_cuoi_du_diem():
    _, hk, mon = cong.doc_van_ban(VAN_BAN_HE)
    assert hk["tctl"].iloc[-1] == 22                          # bỏ tổng kết dở dang của kỳ đang học
    assert list(mon["ten_mon"]) == ["Môn D2", "Môn D3"]       # chỉ môn chưa có điểm, bỏ kỳ mới đăng ký
    assert (mon["hoc_ky"] == 4).all()
    nam_ky = cong.nam_ky_hoc_ky(VAN_BAN_HE)
    assert nam_ky[4] == (2024, 2) and nam_ky[5] == (2025, 1)


def test_ky_cu_sot_diem_khong_bi_coi_la_dang_hoc():
    van_ban = _van_ban(
        _ky(2023, 1, [("A1", 4, 7.0, 3.0), ("A2", 3, None, None)], (4, 3.00, 70, 4, 4, 3.00)),
        _ky(2023, 2, [("B1", 4, 7.0, 3.0)], (4, 3.00, 75, 8, 8, 3.00)),
        _ky(2024, 1, [("C1", 3, None, None)]),
    )
    _, hk, mon = cong.doc_van_ban(van_ban)
    assert len(hk) == 2 and list(mon["ten_mon"]) == ["Môn C1"]


def _mo_chi_tiet(van_ban, ma, diem_gk=""):
    """Thêm khối "Chi tiết học phần" sau dòng môn `ma` (như khi đã bấm mũi tên)."""
    dong = van_ban.split("\n")
    i = next(i for i, d in enumerate(dong) if f"\t{ma}\t" in d)
    dong[i + 1:i + 1] = [f"Chi tiết học phần: {ma} - Môn {ma}",
                         "STT\tTên thành phần\tTrọng số\tĐiểm lần 1\tĐiểm lần 2\tĐiểm lần 3",
                         f"1\tĐiểm Thi giữa học phần\t50%\t{diem_gk}\t\t",
                         "2\tĐiểm thi lý thuyết\t50%\t\t\t"]
    return "\n".join(dong)


def test_canh_bao_khong_doi_drl_hoc_ky_he_va_ky_dang_hoc():
    assert not any("rèn luyện" in c for c in cong.canh_bao_du_lieu(VAN_BAN_HE))


def test_ky_dang_hoc_chua_mo_chi_tiet_thi_bao_ten_mon():
    canh_bao = cong.canh_bao_du_lieu(VAN_BAN_HE)
    assert len(canh_bao) == 1 and "Chưa mở Chi tiết 2 môn của HK2 2024–2025" in canh_bao[0]
    assert "Môn D2, Môn D3" in canh_bao[0]
    # đã mở cả hai (một môn chưa có điểm giữa kỳ vẫn tính là đã mở): hết cảnh báo, lấy được GK
    da_mo = _mo_chi_tiet(_mo_chi_tiet(VAN_BAN_HE, "D2", "8.0"), "D3")
    assert cong.canh_bao_du_lieu(da_mo) == []
    _, _, mon = cong.doc_van_ban(da_mo)
    assert mon["diem_gk"].iloc[0] == 8.0 and mon["ti_trong_gk"].iloc[0] == 0.5
    assert np.isnan(mon["diem_gk"].iloc[1])


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
