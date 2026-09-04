"""Thêm / cập nhật môn học — form nhập điểm thành phần + bảng môn đã lưu.

Form lấy giá trị từ chính widget (nguồn mới nhất) chứ không từ session_state,
trừ lúc nạp lại: mở form mới, bấm Sửa, thêm/xoá dòng thành phần. Những lúc đó
phải xoá key widget cũ rồi mới ghi giá trị mới, nếu không Streamlit giữ nguyên
giá trị đang có và bỏ qua tham số value=.
"""

import html

import streamlit as st

from ui import blocks as b
from ui import data as d
from ui import rules
from ui import tokens as t

_CHON_LOAI = "— Chọn loại lần học —"


def _esc(x) -> str:
    return html.escape(str(x or ""))

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
  /* Nút "Thu gọn": ghim sát góc trên phải của khung form */
  .st-key-btn_collapse {{
    display: flex !important;
    justify-content: flex-end !important;
    /* Không có width thì khung chỉ rộng bằng chữ, justify-content vô nghĩa.
       Nới thêm đúng bằng phần margin âm: width cố định thì margin-right âm
       không đẩy được hộp, chỉ kéo phần tử đứng sau. */
    width: calc(100% + 11px) !important;
    /* Streamlit đặt max-width:100% nên calc() bị kẹp lại nếu không gỡ. */
    max-width: none !important;
    margin: -10px -11px 0 0 !important;
  }}
  .st-key-btn_collapse button {{
    padding: 2px 4px !important;
    font-size: 13px !important;
    min-height: 0 !important;
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


# --- Trạng thái form -------------------------------------------------------
_TIEN_TO = ("row_type_", "row_w_", "row_s_")


def _uid_moi() -> int:
    st.session_state.row_uid = st.session_state.get("row_uid", 0) + 1
    return st.session_state.row_uid


def _nap_dong(rows: list[dict]) -> None:
    """Nạp lại danh sách dòng thành phần, mỗi dòng nhận một uid mới.

    Widget key phải gắn theo uid chứ không theo vị trí. Nếu đánh theo vị trí
    (row_s_0, row_s_1...) thì sau khi xoá một dòng, trình duyệt vẫn gửi lên
    giá trị cũ của đúng vị trí đó và đè lên giá trị mới — hậu quả là dòng
    biến mất luôn là dòng CUỐI chứ không phải dòng được chọn.
    """
    for cu in st.session_state.get("form_rows") or []:
        for tien_to in _TIEN_TO:
            st.session_state.pop(f"{tien_to}{cu.get('uid')}", None)
    st.session_state.form_rows = [dict(r, uid=_uid_moi()) for r in rows]


def _doc_dong() -> list[dict]:
    """Đọc điểm thành phần đang hiện trên màn hình."""
    return [
        {"uid": r["uid"],
         "loai": st.session_state.get(f'row_type_{r["uid"]}', r["loai"]),
         "trong_so": st.session_state.get(f'row_w_{r["uid"]}', r["trong_so"]),
         "diem": st.session_state.get(f'row_s_{r["uid"]}', r["diem"])}
        for r in st.session_state.form_rows
    ]


def _nap_form(mon: dict | None) -> None:
    """Nạp một môn vào form; truyền None để mở form thêm mới."""
    st.session_state.form_open = True
    st.session_state.editing_id = mon["id"] if mon else None
    for khoa in ("f_code", "f_name", "f_credits", "f_attempt"):
        st.session_state.pop(khoa, None)
    if mon:
        st.session_state.f_code = mon.get("code", "")
        st.session_state.f_name = mon["name"]
        st.session_state.f_credits = mon["credits"]
        st.session_state.f_attempt = mon["attempt"]
        # Giữ nguyên số lần học đã lưu: lúc sửa không đếm lại được vì chính
        # môn này bị loại khỏi phép đếm, sẽ ra Lần 1 sai.
        st.session_state.f_attempt_no = mon.get("attempt_no", 1)
        # Khoá kỳ theo chính môn đang sửa, không theo sidebar: đổi kỳ ở
        # sidebar giữa chừng mà vẫn lấy theo sidebar thì môn bị dời kỳ.
        st.session_state.f_year = mon["year"]
        st.session_state.f_sem = mon["sem"]
        _nap_dong([dict(r) for r in mon["rows"]])
    else:
        st.session_state.f_code = ""
        st.session_state.f_name = ""
        st.session_state.f_credits = 3
        st.session_state.f_attempt = _CHON_LOAI
        st.session_state.f_attempt_no = 1
        # Thêm mới thì bám theo kỳ đang xem, lấy lúc bấm Lưu.
        st.session_state.f_year = None
        st.session_state.f_sem = None
        _nap_dong(d.form_rows_moi())


def _chuan_ma(ma) -> str:
    """Chuẩn hoá mã môn: bỏ khoảng trắng, viết hoa.

    Không chuẩn hoá thì "20ct2201" và "20CT2201" bị coi là hai môn khác nhau,
    đúng cái lỗi mà việc dùng mã thay tên sinh ra để tránh.
    """
    return "".join(str(ma or "").split()).upper()


def _goi_y_loai(truoc: list[dict]) -> str:
    """Loại lần học gợi ý, suy từ kết quả lần học gần nhất (SPEC §3.3).

    Lần trước chưa đủ điểm thì không kết luận được đỗ hay trượt, nên để
    trống và bắt sinh viên tự chọn.
    """
    if not truoc:
        return "Học lần 1"
    cuoi = truoc[-1]
    diem = rules.diem_mon(cuoi)
    if diem is None or not rules.du_trong_so(cuoi):
        return _CHON_LOAI
    return "Học cải thiện" if diem >= t.GRADE_FAIL else "Học lại"


def _ma_doi() -> None:
    """Gõ mã môn thì suy lại số lần học, loại lần học, và điền sẵn tên."""
    if st.session_state.editing_id:
        return
    ma = _chuan_ma(st.session_state.f_code)
    st.session_state.f_code = ma
    truoc = _lan_hoc_truoc(ma)
    st.session_state.f_attempt_no = _so_lan_hoc(ma)
    st.session_state.f_attempt = _goi_y_loai(truoc)
    if truoc:
        # Mã là khoá của môn nên tên và số tín chỉ phải khớp lần học trước,
        # nếu không cùng một mã lại mang hai tên.
        st.session_state.f_name = truoc[-1]["name"]
        st.session_state.f_credits = truoc[-1]["credits"]


def ky_cua_form() -> tuple[str, str]:
    """Năm học và học kỳ mà môn trong form thuộc về."""
    if st.session_state.editing_id and st.session_state.get("f_year"):
        return st.session_state.f_year, st.session_state.f_sem
    return st.session_state.nam_hoc, st.session_state.hoc_ky


def _dong_form() -> None:
    st.session_state.form_open = False
    st.session_state.editing_id = None


def _luu() -> None:
    """Ghi môn đang soạn vào danh sách — sửa tại chỗ hoặc thêm dòng mới."""
    rows = [{k: v for k, v in r.items() if k != "uid"} for r in _doc_dong()]
    ma = _chuan_ma(st.session_state.f_code)
    ten = (st.session_state.f_name or "").strip() or "Môn học chưa đặt tên"
    # Đếm lần học theo MÃ, không theo tên.
    lan = (st.session_state.f_attempt_no
           if st.session_state.editing_id else _so_lan_hoc(ma))
    loai = "Học lần 1" if lan == 1 else st.session_state.f_attempt
    nam, ky_hoc = ky_cua_form()
    mon = {
        "year": nam,
        "sem": ky_hoc,
        "code": ma,
        "name": ten,
        "credits": int(st.session_state.f_credits or 0),
        "attempt": "Học lần 1" if loai == _CHON_LOAI else loai,
        # Thêm mới thì đếm từ các lần học cùng mã; sửa thì giữ số đã lưu.
        "attempt_no": lan,
        "rows": rows,
    }
    ds = st.session_state.courses
    if st.session_state.editing_id:
        for i, c in enumerate(ds):
            if c["id"] == st.session_state.editing_id:
                ds[i] = {**c, **mon}
                break
    else:
        ds.append({"id": max((c["id"] for c in ds), default=0) + 1, **mon})
    _dong_form()


def _so_lan_hoc(ma: str) -> int:
    """Số lần học của lần sắp thêm.

    Lấy số lần lớn nhất đã có rồi cộng 1, không đếm số bản ghi: sinh viên có
    thể chỉ nhập lần học lại mà bỏ qua lần đầu, đếm theo số lượng sẽ ra số
    trùng với bản ghi sẵn có.
    """
    truoc = _lan_hoc_truoc(ma)
    return max((c.get("attempt_no", 1) for c in truoc), default=0) + 1


def _lan_hoc_truoc(ma: str) -> list[dict]:
    """Các lần học trước của cùng mã môn, bỏ qua chính môn đang sửa.

    Dò theo mã chứ không theo tên: tên do sinh viên tự gõ nên "CSDL" và
    "Cơ sở dữ liệu" sẽ bị coi là hai môn khác nhau.
    """
    ma = _chuan_ma(ma)
    if not ma:
        return []
    return [c for c in st.session_state.courses
            if _chuan_ma(c.get("code")) == ma
            and c["id"] != st.session_state.editing_id]


def _dup_text(truoc: list[dict], lan: int) -> str:
    """Câu cảnh báo trùng môn, kèm gợi ý loại lần học suy từ kết quả cũ."""
    cuoi = truoc[-1]
    dau = f'Môn này đã học ở {cuoi["sem"]} ({cuoi["year"]})'
    duoi = f" → Tự động ghi nhận là Lần {lan}."
    diem = rules.diem_mon(cuoi)
    if diem is None or not rules.du_trong_so(cuoi):
        return (dau + ", hiện chưa đủ điểm để xác định kết quả — vui lòng "
                "chọn loại lần học phù hợp." + duoi)
    dat = diem >= t.GRADE_FAIL
    goi_y = "“Học cải thiện”" if dat else "“Học lại”"
    ket = "(đã đạt)" if dat else "(chưa đạt)"
    return f"{dau} với điểm {diem:.1f} {ket} — đã gợi ý {goi_y}." + duoi


@st.dialog("Xoá môn học?")
def _hop_xac_nhan(mon: dict) -> None:
    st.markdown(
        f'<div style="font-size:15px;color:{t.MUTED};line-height:1.5">'
        f'Môn <span class="mk-strong">{mon["name"]}</span> cùng toàn bộ điểm '
        "thành phần sẽ bị xoá khỏi học kỳ này. Hành động này không thể hoàn "
        "tác.</div>",
        unsafe_allow_html=True,
    )
    b.spacer(6)
    _, c1, c2 = st.columns([1, 1, 1.3])
    if c1.button("Huỷ", key="xoa_huy", width="stretch"):
        st.session_state.confirm_id = None
        st.rerun()
    if c2.button("Xoá môn học", key="xoa_that", type="primary",
                 width="stretch"):
        st.session_state.courses = [
            c for c in st.session_state.courses if c["id"] != mon["id"]]
        if st.session_state.editing_id == mon["id"]:
            _dong_form()
        st.session_state.confirm_id = None
        st.rerun()


def _o_chi_doc(nhan: str, gia_tri: str) -> None:
    """Ô hiển thị chỉ đọc, trông như ô nhập bị khoá."""
    st.markdown('<div style="font-size:14px;font-weight:600;'
                f'color:{t.TEXT};margin-bottom:6px">{nhan}</div>'
                f'<div class="mk-readonly">{gia_tri}</div>',
                unsafe_allow_html=True)


# --- Form ------------------------------------------------------------------
def _form() -> None:
    dang_sua = st.session_state.editing_id is not None

    # Dòng mặc định do app.py khởi tạo chưa qua _nap_dong nên chưa có uid.
    if any("uid" not in r for r in st.session_state.form_rows):
        _nap_dong(st.session_state.form_rows)

    with st.container(border=True):
        # Hàng đầu: nhãn chế độ + link thu gọn
        dau, cuoi = st.columns([4, 1], vertical_alignment="top")
        dau.markdown(
            '<span class="mk-mode">'
            + ("Đang sửa môn học đã lưu" if dang_sua else "Thêm môn học mới")
            + "</span>", unsafe_allow_html=True)
        if cuoi.button("Thu gọn", key="btn_collapse", type="tertiary"):
            _dong_form()
            st.rerun()

        b.spacer(16)

        c1, c2, c3 = st.columns([1, 2, 1])
        if dang_sua:
            # Sửa thì khoá mã và tên: đổi mã tức là trỏ sang môn khác, còn
            # đổi tên sẽ làm một mã mang hai tên.
            with c1:
                _o_chi_doc("Mã môn học", _esc(st.session_state.f_code))
            with c2:
                _o_chi_doc("Tên môn học", _esc(st.session_state.f_name))
        else:
            # Dấu * báo bắt buộc; nút Lưu bị khoá khi còn trống nên không
            # cần bôi đỏ ngay lúc form vừa mở.
            c1.text_input("Mã môn học *", key="f_code",
                          placeholder="VD: 20CT3201", on_change=_ma_doi)
            c2.text_input("Tên môn học", key="f_name",
                          placeholder="VD: Trí tuệ nhân tạo")
        c3.number_input("Số tín chỉ", min_value=1, max_value=12, step=1,
                        key="f_credits")

        # Trùng mã môn đã lưu: báo ngay dưới ô nhập và tự tăng số lần học.
        # Chỉ cảnh báo khi thêm mới — sửa một môn đã lưu thì không phải là
        # đang tạo thêm lần học nào cả.
        truoc = [] if dang_sua else _lan_hoc_truoc(st.session_state.f_code)
        lan = (st.session_state.f_attempt_no if dang_sua
               else _so_lan_hoc(st.session_state.f_code))
        # Đặt ngoài cột: nằm trong cột Mã thì hộp bị bó hẹp, chữ xuống 4 dòng.
        if truoc:
            b.dup_hint(_dup_text(truoc, lan),
                       f"{st.session_state.nam_hoc} · "
                       f"{st.session_state.hoc_ky}")

        c3, c4 = st.columns([1, 2])
        with c3:
            st.markdown('<div style="font-size:14px;font-weight:600;'
                        f'color:{t.TEXT};margin-bottom:6px">Lần học</div>'
                        f'<div class="mk-readonly">Lần {lan} (tự động)</div>',
                        unsafe_allow_html=True)
        # Lần 1 thì loại lần học là hiển nhiên, không có gì để chọn (SPEC
        # §3.3 mục 5). Từ lần 2 mới xổ danh sách, và chỉ gồm hai loại lặp
        # lại — "Học lần 1" lúc này là lựa chọn vô nghĩa.
        if lan == 1:
            with c4:
                _o_chi_doc("Loại lần học", "Học lần 1 (tự động)")
        else:
            chon = [_CHON_LOAI] + t.ATTEMPT_REPEAT
            if st.session_state.f_attempt not in chon:
                st.session_state.f_attempt = _CHON_LOAI
            c4.selectbox("Loại lần học", chon, key="f_attempt",
                         filter_mode=None)
            if st.session_state.f_attempt == _CHON_LOAI:
                c4.markdown(
                    f'<div style="font-size:12px;color:{t.DANGER}">Chưa xác '
                    "định được từ lần học trước — hãy chọn.</div>",
                    unsafe_allow_html=True)

        st.markdown(f'<div style="height:1px;background:{t.ROW_LINE};'
                    'margin:22px 0"></div>', unsafe_allow_html=True)

        # --- Điểm thành phần ---------------------------------------------
        ty_le = [2, 1, 1, 0.45]
        tieu_de_khoi = st.container()

        cot_dau = st.columns(ty_le)
        for cot, nhan in zip(cot_dau, ["Loại thành phần", "Trọng số (%)",
                                       "Điểm số", ""]):
            cot.markdown(f'<div style="font-size:13px;font-weight:600;'
                         f'color:{t.MUTED}">{nhan}</div>',
                         unsafe_allow_html=True)

        xoa_uid = None
        for r in st.session_state.form_rows:
            u = r["uid"]
            cot = st.columns(ty_le, vertical_alignment="bottom")
            cot[0].selectbox(
                "Loại", t.COMPONENT_TYPES,
                index=t.COMPONENT_TYPES.index(r["loai"]),
                key=f"row_type_{u}", label_visibility="collapsed",
                filter_mode=None)
            cot[1].number_input(
                "Trọng số", value=int(r["trong_so"]), min_value=0,
                max_value=100, step=5, format="%d", key=f"row_w_{u}",
                label_visibility="collapsed")
            cot[2].number_input(
                "Điểm", value=r["diem"], min_value=0.0, max_value=10.0,
                step=0.1, format="%.1f", key=f"row_s_{u}",
                label_visibility="collapsed", placeholder="chưa nhập")
            # Còn đúng một dòng thì không cho xoá nốt, bảng sẽ rỗng vô nghĩa.
            if cot[3].button("✕", key=f"rmrow_{u}", help="Xoá dòng",
                             disabled=len(st.session_state.form_rows) == 1):
                xoa_uid = u

        if xoa_uid is not None:
            _nap_dong([r for r in _doc_dong() if r["uid"] != xoa_uid])
            st.rerun()

        # Tổng trọng số nằm trên bảng nhưng chỉ tính được sau khi đọc widget,
        # nên phần tiêu đề được đặt chỗ trước rồi ghi ngược lại vào đây.
        info = rules.grade_info(_doc_dong())
        with tieu_de_khoi:
            tr, ph = st.columns([2, 1], vertical_alignment="center")
            tr.markdown('<div class="mk-h3">Điểm thành phần</div>',
                        unsafe_allow_html=True)
            mau_ts = t.SUCCESS if info["tong_ts"] == 100 else t.DANGER
            ph.markdown(
                f'<div style="font-size:14px;color:{t.MUTED};'
                f'text-align:right">Tổng trọng số: <strong '
                f'style="font-family:{t.MONO};color:{mau_ts};'
                f'font-weight:600">{info["tong_ts"]}%</strong></div>',
                unsafe_allow_html=True,
            )
            b.spacer(12)

        b.spacer(12)
        with st.container(horizontal=True, vertical_alignment="center",
                          gap="medium"):
            if st.button("+ Thêm dòng thành phần", key="btn_addrow"):
                _nap_dong(_doc_dong()
                          + [{"loai": "Thi cuối kỳ", "trong_so": 0,
                              "diem": None}])
                st.rerun()
            st.markdown(
                f'<span style="font-size:13px;color:{t.FAINT}">Danh sách loại: '
                f'{", ".join(t.COMPONENT_TYPES)}</span>',
                unsafe_allow_html=True)

        b.spacer(12)
        b.weight_box(info["tong_ts"])

        # Hàng nút: điểm tạm tính căn phải, tách khỏi hộp trọng số ở trên.
        b.spacer(4)
        chu, mau = rules.provisional_text(info)
        nut, ghi_chu = st.columns([1, 1], vertical_alignment="center")
        with nut:
            with st.container(horizontal=True, vertical_alignment="center",
                              gap="medium"):
                # Mã là khoá nhận diện môn: thiếu mã thì không dò được lần
                # học, nên chặn ngay ở nút Lưu.
                thieu_ma = not _chuan_ma(st.session_state.f_code)
                if st.button(
                        "Cập nhật môn học" if dang_sua else "Lưu môn học",
                        type="primary", key="btn_save", disabled=thieu_ma,
                        help="Cần nhập mã môn học" if thieu_ma else None):
                    _luu()
                    st.rerun()
                if st.button("Huỷ sửa" if dang_sua else "Huỷ",
                             key="btn_cancel"):
                    _dong_form()
                    st.rerun()
        ghi_chu.markdown(
            f'<div style="font-size:14px;text-align:right;color:{mau}">'
            f"{chu}</div>", unsafe_allow_html=True)


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    b.page_title(
        "Thêm / cập nhật môn học",
        "Nhập điểm thành phần để hệ thống tính điểm tổng kết và cập nhật mức "
        "nguy cơ.",
    )
    # Dòng này phải đổi theo chế độ: lúc sửa thì kỳ đã cố định theo môn, gợi
    # ý "đổi ở sidebar" là sai vì đổi cũng không ảnh hưởng gì.
    nam, ky_hoc = ky_cua_form()
    if st.session_state.form_open and st.session_state.editing_id:
        dong = (f'Đang sửa môn của: <span class="mk-strong">Năm học {nam} · '
                f'{ky_hoc}</span> <span style="color:{t.FAINT}">(môn giữ '
                "nguyên kỳ này dù đổi kỳ đang xem)</span>")
    else:
        dong = (f'Đang thêm môn cho: <span class="mk-strong">Năm học {nam} · '
                f'{ky_hoc}</span> <span style="color:{t.FAINT}">(đổi ở '
                "sidebar bên trái nếu muốn thêm cho kỳ khác)</span>")
    st.markdown(
        f'<div style="font-size:14px;color:{t.MUTED};margin-top:6px">'
        f"{dong}</div>", unsafe_allow_html=True)
    b.spacer(26)

    if not st.session_state.form_open:
        if st.button("+ Thêm môn học", type="primary", key="btn_open_form"):
            _nap_form(None)
            st.rerun()
    else:
        _form()

    b.spacer(26)
    b.section_title("Môn học đã thêm trong học kỳ này",
                    f"{st.session_state.nam_hoc} · {st.session_state.hoc_ky}")
    b.spacer(12)

    def _sua(mon):
        _nap_form(mon)
        st.rerun()

    def _xoa(mon):
        st.session_state.confirm_id = mon["id"]
        st.rerun()

    trong_ky = rules.loc_ky(st.session_state.courses,
                            st.session_state.nam_hoc, st.session_state.hoc_ky)
    b.semester_table(trong_ky, _sua, _xoa, st.session_state.editing_id)

    if st.session_state.confirm_id is not None:
        mon = next((c for c in st.session_state.courses
                    if c["id"] == st.session_state.confirm_id), None)
        if mon:
            _hop_xac_nhan(mon)
        else:
            st.session_state.confirm_id = None

    b.footer(d.FOOTER)
