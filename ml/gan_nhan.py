"""
Gán nhãn theo Quy chế đào tạo QĐ 600/QĐ-ĐHĐL (31/8/2021) của Trường ĐH Đà Lạt.

Mọi sinh viên (kể cả trường khác trả lời khảo sát) đều gán theo quy chế này.
Các hàm luật dùng chung cho hai chỗ:
- mo_phong.py: xét cảnh báo sau mỗi học kỳ, dừng mô phỏng khi buộc thôi học;
- gan_nhan_hoc_ky(): gán nhãn cho bảng học kỳ đọc từ form (doc_form.py).
"""

import pandas as pd


# Điều 13.5a: điểm học phần (thang 10, đã làm tròn 1 chữ số) -> thang 4.
# Trường dùng 4 mức A/B/C/D, không có B+, C+, D+.
MOC_THANG_4 = [(8.5, 4), (7.0, 3), (5.5, 2), (4.0, 1)]
DIEM_DAT = 4.0

# Điều 15.7: trình độ năm theo số TC tích luỹ
MOC_TRINH_DO = [(105, 4), (70, 3), (35, 2)]

# Điều 18.1c: ngưỡng ĐTB tích luỹ theo trình độ năm (năm 4 trở đi dùng 1,8)
NGUONG_DTB_TICH_LUY = {1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8}

# Điều 18.1a, b
TI_LE_ROT_TOI_DA = 0.5
NO_TC_TOI_DA = 24
NGUONG_DTB_HK_DAU = 0.8
NGUONG_DTB_HK = 1.0

# Điều 18.2a: bị cảnh báo "quá 2 lần liên tiếp", tức lần thứ 3 liên tiếp
SO_LAN_CANH_BAO_THOI_HOC = 3


def quy_doi_thang_4(diem_10):
    """Điểm học phần thang 10 -> thang 4 (Điều 13.5a)."""
    for moc, diem_4 in MOC_THANG_4:
        if diem_10 >= moc:
            return diem_4
    return 0


def trinh_do_nam(tctl):
    """Trình độ năm (1..4) theo số TC tích luỹ (Điều 15.7)."""
    for moc, nam in MOC_TRINH_DO:
        if tctl >= moc:
            return nam
    return 1


def ly_do_canh_bao(dtb_hk, dtb_tl, tctl, no_tc, ky_dau, tc_rot_hk=None, tc_dang_ky_hk=None):
    """Danh sách lý do bị cảnh báo học tập cuối học kỳ chính (Điều 18.1).

    Danh sách rỗng = không bị cảnh báo. `tc_rot_hk`, `tc_dang_ky_hk` là số TC
    không đạt / đã đăng ký trong riêng học kỳ này (kể cả môn học lại); form
    khảo sát không hỏi hai số này nên bỏ trống thì bỏ qua điều kiện rớt > 50%.
    """
    ly_do = []
    if tc_dang_ky_hk and tc_rot_hk is not None and tc_rot_hk > TI_LE_ROT_TOI_DA * tc_dang_ky_hk:
        ly_do.append("rớt quá 50% TC đăng ký trong học kỳ")
    if no_tc > NO_TC_TOI_DA:
        ly_do.append("nợ quá 24 TC")

    nguong_hk = NGUONG_DTB_HK_DAU if ky_dau else NGUONG_DTB_HK
    if dtb_hk < nguong_hk:
        ly_do.append(f"ĐTB học kỳ dưới {nguong_hk}")

    nguong_tl = NGUONG_DTB_TICH_LUY[trinh_do_nam(tctl)]
    if dtb_tl < nguong_tl:
        ly_do.append(f"ĐTB tích luỹ dưới {nguong_tl}")
    return ly_do


def gan_nhan_hoc_ky(bang_hoc_ky):
    """Thêm nhãn cảnh báo / buộc thôi học vào bảng học kỳ đọc từ form.

    Thêm các cột: no_tc, trinh_do, ly_do_canh_bao, canh_bao (0/1),
    so_lan_canh_bao_lien_tiep, buoc_thoi_hoc (0/1). Dòng thiếu số liệu điểm
    hoặc tín chỉ thì nhãn để trống (NA).

    Giới hạn: form không có số TC đăng ký riêng từng học kỳ nên không xét được
    điều kiện rớt > 50% TC trong kỳ; điều kiện ĐTB học kỳ thường bắt được các
    ca này.
    """
    bang = bang_hoc_ky.sort_values(["ma_sv", "hoc_ky"]).reset_index(drop=True)
    bang["no_tc"] = bang["tc_dang_ky"] - bang["tctl"]
    bang["trinh_do"] = bang["tctl"].map(trinh_do_nam, na_action="ignore")

    ly_do, canh_bao, lien_tiep, thoi_hoc = [], [], [], []
    dem, sv_truoc = 0, None
    for _, d in bang.iterrows():
        if d["ma_sv"] != sv_truoc:
            dem, sv_truoc = 0, d["ma_sv"]

        if d[["dtb_hk", "dtb_tl", "tctl", "tc_dang_ky"]].isna().any():
            ly_do.append(pd.NA)
            canh_bao.append(pd.NA)
            lien_tiep.append(pd.NA)
            thoi_hoc.append(pd.NA)
            dem = 0
            continue

        cac_ly_do = ly_do_canh_bao(d["dtb_hk"], d["dtb_tl"], d["tctl"], d["no_tc"],
                                   ky_dau=d["hoc_ky"] == 1)
        dem = dem + 1 if cac_ly_do else 0
        ly_do.append("; ".join(cac_ly_do))
        canh_bao.append(int(bool(cac_ly_do)))
        lien_tiep.append(dem)
        thoi_hoc.append(int(dem >= SO_LAN_CANH_BAO_THOI_HOC))

    bang["ly_do_canh_bao"] = ly_do
    bang["canh_bao"] = pd.array(canh_bao, dtype="Int64")
    bang["so_lan_canh_bao_lien_tiep"] = pd.array(lien_tiep, dtype="Int64")
    bang["buoc_thoi_hoc"] = pd.array(thoi_hoc, dtype="Int64")
    return bang


def gan_nhan_mon(bang_mon):
    """Thêm cột truot_mon (0/1) vào bảng môn; "Không muốn trả lời" để trống."""
    bang = bang_mon.copy()
    nhan = {"Đạt": 0, "Không đạt (điểm F)": 1, "Bị cấm thi": 1}
    bang["truot_mon"] = pd.array(bang["ket_qua"].map(nhan), dtype="Int64")
    return bang
