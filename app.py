"""Hệ thống cảnh báo sớm nguy cơ học tập — giao diện Streamlit.

Giai đoạn này chỉ dựng giao diện theo docs/mockups/: mọi số liệu là dữ liệu
tĩnh trong ui/data.py, chưa có nghiệp vụ, chưa nối cơ sở dữ liệu, chưa gắn mô
hình học máy.

Chạy:  streamlit run app.py
"""

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import styles
from ui import tokens as t
from ui.screens import add_course, auth, dashboard, risk

st.set_page_config(
    page_title="Cảnh báo học tập sớm",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

_DEFAULTS = {
    "screen": "dashboard",
    "logged_in": False,
    "auth_mode": "login",
    "ho_ten": "",
    "khoa_from": "2023",
    "khoa_to": "2027",
    "so_ky": 2,
    "nam_hoc": "2025–2026",
    "hoc_ky": "Học kỳ 1",
    "scale": 10,
    "goal": "Đạt loại Khá",
    "form_open": False,
}


def _init() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state.setdefault(k, v)


def _doi_man_hinh() -> None:
    """Chạy ngay khi bấm điều hướng, trước lúc thân trang render."""
    st.session_state.screen = st.session_state.nav


def _doi_ky() -> None:
    st.session_state.nam_hoc = st.session_state.sel_nam
    st.session_state.hoc_ky = st.session_state.sel_ky


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f'<div style="font-size:20px;font-weight:700;'
            f'letter-spacing:-0.01em;color:{t.BODY_TEXT}">'
            "Cảnh báo học tập sớm</div>"
            f'<div style="font-size:13px;color:{t.MUTED};margin-top:6px">'
            "Hệ thống dự đoán nguy cơ học tập</div>",
            unsafe_allow_html=True,
        )
        b.spacer(28)

        if st.session_state.logged_in:
            # Dùng key + on_change thay vì gán giá trị trả về: nếu truyền
            # index= mà không có key, mỗi lần index đổi Streamlit lại coi là
            # widget mới rồi nhảy về lựa chọn cũ — phải bấm hai lần mới chuyển.
            st.session_state.nav = st.session_state.screen
            st.radio(
                "Điều hướng", list(d.SCREENS), key="nav",
                format_func=lambda k: d.SCREENS[k],
                on_change=_doi_man_hinh,
            )
        else:
            st.markdown(
                f'<div style="font-size:14px;color:{t.MUTED};'
                'line-height:1.55">Theo dõi điểm số từng học kỳ, nhận cảnh báo '
                "sớm khi có nguy cơ trượt môn hoặc bị cảnh báo học vụ, kèm gợi "
                "ý cải thiện cụ thể — tất cả ngay trên hệ thống.</div>",
                unsafe_allow_html=True,
            )

        st.markdown(f'<div style="height:1px;background:{t.BORDER_SOFT};'
                    'margin:28px 0"></div>', unsafe_allow_html=True)

        # Trang "Cảnh báo & Mục tiêu" dùng toàn bộ lịch sử nên không chọn kỳ.
        if st.session_state.logged_in and st.session_state.screen in (
                "dashboard", "add"):
            st.markdown(
                f'<div style="font-size:14px;font-weight:600;color:{t.TEXT};'
                'margin-bottom:8px">Kỳ học đang xem</div>',
                unsafe_allow_html=True)
            # Cùng lý do như phần điều hướng: đồng bộ key rồi để on_change
            # cập nhật, không truyền index=.
            st.session_state.sel_nam = st.session_state.nam_hoc
            st.session_state.sel_ky = st.session_state.hoc_ky
            st.selectbox("Năm học", d.YEARS, key="sel_nam",
                         on_change=_doi_ky)
            st.selectbox("Học kỳ", d.SEMESTERS, key="sel_ky",
                         on_change=_doi_ky)

        if st.session_state.logged_in:
            ten = (st.session_state.ho_ten or "").strip() or d.USER["name"]
            chu_cai = "".join(w[0] for w in ten.split()[-2:]).upper()
            st.markdown(
                f'<div style="margin-top:28px;padding-top:20px;'
                f'border-top:1px solid {t.BORDER_SOFT};display:flex;'
                f'align-items:center;gap:10px">'
                f'<div style="width:36px;height:36px;border-radius:50%;'
                f'background:#dbe6f3;color:{t.PRIMARY_DARK};font-size:14px;'
                f'font-weight:700;display:flex;align-items:center;'
                f'justify-content:center;flex:0 0 36px">{chu_cai}</div>'
                f'<div><div style="font-size:14px;font-weight:600">{ten}</div>'
                f'<div style="font-size:12px;color:{t.MUTED}">Niên khoá '
                f'{d.USER["khoa"]}</div></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Đăng xuất", key="btn_logout", type="tertiary"):
                st.session_state.logged_in = False
                st.session_state.screen = "dashboard"
                st.session_state.auth_mode = "login"
                st.rerun()


def main() -> None:
    _init()
    styles.inject()
    _sidebar()

    if not st.session_state.logged_in:
        auth.render()
        return

    {"dashboard": dashboard.render,
     "add": add_course.render,
     "risk": risk.render}[st.session_state.screen]()


if __name__ == "__main__":
    main()
