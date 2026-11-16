"""Đọc và ghi dữ liệu cho hệ thống cảnh báo sớm (SPEC §12).

Hợp đồng hàm chốt ở nhánh feature/hop-dong-repo; phần API (dich_vu/,
FastAPI, tác vụ định kỳ) gọi đúng các hàm này. Đổi chữ ký hàm thì báo bên
gọi; thêm tham số có giá trị mặc định thì không cần.

Bảng dùng: nguoi_dung, lan_cap_nhat, hoc_ky_tong_ket, mon_dang_hoc, du_doan,
email_da_gui (db/nang_cap_canh_bao.sql). Không dùng bảng của giao diện cũ.

Quy ước:
- Bảng học kỳ / môn truyền vào và trả ra là pandas DataFrame, ĐÚNG cột như
  ml/ đang dùng (doc_form.py, doc_cong_thong_tin.py), để đưa thẳng vào
  dac_trung.chuan_bi_du_lieu() và mo_hinh_cuoi.du_doan(du_lieu=...).
- Hàm ghi nhiều bảng chạy trong MỘT giao dịch: lỗi giữa chừng thì không ghi
  gì cả.
- Tài khoản tạo theo luồng mới có niên khoá trống nên các hàm hồ sơ cũ
  repo.ho_so() / repo.ho_so_theo_email() sẽ lỗi với họ: luồng mới dùng
  tai_khoan_theo_email() / ho_so_canh_bao() ở đây.
- Thời điểm là datetime theo giờ máy chủ SQL (SYSDATETIME()), chính xác tới giây.
- Một LƯỢT dự đoán = các dòng du_doan cùng lan_cap_nhat_id và cùng thoi_diem
  (luu_du_doan gán chung một thời điểm cho cả lượt).
"""

import json
import os
import sys
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from db.ket_noi import engine

# Mức nguy cơ lưu trong du_doan.muc_nguy_co
MUC_NGUY_CO = ("thap", "trung_binh", "cao", "chua_du_doan")
# Loại email trong email_da_gui.loai
LOAI_EMAIL = ("nhac_giua_ky", "nhac_cuoi_ky", "hen_nhac", "canh_bao", "mo_hinh_moi")
NGUON = ("cong_thong_tin", "nhap_tay")
SO_LAN_THU_TOI_DA = 3
MA_SV = "SV1"       # du_lieu_cho_ml: mỗi lần cập nhật là một sinh viên, như doc_cong_thong_tin

# Cột bảng học kỳ / môn phía ml/ <-> cột CSDL
_COT_HOC_KY = ["tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl", "muc_vang", "hoc_phi"]
_COT_MON = ["ten_mon", "so_tc", "diem_gk", "ti_trong_gk", "vang_lt", "vang_th"]


def _doc_form():
    """doc_form của ml/ (các module trong ml/ import nhau bằng tên trần)."""
    thu_muc_ml = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
    if thu_muc_ml not in sys.path:
        sys.path.insert(0, thu_muc_ml)
    import doc_form
    return doc_form


def _gia_tri(v):
    """Giá trị pandas / numpy -> kiểu Python để gửi xuống SQL (NaN, NA -> None)."""
    if v is None or (not isinstance(v, (str, list, dict)) and pd.isna(v)):
        return None
    if isinstance(v, np.generic):
        return v.item()
    return v


def _so(v):
    """Decimal của SQL Server -> float (bảng ml/ dùng float)."""
    return float(v) if isinstance(v, Decimal) else v


def _json(v):
    return json.loads(v) if v else []


# --- Tài khoản ---------------------------------------------------------------
def tao_tai_khoan_moi(email: str, mat_khau_bam: str, ho_ten: str) -> int:
    """Tạo tài khoản theo form đăng ký mới (không niên khoá). Trả về user_id.

    Email đã có thì báo ValueError("email đã được dùng"). nhan_email mặc định 1.
    """
    try:
        with engine().begin() as cn:
            return cn.execute(text("""
                INSERT INTO dbo.nguoi_dung (email, mat_khau_hash, ho_ten)
                OUTPUT INSERTED.id
                VALUES (:em, :mk, :ten)
            """), {"em": email.strip(), "mk": mat_khau_bam, "ten": ho_ten.strip()}).scalar_one()
    except IntegrityError as loi:
        if "UQ_nguoi_dung_email" in str(loi):
            raise ValueError("email đã được dùng") from loi
        raise


def tai_khoan_theo_email(email: str) -> dict | None:
    """Dùng cho đăng nhập: {"id", "email", "ho_ten", "mat_khau_hash", "nhan_email"}.

    Không có thì None. Email so không phân biệt hoa thường (collation của CSDL).
    """
    with engine().connect() as cn:
        r = cn.execute(text("""
            SELECT id, email, ho_ten, mat_khau_hash, nhan_email
            FROM dbo.nguoi_dung WHERE email = :em
        """), {"em": email.strip()}).mappings().one_or_none()
    return {**r, "nhan_email": bool(r["nhan_email"])} if r else None


def ho_so_canh_bao(user_id: int) -> dict | None:
    """{"id", "email", "ho_ten", "nhan_email", "ngay_tao"}; không có thì None."""
    with engine().connect() as cn:
        r = cn.execute(text("""
            SELECT id, email, ho_ten, nhan_email, ngay_tao
            FROM dbo.nguoi_dung WHERE id = :id
        """), {"id": user_id}).mappings().one_or_none()
    return {**r, "nhan_email": bool(r["nhan_email"])} if r else None


def dat_nhan_email(user_id: int, bat: bool) -> None:
    """Bật / tắt nhận email (PATCH /toi)."""
    with engine().begin() as cn:
        cn.execute(text("UPDATE dbo.nguoi_dung SET nhan_email = :bat WHERE id = :id"),
                   {"bat": int(bool(bat)), "id": user_id})


# --- Dữ liệu học tập (mỗi lần cập nhật là một bản mới, không ghi đè) ---------
def luu_lan_cap_nhat(user_id: int, nguon: str, thong_tin: dict,
                     bang_hoc_ky: pd.DataFrame, bang_mon: pd.DataFrame) -> int:
    """Lưu một lần cập nhật: 1 dòng lan_cap_nhat + các học kỳ + các môn đang học.

    nguon: "cong_thong_tin" hoặc "nhap_tay".
    thong_tin: {"nam_nhap_hoc", "nganh", "he_dao_tao"} (giá trị có thể None).
    bang_hoc_ky: cột như ml/ — hoc_ky (thứ tự 1, 2...), tc_dat_hk, dtb_hk,
        tctl, tc_dang_ky, dtb_tl, muc_vang, hoc_phi, drl; thêm nam_bat_dau,
        ky_trong_nam nếu biết (không có thì lưu NULL).
    bang_mon: cột như ml/ — stt_mon, ten_mon, so_tc, diem_gk, ti_trong_gk,
        vang_lt, vang_th; thêm ma_mon nếu biết. Có thể rỗng.
    Kiểm tra hợp lệ (doc_form.kiem_tra) là việc của bên gọi; CSDL vẫn chặn số
    sai miền bằng ràng buộc CHECK (báo lỗi, không ghi gì). Trả về lan_cap_nhat_id.
    """
    if nguon not in NGUON:
        raise ValueError(f"nguon phải là một trong {NGUON}, nhận {nguon!r}")
    hoc_ky = [{
        "thu_tu": int(d["hoc_ky"]),
        "nam_bat_dau": _gia_tri(d.get("nam_bat_dau")),
        "hoc_ky": _gia_tri(d.get("ky_trong_nam")),
        **{c: _gia_tri(d.get(c)) for c in _COT_HOC_KY},
    } for d in bang_hoc_ky.to_dict("records")]
    mon = [{
        "stt": int(d["stt_mon"]),
        "ma_mon": _gia_tri(d.get("ma_mon")),
        **{c: _gia_tri(d.get(c)) for c in _COT_MON},
    } for d in bang_mon.to_dict("records")]
    for m in mon:
        m["ten_mon"] = m["ten_mon"] or f"Môn {m['stt']}"     # cột bắt buộc; mô phỏng không có tên

    with engine().begin() as cn:
        lcn_id = cn.execute(text("""
            INSERT INTO dbo.lan_cap_nhat (user_id, nguon, nam_nhap_hoc, nganh, he_dao_tao)
            OUTPUT INSERTED.id
            VALUES (:uid, :nguon, :nam, :nganh, :he)
        """), {"uid": user_id, "nguon": nguon,
               "nam": _gia_tri(thong_tin.get("nam_nhap_hoc")),
               "nganh": _gia_tri(thong_tin.get("nganh")),
               "he": _gia_tri(thong_tin.get("he_dao_tao"))}).scalar_one()
        if hoc_ky:
            cn.execute(text("""
                INSERT INTO dbo.hoc_ky_tong_ket
                    (lan_cap_nhat_id, thu_tu, nam_bat_dau, hoc_ky, tc_dat_hk, dtb_hk, tctl,
                     tc_dang_ky, dtb_tl, drl, muc_vang, hoc_phi)
                VALUES (:lcn, :thu_tu, :nam_bat_dau, :hoc_ky, :tc_dat_hk, :dtb_hk, :tctl,
                        :tc_dang_ky, :dtb_tl, :drl, :muc_vang, :hoc_phi)
            """), [{"lcn": lcn_id, **d} for d in hoc_ky])
        if mon:
            cn.execute(text("""
                INSERT INTO dbo.mon_dang_hoc
                    (lan_cap_nhat_id, stt, ma_mon, ten_mon, so_tc, diem_gk, ti_trong_gk, vang_lt, vang_th)
                VALUES (:lcn, :stt, :ma_mon, :ten_mon, :so_tc, :diem_gk, :ti_trong_gk, :vang_lt, :vang_th)
            """), [{"lcn": lcn_id, **d} for d in mon])
    return lcn_id


def _doc_lan_cap_nhat(cn, lan_cap_nhat_id: int):
    """(dòng lan_cap_nhat, DataFrame học kỳ, DataFrame môn) — cột như ml/."""
    lcn = cn.execute(text("""
        SELECT id, user_id, thoi_diem, nguon, nam_nhap_hoc, nganh, he_dao_tao
        FROM dbo.lan_cap_nhat WHERE id = :id
    """), {"id": lan_cap_nhat_id}).mappings().one_or_none()
    if lcn is None:
        raise LookupError(f"không có lần cập nhật {lan_cap_nhat_id}")

    hk = pd.DataFrame(cn.execute(text("""
        SELECT thu_tu AS hoc_ky, nam_bat_dau, hoc_ky AS ky_trong_nam, tc_dat_hk, dtb_hk, tctl,
               tc_dang_ky, dtb_tl, muc_vang, hoc_phi, drl
        FROM dbo.hoc_ky_tong_ket WHERE lan_cap_nhat_id = :id ORDER BY thu_tu
    """), {"id": lan_cap_nhat_id}).mappings().all(),
        columns=["hoc_ky", "nam_bat_dau", "ky_trong_nam", "tc_dat_hk", "dtb_hk", "tctl",
                 "tc_dang_ky", "dtb_tl", "muc_vang", "hoc_phi", "drl"])
    mon = pd.DataFrame(cn.execute(text("""
        SELECT stt AS stt_mon, ma_mon, ten_mon, so_tc, diem_gk, ti_trong_gk, vang_lt, vang_th
        FROM dbo.mon_dang_hoc WHERE lan_cap_nhat_id = :id ORDER BY stt
    """), {"id": lan_cap_nhat_id}).mappings().all(),
        columns=["stt_mon", "ma_mon", "ten_mon", "so_tc", "diem_gk", "ti_trong_gk", "vang_lt", "vang_th"])
    for bang, cot_so in [(hk, ["tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl"]),
                         (mon, ["so_tc", "diem_gk", "ti_trong_gk"])]:
        bang[cot_so] = bang[cot_so].map(_so).astype(float)
    for cot in ["muc_vang", "hoc_phi"]:
        hk[cot] = hk[cot].astype(object).where(hk[cot].notna(), np.nan)
    for cot in ["vang_lt", "vang_th"]:
        mon[cot] = mon[cot].astype(object).where(mon[cot].notna(), np.nan)
    return lcn, hk, mon


def du_lieu_cho_ml(lan_cap_nhat_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(sinh_vien, bang_hoc_ky, bang_mon) của một lần cập nhật, ĐÚNG dạng
    doc_form.doc_form() trả về (ma_sv = "SV1", có cột hop_le, loi), để gọi:

        du_lieu = dac_trung.chuan_bi_du_lieu(*repo_canh_bao.du_lieu_cho_ml(lcn_id))
        mo_hinh_cuoi.du_doan(None, "canh_bao", du_lieu=du_lieu)

    Các môn được coi là của học kỳ kế tiếp học kỳ cuối đã có điểm (kỳ đang học).
    Không có lần cập nhật đó thì LookupError.
    """
    form = _doc_form()
    with engine().connect() as cn:
        lcn, hk, mon = _doc_lan_cap_nhat(cn, lan_cap_nhat_id)

    # Học kỳ hè không lưu (mô hình không dùng) nhưng giữ cột cho đúng dạng doc_form
    bang_hoc_ky = hk.assign(ma_sv=MA_SV, hoc_he=np.nan)[["ma_sv", "hoc_ky", *form.CAU_HOC_KY.values()]]
    bang_hoc_ky["hoc_ky"] = bang_hoc_ky["hoc_ky"].astype(int)

    ky_dang_hoc = int(hk["hoc_ky"].max()) + 1 if len(hk) else 1
    bang_mon = mon.assign(ma_sv=MA_SV, hoc_ky=ky_dang_hoc, ket_qua=np.nan)
    bang_mon = bang_mon[["ma_sv", "hoc_ky", "stt_mon", *form.CAU_MON.values()]]

    trong = lambda v: np.nan if v is None else v      # ô trống trong CSDL -> NaN như ml/
    sinh_vien = pd.DataFrame({
        "nam_nhap_hoc": [trong(lcn["nam_nhap_hoc"])], "nganh": [trong(lcn["nganh"])],
        "he_dao_tao": [trong(lcn["he_dao_tao"])], "tinh_trang": ["Đang học"], "ky_luat": [np.nan],
        "so_mon_hk_cuoi": [len(mon)],
    }, index=pd.Index([MA_SV], name="ma_sv"))
    loi = form.kiem_tra(bang_hoc_ky, sinh_vien)
    sinh_vien["hop_le"] = [not loi[MA_SV]]
    sinh_vien["loi"] = ["; ".join(loi[MA_SV])]
    return sinh_vien, bang_hoc_ky, bang_mon


def lan_cap_nhat_moi_nhat(user_id: int) -> dict | None:
    """Lần cập nhật gần nhất (GET /du-lieu/moi-nhat, điền sẵn giao diện):

        {"id", "thoi_diem", "nguon", "thong_tin": {...},
         "bang_hoc_ky": DataFrame, "bang_mon": DataFrame}

    Chưa từng cập nhật thì None.
    """
    with engine().connect() as cn:
        lcn_id = cn.execute(text("""
            SELECT TOP 1 id FROM dbo.lan_cap_nhat WHERE user_id = :uid
            ORDER BY thoi_diem DESC, id DESC
        """), {"uid": user_id}).scalar_one_or_none()
        if lcn_id is None:
            return None
        lcn, hk, mon = _doc_lan_cap_nhat(cn, lcn_id)
    return {"id": lcn["id"], "thoi_diem": lcn["thoi_diem"], "nguon": lcn["nguon"],
            "thong_tin": {k: lcn[k] for k in ("nam_nhap_hoc", "nganh", "he_dao_tao")},
            "bang_hoc_ky": hk, "bang_mon": mon}


def nguoi_chua_cap_nhat_tu(moc: datetime) -> list[int]:
    """user_id có nhan_email = 1 và KHÔNG có lần cập nhật nào từ `moc` trở đi
    (tác vụ 2: nhắc theo mốc). Gồm cả người chưa cập nhật lần nào."""
    with engine().connect() as cn:
        return list(cn.execute(text("""
            SELECT u.id FROM dbo.nguoi_dung u
            WHERE u.nhan_email = 1
              AND NOT EXISTS (SELECT 1 FROM dbo.lan_cap_nhat l
                              WHERE l.user_id = u.id AND l.thoi_diem >= :moc)
            ORDER BY u.id
        """), {"moc": moc}).scalars())


def lan_cap_nhat_moi_nhat_moi_nguoi() -> list[tuple[int, int]]:
    """[(user_id, lan_cap_nhat_id mới nhất)] của mọi người đã từng cập nhật
    (tác vụ 3: dự đoán lại khi có mô hình mới)."""
    with engine().connect() as cn:
        return [tuple(r) for r in cn.execute(text("""
            SELECT user_id, id FROM (
                SELECT user_id, id,
                       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY thoi_diem DESC, id DESC) AS rn
                FROM dbo.lan_cap_nhat) x
            WHERE rn = 1 ORDER BY user_id
        """))]


# --- Dự đoán ---------------------------------------------------------------
def luu_du_doan(lan_cap_nhat_id: int, ket_qua: list[dict]) -> list[int]:
    """Lưu các kết quả của một lần dự đoán, trả về id theo đúng thứ tự.

    Mỗi dict: {"muc_tieu": "canh_bao" | "thoi_hoc" | "truot_mon",
               "stt_mon": int | None (bắt buộc với truot_mon — tra ra mon_dang_hoc_id),
               "cho_thu_tu", "cho_ten", "diem_nguy_co" (None khi chưa dự đoán),
               "nguong", "bao_dong", "muc_nguy_co" (một trong MUC_NGUY_CO),
               "ly_do": list[str], "goi_y": list[str], "ghi_chu",
               "phuong_phap", "phien_ban_mo_hinh"}
    Ghi một giao dịch; mọi dòng chung một thoi_diem (một lượt).
    """
    for kq in ket_qua:
        if kq["muc_nguy_co"] not in MUC_NGUY_CO:
            raise ValueError(f"muc_nguy_co phải là một trong {MUC_NGUY_CO}, nhận {kq['muc_nguy_co']!r}")
    ids = []
    with engine().begin() as cn:
        thoi_diem = cn.execute(text("SELECT CAST(SYSDATETIME() AS DATETIME2(0))")).scalar_one()
        mon_id = dict(cn.execute(text(
            "SELECT stt, id FROM dbo.mon_dang_hoc WHERE lan_cap_nhat_id = :id"), {"id": lan_cap_nhat_id}).all())
        for kq in ket_qua:
            stt = _gia_tri(kq.get("stt_mon"))
            if kq["muc_tieu"] == "truot_mon" and stt not in mon_id:
                raise ValueError(f"lần cập nhật {lan_cap_nhat_id} không có môn stt={stt}")
            ids.append(cn.execute(text("""
                INSERT INTO dbo.du_doan
                    (lan_cap_nhat_id, muc_tieu, mon_dang_hoc_id, cho_thu_tu, cho_ten, diem_nguy_co,
                     nguong, bao_dong, muc_nguy_co, ly_do_json, goi_y_json, ghi_chu, phuong_phap,
                     phien_ban_mo_hinh, thoi_diem)
                OUTPUT INSERTED.id
                VALUES (:lcn, :muc_tieu, :mon, :cho_thu_tu, :cho_ten, :diem, :nguong, :bao_dong,
                        :muc, :ly_do, :goi_y, :ghi_chu, :pp, :pb, :td)
            """), {
                "lcn": lan_cap_nhat_id, "muc_tieu": kq["muc_tieu"],
                "mon": mon_id.get(stt) if kq["muc_tieu"] == "truot_mon" else None,
                "cho_thu_tu": int(kq["cho_thu_tu"]), "cho_ten": _gia_tri(kq.get("cho_ten")),
                "diem": _gia_tri(kq.get("diem_nguy_co")), "nguong": float(kq["nguong"]),
                "bao_dong": int(bool(kq["bao_dong"])), "muc": kq["muc_nguy_co"],
                "ly_do": json.dumps(list(kq.get("ly_do") or []), ensure_ascii=False),
                "goi_y": json.dumps(list(kq.get("goi_y") or []), ensure_ascii=False),
                "ghi_chu": _gia_tri(kq.get("ghi_chu")) or None,
                "pp": kq["phuong_phap"], "pb": kq["phien_ban_mo_hinh"], "td": thoi_diem,
            }).scalar_one())
    return ids


_CHON_DU_DOAN = """
    SELECT d.id, d.lan_cap_nhat_id, d.muc_tieu, m.stt AS stt_mon, m.ten_mon, m.so_tc,
           d.cho_thu_tu, d.cho_ten, d.diem_nguy_co, d.nguong, d.bao_dong, d.muc_nguy_co,
           d.ly_do_json, d.goi_y_json, d.ghi_chu, d.phuong_phap, d.phien_ban_mo_hinh, d.thoi_diem
    FROM dbo.du_doan d
    JOIN dbo.lan_cap_nhat l ON l.id = d.lan_cap_nhat_id
    LEFT JOIN dbo.mon_dang_hoc m ON m.id = d.mon_dang_hoc_id
"""


def _dong_du_doan(r) -> dict:
    d = dict(r)
    d["ly_do"], d["goi_y"] = _json(d.pop("ly_do_json")), _json(d.pop("goi_y_json"))
    d["bao_dong"] = bool(d["bao_dong"])
    for c in ("diem_nguy_co", "nguong", "so_tc"):
        d[c] = _so(d[c])
    return d


def ket_qua_moi_nhat(user_id: int) -> dict | None:
    """Lần dự đoán gần nhất (GET /ket-qua/moi-nhat):

        {"lan_cap_nhat_id", "thoi_diem",
         "canh_bao": {cột như luu_du_doan, có "id"},
         "thoi_hoc": {...},
         "truot_mon": [{..., "ten_mon", "so_tc"}, ...]}

    Chưa từng dự đoán thì None.
    """
    with engine().connect() as cn:
        moi_nhat = cn.execute(text(_CHON_DU_DOAN + """
            WHERE l.user_id = :uid ORDER BY d.thoi_diem DESC, d.id DESC
            OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY
        """), {"uid": user_id}).mappings().one_or_none()
        if moi_nhat is None:
            return None
        cac_dong = cn.execute(text(_CHON_DU_DOAN + """
            WHERE d.lan_cap_nhat_id = :lcn AND d.thoi_diem = :td ORDER BY d.id
        """), {"lcn": moi_nhat["lan_cap_nhat_id"], "td": moi_nhat["thoi_diem"]}).mappings().all()

    ket_qua = {"lan_cap_nhat_id": moi_nhat["lan_cap_nhat_id"], "thoi_diem": moi_nhat["thoi_diem"],
               "canh_bao": None, "thoi_hoc": None, "truot_mon": []}
    for r in cac_dong:
        d = _dong_du_doan(r)
        if d["muc_tieu"] == "truot_mon":
            ket_qua["truot_mon"].append(d)
        else:
            ket_qua[d["muc_tieu"]] = d
    ket_qua["truot_mon"].sort(key=lambda d: d["stt_mon"])
    return ket_qua


def lich_su_du_doan(user_id: int, muc_tieu: str = "canh_bao", gioi_han: int = 20) -> list[dict]:
    """Các lần dự đoán trước, mới nhất trước (GET /ket-qua/lich-su):
    [{"id", "thoi_diem", "cho_ten", "muc_nguy_co", "diem_nguy_co", "bao_dong"}]."""
    with engine().connect() as cn:
        cac_dong = cn.execute(text("""
            SELECT TOP (:n) d.id, d.thoi_diem, d.cho_ten, d.muc_nguy_co, d.diem_nguy_co, d.bao_dong
            FROM dbo.du_doan d JOIN dbo.lan_cap_nhat l ON l.id = d.lan_cap_nhat_id
            WHERE l.user_id = :uid AND d.muc_tieu = :mt
            ORDER BY d.thoi_diem DESC, d.id DESC
        """), {"n": int(gioi_han), "uid": user_id, "mt": muc_tieu}).mappings().all()
    return [{**r, "diem_nguy_co": _so(r["diem_nguy_co"]), "bao_dong": bool(r["bao_dong"])}
            for r in cac_dong]


def muc_canh_bao_truoc(user_id: int, tru_lan_cap_nhat_id: int) -> str | None:
    """muc_nguy_co của dự đoán "canh_bao" ngay TRƯỚC lượt mới nhất của lần cập
    nhật đang xét (quy tắc gửi email §12.6: chỉ gửi khi lần này "cao" mà lần
    trước không). GỌI SAU luu_du_doan: lượt vừa lưu bị bỏ qua, nên dùng được cả
    khi dự đoán lại cùng một lần cập nhật (tác vụ 3). Chưa có lần trước thì None.
    """
    with engine().connect() as cn:
        return cn.execute(text("""
            WITH luot_moi AS (
                SELECT MAX(thoi_diem) AS td FROM dbo.du_doan
                WHERE lan_cap_nhat_id = :lcn AND muc_tieu = 'canh_bao')
            SELECT TOP 1 d.muc_nguy_co
            FROM dbo.du_doan d JOIN dbo.lan_cap_nhat l ON l.id = d.lan_cap_nhat_id
            CROSS JOIN luot_moi
            WHERE l.user_id = :uid AND d.muc_tieu = 'canh_bao'
              AND NOT (d.lan_cap_nhat_id = :lcn AND d.thoi_diem = luot_moi.td)
            ORDER BY d.thoi_diem DESC, d.id DESC
        """), {"lcn": tru_lan_cap_nhat_id, "uid": user_id}).scalar_one_or_none()


def phien_ban_mo_hinh_gan_nhat() -> str | None:
    """phien_ban_mo_hinh của dự đoán mới nhất trong toàn hệ thống (tác vụ 3 so
    với thời điểm train trong models/*.joblib). Chưa có dự đoán nào thì None."""
    with engine().connect() as cn:
        return cn.execute(text("""
            SELECT TOP 1 phien_ban_mo_hinh FROM dbo.du_doan ORDER BY thoi_diem DESC, id DESC
        """)).scalar_one_or_none()


# --- Email: hàng đợi và lịch sử cảnh báo ----------------------------------
def them_email(user_id: int, loai: str, tieu_de: str, noi_dung: str, *,
               moc: str | None = None, lan_nhac: int | None = None,
               du_doan_id: int | None = None, hen_gui: datetime | None = None) -> int | None:
    """Xếp một email vào hàng đợi (trạng thái "cho_gui"), trả về id.

    loai: một trong LOAI_EMAIL. Nhắc theo mốc truyền moc + lan_nhac; đã có
    (user_id, loai, moc, lan_nhac) rồi thì KHÔNG thêm, trả về None (chống trùng).
    "Nhắc tôi sau": loai="hen_nhac", hen_gui = ngày hẹn.
    Người dùng nhan_email = 0 vẫn thêm được; email_den_han() mới bỏ qua họ.
    """
    if loai not in LOAI_EMAIL:
        raise ValueError(f"loai phải là một trong {LOAI_EMAIL}, nhận {loai!r}")
    try:
        with engine().begin() as cn:
            return cn.execute(text("""
                INSERT INTO dbo.email_da_gui
                    (user_id, loai, moc, lan_nhac, du_doan_id, hen_gui, tieu_de, noi_dung)
                OUTPUT INSERTED.id
                VALUES (:uid, :loai, :moc, :lan, :dd, :hen, :tieu_de, :noi_dung)
            """), {"uid": user_id, "loai": loai, "moc": moc, "lan": lan_nhac, "dd": du_doan_id,
                   "hen": hen_gui, "tieu_de": tieu_de, "noi_dung": noi_dung}).scalar_one()
    except IntegrityError as loi:
        if "UX_edg_moc" in str(loi):
            return None
        raise


def email_den_han(gioi_han: int = 50) -> list[dict]:
    """Email "cho_gui" có hen_gui trống hoặc đã đến hạn, của người nhan_email = 1,
    cũ nhất trước (tác vụ 1):
    [{"id", "user_id", "den" (email người nhận), "tieu_de", "noi_dung", "so_lan_thu"}]."""
    with engine().connect() as cn:
        return [dict(r) for r in cn.execute(text("""
            SELECT TOP (:n) e.id, e.user_id, u.email AS den, e.tieu_de, e.noi_dung, e.so_lan_thu
            FROM dbo.email_da_gui e JOIN dbo.nguoi_dung u ON u.id = e.user_id
            WHERE e.trang_thai = 'cho_gui' AND u.nhan_email = 1
              AND (e.hen_gui IS NULL OR e.hen_gui <= SYSDATETIME())
            ORDER BY e.thoi_diem_tao, e.id
        """), {"n": int(gioi_han)}).mappings()]


def danh_dau_da_gui(email_id: int) -> None:
    """Trạng thái "da_gui", thoi_diem_gui = bây giờ."""
    with engine().begin() as cn:
        cn.execute(text("""
            UPDATE dbo.email_da_gui SET trang_thai = 'da_gui', thoi_diem_gui = SYSDATETIME()
            WHERE id = :id
        """), {"id": email_id})


def danh_dau_loi(email_id: int, noi_dung_loi: str) -> str:
    """Tăng so_lan_thu; quá SO_LAN_THU_TOI_DA thì chuyển "loi", chưa quá thì vẫn
    "cho_gui" để lượt sau thử lại. Trả về trạng thái mới."""
    with engine().begin() as cn:
        return cn.execute(text("""
            UPDATE dbo.email_da_gui
            SET so_lan_thu = so_lan_thu + 1,
                noi_dung_loi = LEFT(:loi, 500),
                trang_thai = CASE WHEN so_lan_thu + 1 >= :toi_da THEN 'loi' ELSE 'cho_gui' END
            OUTPUT INSERTED.trang_thai
            WHERE id = :id
        """), {"id": email_id, "loi": noi_dung_loi, "toi_da": SO_LAN_THU_TOI_DA}).scalar_one()


def lich_su_email(user_id: int, gioi_han: int = 50) -> list[dict]:
    """Email của một người, mới nhất trước (GET /email/lich-su):
    [{"id", "loai", "tieu_de", "trang_thai", "thoi_diem_tao", "thoi_diem_gui"}]."""
    with engine().connect() as cn:
        return [dict(r) for r in cn.execute(text("""
            SELECT TOP (:n) id, loai, tieu_de, trang_thai, thoi_diem_tao, thoi_diem_gui
            FROM dbo.email_da_gui WHERE user_id = :uid
            ORDER BY thoi_diem_tao DESC, id DESC
        """), {"n": int(gioi_han), "uid": user_id}).mappings()]
