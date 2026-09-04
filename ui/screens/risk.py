"""Cảnh báo & Mục tiêu học tập — dùng toàn bộ lịch sử, không phụ thuộc sidebar."""

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import rules
from ui import tokens as t

_CSS = f"""
<style>
  /* Mục tiêu: nút dạng ô chọn, ô đang chọn viền xanh nền #f5f9ff.
     Phải nhắm kèm [kind="secondary"] mới thắng được quy tắc nút toàn cục. */
  [class*="st-key-goal_"] .stButton button[kind="secondary"] {{
    border: 1px solid {t.BORDER} !important;
    background: {t.SURFACE} !important;
    color: {t.TEXT} !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    padding: 11px 14px !important;
    text-align: left !important;
    justify-content: flex-start !important;
  }}
  /* Cùng lý do như nút điều hướng: div bọc nhãn mới là chỗ căn giữa. */
  [class*="st-key-goal_"] .stButton button[kind="secondary"] > div {{
    justify-content: flex-start !important;
    width: 100% !important;
  }}
  [class*="st-key-goal_"] .stButton button[kind="secondary"] p {{
    width: 100%;
    text-align: left !important;
  }}
  .st-key-{{active}} .stButton button[kind="secondary"] {{
    border-color: {t.PRIMARY} !important;
    background: #f5f9ff !important;
  }}
  .st-key-{{active}} .stButton button[kind="secondary"] p {{
    font-weight: 600 !important;
  }}
</style>
"""


def _the_nguy_co() -> None:
    kieu = t.RISK_STYLES[d.RISK_LABEL]
    ly_do = "".join(
        f'<div style="display:flex;gap:10px;align-items:flex-start">'
        f'<div style="width:6px;height:6px;border-radius:50%;'
        f'background:{t.MUTED};margin-top:8px;flex:0 0 6px"></div>'
        f'<div style="font-size:15px;color:{t.TEXT};line-height:1.5">{r}</div>'
        f"</div>"
        for r in d.REASONS
    )
    st.markdown(
        f'<div style="border:1px solid {kieu["border"]};border-radius:'
        f'{t.RADIUS_CARD}px;padding:24px;background:{kieu["bg"]};'
        f'display:flex;flex-direction:column;gap:18px">'

        f'<div style="display:flex;align-items:center;'
        f'justify-content:space-between">'
        f'<span style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f"Mức nguy cơ hiện tại</span>"
        f'<span style="font-size:13px;font-weight:600;padding:4px 12px;'
        f'border-radius:{t.RADIUS_PILL}px;background:{kieu["dot"]};'
        f'color:#fff">{d.RISK_LABEL}</span></div>'

        f'<div style="display:flex;align-items:flex-end;gap:12px">'
        f'<div class="mk-bignum" style="color:{kieu["dot"]}">'
        f"{d.RISK_PCT}%</div>"
        f'<div style="font-size:14px;color:{t.MUTED};padding-bottom:8px">'
        f"xác suất bị cảnh báo học vụ<br/>trong học kỳ tới</div></div>"

        f'{b.bar(d.RISK_PCT, kieu["dot"])}'

        f'<div style="display:flex;flex-direction:column;gap:10px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f"Lý do chính</div>{ly_do}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _the_goi_y() -> None:
    muc = "".join(
        f'<div style="display:flex;gap:12px;align-items:flex-start;'
        f'padding:12px 14px;border:1px solid {t.BORDER};'
        f'border-radius:{t.RADIUS_INPUT}px;background:{t.SURFACE_ALT}">'
        f'<div style="width:22px;height:22px;border-radius:6px;'
        f'background:{t.TIP_BG};color:{t.SUCCESS};font-size:12px;'
        f'font-weight:700;display:flex;align-items:center;'
        f'justify-content:center;flex:0 0 22px">{tp["n"]}</div>'
        f'<div style="display:flex;flex-direction:column;gap:3px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f'{tp["title"]}</div>'
        f'<div style="font-size:14px;color:{t.MUTED};line-height:1.45">'
        f'{tp["detail"]}</div></div></div>'
        for tp in d.TIPS
    )
    st.markdown(
        f'<div class="mk-card" style="display:flex;flex-direction:column;'
        f'gap:14px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f"Gợi ý cải thiện</div>{muc}</div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    khoa = st.session_state.goal
    st.markdown(_CSS.replace("{active}", f"goal_{list(d.GOALS).index(khoa)}"),
                unsafe_allow_html=True)

    b.page_title("Cảnh báo & Mục tiêu học tập", d.RISK_UPDATED)
    b.spacer(26)

    # Lưới 1.15fr / 1fr như mockup
    trai, phai = st.columns([1.15, 1], vertical_alignment="top")
    with trai:
        _the_nguy_co()
    with phai:
        _the_goi_y()

    b.spacer(26)

    with st.container(border=True):
        st.markdown('<div class="mk-h2">Mục tiêu học tập của bạn</div>',
                    unsafe_allow_html=True)
        b.spacer(18)

        chon, ket_qua = st.columns([1, 1.2], vertical_alignment="top")
        with chon:
            st.markdown(f'<div style="font-size:14px;font-weight:600;'
                        f'color:{t.TEXT};margin-bottom:10px">Bạn muốn đạt'
                        "</div>", unsafe_allow_html=True)
            for i, (ten, g) in enumerate(d.GOALS.items()):
                if st.button(f"{ten}    ·    {g['hint']}", key=f"goal_{i}",
                             width="stretch"):
                    st.session_state.goal = ten
                    st.rerun()

        with ket_qua:
            g = d.GOALS[khoa]
            # Màu theo % khả năng đạt, không gán cứng cho từng mục tiêu.
            mau = rules.goal_color(g["pct"])
            st.markdown(
                f'<div style="padding:20px;border-radius:{t.RADIUS_CARD}px;'
                f'background:{t.PANEL_BG};border:1px solid {t.BORDER};'
                f'display:flex;flex-direction:column;gap:14px">'
                f'<div style="font-size:14px;color:{t.MUTED}">Khả năng đạt '
                f'mục tiêu <span class="mk-strong">{khoa}</span></div>'
                f'<div style="display:flex;align-items:flex-end;gap:10px">'
                f'<div class="mk-bignum-sm" style="color:{mau}">'
                f'{g["pct"]}%</div>'
                f'<div style="font-size:14px;color:{t.MUTED};'
                f'padding-bottom:6px">nếu giữ nhịp học hiện tại</div></div>'
                f'{b.bar(g["pct"], mau)}'
                f'<div style="font-size:14px;color:{t.TEXT};line-height:1.5">'
                f'{g["note"]}</div></div>',
                unsafe_allow_html=True,
            )

    b.footer(d.FOOTER)
