"""Trạng thái phiên đăng nhập và việc nạp dữ liệu từ cơ sở dữ liệu.

Trước đây `st.session_state.courses` là kho dữ liệu thật: thêm/sửa/xoá đều
tác động vào đó và đóng tab là mất. Giờ nó chỉ còn là **bản sao tạm** đọc lại
từ cơ sở dữ liệu ở mỗi lần Streamlit chạy lại trang, giữ tên cũ để các màn
hình không phải sửa chỗ đọc.

Sau mỗi thao tác ghi, gọi `nap_mon()` để bản sao khớp lại với cơ sở dữ liệu.
"""

import streamlit as st

from db import repo

# Các khoá thuộc về một người dùng cụ thể, phải dọn sạch khi đăng xuất để
# người đăng nhập sau không thấy sót dữ liệu của người trước.
_KHOA_CUA_PHIEN = (
    "user_id", "ho_ten", "khoa_from", "khoa_to", "so_ky", "scale", "goal",
    "year_list", "courses", "nam_hoc", "hoc_ky", "editing_id", "confirm_id",
    "form_rows", "form_open", "add_year_open",
)


def nap_mon() -> None:
    """Đọc lại toàn bộ môn học của người đang đăng nhập."""
    st.session_state.courses = repo.tat_ca_mon(st.session_state.user_id)


def _ky_mac_dinh(courses: list[dict], year_list: list[str],
                 so_ky: int) -> tuple[str, str]:
    """Kỳ hiện ra ngay sau khi đăng nhập.

    Chọn kỳ gần nhất đã có môn, để vừa vào là thấy dữ liệu chứ không phải một
    trang trống rồi tự đi tìm. Chưa nhập môn nào thì lấy năm đầu niên khoá.
    """
    cac_ky = sorted({(c["year"], c["sem"]) for c in courses})
    if cac_ky:
        return cac_ky[-1]
    nam = year_list[0] if year_list else ""
    return nam, "Học kỳ 1"


def dang_nhap(ho_so: dict) -> None:
    """Đưa hồ sơ vừa đọc từ cơ sở dữ liệu vào phiên làm việc."""
    st.session_state.user_id = ho_so["id"]
    st.session_state.logged_in = True
    st.session_state.ho_ten = ho_so["ho_ten"]
    st.session_state.khoa_from = ho_so["khoa_from"]
    st.session_state.khoa_to = ho_so["khoa_to"]
    st.session_state.so_ky = ho_so["so_ky"]
    st.session_state.scale = ho_so["scale"]
    st.session_state.goal = ho_so["goal"] or "Đạt loại Khá"
    st.session_state.year_list = ho_so["year_list"]

    nap_mon()
    st.session_state.nam_hoc, st.session_state.hoc_ky = _ky_mac_dinh(
        st.session_state.courses, ho_so["year_list"], ho_so["so_ky"])

    st.session_state.screen = "dashboard"
    st.session_state.form_open = False
    st.session_state.editing_id = None
    st.session_state.confirm_id = None


def dang_xuat() -> None:
    """Xoá sạch dấu vết của người dùng hiện tại khỏi phiên."""
    for khoa in _KHOA_CUA_PHIEN:
        st.session_state.pop(khoa, None)
    st.session_state.logged_in = False
    st.session_state.screen = "dashboard"
    st.session_state.auth_mode = "login"


def nien_khoa() -> str:
    """Chuỗi niên khoá hiện ở đáy sidebar, ví dụ "2023–2027"."""
    return f'{st.session_state.khoa_from}–{st.session_state.khoa_to}'
