"""CSS toàn cục — dịch từ style nội tuyến của mockup sang widget Streamlit.

Mục tiêu: widget gốc của Streamlit mang đúng viền, bo góc, padding, cỡ chữ mà
mockup quy định, để không phải vá lặt vặt ở từng màn hình.
"""

import streamlit as st

from ui import tokens as t

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

/* Vùng nội dung chính: padding 44px 56px 64px như mockup */
.block-container {{
  padding: {t.MAIN_PAD} !important;
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
  padding: 32px 24px 24px;
}}

/* Sidebar luôn hiển thị: ẩn nút thu gọn và nút bung lại */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarHeader"] button {{
  display: none !important;
}}

/* --- Ô nhập & select --------------------------------------------------- */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="select"] > div {{
  border: 1px solid {t.BORDER_INPUT} !important;
  border-radius: {t.RADIUS_INPUT}px !important;
  background: {t.SURFACE} !important;
  color: {t.TEXT} !important;
  font-size: 15px !important;
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

/* --- Điều hướng sidebar: ô chọn bo góc, mục đang chọn nền xanh nhạt ----- */
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 2px !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  padding: 7px 8px !important;
  border-radius: {t.RADIUS_SMALL}px !important;
  margin: 0 !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background: #e4e7ef;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: #e2e8f4;
}}
[data-testid="stSidebar"] [role="radiogroup"] label p {{
  font-size: 15px !important;
  color: {t.TEXT} !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{
  font-weight: 600 !important;
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

/* Bỏ khoảng trắng thừa Streamlit chèn giữa các khối markdown */
[data-testid="stMarkdownContainer"] > div:empty {{ display: none; }}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
