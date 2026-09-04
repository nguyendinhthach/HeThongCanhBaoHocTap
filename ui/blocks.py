"""Khối HTML dựng theo đúng style trong mockup.

Dùng HTML cho phần thuần hiển thị (thẻ chỉ số, bảng, nhãn, thanh tiến trình)
vì widget gốc của Streamlit không tái hiện được lưới và bo góc của mockup.
Phần cần tương tác vẫn dùng widget Streamlit.
"""

import base64
import html
import pathlib

import streamlit as st

from ui import rules
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


# Tỉ lệ cột của hai bảng, giữ đúng lưới mockup.
_COT_DS = "112px 2.3fr 0.9fr 1.1fr 1.4fr"
_COT_KY = [0.95, 2.0, 0.7, 0.85, 0.95, 1.2, 1.4]


def course_table(courses, scale: int = 10) -> None:
    """Bảng môn học ở Dashboard — chỉ để xem nên dựng thẳng bằng HTML."""
    thang = f"DH{scale}"
    dau = (
        f'<div class="mk-thead" style="grid-template-columns:{_COT_DS}">'
        "<div>Mã MH</div><div>Tên môn học</div>"
        '<div style="text-align:right">Tín chỉ</div>'
        f'<div style="text-align:right">Điểm tổng kết ({thang})</div>'
        "<div>Trạng thái</div></div>"
    )

    than = ""
    for i, c in enumerate(courses):
        nen = t.ROW_ALT if i % 2 else t.SURFACE
        diem = rules.diem_mon(c)
        du = rules.du_trong_so(c)
        # Chỉ gắn cờ nguy cơ khi đã đủ trọng số: điểm tạm tính chưa kết luận.
        canh_bao = (f'<span style="color:{t.DANGER};font-size:14px;'
                    f'margin-right:7px" title="Nguy cơ cao">⚠</span>'
                    if du and diem is not None and diem < t.GRADE_FAIL else "")
        than += (
            f'<div class="mk-trow" style="grid-template-columns:{_COT_DS};'
            f'background:{nen}">'
            f'<div class="mk-idx">{_esc(c.get("code") or "—")}</div>'
            f'<div>{canh_bao}{_esc(c["name"])}</div>'
            f'<div class="mk-num">{c["credits"]}</div>'
            f'<div class="mk-num" style="font-weight:600;'
            f'color:{rules.grade_color(diem, du)}">'
            f'{_esc(rules.grade_text(diem, du, scale))}</div>'
            f'<div style="padding:9px 12px">'
            f'{attempt_tag(rules.lan_hoc(c))}</div>'
            "</div>"
        )

    if not courses:
        than = ('<div class="mk-empty">Chưa có môn học nào trong học kỳ này.'
                "</div>")

    st.markdown(f'<div class="mk-table">{dau}{than}</div>',
                unsafe_allow_html=True)


def _o(cot, noi_dung: str, canh: str = "left", **kieu) -> None:
    """Một ô trong bảng dựng bằng st.columns."""
    them = ";".join(f"{k.replace('_', '-')}:{v}" for k, v in kieu.items())
    cot.markdown(
        f'<div style="font-size:15px;color:{t.TEXT};text-align:{canh};'
        f'{them}">{noi_dung}</div>', unsafe_allow_html=True)


def semester_table(courses, on_edit, on_delete, dang_sua=None) -> None:
    """Bảng 'Môn học đã thêm' — dựng bằng st.columns vì cần nút bấm được.

    Không dùng HTML như bảng Dashboard được: HTML trong st.markdown không gọi
    ngược về Python, nên Sửa/Xoá bắt buộc phải là widget thật.

    Bảng này hiện cố định cả DH10 lẫn DH4 nên không nhận tham số thang: nút
    DH10/DH4 chỉ điều khiển Dashboard.
    """
    # Nền so le và nền dòng đang sửa gom vào một thẻ style, phát một lần.
    nen = "".join(
        f'.st-key-semrow_{c["id"]}{{background:'
        f'{"#f5f9ff" if c["id"] == dang_sua else t.ROW_ALT if i % 2 else t.SURFACE}'
        "}"
        for i, c in enumerate(courses)
    )
    st.markdown(f"<style>{nen}</style>", unsafe_allow_html=True)

    with st.container(key="semtable"):
        with st.container(key="semhead"):
            cot = st.columns(_COT_KY, vertical_alignment="center")
            for c, nhan, canh in zip(
                    cot,
                    ["Mã MH", "Tên môn học", "Tín chỉ", "DH10", "DH4",
                     "Lần học", "Thao tác"],
                    ["left", "left", "right", "right", "right", "left",
                     "center"]):
                c.markdown(f'<div style="font-size:13px;font-weight:600;'
                           f'color:{t.MUTED};text-align:{canh}">{nhan}</div>',
                           unsafe_allow_html=True)

        if not courses:
            st.markdown('<div class="mk-empty">Chưa có môn học nào được lưu '
                        "cho học kỳ này.</div>", unsafe_allow_html=True)
            return

        for i, c in enumerate(courses):
            with st.container(key=f'semrow_{c["id"]}'):
                cot = st.columns(_COT_KY, vertical_alignment="center")
                diem = rules.diem_mon(c)
                if diem is None:
                    dh10 = dh4 = "—"
                else:
                    # Dấu * đánh ở DH10 vì đó là điểm gốc; DH4 suy ra từ nó
                    # nên cũng chỉ là tạm tính theo.
                    dh10 = f"{diem:.1f}" + ("" if rules.du_trong_so(c)
                                            else " *")
                    dh4 = f"{rules.to4(diem):.1f} ({rules.chu_cai(diem)})"

                _o(cot[0], _esc(c.get("code") or "—"), color=t.FAINT,
                   font_family=t.MONO, font_size="14px")
                _o(cot[1], _esc(c["name"]))
                _o(cot[2], str(c["credits"]), "right", font_family=t.MONO)
                _o(cot[3], _esc(dh10), "right", font_family=t.MONO,
                   font_weight="600")
                _o(cot[4], _esc(dh4), "right", font_family=t.MONO,
                   color=t.MUTED, font_size="14px")
                _o(cot[5], _esc(rules.lan_hoc(c)), color=t.MUTED,
                   font_size="14px")
                with cot[6]:
                    with st.container(horizontal=True,
                                      horizontal_alignment="center",
                                      key=f'semact_{c["id"]}'):
                        if st.button("Sửa", key=f'edit_{c["id"]}'):
                            on_edit(c)
                        if st.button("Xoá", key=f'del_{c["id"]}'):
                            on_delete(c)


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


# --- Khối mới theo mockup cập nhật -----------------------------------------
# Logo nhúng thẳng dạng data URI: sidebar dựng bằng HTML nên st.image không
# đặt được vào đúng hàng với tên trường.
_LOGO = base64.b64encode(
    (pathlib.Path(__file__).parent / "assets" / "dlu-logo.webp").read_bytes()
).decode()


def header_bar(title: str) -> None:
    """Thanh xanh thương hiệu chạy hết chiều ngang, ghim trên cùng."""
    st.markdown(f'<div class="mk-header">{_esc(title)}</div>',
                unsafe_allow_html=True)


def sidebar_brand(ten: str, phu: str) -> None:
    """Hàng logo + tên trường ở đầu sidebar."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px">'
        f'<img src="data:image/webp;base64,{_LOGO}" alt="Logo {_esc(ten)}" '
        f'style="width:52px;height:52px;flex:0 0 52px;object-fit:contain;'
        f'border-radius:10px" />'
        f'<div style="display:flex;flex-direction:column;line-height:1.25">'
        f'<div style="font-size:14px;font-weight:700;color:{t.TEXT}">'
        f"{_esc(ten)}</div>"
        f'<div style="font-size:12px;color:{t.MUTED}">{_esc(phu)}</div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def weight_box(tong: int) -> None:
    """Hộp trạng thái tổng trọng số — xanh khi đủ, đỏ khi vượt, vàng khi thiếu."""
    k = rules.weight_status(tong)
    st.markdown(
        f'<div style="display:flex;gap:12px;padding:14px 16px;'
        f'border-radius:{t.RADIUS_INPUT}px;background:{k["bg"]};'
        f'border:1px solid {k["border"]};align-items:flex-start">'
        f'<div style="width:20px;height:20px;border-radius:50%;'
        f'background:{k["dot"]};color:#fff;font-size:13px;font-weight:700;'
        f'display:flex;align-items:center;justify-content:center;'
        f'flex:0 0 20px;line-height:1">{k["icon"]}</div>'
        f'<div style="font-size:14px;color:{t.TEXT};line-height:1.5">'
        f'{_esc(k["text"])}</div></div>',
        unsafe_allow_html=True,
    )


def dup_hint(text: str, ky: str) -> None:
    """Cảnh báo vàng khi tên môn trùng môn đã học ở kỳ trước."""
    st.markdown(
        f'<div style="display:flex;gap:9px;align-items:flex-start;'
        f'padding:10px 12px;border:1px solid #f0dfae;background:#fffaef;'
        f'border-radius:{t.RADIUS_INPUT}px;margin-top:2px">'
        f'<span style="font-size:14px;color:{t.WARNING};line-height:1.4">⚠'
        f"</span>"
        f'<div style="display:flex;flex-direction:column;gap:3px">'
        f'<div style="font-size:13px;color:{t.TEXT};line-height:1.5">'
        f"{_esc(text)}</div>"
        f'<div style="font-size:12px;color:{t.WARNING_TEXT};line-height:1.5">'
        f"Bản ghi của lần học trước không bị sửa hay ghi đè — hệ thống tạo "
        f"thêm 1 dòng mới gắn với {_esc(ky)}.</div></div></div>",
        unsafe_allow_html=True,
    )
