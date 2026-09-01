"""Dữ liệu hiển thị tĩnh, chép từ mockup đã render.

Giai đoạn này chỉ dựng giao diện nên mọi con số đều là giá trị cố định — chưa
có tính toán hay mô hình. Khi gắn nghiệp vụ, thay module này bằng lớp truy vấn
và tầng tính điểm.
"""

from ui import tokens as t

YEARS = ["2023–2024", "2024–2025", "2025–2026", "2026–2027"]
SEMESTERS = ["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"]

SCREENS = {
    "dashboard": "Dashboard",
    "add": "Thêm / cập nhật môn học",
    "risk": "Cảnh báo & Mục tiêu",
}

USER = {"name": "Sinh viên", "initials": "SV", "khoa": "2023–2027"}

# --- Dashboard -------------------------------------------------------------
METRICS = [
    {"label": "GPA học kỳ (thang 10)", "value": "6.26", "color": t.TEXT,
     "delta": "↓ 0,42 so với học kỳ trước", "delta_color": t.DANGER},
    {"label": "Tín chỉ đã đăng ký", "value": "13", "color": t.TEXT,
     "delta": "5 môn đang học", "delta_color": t.MUTED},
    {"label": "Môn dưới 5.0", "value": "1", "color": t.DANGER,
     "delta": "Nguy cơ phải học lại", "delta_color": t.MUTED},
    {"label": "Mức nguy cơ", "value": "Trung bình", "color": t.WARNING,
     "delta": "46% bị cảnh báo học vụ", "delta_color": t.MUTED},
]

# grade_color theo mockup: < 5 đỏ, < 6.5 cam, còn lại xanh
COURSES = [
    {"name": "Trí tuệ nhân tạo", "credits": 3, "grade": "5.4",
     "grade_color": t.WARNING, "attempt": "Học lần 1", "warn": False},
    {"name": "Lập trình Python nâng cao", "credits": 3, "grade": "7.8",
     "grade_color": t.SUCCESS, "attempt": "Học lần 1", "warn": False},
    {"name": "Cơ sở dữ liệu phân tán", "credits": 3, "grade": "4.2",
     "grade_color": t.DANGER, "attempt": "Lần 2 · Học lại", "warn": True},
    {"name": "Kiểm thử phần mềm", "credits": 2, "grade": "6.5",
     "grade_color": t.SUCCESS, "attempt": "Học lần 1", "warn": False},
    {"name": "Tiếng Anh chuyên ngành 2", "credits": 2, "grade": "8.1",
     "grade_color": t.SUCCESS, "attempt": "Lần 2 · Học cải thiện",
     "warn": False},
]

COURSE_FOOTNOTE = ('5 môn · 13 tín chỉ trong học kỳ này · môn ghi "tạm tính" '
                   "là chưa nhập đủ 100% trọng số điểm thành phần")

# Chuỗi GPA từng học kỳ; điểm đang chọn ở sidebar được tô sáng.
GPA_SERIES = [
    {"ky": "24–25 HK2", "gpa": 6.58, "dang_xem": False},
    {"ky": "25–26 HK1", "gpa": 6.26, "dang_xem": True},
    {"ky": "26–27 HK1", "gpa": 7.07, "dang_xem": False},
]

# --- Thêm / cập nhật môn học ----------------------------------------------
FORM_ROWS = [
    {"loai": "Chuyên cần", "trong_so": 10, "diem": 6.0},
    {"loai": "Kiểm tra giữa kỳ", "trong_so": 30, "diem": 5.5},
    {"loai": "Thi cuối kỳ", "trong_so": 60, "diem": None},
]

WEIGHT_TOTAL = 100
PROVISIONAL_TEXT = ("Điểm tạm tính (dựa trên 40% trọng số đã có điểm): 5.63 — "
                    "còn 60% (Thi cuối kỳ 60%) chưa nhập")

DUP_TEXT = ("Môn này đã học ở Học kỳ 1 (2025–2026) với điểm 4.2 (chưa đạt) — "
            "đã gợi ý “Học lại”. → Tự động ghi nhận là Lần 3.")

SEMESTER_COURSES = [
    {"name": c["name"], "credits": c["credits"], "grade": c["grade"],
     "attempt": c["attempt"]}
    for c in COURSES
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
        "pct": 24, "hint": "GPA ≥ 3.2", "color": t.WARNING,
        "note": "Cần điểm trung bình từ 8.5 trở lên ở 3 môn còn lại — khá khó "
                "với mức hiện tại.",
    },
    "Đạt loại Khá": {
        "pct": 61, "hint": "GPA ≥ 2.5", "color": t.PRIMARY,
        "note": "Khả thi nếu nâng điểm Trí tuệ nhân tạo lên ≥ 6.5 và giữ các "
                "môn còn lại.",
    },
    "Qua môn (không nợ)": {
        "pct": 88, "hint": "Không môn < 4.0", "color": t.SUCCESS,
        "note": "Chỉ cần đạt ≥ 5.0 điểm thi cuối kỳ môn Cơ sở dữ liệu phân "
                "tán.",
    },
}

FOOTER = ("Mockup Streamlit · Đồ án chuyên ngành Kỹ thuật phần mềm — Hệ thống "
          "cảnh báo sớm nguy cơ học tập của sinh viên")
