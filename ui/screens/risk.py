"""Cảnh báo & Mục tiêu học tập — dùng toàn bộ lịch sử, không phụ thuộc sidebar."""

import html

import streamlit as st

from db import repo
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


def _the_nguy_co(du_doan: dict) -> None:
    muc_nguy_co = du_doan["muc_nguy_co"]
    ty_le = float(du_doan["ty_le"])
    cac_ly_do = du_doan["ly_do"]

    kieu = t.RISK_STYLES[muc_nguy_co]
    ly_do = "".join(
        f'<div style="display:flex;gap:10px;align-items:flex-start">'
        f'<div style="width:6px;height:6px;border-radius:50%;'
        f'background:{t.MUTED};margin-top:8px;flex:0 0 6px"></div>'
        f'<div style="font-size:15px;color:{t.TEXT};line-height:1.5">'
        f'{html.escape(str(r))}</div>'
        f"</div>"
        for r in cac_ly_do
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
        f'color:#fff">{html.escape(muc_nguy_co)}</span></div>'

        f'<div style="display:flex;align-items:flex-end;gap:12px">'
        f'<div class="mk-bignum" style="color:{kieu["dot"]}">'
        f"{ty_le:g}%</div>"
        f'<div style="font-size:14px;color:{t.MUTED};padding-bottom:8px">'
        f"xác suất bị cảnh báo học vụ<br/>ở học kỳ kế tiếp</div></div>"

        f'{b.bar(ty_le, kieu["dot"])}'

        f'<div style="display:flex;flex-direction:column;gap:10px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f"Lý do chính</div>{ly_do}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _the_goi_y(du_doan: dict | None) -> None:
    if du_doan is None:
        goi_y = [
            ("Nhập đủ điểm thành phần",
             "Mô hình chỉ dùng học kỳ có đủ điểm để tạo dự đoán."),
            ("Kiểm tra lịch sử môn học",
             "Rà soát mã môn, tín chỉ và học kỳ đã lưu trước khi xem kết quả."),
            ("Cập nhật khi có điểm mới",
             "Dự đoán được tính lại từ dữ liệu hiện có và không lưu thành lịch sử."),
        ]
    else:
        ty_le = du_doan["ty_le"]
        if ty_le >= 60:
            uu_tien = (
                "Trao đổi sớm với cố vấn học tập",
                "Xem đây là tín hiệu để rà soát kế hoạch học; quyết định chính "
                "thức vẫn theo quy chế của trường.",
            )
        elif ty_le >= 35:
            uu_tien = (
                "Rà soát kế hoạch học tập",
                "Theo dõi các môn và tín chỉ đã đạt để chủ động điều chỉnh "
                "khối lượng học.",
            )
        else:
            uu_tien = (
                "Duy trì tiến độ học tập",
                "Tiếp tục cập nhật điểm đầy đủ để các lần ước lượng sau có "
                "thông tin mới nhất.",
            )
        goi_y = [
            uu_tien,
            ("Kiểm tra lại dữ liệu điểm",
             "Đảm bảo điểm thành phần, trọng số và tín chỉ của các môn đã nhập "
             "đúng."),
            ("Đối chiếu với cố vấn học tập",
             "Mô hình chỉ mang tính tham khảo, không thay thế kết luận học vụ "
             "của nhà trường."),
        ]

    muc = "".join(
        f'<div style="display:flex;gap:12px;align-items:flex-start;'
        f'padding:12px 14px;border:1px solid {t.BORDER};'
        f'border-radius:{t.RADIUS_INPUT}px;background:{t.SURFACE_ALT}">'
        f'<div style="width:22px;height:22px;border-radius:6px;'
        f'background:{t.TIP_BG};color:{t.SUCCESS};font-size:12px;'
        f'font-weight:700;display:flex;align-items:center;'
        f'justify-content:center;flex:0 0 22px">{i}</div>'
        f'<div style="display:flex;flex-direction:column;gap:3px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f'{title}</div>'
        f'<div style="font-size:14px;color:{t.MUTED};line-height:1.45">'
        f'{detail}</div></div></div>'
        for i, (title, detail) in enumerate(goi_y, start=1)
    )
    st.markdown(
        f'<div class="mk-card" style="display:flex;flex-direction:column;'
        f'gap:14px">'
        f'<div style="font-size:15px;font-weight:600;color:{t.TEXT}">'
        f"Gợi ý cải thiện</div>{muc}</div>",
        unsafe_allow_html=True,
    )


def _so_vn(x: float) -> str:
    """2.24 -> "2,24": dấu phẩy thập phân như học bạ."""
    return f"{x:.2f}".replace(".", ",")


def _khung_gpa_tich_luy() -> None:
    """Khung GPA tích luỹ toàn khoá, đặt ngay dưới tiêu đề trang.

    Đây là con số toàn lịch sử (SPEC §6) và là thứ ngưỡng Giỏi/Khá ở mục
    tiêu so vào (SPEC §7), nên phải nổi bật chứ không nằm lẫn trong khối
    mục tiêu. Thang 4 làm chính vì ngưỡng viết theo thang 4, thang 10 kèm
    trong ngoặc; không đổi theo toggle DH10/DH4 của Dashboard.
    """
    mon = rules.mon_tinh_tich_luy(st.session_state.courses)
    if mon:
        tk = rules.tom_tat(mon)
        # Xếp loại chỉ theo thang 4 (SPEC §9.3); thang 10 hiện kèm để tham
        # khảo, không gắn nhãn riêng.
        so = (f'{_so_vn(tk["gpa4"])}<span style="font-size:20px;'
              f'font-weight:600;color:{t.MUTED}">/4,0</span>'
              f'<span style="font-size:15px;font-weight:600;color:{t.TEXT};'
              f'margin-left:12px;padding:4px 12px;border-radius:'
              f'{t.RADIUS_PILL}px;background:{t.CHIP_BG};vertical-align:'
              f'middle">{rules.xep_loai(tk["gpa4"])}</span>'
              f'<span style="font-size:15px;font-weight:500;color:{t.MUTED};'
              f'margin-left:10px">(DH10: {_so_vn(tk["gpa10"])})</span>')
        phu = (f'{len(mon)} môn · {tk["tin_chi"]} tín chỉ đã hoàn tất · '
               "môn học lại/cải thiện lấy lần điểm cao nhất")
    else:
        so = "—"
        phu = "Chưa có môn nào nhập đủ điểm thành phần"
    st.markdown(
        f'<div style="border:1px solid {t.BORDER};border-radius:'
        f'{t.RADIUS_CARD}px;background:{t.PANEL_BG};padding:18px 24px;'
        f'display:flex;align-items:center;justify-content:space-between;'
        f'gap:24px;flex-wrap:wrap">'
        f'<div><div style="font-size:14px;font-weight:600;color:{t.TEXT}">'
        f'GPA tích luỹ (toàn khoá)</div>'
        f'<div style="font-size:14px;color:{t.MUTED};margin-top:4px">{phu}'
        f'</div></div>'
        f'<div style="font-size:34px;font-weight:700;color:{t.PRIMARY};'
        f'letter-spacing:-0.02em;line-height:1;white-space:nowrap">{so}'
        "</div></div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    khoa = st.session_state.goal
    du_doan = d.du_doan_canh_bao(
        st.session_state.courses,
        st.session_state.khoa_from,
        st.session_state.so_ky,
    )
    st.markdown(_CSS.replace("{active}", f"goal_{list(d.GOALS).index(khoa)}"),
                unsafe_allow_html=True)

    cap_nhat = (
        f'Ước lượng từ học kỳ gần nhất đủ điểm: {du_doan["hoc_ky"]}'
        if du_doan else "Chưa đủ dữ liệu điểm hoàn chỉnh để ước lượng"
    )
    b.page_title("Cảnh báo & Mục tiêu học tập", cap_nhat)
    st.caption(
        "Mô hình được huấn luyện trên dữ liệu mô phỏng; điểm rèn luyện, mức "
        "vắng, hệ đào tạo và học phí không có trong hồ sơ nên được xem là "
        "thiếu/không rõ. Kết quả chỉ hiển thị, không lưu vào SQL."
    )
    b.spacer(22)
    _khung_gpa_tich_luy()
    b.spacer(26)

    # Lưới 1.15fr / 1fr như mockup
    trai, phai = st.columns([1.15, 1], vertical_alignment="top")
    with trai:
        if du_doan:
            _the_nguy_co(du_doan)
        else:
            st.info(
                "Hãy nhập đủ điểm thành phần cho ít nhất một học kỳ để xem "
                "dự đoán và lý do SHAP."
            )
    with phai:
        _the_goi_y(du_doan)

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
                    repo.dat_muc_tieu(st.session_state.user_id, ten)
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
