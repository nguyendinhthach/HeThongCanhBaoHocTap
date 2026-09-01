"""Khối HTML dựng theo đúng style trong mockup.

Dùng HTML cho phần thuần hiển thị (thẻ chỉ số, bảng, nhãn, thanh tiến trình)
vì widget gốc của Streamlit không tái hiện được lưới và bo góc của mockup.
Phần cần tương tác vẫn dùng widget Streamlit.
"""

import html

import streamlit as st

from ui import tokens as t


def _esc(x) -> str:
    return html.escape(str(x))


def page_title(title: str, subtitle: str = "") -> None:
    """Tiêu đề trang: 32px/700 + phụ đề 15px."""
    khoi = f'<div class="mk-h1">{_esc(title)}</div>'
    if subtitle:
        khoi += f'<div class="mk-sub">{subtitle}</div>'
    st.markdown(khoi, unsafe_allow_html=True)


def section_title(title: str, note: str = "") -> None:
    """Tiêu đề khối 20px/600, kèm chú thích cùng dòng nếu có."""
    phu = (f'<span class="mk-note" style="margin-left:10px">{note}</span>'
           if note else "")
    st.markdown(
        f'<div style="display:flex;align-items:baseline">'
        f'<span class="mk-h2">{_esc(title)}</span>{phu}</div>',
        unsafe_allow_html=True,
    )


def metrics(items) -> None:
    """Lưới 4 thẻ chỉ số, gap 18px."""
    the = "".join(
        f'<div class="mk-metric">'
        f'<div class="mk-metric-label">{_esc(m["label"])}</div>'
        f'<div class="mk-metric-value" style="color:{m["color"]}">'
        f'{_esc(m["value"])}</div>'
        f'<div class="mk-metric-delta" style="color:{m["delta_color"]}">'
        f'{_esc(m["delta"])}</div>'
        f"</div>"
        for m in items
    )
    st.markdown(f'<div class="mk-metrics">{the}</div>', unsafe_allow_html=True)


def attempt_tag(nhan: str) -> str:
    """Nhãn viên thuốc cho loại lần học."""
    loai = nhan.split("·")[-1].strip()
    kieu = t.ATTEMPT_STYLES.get(loai, t.ATTEMPT_STYLES["Học lần 1"])
    return (f'<span class="mk-tag" style="background:{kieu["bg"]};'
            f'color:{kieu["color"]}">{_esc(nhan)}</span>')


def course_table(courses) -> None:
    """Bảng môn học — lưới 44px 2.4fr 0.9fr 1.1fr 1.4fr như mockup."""
    cot = "44px 2.4fr 0.9fr 1.1fr 1.4fr"

    dau = (
        f'<div class="mk-thead" style="grid-template-columns:{cot}">'
        "<div>#</div><div>Tên môn học</div>"
        '<div style="text-align:right">Tín chỉ</div>'
        '<div style="text-align:right">Điểm tổng kết (thang 10)</div>'
        "<div>Trạng thái</div></div>"
    )

    than = ""
    for i, c in enumerate(courses):
        nen = t.ROW_ALT if i % 2 else t.SURFACE
        canh_bao = (f'<span style="color:{t.DANGER};font-size:14px;'
                    f'margin-right:7px" title="Nguy cơ cao">⚠</span>'
                    if c["warn"] else "")
        than += (
            f'<div class="mk-trow" style="grid-template-columns:{cot};'
            f'background:{nen}">'
            f'<div class="mk-idx">{i + 1}</div>'
            f'<div>{canh_bao}{_esc(c["name"])}</div>'
            f'<div class="mk-num">{c["credits"]}</div>'
            f'<div class="mk-num" style="font-weight:600;'
            f'color:{c["grade_color"]}">{_esc(c["grade"])}</div>'
            f'<div style="padding:9px 12px">{attempt_tag(c["attempt"])}</div>'
            "</div>"
        )

    st.markdown(f'<div class="mk-table">{dau}{than}</div>',
                unsafe_allow_html=True)


def semester_table(courses) -> None:
    """Bảng 'Môn học đã thêm' — thêm cột Thao tác 150px."""
    cot = "44px 2.4fr 0.9fr 1.1fr 1.3fr 150px"

    dau = (
        f'<div class="mk-thead" style="grid-template-columns:{cot}">'
        "<div>#</div><div>Tên môn học</div>"
        '<div style="text-align:right">Tín chỉ</div>'
        '<div style="text-align:right">Điểm tổng kết</div>'
        "<div>Lần học</div>"
        '<div style="text-align:center">Thao tác</div></div>'
    )

    nut = (
        '<div style="padding:8px 12px;display:flex;gap:8px;'
        'justify-content:center">'
        f'<span style="border:1px solid {t.BORDER_INPUT};border-radius:6px;'
        f'padding:6px 14px;font-size:13px;font-weight:600;color:{t.PRIMARY};'
        f'background:{t.SURFACE}">Sửa</span>'
        f'<span style="border:1px solid {t.BORDER_INPUT};border-radius:6px;'
        f'padding:6px 14px;font-size:13px;font-weight:600;color:{t.DANGER};'
        f'background:{t.SURFACE}">Xoá</span></div>'
    )

    than = ""
    for i, c in enumerate(courses):
        nen = t.ROW_ALT if i % 2 else t.SURFACE
        than += (
            f'<div class="mk-trow" style="grid-template-columns:{cot};'
            f'background:{nen}">'
            f'<div class="mk-idx">{i + 1}</div>'
            f'<div>{_esc(c["name"])}</div>'
            f'<div class="mk-num">{c["credits"]}</div>'
            f'<div class="mk-num" style="font-weight:600">'
            f'{_esc(c["grade"])}</div>'
            f'<div style="font-size:14px;color:{t.MUTED}">'
            f'{_esc(c["attempt"])}</div>'
            f"{nut}</div>"
        )

    st.markdown(f'<div class="mk-table">{dau}{than}</div>',
                unsafe_allow_html=True)


def bar(pct: int, mau: str) -> str:
    """Thanh tiến trình đặc, cao 12px, bo tròn."""
    return (f'<div class="mk-bar"><div style="width:{pct}%;'
            f'background:{mau}"></div></div>')


def note(text: str) -> None:
    st.markdown(f'<div class="mk-note">{text}</div>', unsafe_allow_html=True)


def footer(text: str) -> None:
    st.markdown(f'<div class="mk-footer">{_esc(text)}</div>',
                unsafe_allow_html=True)


def spacer(px: int = 28) -> None:
    """Khoảng cách dọc giữa các khối — mockup dùng gap 28px."""
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)
