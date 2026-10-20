"""
Kiểm tra doc_form.py, gan_nhan.py, mo_phong.py.

Chạy:  python ml/test_mo_phong.py     (hoặc pytest ml/ nếu đã cài pytest)

Test đối chiếu tên cột với file khảo sát thật chỉ chạy khi có file đó; đường
dẫn lấy từ biến môi trường KHAO_SAT_THAT, mặc định ở thư mục Downloads.
"""

import os
import tempfile

import pandas as pd

import doc_form as form
import gan_nhan
import mo_phong


DUONG_DAN_KHAO_SAT = os.environ.get(
    "KHAO_SAT_THAT", os.path.expanduser(r"~\Downloads\Kết quả khảo sát học tập (ẩn danh).xlsx"))

SO_SV, SEED = 300, 7
_cache = {}


def du_lieu_mo_phong():
    """Sinh một lần, ghi ra file tạm rồi đọc lại bằng doc_form như dữ liệu thật."""
    if not _cache:
        bang_form, bang_nhan = mo_phong.mo_phong(SO_SV, SEED)
        duong_dan = os.path.join(tempfile.mkdtemp(), "mo_phong.xlsx")
        mo_phong.ghi_xlsx(bang_form, bang_nhan, duong_dan)
        sinh_vien, bang_hoc_ky, bang_mon = form.doc_form(duong_dan)
        _cache.update(bang_form=bang_form, bang_nhan=bang_nhan, sinh_vien=sinh_vien,
                      bang_hoc_ky=bang_hoc_ky, bang_mon=bang_mon)
    return _cache


# --- gan_nhan: số liệu theo QĐ 600 --------------------------------------------

def test_quy_doi_thang_4():
    # Điều 13.5a: A 8,5–10; B 7,0–8,4; C 5,5–6,9; D 4,0–5,4; F dưới 4,0
    cac_ca = {10: 4, 8.5: 4, 8.4: 3, 7.0: 3, 6.9: 2, 5.5: 2, 5.4: 1, 4.0: 1, 3.9: 0, 0: 0}
    for diem_10, diem_4 in cac_ca.items():
        assert gan_nhan.quy_doi_thang_4(diem_10) == diem_4, diem_10


def test_trinh_do_nam():
    # Điều 15.7: dưới 35 / 35–dưới 70 / 70–dưới 105 / từ 105
    cac_ca = {0: 1, 34: 1, 35: 2, 69: 2, 70: 3, 104: 3, 105: 4, 150: 4}
    for tctl, nam in cac_ca.items():
        assert gan_nhan.trinh_do_nam(tctl) == nam, tctl


def test_ly_do_canh_bao():
    tot = dict(dtb_hk=3.0, dtb_tl=3.0, tctl=50, no_tc=0, ky_dau=False)
    assert gan_nhan.ly_do_canh_bao(**tot) == []
    # ĐTB học kỳ: dưới 0,8 ở kỳ đầu, dưới 1,0 các kỳ sau
    assert gan_nhan.ly_do_canh_bao(**{**tot, "dtb_hk": 0.9, "ky_dau": True}) == []
    assert gan_nhan.ly_do_canh_bao(**{**tot, "dtb_hk": 0.9}) != []
    # Nợ: quá 24 TC mới bị
    assert gan_nhan.ly_do_canh_bao(**{**tot, "no_tc": 24}) == []
    assert gan_nhan.ly_do_canh_bao(**{**tot, "no_tc": 25}) != []
    # Rớt quá 50% TC đăng ký trong kỳ: đúng 50% thì chưa bị
    assert gan_nhan.ly_do_canh_bao(**tot, tc_rot_hk=10, tc_dang_ky_hk=20) == []
    assert gan_nhan.ly_do_canh_bao(**tot, tc_rot_hk=11, tc_dang_ky_hk=20) != []
    # ĐTB tích luỹ theo trình độ năm: 1,5 bị ở năm 3 (dưới 1,6) nhưng không bị ở năm 2
    assert gan_nhan.ly_do_canh_bao(**{**tot, "dtb_tl": 1.5, "tctl": 60}) == []
    assert gan_nhan.ly_do_canh_bao(**{**tot, "dtb_tl": 1.5, "tctl": 80}) != []


def test_buoc_thoi_hoc_lan_thu_3_lien_tiep():
    # Điều 18.2a: cảnh báo quá 2 lần liên tiếp; bị lại từ đầu nếu có kỳ xen giữa không bị
    dtb = [0.5, 0.5, 3.0, 0.5, 0.5, 0.5]
    bang = pd.DataFrame({"ma_sv": "SV1", "hoc_ky": range(1, 7), "dtb_hk": dtb,
                         "dtb_tl": 2.5, "tctl": [15, 30, 50, 60, 70, 80],
                         "tc_dang_ky": [15, 30, 50, 60, 70, 80]})
    nhan = gan_nhan.gan_nhan_hoc_ky(bang)
    assert nhan["canh_bao"].tolist() == [1, 1, 0, 1, 1, 1]
    assert nhan["buoc_thoi_hoc"].tolist() == [0, 0, 0, 0, 0, 1]


# --- doc_form ------------------------------------------------------------------

def test_cot_form_khop_file_that():
    if not os.path.exists(DUONG_DAN_KHAO_SAT):
        print("  (bỏ qua: không có file khảo sát thật)")
        return
    that = list(pd.read_excel(DUONG_DAN_KHAO_SAT, nrows=0).columns)
    assert that == form.cac_cot_form()


def test_doc_file_that_dung_5_sv_hop_le():
    if not os.path.exists(DUONG_DAN_KHAO_SAT):
        print("  (bỏ qua: không có file khảo sát thật)")
        return
    sinh_vien, _, _ = form.doc_form(DUONG_DAN_KHAO_SAT)
    assert list(sinh_vien.index[sinh_vien["hop_le"]]) == ["SV1", "SV2", "SV4", "SV6", "SV7"]


# --- mo_phong --------------------------------------------------------------------

def test_cung_seed_ra_cung_du_lieu():
    a, _ = mo_phong.mo_phong(30, 123)
    b, _ = mo_phong.mo_phong(30, 123)
    c, _ = mo_phong.mo_phong(30, 124)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_mo_phong_dung_dinh_dang_form():
    d = du_lieu_mo_phong()
    assert list(d["bang_form"].columns) == form.cac_cot_form()
    assert len(d["sinh_vien"]) == SO_SV


def test_moi_sv_mo_phong_deu_hop_le():
    # Bộ kiểm tra của doc_form (TC đăng ký >= TCTL, không giảm, ĐTB 0–4...)
    sinh_vien = du_lieu_mo_phong()["sinh_vien"]
    loi = sinh_vien.loc[~sinh_vien["hop_le"], "loi"]
    assert loi.empty, loi.head().to_dict()


def test_quy_tac_tin_chi():
    hk = du_lieu_mo_phong()["bang_hoc_ky"].sort_values(["ma_sv", "hoc_ky"])
    nhan = du_lieu_mo_phong()["bang_nhan"]
    assert (hk["tc_dang_ky"] >= hk["tctl"]).all()
    # TCTL tăng ít nhất bằng số TC đạt học kỳ (hè có thể cộng thêm)
    tang = hk.groupby("ma_sv")["tctl"].diff().dropna()
    assert (tang >= hk.loc[tang.index, "tc_dat_hk"]).all()
    # Nợ đọng trong nhãn thật = TC đăng ký − TCTL đọc từ form
    gop = hk.merge(nhan, on=["ma_sv", "hoc_ky"])
    assert (gop["no_tc"] == gop["tc_dang_ky"] - gop["tctl"]).all()


def test_gia_tri_nam_trong_mien():
    hk = du_lieu_mo_phong()["bang_hoc_ky"]
    assert hk["dtb_hk"].between(0, 4).all() and hk["dtb_tl"].between(0, 4).all()
    assert hk["drl"].dropna().between(0, 100).all()
    assert hk["tc_dat_hk"].between(0, mo_phong.TC_HK_NHIEU_NHAT).all()
    assert set(hk["muc_vang"]) <= set(form.MUC_VANG)
    assert set(hk["hoc_phi"]) <= set(form.HOC_PHI)
    assert set(hk["hoc_he"]) <= set(form.HOC_HE)
    mon = du_lieu_mo_phong()["bang_mon"]
    assert set(mon["ket_qua"]) <= set(form.KET_QUA_MON)
    assert mon["diem_gk"].dropna().between(0, 10).all()


def test_diem_gk_khong_lo_nhan_cam_thi():
    # Điểm giữa kỳ là điểm quá trình nên môn bị cấm thi vẫn có; nếu để trống
    # thì "trống" trùng với "cấm thi" và mô hình học mẹo đó thay vì học thật.
    mon = du_lieu_mo_phong()["bang_mon"]
    cam_thi = mon[mon["ket_qua"] == "Bị cấm thi"]
    assert len(cam_thi) > 0
    assert cam_thi["diem_gk"].notna().all()


def test_buoc_thoi_hoc_thi_dung_lai():
    d = du_lieu_mo_phong()
    nhan, sinh_vien = d["bang_nhan"], d["sinh_vien"]
    thoi_hoc = nhan[nhan["buoc_thoi_hoc"] == 1]
    assert len(thoi_hoc) > 0, "mô phỏng phải có ca buộc thôi học"
    hk_cuoi = nhan.groupby("ma_sv")["hoc_ky"].max()
    for _, d in thoi_hoc.iterrows():
        assert d["hoc_ky"] == hk_cuoi[d["ma_sv"]], "còn học kỳ sau khi bị buộc thôi học"
        assert d["so_lan_canh_bao_lien_tiep"] == gan_nhan.SO_LAN_CANH_BAO_THOI_HOC
        assert sinh_vien.loc[d["ma_sv"], "tinh_trang"] == "Bị buộc thôi học"


def test_co_du_ca_duong():
    d = du_lieu_mo_phong()
    assert 0.02 < d["bang_nhan"]["canh_bao"].mean() < 0.2
    truot = gan_nhan.gan_nhan_mon(d["bang_mon"])["truot_mon"]
    assert truot.sum() > 0


def test_nhan_tu_form_gan_nhan_that():
    """Form thiếu số TC rớt trong kỳ nên nhãn gán từ form chỉ xấp xỉ nhãn thật."""
    d = du_lieu_mo_phong()
    tu_form = gan_nhan.gan_nhan_hoc_ky(d["bang_hoc_ky"])
    gop = tu_form.merge(d["bang_nhan"], on=["ma_sv", "hoc_ky"], suffixes=("_form", "_that"))
    khop = (gop["canh_bao_form"] == gop["canh_bao_that"]).mean()
    # Nhãn từ form không bao giờ báo cảnh báo khi nhãn thật không có
    assert not ((gop["canh_bao_form"] == 1) & (gop["canh_bao_that"] == 0)).any()
    print(f"  nhãn cảnh báo từ form khớp nhãn thật: {khop:.1%}")
    assert khop > 0.95


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
