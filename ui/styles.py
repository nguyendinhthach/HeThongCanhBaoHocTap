"""CSS toàn cục — dịch từ style nội tuyến của mockup sang widget Streamlit.

Mục tiêu: widget gốc của Streamlit mang đúng viền, bo góc, padding, cỡ chữ mà
mockup quy định, để không phải vá lặt vặt ở từng màn hình.
"""

import base64

import streamlit as st

from ui import tokens as t

# Icon điều hướng lấy nguyên path từ mockup. Màu nằm trong chính chuỗi SVG nên
# mỗi icon phải dựng hai bản: màu thường và màu khi đang chọn.
_ICON_PATHS = {
    "dashboard": (
        '<rect x="1" y="1" width="6" height="6" rx="1.5" fill="{c}"/>'
        '<rect x="9" y="1" width="6" height="6" rx="1.5" fill="{c}" opacity=".45"/>'
        '<rect x="1" y="9" width="6" height="6" rx="1.5" fill="{c}" opacity=".45"/>'
        '<rect x="9" y="9" width="6" height="6" rx="1.5" fill="{c}"/>'
    ),
    "add": (
        '<rect x="1.5" y="1.5" width="13" height="13" rx="3.5" stroke="{c}" '
        'stroke-width="1.6" fill="none"/>'
        '<rect x="7.2" y="4.4" width="1.6" height="7.2" rx=".8" fill="{c}"/>'
        '<rect x="4.4" y="7.2" width="7.2" height="1.6" rx=".8" fill="{c}"/>'
    ),
    "risk": (
        '<path d="M8 1.8 L15 14.2 H1 Z" stroke="{c}" stroke-width="1.6" '
        'stroke-linejoin="round" fill="none"/>'
        '<rect x="7.2" y="6" width="1.6" height="4" rx=".8" fill="{c}"/>'
        '<rect x="7.2" y="11" width="1.6" height="1.6" rx=".8" fill="{c}"/>'
    ),
}


def _icon(ten: str, mau: str) -> str:
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" '
           'viewBox="0 0 16 16">' + _ICON_PATHS[ten].replace("{c}", mau)
           + "</svg>")
    b64 = base64.b64encode(svg.encode()).decode()
    return f"url('data:image/svg+xml;base64,{b64}')"


_NAV_CSS = "".join(
    f'  [data-testid="stSidebar"] [class*="st-key-nav_"]'
    f'.st-key-nav_{k} .stButton button::before '
    f'{{ background-image: {_icon(k, t.NAV_TEXT)}; }}\n'
    for k in _ICON_PATHS
)


def nav_active_css(key: str) -> str:
    """CSS cho mục điều hướng đang chọn: nền trắng, vạch accent, icon xanh."""
    return f"""
<style>
  [data-testid="stSidebar"] [class*="st-key-nav_"].st-key-nav_{key}
  .stButton button {{
    background: {t.SURFACE} !important;
    box-shadow: inset 3px 0 0 0 {t.BRAND} !important;
  }}
  [data-testid="stSidebar"] [class*="st-key-nav_"].st-key-nav_{key}
  .stButton button p {{
    color: {t.BRAND} !important;
    font-weight: 600 !important;
  }}
  [data-testid="stSidebar"] [class*="st-key-nav_"].st-key-nav_{key}
  .stButton button::before {{
    background-image: {_icon(key, t.BRAND)};
  }}
</style>
"""

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;600&display=swap');

/* --- Khung chung ------------------------------------------------------- */
/* Không nhắm [class*="st-"]: sẽ đè cả font icon của Streamlit khiến nút hiện
   mật khẩu in ra chữ "visibility" thay vì biểu tượng. */
html, body, .stApp, button, input, select, textarea {{
  font-family: "Source Sans 3", "Segoe UI", sans-serif;
}}
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded {{
  font-family: "Material Symbols Rounded", "Material Icons" !important;
}}
body {{ color: {t.BODY_TEXT}; -webkit-font-smoothing: antialiased; }}

.stApp {{ background: {t.SURFACE}; }}

/* Thanh header thương hiệu: ghim trên cùng, phủ hết chiều ngang kể cả
   sidebar. Ẩn header gốc của Streamlit vì mockup không có thanh công cụ. */
[data-testid="stHeader"] {{ display: none !important; }}

.mk-header {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 2147483000;
  height: {t.HEADER_H}px; box-sizing: border-box;
  background: {t.BRAND}; color: {t.SURFACE};
  padding: 16px 32px;
  font-size: 18px; font-weight: 700; letter-spacing: -0.01em;
  display: flex; align-items: center;
}}

/* Vùng nội dung chính: padding 44px 56px 64px như mockup, cộng chiều cao
   thanh header vì thanh này nằm ngoài luồng. */
.block-container {{
  padding: calc(44px + {t.HEADER_H}px) 56px 64px !important;
  max-width: 1180px;
}}

/* --- Sidebar: rộng 300px, nền #f0f2f6 ---------------------------------- */
[data-testid="stSidebar"] {{
  width: {t.SIDEBAR_W}px !important;
  min-width: {t.SIDEBAR_W}px !important;
  background: {t.SIDEBAR_BG};
  border-right: 1px solid {t.BORDER};
}}
[data-testid="stSidebar"] > div:first-child {{
  padding: calc(32px + {t.HEADER_H}px) 24px 24px;
}}

/* Sidebar luôn hiển thị: ẩn nút thu gọn và nút bung lại */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarHeader"] button {{
  display: none !important;
}}

/* --- Ô nhập & select --------------------------------------------------- */
/* Streamlit 1.61 không còn gắn data-baseweb="select" cho ô chọn; hook ổn định
   là stSelectbox, với khung viền nằm ở div lồng thứ hai. */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div > div {{
  border: 1px solid {t.BORDER_INPUT} !important;
  border-radius: {t.RADIUS_INPUT}px !important;
  background: {t.SURFACE} !important;
  color: {t.TEXT} !important;
  font-size: 15px !important;
}}
[data-testid="stSelectbox"] input {{
  font-size: 15px !important;
  padding: 9px 12px !important;
  color: {t.TEXT} !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
  padding: 11px 13px !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {{
  border-color: {t.PRIMARY} !important;
  box-shadow: 0 0 0 3px rgba(0,104,201,0.15) !important;
}}

/* Ô chọn chỉ được bung danh sách rồi chọn, đúng như <select> của mockup.
   Việc này chia hai phần và cần cả hai:

   - Bàn phím do `filter_mode=None` ở mỗi st.selectbox lo (xem app.py và các
     màn hình) — tắt hẳn tính năng gõ để lọc.
   - Con trỏ chuột do khối này lo: filter_mode không làm <input> thành
     readonly, nên bấm vào vẫn hiện con trỏ nháy và bôi đen được chữ.

   Tắt pointer trên ô nhập thì cú bấm rơi xuống div bao, mà div đó lại không
   mở danh sách — chỉ nút mũi tên mở được. Nên kéo luôn nút mũi tên phủ kín
   khung để bấm chỗ nào trong ô cũng bung danh sách. */
[data-testid="stSelectbox"] input {{
  pointer-events: none !important;
  caret-color: transparent !important;
  user-select: none !important;
  cursor: pointer !important;
}}
[data-testid="stSelectbox"] > div > div {{
  position: relative !important;
  cursor: pointer !important;
}}
[data-testid="stSelectbox"] > div > div > button {{
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: transparent !important;
  border: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  padding: 0 10px 0 0 !important;
  cursor: pointer !important;
}}

/* Nhãn của widget: 14px/600 như mockup */
[data-testid="stWidgetLabel"] p {{
  font-size: 14px !important;
  font-weight: 600 !important;
  color: {t.TEXT} !important;
}}
/* Nhãn ô chọn trong sidebar: 13px màu phụ (mockup dùng cỡ này cho Năm học,
   Học kỳ) — nhãn nhóm điều hướng vẫn giữ 14px/600 nên chỉ nhắm selectbox. */
[data-testid="stSidebar"] [data-testid="stSelectbox"]
[data-testid="stWidgetLabel"] p {{
  font-size: 13px !important;
  font-weight: 400 !important;
  color: {t.MUTED} !important;
}}

/* --- Điều hướng sidebar: nút có icon, mục đang chọn nền trắng + vạch trái -
   Dùng nút thay vì radio để đặt được icon và vạch accent; đổi màn hình bằng
   rerun nên cũng tránh luôn lỗi radio phải bấm hai lần. */
[data-testid="stSidebar"] [class*="st-key-nav_"] .stButton button {{
  border: none !important;
  background: transparent !important;
  border-radius: {t.RADIUS_INPUT}px !important;
  padding: 10px 12px 10px 40px !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  color: {t.NAV_TEXT} !important;
  text-align: left !important;
  width: 100% !important;
  position: relative;
  box-shadow: inset 3px 0 0 0 transparent !important;
  justify-content: flex-start !important;
}}
/* Streamlit bọc nhãn nút trong một div flex căn giữa; text-align trên <p>
   không thắng được nó nên phải căn trái ngay ở div đó. */
[data-testid="stSidebar"] [class*="st-key-nav_"] .stButton button > div {{
  justify-content: flex-start !important;
  width: 100% !important;
}}
[data-testid="stSidebar"] [class*="st-key-nav_"] .stButton button p {{
  text-align: left !important;
  width: 100%;
  color: {t.NAV_TEXT} !important;
}}
[data-testid="stSidebar"] [class*="st-key-nav_"] .stButton button::before {{
  content: "";
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  width: 17px; height: 17px;
  background-repeat: no-repeat; background-position: center;
}}
[data-testid="stSidebar"] [class*="st-key-nav_"] .stButton button:hover {{
  background: {t.NAV_HOVER} !important;
  color: {t.NAV_TEXT} !important;
}}
.st-key-nav_group {{ gap: 4px !important; }}
{_NAV_CSS}
/* Nhãn nhóm "Chức năng" và "Kỳ học đang xem" */
.mk-side-label {{
  font-size: 14px; font-weight: 600; color: {t.TEXT}; margin-bottom: 10px;
}}

/* Link "+ Thêm học kỳ mới" */
.st-key-btn_add_term button {{
  border: none !important; padding: 0 !important;
  font-size: 13px !important; font-weight: 600 !important;
  color: {t.BRAND} !important;
}}
.st-key-btn_add_term button:hover {{ text-decoration: underline !important; }}

/* Form thêm học kỳ: thẻ trắng thu nhỏ trong sidebar */
.st-key-add_term_box {{
  background: {t.SURFACE}; border: 1px solid {t.BORDER};
  border-radius: {t.RADIUS_INPUT}px; padding: 12px !important;
  gap: 8px !important;
}}
.st-key-add_term_box [data-testid="stTextInput"] input,
.st-key-add_term_box [data-testid="stSelectbox"] input {{
  padding: 8px 10px !important; font-size: 14px !important;
}}
.st-key-add_term_box [data-testid="stSelectbox"] > div > div {{
  border-radius: {t.RADIUS_SMALL}px !important;
}}
.st-key-add_term_box [data-testid="stTextInput"] input {{
  border-radius: {t.RADIUS_SMALL}px !important;
}}
.st-key-add_term_box [data-testid="stWidgetLabel"] p {{
  font-size: 12px !important; font-weight: 400 !important;
  color: {t.MUTED} !important;
}}
.st-key-btn_save_term button, .st-key-btn_cancel_term button {{
  font-size: 13px !important; padding: 8px 14px !important;
}}

/* Nút Đăng xuất: chữ nhỏ, thụt vào ngang với tên người dùng */
.st-key-btn_logout button {{
  border: none !important;
  padding: 0 0 0 46px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  color: {t.MUTED} !important;
}}
.st-key-btn_logout button:hover {{
  color: {t.DANGER} !important;
  text-decoration: underline !important;
}}

/* Ẩn thanh công cụ Vega/Streamlit nổi trên biểu đồ và bảng */
[data-testid="stElementToolbar"] {{ display: none !important; }}
.vega-embed .vega-actions, .vega-embed summary {{ display: none !important; }}

/* --- Nút --------------------------------------------------------------- */
.stButton button {{
  border-radius: {t.RADIUS_INPUT}px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  padding: 11px 22px !important;
  transition: none !important;
}}
.stButton button[kind="primary"] {{
  background: {t.PRIMARY} !important;
  border: 1px solid {t.PRIMARY} !important;
  color: {t.SURFACE} !important;
}}
.stButton button[kind="primary"]:hover {{
  background: {t.PRIMARY_HOVER} !important;
  border-color: {t.PRIMARY_HOVER} !important;
}}
.stButton button[kind="secondary"] {{
  background: {t.SURFACE} !important;
  border: 1px solid {t.BORDER_INPUT} !important;
  color: {t.TEXT} !important;
  font-weight: 400 !important;
}}
.stButton button[kind="secondary"]:hover {{
  border-color: {t.FAINT} !important;
  color: {t.TEXT} !important;
}}

/* --- Khối HTML tự dựng -------------------------------------------------- */
.mk-h1 {{
  font-size: 32px; font-weight: 700; letter-spacing: -0.02em;
  color: {t.BODY_TEXT}; margin: 0;
}}
.mk-sub {{ font-size: 15px; color: {t.MUTED}; margin: 6px 0 0; }}
.mk-h2 {{ font-size: 20px; font-weight: 600; color: {t.BODY_TEXT}; margin: 0; }}
.mk-h3 {{ font-size: 18px; font-weight: 600; color: {t.BODY_TEXT}; margin: 0; }}
.mk-note {{ font-size: 13px; color: {t.FAINT}; margin: 0; }}
.mk-muted {{ font-size: 14px; color: {t.MUTED}; margin: 0; }}
.mk-strong {{ color: {t.TEXT}; font-weight: 600; }}

.mk-card {{
  border: 1px solid {t.BORDER};
  border-radius: {t.RADIUS_CARD}px;
  background: {t.SURFACE};
  padding: 24px;
}}

/* Thẻ chỉ số: grid 4 cột, gap 18 */
.mk-metrics {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
}}
.mk-metric {{
  border: 1px solid {t.BORDER}; border-radius: {t.RADIUS_CARD}px;
  padding: 18px 20px; background: {t.SURFACE};
  display: flex; flex-direction: column; gap: 6px;
}}
.mk-metric-label {{ font-size: 14px; color: {t.MUTED}; }}
.mk-metric-value {{
  font-size: 30px; font-weight: 700; letter-spacing: -0.02em;
}}
.mk-metric-delta {{ font-size: 13px; }}

/* Bảng dạng grid, khớp tỉ lệ cột của mockup */
.mk-table {{
  border: 1px solid {t.BORDER}; border-radius: {t.RADIUS_CARD}px;
  overflow: hidden;
}}
.mk-thead, .mk-trow {{ display: grid; }}
.mk-thead {{
  background: {t.SIDEBAR_BG}; border-bottom: 1px solid {t.BORDER};
}}
.mk-thead > div {{
  padding: 11px 12px; font-size: 13px; font-weight: 600; color: {t.MUTED};
}}
.mk-trow {{ border-bottom: 1px solid {t.ROW_LINE}; align-items: center; }}
.mk-trow > div {{ padding: 12px; font-size: 15px; color: {t.TEXT}; }}
.mk-num {{ font-family: {t.MONO}; text-align: right; }}
.mk-idx {{ font-family: {t.MONO}; color: {t.FAINT}; font-size: 14px; }}
.mk-empty {{
  padding: 22px; font-size: 14px; color: {t.FAINT}; text-align: center;
}}

.mk-tag {{
  display: inline-block; font-size: 13px; padding: 3px 10px;
  border-radius: {t.RADIUS_PILL}px;
}}
.mk-chip {{
  display: inline-block; font-size: 12px; font-family: {t.MONO};
  background: {t.CHIP_BG}; color: {t.PRIMARY_DARK};
  border-radius: {t.RADIUS_PILL}px; padding: 4px 10px;
}}

/* Thanh tiến trình đặc (mockup dùng div lồng, không dùng progress gốc) */
.mk-bar {{
  height: 12px; border-radius: {t.RADIUS_PILL}px;
  background: {t.BORDER}; overflow: hidden;
}}
.mk-bar > div {{ height: 12px; border-radius: {t.RADIUS_PILL}px; }}

.mk-bignum {{
  font-size: 60px; font-weight: 700; line-height: 0.95;
  letter-spacing: -0.03em;
}}
.mk-bignum-sm {{
  font-size: 52px; font-weight: 700; line-height: 0.95;
  letter-spacing: -0.03em;
}}

.mk-footer {{
  margin-top: 40px; padding-top: 24px; border-top: 1px solid {t.ROW_LINE};
  font-size: 13px; color: {t.FAINT};
}}

/* --- Màn đăng nhập / đăng ký ------------------------------------------ */
.st-key-auth_col {{ align-self: center; margin: 0 auto; }}
.st-key-auth_wrap {{
  background: {t.SIDEBAR_BG};
  border-radius: 14px;
  margin: -8px -16px 0;
  padding: 48px 16px 56px !important;
  min-height: 640px;
  align-items: center;
}}
.st-key-auth_card {{
  border: 1px solid {t.BORDER};
  border-radius: 12px;
  background: {t.SURFACE};
  padding: 26px 28px 28px !important;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}}
/* Khối niên khoá trong tab Đăng ký */
.st-key-auth_khoa {{
  background: {t.PANEL_BG};
  border: 1px solid {t.BORDER};
  border-radius: {t.RADIUS_CARD}px;
  padding: 18px !important;
}}
.mk-h1-auth {{
  font-size: 34px; font-weight: 700; letter-spacing: -0.02em;
  color: {t.BODY_TEXT}; margin: 0;
}}

/* --- Bảng "Môn học đã thêm" ------------------------------------------- */
/* Bảng này dựng bằng st.columns (cần nút bấm được) nên phải vá lại cho
   giống bảng HTML: viền bao, hàng tiêu đề, kẻ ngang, ô gọn. */
.st-key-semtable {{
  border: 1px solid {t.BORDER};
  border-radius: {t.RADIUS_CARD}px;
  overflow: hidden;
  padding: 0 !important;
  gap: 0 !important;
}}
.st-key-semhead {{
  background: {t.SIDEBAR_BG};
  border-bottom: 1px solid {t.BORDER};
  padding: 11px 12px !important;
  gap: 0 !important;
}}
[class*="st-key-semrow_"] {{
  border-bottom: 1px solid {t.ROW_LINE};
  padding: 6px 12px !important;
  gap: 0 !important;
}}
/* Nút Sửa / Xoá: viền mảnh, chữ 13px như mockup */
[class*="st-key-semact_"] {{ gap: 8px !important; }}
[class*="st-key-edit_"] .stButton button,
[class*="st-key-del_"] .stButton button {{
  border: 1px solid {t.BORDER_INPUT} !important;
  background: {t.SURFACE} !important;
  border-radius: {t.RADIUS_SMALL}px !important;
  padding: 6px 14px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  min-height: 0 !important;
}}
[class*="st-key-edit_"] .stButton button {{ color: {t.PRIMARY} !important; }}
[class*="st-key-edit_"] .stButton button:hover {{
  border-color: {t.PRIMARY} !important; background: #f5f9ff !important;
}}
[class*="st-key-del_"] .stButton button {{ color: {t.DANGER} !important; }}
[class*="st-key-del_"] .stButton button:hover {{
  border-color: {t.DANGER} !important; background: #fdf1f1 !important;
}}

/* Nút xoá trong hộp xác nhận: nền đỏ đặc */
.st-key-xoa_that .stButton button[kind="primary"] {{
  background: {t.DANGER} !important;
  border-color: {t.DANGER} !important;
}}
.st-key-xoa_that .stButton button[kind="primary"]:hover {{
  background: {t.DANGER_HOVER} !important;
  border-color: {t.DANGER_HOVER} !important;
}}

/* Bỏ khoảng trắng thừa Streamlit chèn giữa các khối markdown */
[data-testid="stMarkdownContainer"] > div:empty {{ display: none; }}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hide_sidebar() -> None:
    """Ẩn hẳn sidebar ở màn đăng nhập/đăng ký.

    Không dựng nội dung sidebar là chưa đủ: Streamlit vẫn giữ khung rỗng và
    thân trang vẫn bị thụt vào 300px, nên phải ẩn chính phần tử đó.
    """
    st.markdown(
        '<style>[data-testid="stSidebar"]{display:none !important;}</style>',
        unsafe_allow_html=True,
    )
