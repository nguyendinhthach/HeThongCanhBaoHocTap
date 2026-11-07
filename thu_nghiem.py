"""Giao diện thử nghiệm dự đoán từ kết quả học tập trên cổng thông tin sinh viên.

Tách riêng khỏi app.py và ui/ (giao diện cũ): chỉ để kiểm thử dữ liệu và mô
hình, không dùng cơ sở dữ liệu, không lưu văn bản người dùng đưa vào.

Chạy:  streamlit run thu_nghiem.py
Cần có models/ trước (python ml/mo_phong.py rồi python ml/mo_hinh_cuoi.py).
"""

import os
import sys

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(THU_MUC_GOC, "ml"))

import dac_trung
import doc_cong_thong_tin as cong
import doc_form as form
import mo_hinh_cuoi
from gan_nhan import (NGUONG_DTB_TICH_LUY, SO_LAN_CANH_BAO_THOI_HOC, gan_nhan_hoc_ky,
                      trinh_do_nam)

FILE_MAU = os.path.join(THU_MUC_GOC, "ml", "du_lieu_mau", "cong_thong_tin_mau.txt")
BUOC_DU_LIEU, BUOC_KIEM_TRA, BUOC_KET_QUA = "1. Dữ liệu", "2. Kiểm tra", "3. Kết quả"
CHUA_KHAI = "Chưa khai"
CAU_VANG = [CHUA_KHAI, *form.MUC_VANG[:4]]
CAU_HOC_PHI = [CHUA_KHAI, *form.HOC_PHI[:4]]
COT_HOC_KY = {"tc_dat_hk": "TC đạt", "dtb_hk": "ĐTB học kỳ", "tctl": "TC tích luỹ",
              "tc_dang_ky": "TC đăng ký", "dtb_tl": "ĐTB tích luỹ", "drl": "ĐRL"}


def den_buoc(buoc):
    st.session_state.buoc = buoc


def nap_du_lieu(van_ban):
    """Đọc văn bản vào phiên làm việc; đọc được thì sang bước Kiểm tra."""
    try:
        sinh_vien, bang_hoc_ky, bang_mon = cong.doc_van_ban(van_ban)
    except ValueError as loi:
        st.session_state.loi_doc = str(loi)
        return
    st.session_state.update(
        loi_doc=None, sinh_vien=sinh_vien, ten_ky=cong.ten_hoc_ky(van_ban),
        canh_bao_doc=cong.canh_bao_du_lieu(van_ban),
        hk_goc=bang_hoc_ky, hk_sua=bang_hoc_ky, mon_goc=bang_mon, mon_sua=bang_mon,
        vang_chon=CHUA_KHAI, hoc_phi_chon=CHUA_KHAI, buoc=BUOC_KIEM_TRA)


def doc_o_nhap():
    nap_du_lieu(st.session_state.get("van_ban", ""))


def doc_file_mau():
    with open(FILE_MAU, encoding="utf-8") as f:
        nap_du_lieu(f.read())


def chot_ban_sua():
    """Bảng sửa chỉ sống khi ô sửa đang hiện, nên rời bước Kiểm tra thì giữ lại."""
    if "hk_sua" in st.session_state:
        st.session_state.hk_goc = st.session_state.hk_sua
        st.session_state.mon_goc = st.session_state.mon_sua


def bang_da_khai():
    """Bảng học kỳ sau khi sửa, ghi thêm mức vắng và học phí vào kỳ gần nhất."""
    hk = st.session_state.hk_sua.copy()
    if len(hk):
        cuoi = hk.index[-1]
        if st.session_state.vang_chon != CHUA_KHAI:
            hk.loc[cuoi, "muc_vang"] = st.session_state.vang_chon
        if st.session_state.hoc_phi_chon != CHUA_KHAI:
            hk.loc[cuoi, "hoc_phi"] = st.session_state.hoc_phi_chon
    return hk


def trang_du_lieu():
    st.title("Nhập kết quả học tập của bạn")
    st.write("Hệ thống đọc số liệu từ trang Xem điểm để dự đoán nguy cơ ở học kỳ sắp tới.")

    trai, phai = st.columns([1, 2], gap="large")
    with trai:
        st.subheader("Cách lấy dữ liệu")
        st.markdown(
            "1. Đăng nhập **online.dlu.edu.vn**, vào **Kết quả học tập**, để Năm học và "
            "Học kỳ ở mức tất cả.\n"
            "2. Nhấn **Ctrl+A** rồi **Ctrl+C**. Muốn dự đoán từng môn thì mở **Chi tiết** "
            "các môn đang học trước.\n"
            "3. Nhấp vào ô bên cạnh, nhấn **Ctrl+V**, rồi bấm **Đọc dữ liệu**.")
        st.caption("Nên làm trên máy tính. Không cần tự xoá họ tên hay MSSV: hệ thống "
                   "không đọc và không lưu văn bản gốc.")
    with phai:
        st.text_area("Văn bản trang Xem điểm", key="van_ban", height=340,
                     placeholder="Nhấn Ctrl+V để đưa toàn bộ trang vào đây")
        nut1, nut2, _ = st.columns([1, 1, 2])
        nut1.button("Đọc dữ liệu", type="primary", on_click=doc_o_nhap, width="stretch")
        nut2.button("Dùng dữ liệu mẫu", on_click=doc_file_mau, width="stretch")
        if st.session_state.get("loi_doc"):
            st.error(st.session_state.loi_doc)


def trang_kiem_tra():
    st.title("Kiểm tra dữ liệu đã đọc")
    st.write("Đối chiếu với trang Xem điểm. Số nào sai thì bấm vào ô để sửa.")

    sv = st.session_state.sinh_vien.iloc[0]
    hk_goc, mon_goc, ten_ky = (st.session_state.hk_goc, st.session_state.mon_goc,
                               st.session_state.ten_ky)
    khong_ro = "Chưa rõ"
    cot1, cot2, cot3, cot4 = st.columns(4)
    cot1.metric("Học kỳ đã có điểm", len(hk_goc))
    cot2.metric("Môn trong bảng môn", len(mon_goc))
    cot3.metric("Ngành, hệ đào tạo", "CNTT, kỹ sư" if sv["he_dao_tao"] == "Kỹ sư (4,5 năm)"
                and sv["nganh"] == "Công nghệ thông tin" else
                (sv["nganh"] if pd.notna(sv["nganh"]) else khong_ro))
    cot4.metric("Năm nhập học", sv["nam_nhap_hoc"] if pd.notna(sv["nam_nhap_hoc"]) else khong_ro)

    if st.session_state.canh_bao_doc:
        st.warning("Cần kiểm tra lại:\n\n" + "\n".join(f"- {c}" for c in st.session_state.canh_bao_doc))
    else:
        st.success("Không phát hiện lỗi: các học kỳ liên tục, đủ dòng tổng kết.")

    st.subheader("Các học kỳ đã có điểm")
    hien_thi = hk_goc.assign(ten_ky=hk_goc["hoc_ky"].map(ten_ky))[["ten_ky", *COT_HOC_KY]]
    sua = st.data_editor(
        hien_thi, hide_index=True, width="stretch", num_rows="fixed", key="sua_hoc_ky",
        disabled=["ten_ky"],
        column_config={"ten_ky": "Học kỳ",
                       **{c: st.column_config.NumberColumn(n, min_value=0.0) for c, n in COT_HOC_KY.items()}})
    hk_sua = hk_goc.copy()
    hk_sua[list(COT_HOC_KY)] = sua[list(COT_HOC_KY)].to_numpy()
    st.session_state.hk_sua = hk_sua

    co_nhan = gan_nhan_hoc_ky(hk_sua)
    ky_canh_bao = co_nhan[co_nhan["canh_bao"].fillna(0) == 1]
    if len(ky_canh_bao):
        st.write("**Cảnh báo tự xét:** " + "; ".join(
            f"{ten_ky[d.hoc_ky]} ({d.ly_do_canh_bao})" for d in ky_canh_bao.itertuples()))
    else:
        st.write("**Cảnh báo tự xét:** không có học kỳ nào.")
    st.caption("Trang Xem điểm không ghi kỳ nào bị cảnh báo. Dòng trên do hệ thống tự xét theo "
               "Điều 18.1 QĐ 600, chưa gồm điều kiện rớt trên 50% TC trong kỳ; không phải "
               "danh sách chính thức của trường.")

    if len(hk_goc):
        st.subheader(f"Khai thêm về {ten_ky[hk_goc['hoc_ky'].iloc[-1]]} (không bắt buộc)")
        cot1, cot2 = st.columns(2)
        st.session_state.vang_chon = cot1.selectbox(
            "Mức vắng học", CAU_VANG, index=CAU_VANG.index(st.session_state.vang_chon))
        st.session_state.hoc_phi_chon = cot2.selectbox(
            "Tình trạng học phí", CAU_HOC_PHI, index=CAU_HOC_PHI.index(st.session_state.hoc_phi_chon))

    if len(mon_goc):
        ky_mon = mon_goc["hoc_ky"].iloc[0]
        st.subheader(f"Môn của {ten_ky.get(ky_mon, 'học kỳ gần nhất')}")
        st.caption("Muốn dự đoán trượt môn thì nhập điểm giữa kỳ và tỉ trọng (ví dụ 0,4 là 40%). "
                   "Ô trống thì môn đó chưa được dự đoán.")
        cot_sua = ["ten_mon", "so_tc", "diem_gk", "ti_trong_gk", "vang_lt", "vang_th"]
        # Cột vắng còn trống có kiểu số; ô chọn của Streamlit cần cột chữ
        mon_sua = st.data_editor(
            mon_goc[cot_sua].astype({"vang_lt": "string", "vang_th": "string"}),
            hide_index=True, width="stretch", num_rows="fixed",
            key="sua_mon", disabled=["ten_mon", "so_tc"],
            column_config={
                "ten_mon": "Môn", "so_tc": "TC",
                "diem_gk": st.column_config.NumberColumn("Điểm giữa kỳ", min_value=0.0, max_value=10.0, step=0.1),
                "ti_trong_gk": st.column_config.NumberColumn("Tỉ trọng giữa kỳ", min_value=0.0, max_value=1.0, step=0.05),
                "vang_lt": st.column_config.SelectboxColumn("Vắng lý thuyết", options=form.VANG_LY_THUYET[:3]),
                "vang_th": st.column_config.SelectboxColumn("Vắng thực hành", options=form.VANG_THUC_HANH[:3]),
            })
        ban_moi = mon_goc.copy()
        for cot in ["diem_gk", "ti_trong_gk"]:
            ban_moi[cot] = pd.to_numeric(mon_sua[cot], errors="coerce").to_numpy()
        for cot in ["vang_lt", "vang_th"]:
            ban_moi[cot] = mon_sua[cot].astype(object).where(mon_sua[cot].notna(), np.nan).to_numpy()
        st.session_state.mon_sua = ban_moi

    nut1, nut2, _ = st.columns([2, 1, 3])
    nut1.button("Dữ liệu đúng, xem kết quả", type="primary", on_click=den_buoc,
                args=(BUOC_KET_QUA,), width="stretch")
    nut2.button("Quay lại", on_click=den_buoc, args=(BUOC_DU_LIEU,), width="stretch")


def the_nguy_co(tieu_de, co_nguy_co, ly_do):
    st.subheader(tieu_de)
    if co_nguy_co:
        st.error("**Nguy cơ cao**")
        if ly_do:
            st.write("**Lý do chính**")
            st.markdown("\n".join(f"- {l}" for l in ly_do))
    else:
        st.success("**Nguy cơ thấp**: dưới ngưỡng báo động.")


def bieu_do_xu_huong(hk, ten_ky):
    du_lieu = hk.assign(ky=hk["hoc_ky"].map(ten_ky)).melt(
        id_vars="ky", value_vars=["dtb_hk", "dtb_tl"], var_name="loai", value_name="dtb")
    du_lieu["loai"] = du_lieu["loai"].map({"dtb_hk": "ĐTB học kỳ", "dtb_tl": "ĐTB tích luỹ"})
    thu_tu = list(hk["hoc_ky"].map(ten_ky))
    duong = alt.Chart(du_lieu).mark_line(point=alt.OverlayMarkDef(size=64), strokeWidth=2).encode(
        x=alt.X("ky:N", sort=thu_tu, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("dtb:Q", scale=alt.Scale(domain=[0, 4]), title="Điểm trung bình (thang 4)"),
        color=alt.Color("loai:N", title=None, scale=alt.Scale(
            domain=["ĐTB học kỳ", "ĐTB tích luỹ"], range=["#2a78d6", "#eb6834"]),
            legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("ky:N", title="Học kỳ"), alt.Tooltip("loai:N", title="Loại"),
                 alt.Tooltip("dtb:Q", title="Điểm", format=".2f")])
    nguong = NGUONG_DTB_TICH_LUY[trinh_do_nam(hk["tctl"].iloc[-1])]
    ke = alt.Chart(pd.DataFrame({"nguong": [nguong]})).mark_rule(
        strokeDash=[4, 4], color="#6b7280").encode(y="nguong:Q")
    st.altair_chart(duong + ke, width="stretch")
    st.caption(f"Đường nét đứt: ngưỡng cảnh báo ĐTB tích luỹ hiện tại của bạn ({nguong}).")


def trang_ket_qua():
    hk = bang_da_khai()
    if hk.empty:
        st.warning("Chưa có học kỳ nào có tổng kết nên chưa dự đoán được.")
        return

    sinh_vien = st.session_state.sinh_vien.copy()
    loi = form.kiem_tra(hk, sinh_vien)
    sinh_vien["hop_le"] = [not loi[ma] for ma in sinh_vien.index]
    if not sinh_vien["hop_le"].all():
        st.error("Dữ liệu chưa hợp lệ, hãy sửa ở bước Kiểm tra:\n\n"
                 + "\n".join(f"- {l}" for l in loi[sinh_vien.index[0]]))
        st.button("Về bước Kiểm tra", on_click=den_buoc, args=(BUOC_KIEM_TRA,))
        return

    du_lieu = dac_trung.chuan_bi_du_lieu(sinh_vien, hk, st.session_state.mon_sua)
    try:
        cb, th, tm = (mo_hinh_cuoi.du_doan(None, m, du_lieu=du_lieu)
                      for m in ["canh_bao", "thoi_hoc", "truot_mon"])
    except FileNotFoundError as loi_mo_hinh:
        st.error(str(loi_mo_hinh))
        return

    ten_ky = st.session_state.ten_ky
    dong = cb.iloc[0]
    st.title(f"Dự đoán cho {ten_ky[dong['du_doan_cho_hk']]}")
    st.write(f"Dựa trên dữ liệu đến {ten_ky[dong['dua_tren_hk']]}. Kết quả chỉ để tham khảo, "
             "không thay thế quyết định học vụ của trường.")

    lien_tiep = int(gan_nhan_hoc_ky(hk)["so_lan_canh_bao_lien_tiep"].iloc[-1])
    trai, phai = st.columns(2, gap="large")
    with trai:
        the_nguy_co("Bị cảnh báo học tập", bool(dong["bao_dong"]), dong["ly_do"])
    with phai:
        if lien_tiep < SO_LAN_CANH_BAO_THOI_HOC - 1:
            st.subheader("Bị buộc thôi học do cảnh báo")
            st.info(f"**Chưa thể xảy ra ở kỳ này.** Tự xét: {lien_tiep} kỳ bị cảnh báo liên tiếp, "
                    f"quy chế cần {SO_LAN_CANH_BAO_THOI_HOC - 1} kỳ liên tiếp trước đó.")
        else:
            d = th.iloc[0]
            the_nguy_co("Bị buộc thôi học do cảnh báo", bool(d["bao_dong"]), d["ly_do"])

    st.subheader("Trượt từng môn")
    if tm.empty:
        st.write("Không có môn nào để dự đoán.")
    else:
        bang = pd.DataFrame({
            "Môn": tm["ten_mon"],
            "Kết quả": np.where(tm["ghi_chu"] != "", tm["ghi_chu"],
                                np.where(tm["bao_dong"], "Nguy cơ cao", "Nguy cơ thấp")),
            "Lý do chính": tm["ly_do"].map("; ".join),
        })
        st.dataframe(bang, hide_index=True, width="stretch")

    st.subheader("Xu hướng điểm trung bình")
    bieu_do_xu_huong(hk, ten_ky)

    st.subheader("Gợi ý cải thiện")
    st.caption("Chưa có nội dung: luật gợi ý sẽ làm sau.")

    with st.expander("Số liệu kỹ thuật (để kiểm thử)"):
        st.write(f"Mô hình cảnh báo: {mo_hinh_cuoi.tai('canh_bao')['phuong_phap']}, "
                 f"ngưỡng F2 = {mo_hinh_cuoi.tai('canh_bao')['nguong']:.3f}, "
                 f"điểm nguy cơ = {dong['xac_suat']:.3f}.")
        st.write(f"Mô hình trượt môn: {mo_hinh_cuoi.tai('truot_mon')['phuong_phap']}, "
                 f"ngưỡng F2 = {mo_hinh_cuoi.tai('truot_mon')['nguong']:.3f}.")
        st.dataframe(tm.drop(columns=["ma_sv", "ly_do"]), hide_index=True, width="stretch")
        st.caption("Điểm nguy cơ dùng để xếp hạng và so với ngưỡng, chưa phải xác suất đã hiệu chỉnh.")

    st.button("Quay lại sửa dữ liệu", on_click=den_buoc, args=(BUOC_KIEM_TRA,))


st.set_page_config(page_title="Thử nghiệm cảnh báo học tập", layout="wide")
st.radio("Bước", [BUOC_DU_LIEU, BUOC_KIEM_TRA, BUOC_KET_QUA], key="buoc", horizontal=True,
         label_visibility="collapsed")

buoc = st.session_state.buoc
if buoc == BUOC_DU_LIEU:
    chot_ban_sua()
    trang_du_lieu()
elif "sinh_vien" not in st.session_state:
    st.info("Chưa có dữ liệu. Hãy nhập ở bước 1.")
elif buoc == BUOC_KIEM_TRA:
    trang_kiem_tra()
else:
    chot_ban_sua()
    trang_ket_qua()
