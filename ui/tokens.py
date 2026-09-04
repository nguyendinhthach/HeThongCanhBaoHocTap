"""Token thiết kế trích nguyên văn từ docs/mockups/MockupStreamlit/.

Đây là nguồn duy nhất cho màu và kích thước. Khi mockup đổi, sửa ở đây trước
rồi mới sửa chỗ dùng — không rải giá trị cứng trong các file màn hình.
"""

# --- Màu -------------------------------------------------------------------
BODY_TEXT = "#262730"       # body color
TEXT = "#31333f"            # chữ chính trong khối
MUTED = "#6b7280"           # chữ phụ
FAINT = "#9ba3af"           # chú thích mờ
PRIMARY = "#0068c9"
PRIMARY_HOVER = "#00539f"
PRIMARY_DARK = "#00489a"

# Xanh thương hiệu — chỉ dùng cho thanh header và mục điều hướng đang chọn.
# Khác PRIMARY (màu hành động của nút/liên kết), mockup cố ý tách hai màu này.
BRAND = "#004cff"
NAV_TEXT = "#4b5563"      # chữ mục điều hướng chưa chọn
NAV_HOVER = "#e4e7ef"

SURFACE = "#ffffff"
SURFACE_ALT = "#f9fafc"     # nền thẻ gợi ý
SIDEBAR_BG = "#f0f2f6"
PANEL_BG = "#f7f8fb"        # nền khối kết quả mục tiêu

BORDER = "#e6eaf1"          # viền thẻ/bảng
BORDER_INPUT = "#d5d8de"    # viền ô nhập
BORDER_SOFT = "#dfe3ec"     # đường kẻ trong sidebar
BORDER_DASH = "#b9c0cc"     # viền nét đứt
ROW_LINE = "#f0f2f6"        # kẻ giữa các dòng bảng
ROW_ALT = "#fbfcfd"

DANGER = "#c1121f"
DANGER_HOVER = "#9d0f19"
WARNING = "#d68910"
WARNING_TEXT = "#8a6100"
WARNING_DEEP = "#a9750a"   # điểm nằm giữa ngưỡng trượt và ngưỡng an toàn
SUCCESS = "#0b7a2c"
DISABLED = "#c9ced8"       # nền nút khi chưa đủ điều kiện bấm

CHIP_BG = "#e8f0fa"         # chip niên khoá / nhãn chế độ form
TIP_BG = "#e3f4e8"          # ô số thứ tự gợi ý

# --- Kích thước ------------------------------------------------------------
HEADER_H = 59               # padding 16*2 + dòng chữ 18px * 1.5
SIDEBAR_W = 300
MAIN_PAD = "44px 56px 64px"
AUTH_W = 560
SHELL_GAP = 28
RADIUS_CARD = 10
RADIUS_INPUT = 8
RADIUS_SMALL = 6
RADIUS_PILL = 999

# --- Trạng thái nguy cơ ----------------------------------------------------
RISK_STYLES = {
    "Cao": {"dot": DANGER, "bg": "#fdf1f1", "border": "#f3c9c9"},
    "Trung bình": {"dot": WARNING, "bg": "#fffaef", "border": "#f0dfae"},
    "Thấp": {"dot": SUCCESS, "bg": "#f2fbf4", "border": "#c6e8cf"},
}

# --- Nhãn loại lần học -----------------------------------------------------
ATTEMPT_STYLES = {
    "Học lại": {"bg": "#fdeaea", "color": DANGER},
    "Học cải thiện": {"bg": "#fff6da", "color": WARNING_TEXT},
    "Học lần 1": {"bg": "#eef1f6", "color": MUTED},
}

# --- Ngưỡng nghiệp vụ ------------------------------------------------------
# Mockup: < 4.0 là trượt (phải học lại), < 5.5 là vùng cảnh báo.
GRADE_FAIL = 4.0
GRADE_WARN = 5.5

COMPONENT_TYPES = [
    "Chuyên cần", "Bài tập", "Thực hành", "Kiểm tra giữa kỳ",
    "Bài tập nhóm", "Thi cuối kỳ", "Khác",
]
ATTEMPT_TYPES = ["Học lần 1", "Học lại", "Học cải thiện"]
# Từ lần 2 trở đi mới có gì để chọn: lần 1 thì loại lần học là hiển nhiên.
ATTEMPT_REPEAT = ["Học lại", "Học cải thiện"]

MONO = "'Source Code Pro', monospace"
