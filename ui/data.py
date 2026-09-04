"""Dữ liệu mẫu và cấu hình hiển thị.

Môn học là mô hình thật, không phải ảnh chụp kết quả: mỗi môn gắn năm–kỳ và
giữ nguyên danh sách điểm thành phần, còn điểm tổng kết do ui/rules.py tính.
Nhờ vậy đổi kỳ, sửa, xoá đều chạy được mà không phải sửa chỗ hiển thị.

Danh sách môn sống trong st.session_state (xem seed_courses) chứ không để ở
cấp module: mọi phiên trình duyệt phải có bản riêng, nếu không hai tab sẽ
giẫm lên nhau.

Các con số ở phần "Cảnh báo & Mục tiêu" vẫn là giá trị cố định — phần đó chờ
mô hình dự đoán.
"""

from ui import rules
from ui import tokens as t

YEARS = ["2023–2024", "2024–2025", "2025–2026", "2026–2027"]
SEMESTERS = ["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"]


def semesters(so_ky: int) -> list[str]:
    """Học kỳ của một năm học.

    Học kỳ không phải thứ người dùng tạo ra: mọi năm đều có như nhau, số
    lượng lấy từ "Số học kỳ mỗi năm" chọn lúc đăng ký. Nhờ vậy không tồn tại
    cặp năm–kỳ không hợp lệ; kỳ chưa nhập môn chỉ là kỳ rỗng.
    """
    return SEMESTERS[:so_ky]


def years(khoa_from, khoa_to) -> list[str]:
    """Danh sách năm học suy từ niên khoá, dùng khi tạo tài khoản."""
    try:
        tu, den = int(khoa_from), int(khoa_to)
    except (TypeError, ValueError):
        return []
    if den <= tu or den - tu > 8:
        return []
    return [f"{y}–{y + 1}" for y in range(tu, den)]

SCREENS = {
    "dashboard": "Dashboard",
    "add": "Thêm / cập nhật môn học",
    "risk": "Cảnh báo & Mục tiêu",
}

USER = {"name": "Sinh viên", "initials": "SV", "khoa": "2023–2027"}

# --- Môn học ---------------------------------------------------------------
# Port nguyên SEED của mockup, thêm mã môn học. Mã mới là khoá nhận diện môn
# (tên nhập tay không đáng tin), còn điểm thành phần dựng lại từ điểm mục tiêu
# bằng rules.mk_rows thay vì lưu điểm tổng kết.
_SEED = [
    ("2024–2025", "Học kỳ 2", "20CT3101", "Công nghệ phần mềm", 3, 7.1,
     "Học lần 1"),
    ("2024–2025", "Học kỳ 2", "20CT2203", "Mạng máy tính", 3, 6.0,
     "Học lần 1"),
    ("2024–2025", "Học kỳ 2", "20TN1301", "Xác suất thống kê", 3, 4.8,
     "Học lại"),
    ("2024–2025", "Học kỳ 2", "20CT2301", "Lập trình web", 3, 8.4,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3201", "Trí tuệ nhân tạo", 3, 5.4,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3202", "Lập trình Python nâng cao", 3, 7.8,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3203", "Cơ sở dữ liệu phân tán", 3, 4.2,
     "Học lại"),
    ("2025–2026", "Học kỳ 1", "20CT3204", "Kiểm thử phần mềm", 2, 6.5,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT2104", "Tiếng Anh chuyên ngành 2", 2, 8.1,
     "Học cải thiện"),
    ("2026–2027", "Học kỳ 1", "20CT4901", "Đồ án tốt nghiệp", 6, 7.5,
     "Học lần 1"),
    ("2026–2027", "Học kỳ 1", "20CT4201", "Học máy ứng dụng", 3, 6.2,
     "Học lần 1"),
]


def seed_courses() -> list[dict]:
    """Bản sao dữ liệu mẫu cho một phiên mới."""
    return [
        {"id": i + 1, "year": nam, "sem": ky, "code": ma, "name": ten,
         "credits": tc, "attempt": loai,
         "attempt_no": 1 if loai == "Học lần 1" else 2,
         "rows": rules.mk_rows(diem)}
        for i, (nam, ky, ma, ten, tc, diem, loai) in enumerate(_SEED)
    ]


def metrics(courses: list[dict], scale: int, tat_ca: list[dict],
            nam: str, ky: str) -> list[dict]:
    """Bốn thẻ chỉ số của kỳ đang xem; nhãn đổi theo thang điểm."""
    tk = rules.tom_tat(courses)
    delta, mau_delta = rules.so_sanh_ky_truoc(tat_ca, nam, ky, scale)
    gpa = rules.gpa_thang(tk, scale)
    if tk["tam_tinh"]:
        no_delta = f'Chỉ tính {len(courses) - tk["tam_tinh"]} môn đã đủ điểm'
    else:
        no_delta = "Phải học lại" if tk["truot"] else "Không có môn nợ"
    return [
        {"label": f"GPA học kỳ (DH{scale})",
         "value": f"{gpa:.2f}" if courses else "—",
         "color": t.TEXT, "delta": delta, "delta_color": mau_delta},
        {"label": "Tín chỉ đã đăng ký", "value": str(tk["tin_chi"]),
         "color": t.TEXT, "delta": f"{len(courses)} môn đang học",
         "delta_color": t.MUTED},
        {"label": ("Môn điểm E (học lại)" if scale == 4
                   else f"Môn dưới {t.GRADE_FAIL:.1f} (học lại)"),
         "value": str(tk["truot"]),
         "color": t.DANGER if tk["truot"] else t.SUCCESS,
         "delta": no_delta, "delta_color": t.MUTED},
        {"label": "Mức nguy cơ", "value": RISK_LABEL,
         "color": t.RISK_STYLES[RISK_LABEL]["dot"],
         "delta": f"{RISK_PCT}% bị cảnh báo học vụ", "delta_color": t.MUTED},
    ]


def course_footnote(courses: list[dict]) -> str:
    tk = rules.tom_tat(courses)
    return (f'{len(courses)} môn · {tk["tin_chi"]} tín chỉ trong học kỳ này · '
            'môn ghi "tạm tính" là chưa nhập đủ 100% trọng số điểm thành phần')


# --- Thêm / cập nhật môn học ----------------------------------------------
# Bộ dòng mặc định khi mở form thêm môn mới: đủ 100% trọng số, chưa có điểm.
def form_rows_moi() -> list[dict]:
    return [
        {"loai": "Chuyên cần", "trong_so": 10, "diem": None},
        {"loai": "Kiểm tra giữa kỳ", "trong_so": 30, "diem": None},
        {"loai": "Thi cuối kỳ", "trong_so": 60, "diem": None},
    ]


# --- Cảnh báo & Mục tiêu ---------------------------------------------------
RISK_PCT = 46
RISK_LABEL = "Trung bình"
RISK_UPDATED = ("Cập nhật lần cuối: 30/08/2026 · dựa trên toàn bộ 11 môn "
                "(32 tín chỉ) đã ghi nhận qua các học kỳ")

REASONS = [
    "Điểm giữa kỳ môn Trí tuệ nhân tạo chỉ 5,5 — thấp hơn 2,1 điểm so với "
    "trung bình các môn khác.",
    "Đang có 1 môn dưới 5.0 (Cơ sở dữ liệu phân tán, học lại lần 2).",
    "GPA giảm liên tiếp 2 học kỳ gần nhất (2,95 → 2,55).",
]

TIPS = [
    {"n": "1", "title": "Cần cải thiện điểm chuyên cần",
     "detail": "Chuyên cần chiếm 10% nhưng đang ở mức 6,0 — dễ nâng nhất "
               "trong các thành phần."},
    {"n": "2", "title": "Ưu tiên ôn thi Cơ sở dữ liệu phân tán",
     "detail": "Chỉ cần 5,0 điểm thi cuối kỳ là đủ qua môn và xoá nợ tín chỉ."},
    {"n": "3", "title": "Giảm số tín chỉ học kỳ tới xuống 12–14",
     "detail": "Giúp tập trung vào các môn đang có nguy cơ trượt."},
]

GOALS = {
    "Đạt loại Giỏi": {
        "pct": 24, "hint": "GPA ≥ 3.2",
        "note": "Cần điểm trung bình từ 8.5 trở lên ở 3 môn còn lại — khá khó "
                "với mức hiện tại.",
    },
    "Đạt loại Khá": {
        "pct": 61, "hint": "GPA ≥ 2.5",
        "note": "Khả thi nếu nâng điểm Trí tuệ nhân tạo lên ≥ 6.5 và giữ các "
                "môn còn lại.",
    },
    "Qua môn (không nợ)": {
        "pct": 88, "hint": "Không môn < 4.0",
        "note": "Chỉ cần đạt ≥ 5.0 điểm thi cuối kỳ môn Cơ sở dữ liệu phân "
                "tán.",
    },
}

FOOTER = ("Mockup Streamlit · Đồ án chuyên ngành Kỹ thuật phần mềm — Hệ thống "
          "cảnh báo sớm nguy cơ học tập của sinh viên")
