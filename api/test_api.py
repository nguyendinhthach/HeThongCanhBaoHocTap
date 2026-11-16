"""
Kiểm tra API (api/main.py) trên CSDL tạm HT_THU_REPO, không đụng HT_CANHBAOHOCTAP.

Chạy:  python api/test_api.py

Dùng lại phần dựng / xoá CSDL tạm của db/test_repo_canh_bao.py; cần models/
đã train (python ml/mo_hinh_cuoi.py).
"""

import os
import sys
import traceback

THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [THU_MUC_GOC, os.path.join(THU_MUC_GOC, "ml")]

# Import trước tiên: đặt HT_DB_NAME sang CSDL tạm trước khi engine được tạo
from db import test_repo_canh_bao as csdl_tam
os.environ["HT_JWT_SECRET"] = "khoa-chi-de-test-" + "x" * 32       # >= 32 byte như cau_hinh yêu cầu

from fastapi.testclient import TestClient

from api.main import app
from db import ket_noi

FILE_MAU = os.path.join(THU_MUC_GOC, "ml", "du_lieu_mau", "cong_thong_tin_mau.txt")
VAN_BAN = open(FILE_MAU, encoding="utf-8").read()
kh = TestClient(app)


def dang_ky_va_dang_nhap(ten):
    email = f"{ten}@dlu.edu.vn"
    r = kh.post("/auth/dang-ky", json={"email": email, "mat_khau": "matkhau123", "ho_ten": f"SV {ten}"})
    assert r.status_code == 201, r.text
    r = kh.post("/auth/dang-nhap", data={"username": email, "password": "matkhau123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def luu_tu_van_ban(dau, sua=None, **them):
    xem = kh.post("/du-lieu/doc", json={"van_ban": VAN_BAN}, headers=dau).json()
    if sua:
        sua(xem)
    return kh.post("/du-lieu", headers=dau, json={"nguon": "cong_thong_tin", "thong_tin": xem["thong_tin"],
                                                    "hoc_ky": xem["hoc_ky"], "mon": xem["mon"], **them})


def lam_kem(xem):
    """Học kỳ gần nhất rất kém -> mô hình phải báo nguy cơ cao."""
    xem["hoc_ky"][-1].update(dtb_hk=0.3, dtb_tl=1.2, tc_dang_ky=125.0)


# --- Tài khoản ------------------------------------------------------------------
def test_dang_ky_dang_nhap():
    dau = dang_ky_va_dang_nhap("tk")
    r = kh.get("/toi", headers=dau)
    assert r.status_code == 200 and r.json()["nhan_email"] is True and "mat_khau_hash" not in r.json()
    assert kh.post("/auth/dang-ky", json={"email": "tk@dlu.edu.vn", "mat_khau": "matkhau123",
                                          "ho_ten": "x"}).status_code == 409
    r = kh.post("/auth/dang-ky", json={"email": "khong-phai-email", "mat_khau": "123", "ho_ten": ""})
    assert r.status_code == 422 and len(r.json()["loi"]) == 3
    assert kh.post("/auth/dang-nhap", data={"username": "tk@dlu.edu.vn", "password": "sai"}).status_code == 401
    r = kh.patch("/toi", json={"nhan_email": False}, headers=dau)
    assert r.json()["nhan_email"] is False


def test_can_dang_nhap():
    for phuong_thuc, duong_dan in [("get", "/toi"), ("post", "/du-doan"), ("get", "/ket-qua/moi-nhat"),
                                   ("get", "/email/lich-su")]:
        assert getattr(kh, phuong_thuc)(duong_dan).status_code == 401, duong_dan
    assert kh.get("/toi", headers={"Authorization": "Bearer sai"}).status_code == 401


# --- Dữ liệu --------------------------------------------------------------------
def test_doc_xem_truoc_khong_luu():
    dau = dang_ky_va_dang_nhap("doc")
    r = kh.post("/du-lieu/doc", json={"van_ban": VAN_BAN}, headers=dau)
    x = r.json()
    assert r.status_code == 200 and x["hop_le"] and x["ky_mon"] == "HK1 2026–2027"
    assert x["hoc_ky"][-1]["ten"] == "HK2 2025–2026" and len(x["mon"]) == 6
    assert kh.get("/du-lieu/moi-nhat", headers=dau).json() is None          # chưa lưu gì
    assert kh.post("/du-lieu/doc", json={"van_ban": "Trang chủ"}, headers=dau).status_code == 422


def test_luu_va_doc_lai():
    dau = dang_ky_va_dang_nhap("luu")
    r = luu_tu_van_ban(dau, muc_vang="Từ 5% đến dưới 10%", hoc_phi="Đóng đủ, đúng hạn")
    assert r.status_code == 201, r.text
    moi = kh.get("/du-lieu/moi-nhat", headers=dau).json()
    assert moi["id"] == r.json()["lan_cap_nhat_id"] and len(moi["bang_hoc_ky"]) == 6
    cuoi = moi["bang_hoc_ky"][-1]
    assert cuoi["muc_vang"] == "Từ 5% đến dưới 10%" and cuoi["nam_bat_dau"] == 2025 and cuoi["ky_trong_nam"] == 2


def test_luu_du_lieu_sai_bao_loi_khong_luu():
    dau = dang_ky_va_dang_nhap("sai")
    def sai(xem):
        xem["hoc_ky"][-1]["tc_dang_ky"] = 10.0                               # < TCTL
        xem["mon"][0].update(diem_gk=11.0, vang_lt="Vắng nhiều lắm")
    r = luu_tu_van_ban(dau, sai, muc_vang="không có lựa chọn này")
    assert r.status_code == 422
    loi = " ".join(r.json()["loi"])
    assert "TC đăng ký" in loi and "Điểm giữa kỳ" in loi and "muc_vang" in loi and "vang_lt" in loi
    assert kh.get("/du-lieu/moi-nhat", headers=dau).json() is None


# --- Dự đoán --------------------------------------------------------------------
def test_du_doan_hoc_tot():
    dau = dang_ky_va_dang_nhap("tot")
    assert kh.post("/du-doan", headers=dau).status_code == 422             # chưa có dữ liệu
    luu_tu_van_ban(dau)
    r = kh.post("/du-doan", headers=dau)
    assert r.status_code == 200, r.text
    kq = r.json()
    assert kq["canh_bao"]["cho_ten"] == "HK1 2026–2027" and kq["canh_bao"]["muc_nguy_co"] == "thap"
    assert kq["canh_bao"]["goi_y"] == [] and kq["email_canh_bao"] is False
    assert kq["thoi_hoc"]["ghi_chu"].startswith("Chưa thể xảy ra")
    assert len(kq["truot_mon"]) == 6 and all(m["muc_nguy_co"] == "chua_du_doan" for m in kq["truot_mon"])
    assert kh.get("/ket-qua/moi-nhat", headers=dau).json()["lan_cap_nhat_id"] == kq["lan_cap_nhat_id"]
    assert kh.get("/email/lich-su", headers=dau).json() == []


def test_du_doan_kem_xep_email_mot_lan():
    dau = dang_ky_va_dang_nhap("kem")
    luu_tu_van_ban(dau, lam_kem)
    kq = kh.post("/du-doan", headers=dau).json()
    assert kq["canh_bao"]["muc_nguy_co"] == "cao" and kq["canh_bao"]["ly_do"] and kq["canh_bao"]["goi_y"]
    assert kq["email_canh_bao"] is True
    # Cập nhật lại vẫn kém: vẫn "cao" như lần trước -> không gửi lại
    luu_tu_van_ban(dau, lam_kem)
    assert kh.post("/du-doan", headers=dau).json()["email_canh_bao"] is False
    thu = kh.get("/email/lich-su", headers=dau).json()
    assert [e["loai"] for e in thu] == ["canh_bao"] and thu[0]["trang_thai"] == "cho_gui"
    ls = kh.get("/ket-qua/lich-su", headers=dau).json()
    assert [d["muc_nguy_co"] for d in ls] == ["cao", "cao"]


def test_nhap_diem_giua_ky_thi_du_doan_mon_va_goi_y():
    dau = dang_ky_va_dang_nhap("mon")
    luu_tu_van_ban(dau, lambda x: x["mon"][0].update(diem_gk=1.5, ti_trong_gk=0.5,
                                                     vang_lt="Ít hoặc không vắng",
                                                     vang_th="Không vắng buổi nào"))
    mon = kh.post("/du-doan", headers=dau).json()["truot_mon"]
    assert mon[0]["muc_nguy_co"] in ("cao", "thap") and mon[0]["diem_nguy_co"] is not None
    assert any("6,5 điểm thi cuối kỳ" in g for g in mon[0]["goi_y"])
    assert mon[1]["muc_nguy_co"] == "chua_du_doan"


# --- Nhắc, hệ thống ---------------------------------------------------------------
def test_hen_nhac():
    dau = dang_ky_va_dang_nhap("hen")
    assert kh.post("/hen-nhac", json={"so_ngay": 7}, headers=dau).status_code == 201
    assert kh.post("/hen-nhac", json={"so_ngay": 3}, headers=dau).status_code == 422
    assert [e["loai"] for e in kh.get("/email/lich-su", headers=dau).json()] == ["hen_nhac"]


def test_suc_khoe():
    r = kh.get("/suc-khoe").json()
    assert r["api"] == "ok" and r["csdl"] == csdl_tam.TEN_CSDL_THU
    assert r["mo_hinh"]["canh_bao"]["phuong_phap"] == "Random Forest"


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    csdl_tam.dung_csdl_tam()
    loi = 0
    try:
        cac_test = [(ten, ham) for ten, ham in globals().items() if ten.startswith("test_")]
        for ten, ham in cac_test:
            try:
                ham()
                print(f"OK    {ten}")
            except Exception as e:
                loi += 1
                print(f"LỖI   {ten}: {type(e).__name__}: {str(e)[:300]}")
                traceback.print_exc(limit=3)
        print(f"\n{len(cac_test) - loi}/{len(cac_test)} test đạt")
    finally:
        ket_noi.engine().dispose()
        cn = csdl_tam._ket_noi_master()
        csdl_tam.xoa_csdl_tam(cn)
        cn.close()
        print(f"Đã xoá CSDL tạm {csdl_tam.TEN_CSDL_THU}")
    raise SystemExit(1 if loi else 0)
