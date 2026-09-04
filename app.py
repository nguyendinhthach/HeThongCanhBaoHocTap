"""Hệ thống cảnh báo sớm nguy cơ học tập — giao diện Streamlit.

Giai đoạn này chỉ dựng giao diện theo docs/mockups/: mọi số liệu là dữ liệu
tĩnh trong ui/data.py, chưa có nghiệp vụ, chưa nối cơ sở dữ liệu, chưa gắn mô
hình học máy.

Chạy:  streamlit run app.py
"""

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import rules
from ui import styles
from ui import tokens as t
from ui.screens import add_course, auth, dashboard, risk

st.set_page_config(
    page_title="Cảnh báo nguy cơ học tập",
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
    # Môn học phải ở session_state chứ không phải hằng số cấp module: sửa/xoá
    # của phiên này không được ảnh hưởng tab khác.
    "courses": None,          # nạp bằng seed_courses() trong _init
    "editing_id": None,
    "confirm_id": None,
    "form_rows": None,
    # Trạng thái form, bình thường do _nap_form đặt; để mặc định ở đây phòng
    # phiên cũ còn sót editing_id mà thiếu các khoá đi kèm.
    "f_code": "",
    "f_attempt_no": 1,
    "f_year": None,
    "f_sem": None,
    # Năm học: đăng ký sinh ra từ niên khoá, sau đó nới thêm bằng form
    # "Thêm năm học mới". Học kỳ không nằm ở đây vì suy từ so_ky.
    "year_list": list(d.YEARS),
    "add_year_open": False,
}


def _init() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state.setdefault(k, v)
    if st.session_state.courses is None:
        st.session_state.courses = d.seed_courses()
    if st.session_state.form_rows is None:
        st.session_state.form_rows = d.form_rows_moi()


def _doi_ky() -> None:
    st.session_state.nam_hoc = st.session_state.sel_nam
    st.session_state.hoc_ky = st.session_state.sel_ky


def _di_toi(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()


def _chi_so(chuoi) -> str:
    """Giữ lại tối đa 4 chữ số — ô năm trong mockup chỉ nhận số."""
    return "".join(c for c in str(chuoi) if c.isdigit())[:4]


def _sua_nam_bat_dau() -> None:
    """Nhập đủ 4 số ở năm bắt đầu thì tự điền năm kết thúc kề sau."""
    tu = _chi_so(st.session_state.nt_from)
    st.session_state.nt_from = tu
    if len(tu) == 4:
        st.session_state.nt_to = str(int(tu) + 1)


def _sua_nam_ket_thuc() -> None:
    st.session_state.nt_to = _chi_so(st.session_state.nt_to)


def _mo_them_nam() -> None:
    """Mở form với năm gợi ý nối tiếp năm học cuối trong danh sách."""
    cuoi = st.session_state.year_list[-1] if st.session_state.year_list else ""
    so = [x for x in cuoi.replace("–", "-").split("-") if x.strip().isdigit()]
    tu = int(so[-1]) if so else 2025
    st.session_state.add_year_open = True
    st.session_state.nt_from = str(tu)
    st.session_state.nt_to = str(tu + 1)
    st.rerun()


def _form_them_nam() -> None:
    """Chỉ nhập năm — học kỳ suy từ hồ sơ nên không có gì để chọn ở đây."""
    with st.container(key="add_term_box"):
        st.markdown('<div style="font-size:13px;font-weight:600;'
                    f'color:{t.TEXT}">Thêm năm học</div>',
                    unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.text_input("Năm bắt đầu", key="nt_from", placeholder="2027",
                      on_change=_sua_nam_bat_dau)
        c2.text_input("Năm kết thúc", key="nt_to", placeholder="2028",
                      on_change=_sua_nam_ket_thuc)

        kt = rules.validate_year(st.session_state.nt_from,
                                 st.session_state.nt_to,
                                 st.session_state.year_list)
        if kt["loi"]:
            st.markdown(f'<div style="font-size:12px;color:{t.DANGER};'
                        f'line-height:1.4">{kt["loi"]}</div>',
                        unsafe_allow_html=True)
        else:
            ky = d.semesters(st.session_state.so_ky)
            st.markdown(f'<div style="font-size:12px;color:{t.MUTED};'
                        f'line-height:1.4">Năm học mới sẽ có sẵn '
                        f'{len(ky)} học kỳ: {", ".join(ky)}.</div>',
                        unsafe_allow_html=True)

        # Nút Lưu xám và không bấm được khi chưa hợp lệ, đúng như mockup.
        # Phải kèm [kind="primary"] mới thắng được quy tắc nút toàn cục.
        mau = t.BRAND if kt["ok"] else t.DISABLED
        st.markdown(
            '<style>.st-key-btn_save_term .stButton button[kind="primary"]{'
            f"background:{mau} !important;border-color:{mau} !important;"
            f"color:{t.SURFACE} !important;opacity:1 !important;}}</style>",
            unsafe_allow_html=True,
        )
        n1, n2 = st.columns(2)
        if n1.button("Lưu", key="btn_save_term", type="primary",
                     disabled=not kt["ok"], width="stretch"):
            st.session_state.year_list.append(kt["nhan"])
            st.session_state.nam_hoc = kt["nhan"]
            st.session_state.hoc_ky = d.semesters(st.session_state.so_ky)[0]
            st.session_state.add_year_open = False
            st.rerun()
        if n2.button("Huỷ", key="btn_cancel_term", width="stretch"):
            st.session_state.add_year_open = False
            st.rerun()


def _sidebar() -> None:
    """Chỉ gọi khi đã đăng nhập — mockup ẩn hẳn sidebar ở màn auth."""
    with st.sidebar:
        b.sidebar_brand("TRƯỜNG ĐẠI HỌC ĐÀ LẠT", "Dalat University")
        b.spacer(28)

        st.markdown(styles.nav_active_css(st.session_state.screen),
                    unsafe_allow_html=True)
        st.markdown('<div class="mk-side-label">Chức năng</div>',
                    unsafe_allow_html=True)
        with st.container(key="nav_group"):
            for khoa, nhan in d.SCREENS.items():
                if st.button(nhan, key=f"nav_{khoa}", width="stretch"):
                    _di_toi(khoa)

        st.markdown(f'<div style="height:1px;background:{t.BORDER_SOFT};'
                    'margin:28px 0"></div>', unsafe_allow_html=True)

        # Trang "Cảnh báo & Mục tiêu" dùng toàn bộ lịch sử nên không chọn kỳ.
        if st.session_state.screen in ("dashboard", "add"):
            st.markdown('<div class="mk-side-label">Kỳ học đang xem</div>',
                        unsafe_allow_html=True)
            # Đồng bộ key rồi để on_change cập nhật, không truyền index=: nếu
            # truyền index mà không có key thì mỗi lần index đổi Streamlit coi
            # là widget mới rồi nhảy về lựa chọn cũ, phải bấm hai lần.
            ky_co = d.semesters(st.session_state.so_ky)
            # Đổi số học kỳ mỗi năm có thể làm kỳ đang xem biến mất (ví dụ
            # đang ở HK3 rồi hồ sơ rút còn 2 kỳ) — chốt lại về kỳ đầu tiên
            # thay vì để selectbox rơi vào giá trị không có trong danh sách.
            if st.session_state.hoc_ky not in ky_co:
                st.session_state.hoc_ky = ky_co[0]

            st.session_state.sel_nam = st.session_state.nam_hoc
            st.session_state.sel_ky = st.session_state.hoc_ky
            st.selectbox("Năm học", st.session_state.year_list, key="sel_nam",
                         on_change=_doi_ky, filter_mode=None)
            st.selectbox("Học kỳ", ky_co, key="sel_ky",
                         on_change=_doi_ky, filter_mode=None)

            if st.session_state.add_year_open:
                _form_them_nam()
            elif st.button("+ Thêm năm học mới", key="btn_add_term",
                           type="tertiary"):
                _mo_them_nam()

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
    b.header_bar("HỆ THỐNG CẢNH BÁO NGUY CƠ HỌC TẬP")

    if not st.session_state.logged_in:
        # Màn đăng nhập chiếm trọn bề ngang: không dựng sidebar, đồng thời ẩn
        # khung rỗng Streamlit vẫn chừa sẵn cho nó.
        styles.hide_sidebar()
        auth.render()
        return

    _sidebar()

    {"dashboard": dashboard.render,
     "add": add_course.render,
     "risk": risk.render}[st.session_state.screen]()


if __name__ == "__main__":
    main()
