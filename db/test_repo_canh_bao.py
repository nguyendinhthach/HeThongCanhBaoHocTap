"""
Kiểm tra db/repo_canh_bao.py trên một cơ sở dữ liệu TẠM, không đụng HT_CANHBAOHOCTAP.

Chạy:  python db/test_repo_canh_bao.py

Test tự dựng CSDL HT_THU_REPO từ db/hethongcanhbao.sql + db/nang_cap_canh_bao.sql
(đổi tên CSDL trong nội dung script), chạy các test, rồi xoá CSDL đó dù test
đạt hay lỗi. Cần SQL Server trên máy này với xác thực Windows, như khi chạy app.
"""

import os
import re
import sys
import traceback
from datetime import datetime, timedelta

THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [THU_MUC_GOC, os.path.join(THU_MUC_GOC, "ml")]

TEN_CSDL_THU = "HT_THU_REPO"
os.environ["HT_DB_NAME"] = TEN_CSDL_THU          # phải đặt trước khi engine() được tạo
os.environ.pop("HT_DB_URL", None)

import pyodbc

from db import ket_noi
from db import repo_canh_bao as repo
import doc_cong_thong_tin as cong

FILE_MAU = os.path.join(THU_MUC_GOC, "ml", "du_lieu_mau", "cong_thong_tin_mau.txt")


# --- Dựng / xoá CSDL tạm --------------------------------------------------------
def _ket_noi_master():
    driver = ket_noi.driver_odbc()
    chuoi = f"DRIVER={{{driver}}};SERVER=localhost;DATABASE=master;Trusted_Connection=yes;"
    if "18" in driver:
        chuoi += "Encrypt=yes;TrustServerCertificate=yes;"
    return pyodbc.connect(chuoi, autocommit=True)


def _chay_script(cn, ten_file):
    with open(os.path.join(THU_MUC_GOC, "db", ten_file), encoding="utf-8-sig") as f:
        noi_dung = f.read().replace("HT_CANHBAOHOCTAP", TEN_CSDL_THU)
    for khoi in re.split(r"^\s*GO\s*$", noi_dung, flags=re.MULTILINE | re.IGNORECASE):
        if khoi.strip():
            con_tro = cn.execute(khoi)
            while con_tro.nextset():      # đọc hết kết quả để lỗi ở câu lệnh sau cũng hiện ra
                pass


def xoa_csdl_tam(cn):
    cn.execute(f"IF DB_ID('{TEN_CSDL_THU}') IS NOT NULL BEGIN "
               f"ALTER DATABASE {TEN_CSDL_THU} SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
               f"DROP DATABASE {TEN_CSDL_THU}; END")


def dung_csdl_tam():
    cn = _ket_noi_master()
    xoa_csdl_tam(cn)
    _chay_script(cn, "hethongcanhbao.sql")
    _chay_script(cn, "nang_cap_canh_bao.sql")
    cn.close()


# --- Dữ liệu dùng chung ----------------------------------------------------------
def doc_mau():
    with open(FILE_MAU, encoding="utf-8") as f:
        return cong.doc_van_ban(f.read())


def tao_nguoi(ten="a"):
    return repo.tao_tai_khoan_moi(f"{ten}@dlu.edu.vn", "bam", f"SV {ten}")


def luu_mau(user_id):
    sinh_vien, hk, mon = doc_mau()
    sv = sinh_vien.iloc[0]
    return repo.luu_lan_cap_nhat(user_id, "cong_thong_tin",
                                 {"nam_nhap_hoc": int(sv["nam_nhap_hoc"]), "nganh": sv["nganh"],
                                  "he_dao_tao": sv["he_dao_tao"]}, hk, mon)


def mot_ket_qua(muc_tieu="canh_bao", muc="thap", **them):
    return {"muc_tieu": muc_tieu, "stt_mon": None, "cho_thu_tu": 7, "cho_ten": "HK1 2026–2027",
            "diem_nguy_co": 0.04, "nguong": 0.585, "bao_dong": muc == "cao", "muc_nguy_co": muc,
            "ly_do": [], "goi_y": [], "ghi_chu": None, "phuong_phap": "Random Forest",
            "phien_ban_mo_hinh": "2026-11-02T20:41:00", **them}


# --- Tài khoản -------------------------------------------------------------------
def test_tai_khoan():
    uid = tao_nguoi("tk")
    tk = repo.tai_khoan_theo_email("  TK@dlu.edu.vn ")          # không phân biệt hoa thường, bỏ khoảng trắng
    assert tk["id"] == uid and tk["mat_khau_hash"] == "bam" and tk["nhan_email"] is True
    assert repo.tai_khoan_theo_email("khong-co@dlu.edu.vn") is None
    try:
        tao_nguoi("tk")
        raise AssertionError("email trùng phải báo ValueError")
    except ValueError:
        pass
    repo.dat_nhan_email(uid, False)
    hs = repo.ho_so_canh_bao(uid)
    assert hs["nhan_email"] is False and hs["ho_ten"] == "SV tk" and isinstance(hs["ngay_tao"], datetime)
    assert repo.ho_so_canh_bao(999999) is None


# --- Dữ liệu học tập ------------------------------------------------------------
def test_luu_va_doc_lai_dung_so_lieu():
    uid = tao_nguoi("dl")
    _, hk_goc, mon_goc = doc_mau()
    lcn = luu_mau(uid)
    moi = repo.lan_cap_nhat_moi_nhat(uid)
    assert moi["id"] == lcn and moi["nguon"] == "cong_thong_tin"
    assert moi["thong_tin"] == {"nam_nhap_hoc": 2023, "nganh": "Công nghệ thông tin",
                                "he_dao_tao": "Kỹ sư (4,5 năm)"}
    hk = moi["bang_hoc_ky"]
    assert list(hk["hoc_ky"]) == list(hk_goc["hoc_ky"])
    for cot in ["tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl"]:
        assert list(hk[cot]) == list(hk_goc[cot].astype(float)), cot
    assert list(moi["bang_mon"]["ten_mon"]) == list(mon_goc["ten_mon"])
    assert repo.lan_cap_nhat_moi_nhat(tao_nguoi("chua")) is None


def test_du_lieu_cho_ml_dung_dang_doc_form_va_du_doan_duoc():
    import dac_trung
    import mo_hinh_cuoi
    uid = tao_nguoi("ml")
    sv_goc, hk_goc, mon_goc = doc_mau()
    sinh_vien, hk, mon = repo.du_lieu_cho_ml(luu_mau(uid))
    assert list(hk.columns) == list(hk_goc.columns) and list(mon.columns) == list(mon_goc.columns)
    assert sinh_vien.loc["SV1", "hop_le"], sinh_vien.loc["SV1", "loi"]
    assert (mon["hoc_ky"] == 7).all()
    if not os.path.exists(os.path.join(THU_MUC_GOC, "models", "canh_bao.joblib")):
        print("  (bỏ qua phần dự đoán: chưa có models/)")
        return
    du_lieu = dac_trung.chuan_bi_du_lieu(sinh_vien, hk, mon)
    cb = mo_hinh_cuoi.du_doan(None, "canh_bao", du_lieu=du_lieu)
    cb_goc = mo_hinh_cuoi.du_doan(FILE_MAU, "canh_bao")
    # Đi qua CSDL rồi dự đoán phải ra đúng như đọc thẳng từ văn bản
    assert abs(cb["xac_suat"].iloc[0] - cb_goc["xac_suat"].iloc[0]) < 1e-9
    assert cb["du_doan_cho_hk"].iloc[0] == 7


def test_du_lieu_cho_ml_khong_co():
    try:
        repo.du_lieu_cho_ml(999999)
        raise AssertionError("phải báo LookupError")
    except LookupError:
        pass


def test_so_sai_mien_khong_ghi_gi():
    uid = tao_nguoi("sai")
    _, hk, mon = doc_mau()
    hk.loc[hk.index[0], "dtb_hk"] = 5.0                       # vượt thang 4
    try:
        repo.luu_lan_cap_nhat(uid, "cong_thong_tin", {}, hk, mon)
        raise AssertionError("CSDL phải chặn ĐTB > 4")
    except AssertionError:
        raise
    except Exception:
        pass
    assert repo.lan_cap_nhat_moi_nhat(uid) is None            # giao dịch huỷ hết, không sót dòng nào


def test_nguoi_chua_cap_nhat_va_moi_nhat_moi_nguoi():
    truoc = datetime.now() - timedelta(minutes=5)
    a, b, c = tao_nguoi("nc_a"), tao_nguoi("nc_b"), tao_nguoi("nc_c")
    lcn_a1 = luu_mau(a)
    lcn_a2 = luu_mau(a)
    repo.dat_nhan_email(c, False)
    chua = repo.nguoi_chua_cap_nhat_tu(truoc)
    assert b in chua and a not in chua and c not in chua      # c tắt email nên không nhắc
    assert a in repo.nguoi_chua_cap_nhat_tu(datetime.now() + timedelta(days=1))
    cap = dict(repo.lan_cap_nhat_moi_nhat_moi_nguoi())
    assert cap[a] == lcn_a2 != lcn_a1 and b not in cap


# --- Dự đoán ---------------------------------------------------------------------
def test_luu_va_doc_ket_qua():
    uid = tao_nguoi("dd")
    lcn = luu_mau(uid)
    ids = repo.luu_du_doan(lcn, [
        mot_ket_qua("canh_bao", "thap"),
        mot_ket_qua("thoi_hoc", "thap", diem_nguy_co=0.0),
        mot_ket_qua("truot_mon", "cao", stt_mon=2, diem_nguy_co=0.9, ly_do=["Điểm giữa kỳ = 1.5"]),
        mot_ket_qua("truot_mon", "chua_du_doan", stt_mon=1, diem_nguy_co=None,
                    ghi_chu="Chưa có điểm giữa kỳ hoặc tỉ trọng nên chưa dự đoán"),
    ])
    assert len(ids) == 4
    kq = repo.ket_qua_moi_nhat(uid)
    assert kq["lan_cap_nhat_id"] == lcn
    assert kq["canh_bao"]["muc_nguy_co"] == "thap" and kq["thoi_hoc"]["diem_nguy_co"] == 0.0
    assert [m["stt_mon"] for m in kq["truot_mon"]] == [1, 2]            # sắp theo stt
    assert kq["truot_mon"][1]["ly_do"] == ["Điểm giữa kỳ = 1.5"] and kq["truot_mon"][1]["bao_dong"]
    assert kq["truot_mon"][0]["diem_nguy_co"] is None
    assert kq["truot_mon"][0]["ten_mon"] == "Phát triển ứng dụng web nâng cao"
    assert repo.ket_qua_moi_nhat(tao_nguoi("dd_chua")) is None


def test_luu_du_doan_chan_sai():
    uid = tao_nguoi("dd_sai")
    lcn = luu_mau(uid)
    for sai in [mot_ket_qua(muc="rat_cao"), mot_ket_qua("truot_mon", stt_mon=99)]:
        try:
            repo.luu_du_doan(lcn, [sai])
            raise AssertionError(f"phải chặn {sai}")
        except ValueError:
            pass
    assert repo.ket_qua_moi_nhat(uid) is None


def test_muc_truoc_lich_su_va_phien_ban():
    uid = tao_nguoi("ls")
    lcn1 = luu_mau(uid)
    repo.luu_du_doan(lcn1, [mot_ket_qua(muc="thap")])
    assert repo.muc_canh_bao_truoc(uid, lcn1) is None              # lần đầu
    lcn2 = luu_mau(uid)
    repo.luu_du_doan(lcn2, [mot_ket_qua(muc="cao", phien_ban_mo_hinh="2026-12-01T00:00:00")])
    assert repo.muc_canh_bao_truoc(uid, lcn2) == "thap"            # lần trước thấp -> sẽ gửi email
    ls = repo.lich_su_du_doan(uid)
    assert [d["muc_nguy_co"] for d in ls] == ["cao", "thap"]
    assert repo.phien_ban_mo_hinh_gan_nhat() == "2026-12-01T00:00:00"


# --- Email ---------------------------------------------------------------------
def test_hang_doi_email():
    uid = tao_nguoi("em")
    gui_ngay = repo.them_email(uid, "canh_bao", "Cảnh báo", "Nội dung")
    hen_sau = repo.them_email(uid, "hen_nhac", "Nhắc", "Nội dung", hen_gui=datetime.now() + timedelta(days=7))
    assert repo.them_email(uid, "nhac_giua_ky", "Nhắc", "x", moc="HK1 giữa kỳ", lan_nhac=1)
    assert repo.them_email(uid, "nhac_giua_ky", "Nhắc", "x", moc="HK1 giữa kỳ", lan_nhac=1) is None   # trùng
    assert repo.them_email(uid, "nhac_giua_ky", "Nhắc", "x", moc="HK1 giữa kỳ", lan_nhac=2)
    try:
        repo.them_email(uid, "khong_co", "x", "x")
        raise AssertionError("loai sai phải báo ValueError")
    except ValueError:
        pass

    den_han = [e["id"] for e in repo.email_den_han() if e["user_id"] == uid]
    assert gui_ngay in den_han and hen_sau not in den_han           # hẹn 7 ngày chưa tới
    assert repo.email_den_han()[0]["den"].endswith("@dlu.edu.vn")

    repo.danh_dau_da_gui(gui_ngay)
    assert gui_ngay not in [e["id"] for e in repo.email_den_han()]
    ls = {e["id"]: e for e in repo.lich_su_email(uid)}
    assert ls[gui_ngay]["trang_thai"] == "da_gui" and ls[gui_ngay]["thoi_diem_gui"] is not None


def test_thu_lai_toi_da_3_lan():
    uid = tao_nguoi("loi")
    eid = repo.them_email(uid, "canh_bao", "x", "x")
    assert [repo.danh_dau_loi(eid, "SMTP lỗi") for _ in range(3)] == ["cho_gui", "cho_gui", "loi"]
    assert eid not in [e["id"] for e in repo.email_den_han()]


def test_tat_email_thi_khong_gui():
    uid = tao_nguoi("tat")
    eid = repo.them_email(uid, "canh_bao", "x", "x")
    repo.dat_nhan_email(uid, False)
    assert eid not in [e["id"] for e in repo.email_den_han()]


def test_xoa_tai_khoan_xoa_sach():
    from sqlalchemy import text
    uid = tao_nguoi("xoa")
    lcn = luu_mau(uid)
    dd = repo.luu_du_doan(lcn, [mot_ket_qua(), mot_ket_qua("truot_mon", stt_mon=1)])
    repo.them_email(uid, "canh_bao", "x", "x", du_doan_id=dd[0])
    with ket_noi.engine().begin() as cn:
        cn.execute(text("DELETE FROM dbo.nguoi_dung WHERE id = :id"), {"id": uid})
        con = cn.execute(text("""SELECT (SELECT COUNT(*) FROM dbo.lan_cap_nhat WHERE user_id = :id)
                                      + (SELECT COUNT(*) FROM dbo.email_da_gui WHERE user_id = :id)
                                      + (SELECT COUNT(*) FROM dbo.du_doan WHERE lan_cap_nhat_id = :lcn)"""),
                         {"id": uid, "lcn": lcn}).scalar_one()
    assert con == 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dung_csdl_tam()
    try:
        assert ket_noi.kiem_tra() == TEN_CSDL_THU, "đang nối nhầm CSDL"
        cac_test = [(ten, ham) for ten, ham in globals().items() if ten.startswith("test_")]
        loi = 0
        for ten, ham in cac_test:
            try:
                ham()
                print(f"OK    {ten}")
            except Exception as e:
                loi += 1
                print(f"LỖI   {ten}: {type(e).__name__}: {str(e)[:300]}")
                traceback.print_exc(limit=2)
        print(f"\n{len(cac_test) - loi}/{len(cac_test)} test đạt")
    finally:
        ket_noi.engine().dispose()
        cn = _ket_noi_master()
        xoa_csdl_tam(cn)
        cn.close()
        print(f"Đã xoá CSDL tạm {TEN_CSDL_THU}")
    raise SystemExit(1 if loi else 0)
