"""Đọc và ghi dữ liệu — toàn bộ câu lệnh SQL của ứng dụng nằm ở đây.

Các hàm trả về đúng cấu trúc dict mà ui/rules.py và các màn hình đang dùng
(`year`, `sem`, `code`, `rows`...), nên khi chuyển từ dữ liệu tĩnh sang cơ sở
dữ liệu thì phần hiển thị không phải sửa.

Quy ước chuyển đổi giữa hai bên:

    cơ sở dữ liệu          giao diện
    nam_bat_dau = 2025  →  year    = "2025–2026"
    hoc_ky      = 1     →  sem     = "Học kỳ 1"
    loai_lan_hoc= hoc_lai→ attempt = "Học lại"

Cơ sở dữ liệu lưu mã (`hoc_lai`) chứ không lưu nhãn tiếng Việt, để đổi cách
viết trên giao diện không phải cập nhật lại dữ liệu cũ.
"""

import json
from decimal import Decimal

from sqlalchemy import text

from db.ket_noi import engine

# --- Bảng quy đổi mã <-> nhãn ---------------------------------------------
LAN_HOC = {"hoc_moi": "Học lần 1", "hoc_lai": "Học lại",
           "hoc_cai_thien": "Học cải thiện"}
MA_LAN_HOC = {v: k for k, v in LAN_HOC.items()}

MUC_NGUY_CO = {"thap": "Thấp", "trung_binh": "Trung bình", "cao": "Cao"}

MUC_TIEU = {"gioi": "Đạt loại Giỏi", "kha": "Đạt loại Khá",
            "qua_mon": "Qua môn (không nợ)"}
MA_MUC_TIEU = {v: k for k, v in MUC_TIEU.items()}


# --- Chuyển đổi định dạng --------------------------------------------------
def nhan_nam(nam_bat_dau: int) -> str:
    """2025 -> "2025–2026". Dấu ngăn là en dash, đúng như trên giao diện."""
    return f"{nam_bat_dau}–{nam_bat_dau + 1}"


def so_nam(nhan: str) -> int:
    """"2025–2026" -> 2025. Nhận cả en dash lẫn dấu trừ thường."""
    return int(nhan.replace("–", "-").split("-")[0].strip())


def nhan_ky(hoc_ky: int) -> str:
    return f"Học kỳ {hoc_ky}"


def so_ky(nhan: str) -> int:
    return int("".join(c for c in nhan if c.isdigit()) or 1)


def _so(x):
    """Decimal của SQL Server -> int hoặc float cho phía Python.

    Trọng số 10.00 phải thành 10 chứ không phải 10.0, vì giao diện in thẳng
    con số này ra kèm dấu %.
    """
    if x is None:
        return None
    if isinstance(x, Decimal):
        return int(x) if x == x.to_integral_value() else float(x)
    return x


# --- Danh mục loại điểm thành phần ----------------------------------------
_cache_loai: list[dict] | None = None


def loai_thanh_phan(lam_moi: bool = False) -> list[dict]:
    """Bảy loại điểm thành phần, theo thứ tự hiển thị trong menu chọn.

    Đây là dữ liệu danh mục, gần như không đổi, nên đọc một lần rồi giữ lại.
    """
    global _cache_loai
    if _cache_loai is None or lam_moi:
        with engine().connect() as cn:
            _cache_loai = [
                {"id": r.id, "ma": r.ma, "ten": r.ten}
                for r in cn.execute(text(
                    "SELECT id, ma, ten FROM dbo.loai_thanh_phan "
                    "ORDER BY thu_tu"))]
    return _cache_loai


def ten_loai() -> list[str]:
    """Danh sách nhãn để đổ vào ô chọn loại thành phần."""
    return [l["ten"] for l in loai_thanh_phan()]


def _id_theo_ten_loai() -> dict[str, int]:
    return {l["ten"]: l["id"] for l in loai_thanh_phan()}


# --- Hồ sơ người dùng ------------------------------------------------------
_CHON_HO_SO = """
    SELECT id, email, ho_ten, nien_khoa_tu, nien_khoa_den,
           so_ky_moi_nam, thang_diem, muc_tieu
    FROM   dbo.nguoi_dung
"""


def _dong_ho_so(r) -> dict:
    return {
        "id": r.id,
        "email": r.email,
        "ho_ten": r.ho_ten,
        "khoa_from": str(r.nien_khoa_tu),
        "khoa_to": str(r.nien_khoa_den),
        "so_ky": r.so_ky_moi_nam,
        "scale": r.thang_diem,
        "goal": MUC_TIEU.get(r.muc_tieu),
        # Năm học không lưu thành bảng: suy thẳng từ niên khoá, các năm luôn
        # liên tiếp nhau nên không cần lưu lại danh sách.
        "year_list": [nhan_nam(n)
                      for n in range(r.nien_khoa_tu, r.nien_khoa_den)],
    }


def ho_so(user_id: int) -> dict | None:
    with engine().connect() as cn:
        r = cn.execute(text(_CHON_HO_SO + " WHERE id = :id"),
                       {"id": user_id}).one_or_none()
    return _dong_ho_so(r) if r else None


def ho_so_theo_email(email: str) -> dict | None:
    with engine().connect() as cn:
        r = cn.execute(text(_CHON_HO_SO + " WHERE email = :em"),
                       {"em": email.strip()}).one_or_none()
    return _dong_ho_so(r) if r else None


def email_da_dung(email: str) -> bool:
    with engine().connect() as cn:
        return cn.execute(
            text("SELECT 1 FROM dbo.nguoi_dung WHERE email = :em"),
            {"em": email.strip()}).first() is not None


def tao_tai_khoan(email: str, mat_khau_bam: str, ho_ten: str,
                  khoa_from: int, khoa_to: int, so_ky_moi_nam: int) -> int:
    """Thêm tài khoản mới, trả về id vừa sinh."""
    with engine().begin() as cn:
        return cn.execute(text("""
            INSERT INTO dbo.nguoi_dung
                (email, mat_khau_hash, ho_ten, nien_khoa_tu, nien_khoa_den,
                 so_ky_moi_nam)
            OUTPUT INSERTED.id
            VALUES (:em, :mk, :ten, :tu, :den, :so_ky)
        """), {"em": email.strip(), "mk": mat_khau_bam, "ten": ho_ten.strip(),
               "tu": khoa_from, "den": khoa_to,
               "so_ky": so_ky_moi_nam}).scalar_one()


def lay_hash_mat_khau(email: str) -> str | None:
    with engine().connect() as cn:
        return cn.execute(
            text("SELECT mat_khau_hash FROM dbo.nguoi_dung WHERE email = :em"),
            {"em": email.strip()}).scalar_one_or_none()


def dat_thang_diem(user_id: int, thang: int) -> None:
    with engine().begin() as cn:
        cn.execute(text("UPDATE dbo.nguoi_dung SET thang_diem = :t "
                        "WHERE id = :id"), {"t": thang, "id": user_id})


def dat_muc_tieu(user_id: int, nhan_muc_tieu: str) -> None:
    with engine().begin() as cn:
        cn.execute(text("UPDATE dbo.nguoi_dung SET muc_tieu = :m "
                        "WHERE id = :id"),
                   {"m": MA_MUC_TIEU.get(nhan_muc_tieu), "id": user_id})


def them_nam_hoc(user_id: int) -> None:
    """Nới niên khoá thêm một năm.

    Giao diện cho thêm năm học mới khi sinh viên học kéo dài hơn dự kiến. Vì
    các năm luôn liên tiếp, thêm một năm chỉ là tăng năm kết thúc lên 1.
    """
    with engine().begin() as cn:
        cn.execute(text("UPDATE dbo.nguoi_dung "
                        "SET nien_khoa_den = nien_khoa_den + 1 "
                        "WHERE id = :id"), {"id": user_id})


# --- Môn học ---------------------------------------------------------------
_CHON_MON = """
    SELECT m.id, m.nam_bat_dau, m.hoc_ky, m.ma_mon, m.ten_mon,
           m.so_tin_chi, m.lan_hoc, m.loai_lan_hoc,
           l.ten  AS loai_tp, d.trong_so_phan_tram, d.diem,
           l.thu_tu, d.id AS dtp_id
    FROM        dbo.mon_hoc          m
    LEFT JOIN   dbo.diem_thanh_phan  d ON d.mon_hoc_id = m.id
    LEFT JOIN   dbo.loai_thanh_phan  l ON l.id = d.loai_thanh_phan_id
    WHERE       m.user_id = :uid
"""

_XEP_MON = " ORDER BY m.nam_bat_dau, m.hoc_ky, m.id, l.thu_tu, d.id"


def _gom_mon(rows) -> list[dict]:
    """Gộp kết quả phẳng của phép JOIN thành danh sách môn, mỗi môn kèm rows.

    Một môn trải ra nhiều dòng vì nối với bảng điểm thành phần, nên phải gom
    lại theo id. Thứ tự đã do câu SQL quyết định, ở đây chỉ giữ nguyên.
    """
    theo_id: dict[int, dict] = {}
    for r in rows:
        mon = theo_id.get(r.id)
        if mon is None:
            mon = theo_id[r.id] = {
                "id": r.id,
                "year": nhan_nam(r.nam_bat_dau),
                "sem": nhan_ky(r.hoc_ky),
                "code": r.ma_mon,
                "name": r.ten_mon,
                "credits": r.so_tin_chi,
                "attempt": LAN_HOC.get(r.loai_lan_hoc, r.loai_lan_hoc),
                "attempt_no": r.lan_hoc,
                "rows": [],
            }
        # LEFT JOIN: môn chưa có dòng điểm nào thì loai_tp là NULL
        if r.loai_tp is not None:
            mon["rows"].append({
                "loai": r.loai_tp,
                "trong_so": _so(r.trong_so_phan_tram),
                "diem": _so(r.diem),
            })
    return list(theo_id.values())


def tat_ca_mon(user_id: int) -> list[dict]:
    """Toàn bộ môn của một sinh viên, mọi học kỳ.

    Biểu đồ xu hướng và trang Cảnh báo cần toàn bộ lịch sử (SPEC §6), còn
    Dashboard tự lọc ra kỳ đang xem bằng rules.loc_ky.
    """
    with engine().connect() as cn:
        return _gom_mon(cn.execute(text(_CHON_MON + _XEP_MON),
                                   {"uid": user_id}))


def mon_theo_ky(user_id: int, year: str, sem: str) -> list[dict]:
    with engine().connect() as cn:
        return _gom_mon(cn.execute(
            text(_CHON_MON + " AND m.nam_bat_dau = :nam AND m.hoc_ky = :ky"
                 + _XEP_MON),
            {"uid": user_id, "nam": so_nam(year), "ky": so_ky(sem)}))


def mot_mon(user_id: int, mon_id: int) -> dict | None:
    with engine().connect() as cn:
        ds = _gom_mon(cn.execute(text(_CHON_MON + " AND m.id = :mid" + _XEP_MON),
                                 {"uid": user_id, "mid": mon_id}))
    return ds[0] if ds else None


def _ghi_thanh_phan(cn, mon_id: int, rows: list[dict]) -> None:
    """Ghi lại toàn bộ dòng điểm thành phần của một môn.

    Xoá hết rồi chèn lại thay vì so từng dòng: form cho phép thêm, bớt, đổi
    loại tuỳ ý nên đối chiếu từng dòng vừa phức tạp vừa dễ sót.
    """
    cn.execute(text("DELETE FROM dbo.diem_thanh_phan WHERE mon_hoc_id = :mid"),
               {"mid": mon_id})
    id_loai = _id_theo_ten_loai()
    for r in rows:
        if not r.get("loai"):
            continue
        cn.execute(text("""
            INSERT INTO dbo.diem_thanh_phan
                (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem)
            VALUES (:mid, :loai, :ts, :diem)
        """), {"mid": mon_id, "loai": id_loai[r["loai"]],
               "ts": r["trong_so"], "diem": r.get("diem")})


def luu_mon(user_id: int, year: str, sem: str, code: str, name: str,
            credits: int, attempt: str, attempt_no: int,
            rows: list[dict]) -> int:
    """Thêm một lần học mới. Trả về id của môn vừa tạo."""
    with engine().begin() as cn:
        mon_id = cn.execute(text("""
            INSERT INTO dbo.mon_hoc
                (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon,
                 so_tin_chi, lan_hoc, loai_lan_hoc)
            OUTPUT INSERTED.id
            VALUES (:uid, :nam, :ky, :ma, :ten, :tc, :lan, :loai)
        """), {"uid": user_id, "nam": so_nam(year), "ky": so_ky(sem),
               "ma": code.strip(), "ten": name.strip(), "tc": credits,
               "lan": attempt_no,
               "loai": MA_LAN_HOC.get(attempt, "hoc_moi")}).scalar_one()
        _ghi_thanh_phan(cn, mon_id, rows)
    return mon_id


def cap_nhat_mon(user_id: int, mon_id: int, code: str, name: str,
                 credits: int, attempt: str, attempt_no: int,
                 rows: list[dict]) -> None:
    """Sửa một lần học đã có. Không đổi năm–kỳ: muốn chuyển kỳ thì xoá rồi
    thêm lại, đúng tinh thần mỗi bản ghi gắn chặt với học kỳ diễn ra."""
    with engine().begin() as cn:
        cn.execute(text("""
            UPDATE dbo.mon_hoc
            SET    ma_mon = :ma, ten_mon = :ten, so_tin_chi = :tc,
                   lan_hoc = :lan, loai_lan_hoc = :loai,
                   ngay_cap_nhat = SYSDATETIME()
            WHERE  id = :mid AND user_id = :uid
        """), {"mid": mon_id, "uid": user_id, "ma": code.strip(),
               "ten": name.strip(), "tc": credits, "lan": attempt_no,
               "loai": MA_LAN_HOC.get(attempt, "hoc_moi")})
        _ghi_thanh_phan(cn, mon_id, rows)


def xoa_mon(user_id: int, mon_id: int) -> None:
    """Xoá một lần học. Điểm thành phần tự xoá theo nhờ ON DELETE CASCADE."""
    with engine().begin() as cn:
        cn.execute(text("DELETE FROM dbo.mon_hoc "
                        "WHERE id = :mid AND user_id = :uid"),
                   {"mid": mon_id, "uid": user_id})


def lan_hoc_truoc(user_id: int, code: str, tru_mon_id: int | None = None):
    """Các lần đã học môn này trước đó, mới nhất trước.

    Dùng cho quy tắc lần học ở SPEC §3.3: đếm để ra số lần, và xem điểm lần
    gần nhất để gợi ý Học lại hay Học cải thiện. So trùng theo MÃ MÔN, không
    theo tên — tên gõ tay không đáng tin.

    `tru_mon_id` để lúc đang sửa một môn thì không tính chính nó là lần trước.
    """
    dieu_kien = ""
    tham_so = {"uid": user_id, "ma": code.strip()}
    if tru_mon_id is not None:
        dieu_kien = " AND m.id <> :bo"
        tham_so["bo"] = tru_mon_id
    with engine().connect() as cn:
        return _gom_mon(cn.execute(
            text(_CHON_MON + " AND m.ma_mon = :ma" + dieu_kien + _XEP_MON),
            tham_so))


# --- Dự đoán và cảnh báo ---------------------------------------------------
def du_doan_moi_nhat(user_id: int) -> dict | None:
    """Bản dự đoán gần nhất, kèm khả năng đạt cả ba mục tiêu.

    Trả về None khi chưa từng chạy mô hình — giai đoạn hiện tại luôn là None,
    giao diện phải chịu được trường hợp đó.
    """
    with engine().connect() as cn:
        r = cn.execute(text("""
            SELECT TOP 1 id, thoi_diem, muc_nguy_co, ty_le_phan_tram,
                         ly_do_json, goi_y_json
            FROM   dbo.du_doan_canh_bao
            WHERE  user_id = :uid
            ORDER BY thoi_diem DESC, id DESC
        """), {"uid": user_id}).one_or_none()
        if r is None:
            return None

        muc_tieu = {
            MUC_TIEU.get(m.ma_muc_tieu, m.ma_muc_tieu): {
                "pct": _so(m.ty_le), "note": m.ghi_chu}
            for m in cn.execute(text(
                "SELECT ma_muc_tieu, ty_le, ghi_chu "
                "FROM dbo.du_doan_muc_tieu WHERE du_doan_id = :did"),
                {"did": r.id})}

    return {
        "id": r.id,
        "thoi_diem": r.thoi_diem,
        "muc_nguy_co": MUC_NGUY_CO.get(r.muc_nguy_co, r.muc_nguy_co),
        "ty_le": _so(r.ty_le_phan_tram),
        "ly_do": json.loads(r.ly_do_json) if r.ly_do_json else [],
        "goi_y": json.loads(r.goi_y_json) if r.goi_y_json else [],
        "muc_tieu": muc_tieu,
    }
