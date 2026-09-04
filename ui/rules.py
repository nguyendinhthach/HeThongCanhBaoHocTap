"""Quy tắc quy đổi và tô màu, port nguyên từ phần script của mockup.

Tách riêng khỏi tokens (chỉ chứa hằng số) và data (chỉ chứa dữ liệu mẫu) để
khi gắn nghiệp vụ thật thì màn hình không phải sửa: chỉ nguồn dữ liệu đổi,
còn cách hiển thị vẫn đi qua các hàm ở đây.
"""

import math

from ui import tokens as t

# Thang chữ 5 bậc: điểm sàn thang 10 -> (chữ, điểm thang 4).
# Điểm luôn được nhập ở thang 10; thang 4 chỉ là lớp quy đổi khi hiển thị.
_THANG_4 = [
    (8.5, "A", 4.0),
    (7.0, "B", 3.0),
    (5.5, "C", 2.0),
    (4.0, "D", 1.0),
]
_DIEM_LIET = ("E", 0.0)   # dưới 4.0 là trượt, phải học lại


def _lam_tron(x: float, so_le: int = 1) -> float:
    """Làm tròn nửa lên như Math.round của mockup.

    round() của Python làm tròn về số chẵn (2.5 -> 2), lệch với mockup ở
    những điểm rơi đúng .5 nên phải tự tính.
    """
    he = 10 ** so_le
    return math.floor(x * he + 0.5) / he


def mk_rows(diem_muc_tieu: float) -> list[dict]:
    """Dựng ba dòng điểm thành phần sao cho điểm tổng kết ra đúng mục tiêu.

    Chỉ dùng để tạo dữ liệu mẫu — port từ hàm mkRows của mockup.
    """
    g = diem_muc_tieu
    return [
        {"loai": "Chuyên cần", "trong_so": 10,
         "diem": min(10.0, _lam_tron(g + 1))},
        {"loai": "Kiểm tra giữa kỳ", "trong_so": 30, "diem": _lam_tron(g - 0.5)},
        {"loai": "Thi cuối kỳ", "trong_so": 60, "diem": _lam_tron(g + 0.08)},
    ]


def to4(diem10: float) -> float:
    """Quy đổi một điểm thang 10 sang thang 4."""
    for nguong, _, quy_doi in _THANG_4:
        if diem10 >= nguong:
            return quy_doi
    return _DIEM_LIET[1]


def chu_cai(diem10: float) -> str:
    """Điểm chữ tương ứng: A, B, C, D hoặc E."""
    for nguong, chu, _ in _THANG_4:
        if diem10 >= nguong:
            return chu
    return _DIEM_LIET[0]


def theo_thang(diem10: float, scale: int) -> float:
    return to4(diem10) if scale == 4 else diem10


def grade_color(diem10: float | None, du_trong_so: bool) -> str:
    """Màu điểm tổng kết.

    Chưa đủ 100% trọng số thì luôn xám — mockup cố ý không tô xanh/đỏ cho
    điểm tạm tính để tránh hiểu nhầm là kết quả cuối.
    """
    if diem10 is None or not du_trong_so:
        return t.MUTED
    if diem10 < t.GRADE_FAIL:
        return t.DANGER
    if diem10 < t.GRADE_WARN:
        return t.WARNING_DEEP
    return t.SUCCESS


def grade_text(diem10: float | None, du_trong_so: bool, scale: int) -> str:
    """Chuỗi điểm hiển thị trong bảng, kèm chú thích khi còn tạm tính.

    Ở DH4 kèm luôn điểm chữ vì thang này vốn gắn với chữ; DH10 thì không,
    con số đã tự nói lên.
    """
    if diem10 is None:
        return "— (chưa có điểm)"
    so = f"{theo_thang(diem10, scale):.1f}"
    if scale == 4:
        so += f" ({chu_cai(diem10)})"
    return so if du_trong_so else f"{so} (tạm tính, chưa đủ điểm)"


def grade_info(rows) -> dict:
    """Điểm tổng kết từ danh sách điểm thành phần.

    Chỉ lấy trung bình trên phần trọng số ĐÃ có điểm, nên môn nhập dở vẫn ra
    được điểm tạm tính. `du_trong_so` cho biết đã đủ 100% hay chưa.
    """
    tong_ts = sum(r["trong_so"] or 0 for r in rows)
    da_nhap = [r for r in rows if r.get("diem") is not None]
    ts_da_nhap = sum(r["trong_so"] or 0 for r in da_nhap)
    diem = (sum(r["trong_so"] * r["diem"] for r in da_nhap) / ts_da_nhap
            if ts_da_nhap else None)
    return {
        "diem": round(diem, 2) if diem is not None else None,
        "tong_ts": tong_ts,
        "ts_da_nhap": ts_da_nhap,
        "thieu": [r for r in rows if r.get("diem") is None],
        "du_trong_so": ts_da_nhap >= 100,
    }


def weight_status(tong: int) -> dict:
    """Ba trạng thái của hộp tổng trọng số: đủ / vượt / thiếu."""
    if tong == 100:
        return {"bg": "#f2fbf4", "border": "#c6e8cf", "dot": t.SUCCESS,
                "icon": "✓", "color": t.SUCCESS,
                "text": "Tổng trọng số đã đủ 100%. Có thể lưu môn học."}
    if tong > 100:
        return {"bg": "#fdf1f1", "border": "#f3c9c9", "dot": t.DANGER,
                "icon": "!", "color": t.DANGER,
                "text": f"Tổng trọng số là {tong}%, vượt quá 100%. Hãy giảm "
                        "bớt trọng số ở một số dòng."}
    return {"bg": "#fffaef", "border": "#f0dfae", "dot": t.WARNING,
            "icon": "!", "color": t.DANGER,
            "text": f"Tổng trọng số hiện là {tong}%, còn thiếu "
                    f"{100 - tong}% mới đủ 100%. Điểm tổng kết sẽ chỉ là "
                    "tạm tính."}


def provisional_text(info: dict) -> tuple[str, str]:
    """Dòng điểm tạm tính ở hàng nút Lưu — trả về (chuỗi, màu)."""
    if info["diem"] is None:
        return ("Điểm tạm tính: — (chưa nhập điểm thành phần nào)",
                t.WARNING_TEXT)
    if info["du_trong_so"]:
        return (f'Điểm tổng kết: {info["diem"]:.2f} (đã đủ 100% trọng số)',
                t.TEXT)
    thieu = ", ".join(f'{r["loai"]} {r["trong_so"]}%' for r in info["thieu"])
    con = info["tong_ts"] - info["ts_da_nhap"]
    return (f'Điểm tạm tính (dựa trên {info["ts_da_nhap"]}% trọng số đã có '
            f'điểm): {info["diem"]:.2f} — còn {con}% ({thieu}) chưa nhập',
            t.WARNING_TEXT)


def goal_color(pct: int) -> str:
    """Màu khả năng đạt mục tiêu — theo % chứ không gán cứng cho từng mục."""
    if pct >= 70:
        return t.SUCCESS
    if pct >= 40:
        return t.WARNING
    return t.DANGER


def risk_label(pct: int) -> str:
    if pct >= 60:
        return "Cao"
    return "Trung bình" if pct >= 35 else "Thấp"


def validate_year(tu: str, den: str, da_co: list[str]) -> dict:
    """Kiểm tra năm học mới trước khi cho lưu.

    Chỉ xét năm: học kỳ không còn là thứ người dùng tạo ra mà suy từ số học
    kỳ mỗi năm trong hồ sơ, nên mọi năm đều có sẵn đủ kỳ.
    """
    nhan = f"{tu}–{den}" if tu and den else ""
    if not (tu.isdigit() and den.isdigit()
            and len(tu) == 4 and len(den) == 4):
        return {"ok": False, "loi": "", "nhan": nhan}
    if int(den) != int(tu) + 1:
        return {"ok": False, "nhan": nhan,
                "loi": "Năm kết thúc phải bằng năm bắt đầu + 1."}
    if nhan in da_co:
        return {"ok": False, "nhan": nhan,
                "loi": f"Năm học {nhan} đã tồn tại."}
    return {"ok": True, "loi": "", "nhan": nhan}


# --- Tổng hợp theo học kỳ --------------------------------------------------
def diem_mon(mon: dict) -> float | None:
    """Điểm tổng kết chính thức của một môn — làm tròn 1 chữ số như học bạ.

    GPA tính từ con số đã làm tròn này chứ không từ giá trị thô, đúng cách
    trường ghi điểm và cũng là cách mockup làm.
    """
    g = grade_info(mon["rows"])["diem"]
    return None if g is None else _lam_tron(g)


def du_trong_so(mon: dict) -> bool:
    return grade_info(mon["rows"])["du_trong_so"]


def lan_hoc(mon: dict) -> str:
    """Nhãn lần học: từ lần 2 trở đi mới ghi rõ số lần."""
    so = mon.get("attempt_no", 1)
    return f'Lần {so} · {mon["attempt"]}' if so > 1 else mon["attempt"]


def loc_ky(courses: list[dict], nam: str, ky: str) -> list[dict]:
    return [c for c in courses if c["year"] == nam and c["sem"] == ky]


def tom_tat(courses: list[dict]) -> dict:
    """GPA, tín chỉ, số môn trượt / còn tạm tính của một nhóm môn.

    GPA thang 4 phải quy đổi TỪNG MÔN rồi mới lấy trung bình, không được quy
    đổi điểm trung bình thang 10 — hai cách cho kết quả khác nhau vì to4 là
    hàm bậc thang, không tuyến tính.
    """
    tin_chi = sum(c["credits"] for c in courses)
    co_diem = [(diem_mon(c), c["credits"]) for c in courses
               if diem_mon(c) is not None]
    tc_co_diem = sum(tc for _, tc in co_diem)
    gpa10 = (sum(d * tc for d, tc in co_diem) / tc_co_diem
             if tc_co_diem else 0.0)
    gpa4 = (sum(to4(d) * tc for d, tc in co_diem) / tc_co_diem
            if tc_co_diem else 0.0)
    return {
        "tin_chi": tin_chi,
        "gpa10": gpa10,
        "gpa4": gpa4,
        # Môn chưa đủ trọng số thì chưa kết luận được đỗ hay trượt.
        "truot": sum(1 for c in courses if du_trong_so(c)
                     and (diem_mon(c) or 0) < t.GRADE_FAIL),
        "tam_tinh": sum(1 for c in courses if not du_trong_so(c)),
    }


def gpa_thang(tk: dict, scale: int) -> float:
    """Lấy GPA đúng thang từ kết quả tom_tat."""
    return tk["gpa4"] if scale == 4 else tk["gpa10"]


def chuoi_gpa(courses: list[dict], scale: int, nam: str, ky: str) -> list[dict]:
    """Chuỗi GPA cho biểu đồ: mỗi kỳ đã có môn là một điểm, sắp theo thời gian.

    Kỳ đang chọn ở sidebar được đánh dấu để tô sáng.
    """
    cac_ky = sorted({(c["year"], c["sem"]) for c in courses})
    out = []
    for y, s in cac_ky:
        tk = tom_tat(loc_ky(courses, y, s))
        so_ky = "".join(ch for ch in s if ch.isdigit()) or "?"
        out.append({
            "ky": f"{y[2:4]}–{y[-2:]} HK{so_ky}",
            "gpa": round(gpa_thang(tk, scale), 2),
            "dang_xem": y == nam and s == ky,
        })
    return out


def so_sanh_ky_truoc(courses: list[dict], nam: str, ky: str,
                     scale: int) -> tuple[str, str]:
    """So GPA kỳ đang xem với kỳ liền trước đã có dữ liệu.

    Trả về (chuỗi, màu). Mockup ghi cứng "↓ 0,42"; ở đây GPA đã tính thật nên
    con số này cũng phải tính, không thì hiện sai ở mọi kỳ khác.
    """
    cac_ky = sorted({(c["year"], c["sem"]) for c in courses})
    if (nam, ky) not in cac_ky:
        return "Chưa có dữ liệu", t.MUTED
    i = cac_ky.index((nam, ky))
    if i == 0:
        return "Kỳ đầu tiên có dữ liệu", t.MUTED
    gio = gpa_thang(tom_tat(loc_ky(courses, nam, ky)), scale)
    truoc = gpa_thang(tom_tat(loc_ky(courses, *cac_ky[i - 1])), scale)
    lech = round(gio - truoc, 2)
    if abs(lech) < 0.005:
        return "Không đổi so với học kỳ trước", t.MUTED
    mui = "↑" if lech > 0 else "↓"
    mau = t.SUCCESS if lech > 0 else t.DANGER
    return f'{mui} {abs(lech):.2f} so với học kỳ trước'.replace(".", ","), mau
