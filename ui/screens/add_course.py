"""Thêm / cập nhật môn học — form nhập điểm thành phần + bảng môn đã lưu."""

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import tokens as t

_CSS = f"""
<style>
  /* Nhãn chế độ form: viên thuốc xanh nhạt */
  .mk-mode {{
    display: inline-block; font-size: 13px; font-weight: 600;
    color: {t.PRIMARY_DARK}; background: {t.CHIP_BG};
    border-radius: {t.RADIUS_PILL}px; padding: 5px 14px;
  }}
  /* Ô "Lần học" chỉ đọc */
  .mk-readonly {{
    background: {t.SIDEBAR_BG}; border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_INPUT}px; padding: 10px 12px;
    font-size: 15px; color: {t.MUTED};
  }}
  /* Nút thêm dòng: viền nét đứt */
  .st-key-btn_addrow button {{
    border: 1px dashed {t.BORDER_DASH} !important;
    background: {t.SURFACE} !important;
    color: {t.PRIMARY} !important;
    font-size: 14px !important; font-weight: 600 !important;
    padding: 9px 16px !important;
  }}
  /* Nút xoá dòng: ô vuông 28px */
  [class*="st-key-rmrow_"] button {{
    border: 1px solid {t.BORDER} !important;
    color: {t.FAINT} !important;
    padding: 2px 0 !important; min-height: 34px !important;
    border-radius: {t.RADIUS_SMALL}px !important;
  }}
</style>
"""


def _form() -> None:
    with st.container(border=True):
        # Hàng đầu: nhãn chế độ + link thu gọn
        dau, cuoi = st.columns([3, 1], vertical_alignment="center")
        dau.markdown('<span class="mk-mode">Thêm môn học mới</span>',
                     unsafe_allow_html=True)
        if cuoi.button("Thu gọn", key="btn_collapse", type="tertiary"):
            st.session_state.form_open = False
            st.rerun()

        b.spacer(16)

        # Lưới 1fr 1fr 1fr — tên môn chiếm 2 cột như mockup
        c1, c2 = st.columns([2, 1])
        c1.text_input("Tên môn học", key="f_name",
                      placeholder="VD: Trí tuệ nhân tạo")
        c2.number_input("Số tín chỉ", min_value=1, max_value=12, value=3,
                        step=1, key="f_credits")

        c3, c4 = st.columns([1, 2])
        with c3:
            st.markdown('<div style="font-size:14px;font-weight:600;'
                        f'color:{t.TEXT};margin-bottom:6px">Lần học</div>'
                        '<div class="mk-readonly">Lần 1 (tự động)</div>',
                        unsafe_allow_html=True)
        c4.selectbox("Loại lần học", t.ATTEMPT_TYPES, key="f_attempt")

        st.markdown(f'<div style="height:1px;background:{t.ROW_LINE};'
                    'margin:22px 0"></div>', unsafe_allow_html=True)

        # --- Điểm thành phần ---------------------------------------------
        tr, ph = st.columns([2, 1], vertical_alignment="center")
        tr.markdown('<div class="mk-h3">Điểm thành phần</div>',
                    unsafe_allow_html=True)
        ph.markdown(
            f'<div style="font-size:14px;color:{t.MUTED};text-align:right">'
            f'Tổng trọng số: <strong style="font-family:{t.MONO};'
            f'color:{t.SUCCESS};font-weight:600">{d.WEIGHT_TOTAL}%</strong>'
            "</div>",
            unsafe_allow_html=True,
        )
        b.spacer(12)

        ty_le = [2, 1, 1, 0.45]
        tieu_de = st.columns(ty_le)
        for cot, nhan in zip(tieu_de, ["Loại thành phần", "Trọng số (%)",
                                       "Điểm số", ""]):
            cot.markdown(f'<div style="font-size:13px;font-weight:600;'
                         f'color:{t.MUTED}">{nhan}</div>',
                         unsafe_allow_html=True)

        for i, r in enumerate(d.FORM_ROWS):
            cot = st.columns(ty_le, vertical_alignment="bottom")
            cot[0].selectbox("Loại", t.COMPONENT_TYPES,
                             index=t.COMPONENT_TYPES.index(r["loai"]),
                             key=f"row_type_{i}", label_visibility="collapsed")
            cot[1].number_input("Trọng số", value=int(r["trong_so"]),
                                min_value=0, max_value=100, step=5,
                                format="%d", key=f"row_w_{i}",
                                label_visibility="collapsed")
            cot[2].number_input("Điểm", value=r["diem"], min_value=0.0,
                                max_value=10.0, step=0.1, format="%.1f",
                                key=f"row_s_{i}", label_visibility="collapsed",
                                placeholder="chưa nhập")
            cot[3].button("✕", key=f"rmrow_{i}", help="Xoá dòng")

        b.spacer(12)
        with st.container(horizontal=True, vertical_alignment="center",
                          gap="medium"):
            st.button("+ Thêm dòng thành phần", key="btn_addrow")
            st.markdown(
                f'<span style="font-size:13px;color:{t.FAINT}">Danh sách loại: '
                f'{", ".join(t.COMPONENT_TYPES)}</span>',
                unsafe_allow_html=True)

        b.spacer(12)
        st.warning(d.PROVISIONAL_TEXT, icon="⚠️")

        b.spacer(4)
        with st.container(horizontal=True, vertical_alignment="center",
                          gap="medium"):
            st.button("Lưu môn học", type="primary", key="btn_save")
            st.button("Huỷ", key="btn_cancel")


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    b.page_title(
        "Thêm / cập nhật môn học",
        "Nhập điểm thành phần để hệ thống tính điểm tổng kết và cập nhật mức "
        "nguy cơ.",
    )
    st.markdown(
        f'<div style="font-size:14px;color:{t.MUTED};margin-top:6px">'
        f'Đang thêm môn cho: <span class="mk-strong">Năm học '
        f"{st.session_state.nam_hoc} · {st.session_state.hoc_ky}</span> "
        f'<span style="color:{t.FAINT}">(đổi ở sidebar bên trái nếu muốn thêm '
        "cho kỳ khác)</span></div>",
        unsafe_allow_html=True,
    )
    b.spacer(26)

    if not st.session_state.form_open:
        if st.button("+ Thêm môn học", type="primary", key="btn_open_form"):
            st.session_state.form_open = True
            st.rerun()
    else:
        _form()

    b.spacer(26)
    b.section_title("Môn học đã thêm trong học kỳ này",
                    f"{st.session_state.nam_hoc} · {st.session_state.hoc_ky}")
    b.spacer(12)
    b.semester_table(d.SEMESTER_COURSES)

    b.footer(d.FOOTER)
