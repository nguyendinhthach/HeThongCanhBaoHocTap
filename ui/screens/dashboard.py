"""Dashboard — thẻ chỉ số, bảng môn học, biểu đồ xu hướng GPA."""

import altair as alt
import pandas as pd
import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import tokens as t

# Nhóm chuyển thang: nền #f0f2f6, padding 3, mỗi nút 7px 14px, nút đang chọn
# nền trắng kèm đổ bóng nhẹ — theo mockup.
_CSS = f"""
<style>
  .st-key-scale_group {{
    background: {t.SIDEBAR_BG};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_INPUT}px;
    padding: 3px !important;
    gap: 3px !important;
  }}
  .st-key-scale_10 .stButton button[kind="secondary"],
  .st-key-scale_4 .stButton button[kind="secondary"] {{
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: {t.RADIUS_SMALL}px !important;
    padding: 7px 14px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    color: {t.MUTED} !important;
  }}
  .st-key-{{active}} .stButton button[kind="secondary"] {{
    background: {t.SURFACE} !important;
    color: {t.PRIMARY} !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08) !important;
  }}
  .st-key-btn_add button {{
    padding: 10px 18px !important;
    font-size: 14px !important;
  }}
</style>
"""


def _chart(scale: int) -> alt.LayerChart:
    """Đường GPA theo học kỳ; điểm đang xem tô rỗng viền cam như mockup."""
    df = pd.DataFrame(d.GPA_SERIES)
    toi_da = 4 if scale == 4 else 10
    if scale == 4:
        df["gpa"] = (df["gpa"] / 10 * 4).round(2)

    x = alt.X("ky:N", sort=None, title=None,
              axis=alt.Axis(labelAngle=0, labelFontSize=13,
                            labelColor=t.MUTED, domain=False, ticks=False))
    y = alt.Y("gpa:Q", title=f"GPA (thang {toi_da})",
              scale=alt.Scale(domain=[0, toi_da], nice=False),
              axis=alt.Axis(values=list(range(0, toi_da + 1,
                                              1 if scale == 4 else 2)),
                            labelFontSize=13, labelColor=t.FAINT,
                            titleFontSize=13, titleColor=t.MUTED,
                            gridColor=t.ROW_LINE, domain=False, ticks=False))

    duong = alt.Chart(df).mark_line(color=t.PRIMARY, strokeWidth=3).encode(x, y)
    diem = alt.Chart(df).mark_point(size=130, filled=True).encode(
        x, y,
        color=alt.condition(alt.datum.dang_xem, alt.value(t.SURFACE),
                            alt.value(t.PRIMARY)),
        stroke=alt.condition(alt.datum.dang_xem, alt.value(t.WARNING),
                             alt.value(t.PRIMARY)),
        strokeWidth=alt.condition(alt.datum.dang_xem, alt.value(4),
                                  alt.value(0)),
        tooltip=[alt.Tooltip("ky:N", title="Học kỳ"),
                 alt.Tooltip("gpa:Q", title="GPA")],
    )
    nhan = alt.Chart(df).mark_text(dy=-18, fontSize=13, fontWeight="bold",
                                   color=t.TEXT, font="Source Code Pro").encode(
        x, y, text=alt.Text("gpa:Q", format=".2f"))

    return (duong + diem + nhan).properties(height=260).configure_view(
        strokeWidth=0)


def render() -> None:
    scale = st.session_state.scale
    st.markdown(_CSS.replace("{active}", f"scale_{scale}"),
                unsafe_allow_html=True)

    # --- Hàng tiêu đề: tiêu đề trái, điều khiển phải ----------------------
    trai, phai = st.columns([2, 1], vertical_alignment="bottom")
    with trai:
        b.page_title(
            "Tổng quan học tập",
            f'Đang xem <span class="mk-strong">{st.session_state.nam_hoc} · '
            f"{st.session_state.hoc_ky}</span>",
        )
    with phai:
        with st.container(horizontal=True, horizontal_alignment="right",
                          vertical_alignment="center", gap="medium"):
            with st.container(horizontal=True, key="scale_group"):
                if st.button("Thang 10", key="scale_10"):
                    st.session_state.scale = 10
                    st.rerun()
                if st.button("Thang 4", key="scale_4"):
                    st.session_state.scale = 4
                    st.rerun()
            if st.button("+ Thêm môn học", key="btn_add"):
                st.session_state.screen = "add"
                st.rerun()

    b.spacer(t.SHELL_GAP)
    b.metrics(d.METRICS)
    b.spacer(t.SHELL_GAP)

    # --- Bảng môn học -----------------------------------------------------
    b.section_title("Danh sách môn học")
    b.spacer(12)
    b.course_table(d.COURSES)
    b.spacer(8)
    b.note(d.COURSE_FOOTNOTE)

    # --- Biểu đồ ----------------------------------------------------------
    b.spacer(t.SHELL_GAP)
    thang = "thang 4" if scale == 4 else "thang 10"
    b.section_title("Xu hướng điểm trung bình học kỳ",
                    f"Dữ liệu lưu theo thang 10 · đang hiển thị {thang}")
    st.markdown(
        f'<div style="font-size:13px;color:{t.MUTED};margin-top:3px">'
        "Hiển thị toàn bộ các học kỳ đã có dữ liệu; kỳ đang chọn ở sidebar "
        "được đánh dấu bằng điểm tô sáng.</div>",
        unsafe_allow_html=True,
    )
    b.spacer(12)
    with st.container(border=True):
        st.altair_chart(_chart(scale), width="stretch")

    b.footer(d.FOOTER)
