"""Đăng nhập / Đăng ký — cột giữa rộng 560px, tab gạch chân.

Tab điều khiển bằng session_state (không dùng st.tabs) vì link "Đăng ký" nằm
cạnh nút CTA phải chuyển được sang tab đăng ký.
"""

import streamlit as st

from db import bao_mat, repo
from ui import blocks as b
from ui import data as d
from ui import phien
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


def _bao_loi(thong_bao: str) -> None:
    b.spacer(10)
    st.markdown(
        f'<div style="background:#fdf1f1;border:1px solid #f3c9c9;'
        f'border-radius:{t.RADIUS_INPUT}px;padding:11px 14px;'
        f'font-size:14px;color:{t.DANGER}">{thong_bao}</div>',
        unsafe_allow_html=True,
    )


def _kiem_dang_nhap() -> str:
    """Kiểm tra thông tin đăng nhập; trả về chuỗi lỗi, rỗng là thành công."""
    email = (st.session_state.dn_email or "").strip()
    mat_khau = st.session_state.dn_mat_khau or ""
    if not email or not mat_khau:
        return "Nhập đủ email và mật khẩu."

    chuoi_bam = repo.lay_hash_mat_khau(email)
    if not chuoi_bam or not bao_mat.kiem_tra(mat_khau, chuoi_bam):
        # Cố ý dùng CHUNG một câu cho cả hai trường hợp sai email và sai mật
        # khẩu: trả lời khác nhau sẽ giúp người ngoài dò ra email nào đã có
        # tài khoản trong hệ thống.
        return "Email hoặc mật khẩu không đúng."

    phien.dang_nhap(repo.ho_so_theo_email(email))
    return ""


def _dang_nhap() -> None:
    st.text_input("Email", key="dn_email", placeholder="ban@dlu.edu.vn")
    st.text_input("Mật khẩu", type="password", key="dn_mat_khau")
    b.spacer(4)

    loi = ""
    # Mockup: CTA và dòng "Chưa có tài khoản? Đăng ký" nằm CÙNG HÀNG, gap 14px
    with st.container(horizontal=True, vertical_alignment="center",
                      gap="medium"):
        if st.button("Đăng nhập", type="primary", key="cta_login"):
            loi = _kiem_dang_nhap()
            if not loi:
                st.rerun()
        st.markdown(
            f'<span style="font-size:14px;color:{t.MUTED};'
            f'white-space:nowrap">Chưa có tài khoản?</span>',
            unsafe_allow_html=True,
        )
        if st.button("Đăng ký", key="link_register", type="tertiary"):
            _chuyen("register")

    if loi:
        _bao_loi(loi)


def _sinh_hoc_ky() -> list[str]:
    """Chip xem trước: mọi năm trong niên khoá nhân số học kỳ mỗi năm."""
    so = len(d.semesters(st.session_state.so_ky))
    return [f"{nam} HK{k}"
            for nam in d.years(st.session_state.khoa_from,
                               st.session_state.khoa_to)
            for k in range(1, so + 1)]


_TOI_THIEU_MAT_KHAU = 8


def _tao_tai_khoan() -> str:
    """Tạo tài khoản mới rồi đăng nhập luôn.

    Trả về chuỗi lỗi, rỗng nghĩa là đã tạo xong. Niên khoá không lưu thành
    danh sách năm học: cơ sở dữ liệu chỉ giữ năm đầu và năm cuối, danh sách
    suy ra từ đó (xem db/repo.py).
    """
    ten = (st.session_state.ho_ten or "").strip()
    email = (st.session_state.dk_email or "").strip()
    mat_khau = st.session_state.dk_mat_khau or ""

    if not ten:
        return "Nhập họ và tên."
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Email không hợp lệ."
    if len(mat_khau) < _TOI_THIEU_MAT_KHAU:
        return f"Mật khẩu phải từ {_TOI_THIEU_MAT_KHAU} ký tự trở lên."
    if not d.years(st.session_state.khoa_from, st.session_state.khoa_to):
        return ("Niên khoá không hợp lệ — năm kết thúc phải lớn hơn năm bắt "
                "đầu và cách nhau không quá 8 năm.")
    if repo.email_da_dung(email):
        return "Email này đã có tài khoản. Hãy đăng nhập."

    repo.tao_tai_khoan(email, bao_mat.bam(mat_khau), ten,
                       int(st.session_state.khoa_from),
                       int(st.session_state.khoa_to),
                       st.session_state.so_ky)
    phien.dang_nhap(repo.ho_so_theo_email(email))
    return ""


def _dang_ky() -> None:
    st.session_state.ho_ten = st.text_input(
        "Họ và Tên", value=st.session_state.ho_ten)
    st.text_input("Email", key="dk_email")
    st.text_input("Mật khẩu", type="password", key="dk_mat_khau")

    b.spacer(2)
    with st.container(key="auth_khoa"):
        _khoi_nien_khoa()

    # Mockup đặt cụm CTA ngoài panel xám, ngay dưới nó.
    b.spacer(14)
    loi = ""
    with st.container(horizontal=True, vertical_alignment="center",
                      gap="medium"):
        if st.button("Tạo tài khoản", type="primary", key="cta_register"):
            loi = _tao_tai_khoan()
            if not loi:
                st.rerun()
        st.markdown(
            f'<span style="font-size:14px;color:{t.MUTED}">Có thể thêm học kỳ '
            f"mới bất cứ lúc nào sau này.</span>",
            unsafe_allow_html=True,
        )

    if loi:
        _bao_loi(loi)


def _khoi_nien_khoa() -> None:
    """Panel xám gom các thông tin dùng để sinh danh sách học kỳ."""
    st.markdown(
        f'<div style="font-size:14px;color:{t.MUTED};line-height:1.45">'
        "Hệ thống sẽ tự sinh danh sách năm học – học kỳ từ thông tin dưới "
        "đây. Bạn vẫn có thể thêm học kỳ mới sau.</div>",
        unsafe_allow_html=True,
    )
    b.spacer(10)

    c1, c2 = st.columns(2)
    st.session_state.khoa_from = c1.text_input(
        "Niên khoá (từ)", value=st.session_state.khoa_from)
    st.session_state.khoa_to = c2.text_input(
        "Niên khoá (đến)", value=st.session_state.khoa_to)

    c3, c4 = st.columns(2)
    c3.selectbox("Số năm học dự kiến", ["4 năm", "4.5 năm", "5 năm"],
                 key="dk_so_nam", filter_mode=None)
    ky = [2, 3]
    st.session_state.so_ky = c4.selectbox(
        "Số học kỳ mỗi năm", ky, index=ky.index(st.session_state.so_ky),
        format_func=lambda n: f"{n} học kỳ", filter_mode=None)

    # Chip niên khoá: 12px monospace, nền #e8f0fa, bo tròn
    hoc_ky = _sinh_hoc_ky()
    if hoc_ky:
        chip = "".join(f'<span class="mk-chip">{k}</span>' for k in hoc_ky)
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;'
            f'align-items:center;margin-top:8px">'
            f'<span style="font-size:13px;color:{t.MUTED};margin-right:4px">'
            f"Danh sách học kỳ dự kiến:</span>{chip}</div>",
            unsafe_allow_html=True,
        )


def render() -> None:
    # Mockup đặt cả màn auth trên nền xám bo góc, form nằm trong thẻ trắng.
    with st.container(key="auth_wrap"):
        with st.container(key="auth_col"):
            st.markdown(
                '<div class="mk-h1-auth">Chào mừng bạn trở lại</div>'
                f'<div style="font-size:16px;color:{t.MUTED};margin-top:6px">'
                "Đăng nhập để theo dõi điểm và mức nguy cơ của bạn.</div>",
                unsafe_allow_html=True,
            )
            b.spacer(22)

            with st.container(key="auth_card"):
                la_dang_nhap = st.session_state.auth_mode == "login"
                _tabs(la_dang_nhap)

                if la_dang_nhap:
                    _dang_nhap()
                else:
                    _dang_ky()

    b.footer(d.FOOTER)
