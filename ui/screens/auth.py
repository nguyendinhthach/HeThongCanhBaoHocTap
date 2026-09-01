"""Đăng nhập / Đăng ký — cột giữa rộng 560px, tab gạch chân.

Tab điều khiển bằng session_state (không dùng st.tabs) vì link "Đăng ký" nằm
cạnh nút CTA phải chuyển được sang tab đăng ký.
"""

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import tokens as t

# Chiều rộng cột form và kiểu tab, lấy đúng số đo trong mockup.
_CSS = f"""
<style>
  .st-key-auth_col {{ max-width: {t.AUTH_W}px; }}

  /* Thanh tab: gap 24, gạch dưới toàn thanh 1px */
  .st-key-auth_tabs {{
    border-bottom: 1px solid {t.BORDER};
    gap: 24px !important;
    margin-bottom: 22px;
  }}
  .st-key-tab_login button, .st-key-tab_register button {{
    border: none !important;
    border-radius: 0 !important;
    padding: 10px 2px !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    color: {t.MUTED} !important;
    white-space: nowrap !important;
  }}
  .st-key-{{active}} button {{
    color: {t.PRIMARY} !important;
    font-weight: 600 !important;
    box-shadow: inset 0 -3px 0 0 {t.PRIMARY} !important;
  }}

  /* Link "Đăng ký" cạnh nút CTA: chữ thường, đậm, xanh */
  .st-key-link_register button {{
    border: none !important;
    padding: 0 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: {t.PRIMARY} !important;
    white-space: nowrap !important;
  }}
  .st-key-link_register button:hover {{ text-decoration: underline !important; }}
</style>
"""


def _chuyen(mode: str) -> None:
    st.session_state.auth_mode = mode
    st.rerun()


def _tabs(la_dang_nhap: bool) -> None:
    active = "tab_login" if la_dang_nhap else "tab_register"
    st.markdown(_CSS.replace("{active}", active), unsafe_allow_html=True)

    with st.container(horizontal=True, key="auth_tabs"):
        if st.button("Đăng nhập", key="tab_login", type="tertiary"):
            _chuyen("login")
        if st.button("Đăng ký", key="tab_register", type="tertiary"):
            _chuyen("register")


def _vao_dashboard() -> None:
    st.session_state.logged_in = True
    st.session_state.screen = "dashboard"
    st.rerun()


def _dang_nhap() -> None:
    st.text_input("Email", value="sinhvien@sv.edu.vn", key="dn_email")
    st.text_input("Mật khẩu", type="password", value="12345678",
                  key="dn_mat_khau")
    b.spacer(4)

    # Mockup: CTA và dòng "Chưa có tài khoản? Đăng ký" nằm CÙNG HÀNG, gap 14px
    with st.container(horizontal=True, vertical_alignment="center",
                      gap="medium"):
        if st.button("Đăng nhập", type="primary", key="cta_login"):
            _vao_dashboard()
        st.markdown(
            f'<span style="font-size:14px;color:{t.MUTED};'
            f'white-space:nowrap">Chưa có tài khoản?</span>',
            unsafe_allow_html=True,
        )
        if st.button("Đăng ký", key="link_register", type="tertiary"):
            _chuyen("register")


def _sinh_hoc_ky() -> list[str]:
    """Danh sách năm học – học kỳ suy ra từ niên khoá."""
    try:
        tu, den = int(st.session_state.khoa_from), int(st.session_state.khoa_to)
    except (TypeError, ValueError):
        return []
    if den <= tu or den - tu > 8:
        return []
    return [f"{y}–{y + 1} HK{k}"
            for y in range(tu, den)
            for k in range(1, st.session_state.so_ky + 1)]


def _dang_ky() -> None:
    st.session_state.ho_ten = st.text_input(
        "Họ và Tên", value=st.session_state.ho_ten,
        placeholder="Nguyễn Đình Thạch")
    st.text_input("Email", value="sinhvien@sv.edu.vn", key="dk_email")
    st.text_input("Mật khẩu", type="password", key="dk_mat_khau")

    b.note("Hệ thống sẽ tự sinh danh sách năm học – học kỳ từ thông tin dưới "
           "đây. Bạn vẫn có thể thêm học kỳ mới sau.")
    b.spacer(10)

    c1, c2 = st.columns(2)
    st.session_state.khoa_from = c1.text_input(
        "Niên khoá (từ)", value=st.session_state.khoa_from)
    st.session_state.khoa_to = c2.text_input(
        "Niên khoá (đến)", value=st.session_state.khoa_to)

    c3, c4 = st.columns(2)
    c3.selectbox("Số năm học dự kiến", ["4 năm", "4.5 năm", "5 năm"],
                 key="dk_so_nam")
    ky = [2, 3]
    st.session_state.so_ky = c4.selectbox(
        "Số học kỳ mỗi năm", ky, index=ky.index(st.session_state.so_ky),
        format_func=lambda n: f"{n} học kỳ")

    # Chip niên khoá: 12px monospace, nền #e8f0fa, bo tròn
    hoc_ky = _sinh_hoc_ky()
    if hoc_ky:
        chip = "".join(f'<span class="mk-chip">{k}</span>' for k in hoc_ky)
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;'
            f'align-items:center;margin-top:8px">'
            f'<span style="font-size:13px;color:{t.MUTED};margin-right:4px">'
            f"Sẽ tạo:</span>{chip}</div>",
            unsafe_allow_html=True,
        )
    b.spacer(14)

    with st.container(horizontal=True, vertical_alignment="center",
                      gap="medium"):
        if st.button("Tạo tài khoản", type="primary", key="cta_register"):
            _vao_dashboard()
        st.markdown(
            f'<span style="font-size:14px;color:{t.MUTED}">Có thể thêm học kỳ '
            f"mới bất cứ lúc nào sau này.</span>",
            unsafe_allow_html=True,
        )


def render() -> None:
    with st.container(key="auth_col"):
        b.page_title("Cảnh báo học tập sớm",
                     "Đăng nhập để theo dõi điểm và mức nguy cơ của bạn.")
        b.spacer(22)

        la_dang_nhap = st.session_state.auth_mode == "login"
        _tabs(la_dang_nhap)

        if la_dang_nhap:
            _dang_nhap()
        else:
            _dang_ky()

    b.footer(d.FOOTER)
