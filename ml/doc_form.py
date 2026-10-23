"""
Đọc file xlsx xuất từ Google Form khảo sát học tập.

File form có 1 dòng = 1 sinh viên, các học kỳ và các môn nằm ngang. Google Form
tự thêm hậu tố " 2", " 3"... cho câu hỏi trùng tiêu đề (học kỳ / môn thứ nhất
không có hậu tố). File này chuyển nó thành 2 bảng dọc:

- bảng học kỳ: 1 dòng = 1 sinh viên × 1 học kỳ chính đã học xong
- bảng môn:    1 dòng = 1 môn của học kỳ chính gần nhất

và kiểm tra số liệu từng sinh viên. Dữ liệu mô phỏng (mo_phong.py) xuất đúng
định dạng này nên dùng chung bộ đọc với dữ liệu thật.

Chạy thử:  python ml/doc_form.py "đường/dẫn/file.xlsx"
"""

import sys

import pandas as pd


SO_HOC_KY_TOI_DA = 12
SO_MON_TOI_DA = 10

# Câu hỏi chung (mỗi sinh viên một lần) -> tên cột trong bảng
CAU_CHUNG = {
    "Năm nhập học": "nam_nhap_hoc",
    "Ngành học": "nganh",
    "Hệ đào tạo": "he_dao_tao",
    "Tình trạng học tập hiện tại": "tinh_trang",
    "Trong thời gian học, bạn đã từng nhận hình thức kỷ luật nào chưa?": "ky_luat",
}

# Câu hỏi lặp lại mỗi học kỳ, đúng thứ tự trên form
CAU_HOC_KY = {
    "Số TC đạt học kỳ": "tc_dat_hk",
    "Điểm TB học kỳ (thang 4)": "dtb_hk",
    "Tổng số TC tích luỹ đến học kỳ này": "tctl",
    "Tổng số TC đăng ký đến học kỳ này": "tc_dang_ky",
    "Điểm TB tích luỹ (thang 4)": "dtb_tl",
    "Mức vắng học trung bình trong học kỳ này": "muc_vang",
    "Tình trạng học phí học kỳ này": "hoc_phi",
    "Điểm rèn luyện (thang 100)": "drl",
    "Học kỳ hè ngay sau học kỳ này bạn có học không?": "hoc_he",
}
COT_SO_HOC_KY = ["tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl"]

# Câu hỏi lặp lại mỗi môn (chi tiết học kỳ gần nhất)
CAU_MON = {
    "Tên môn học": "ten_mon",
    "Số tín chỉ của môn": "so_tc",
    "Kết quả cuối kỳ của môn này": "ket_qua",
    "Điểm giữa kỳ (thang 10)": "diem_gk",
    "Tỉ trọng điểm giữa kỳ của môn này": "ti_trong_gk",
    "Vắng giờ lý thuyết của môn này": "vang_lt",
    "Vắng buổi thực hành của môn này": "vang_th",
}

# Câu hỏi "đã học xong học kỳ k chưa?" — học kỳ 1 hỏi khác các kỳ sau
CAU_XONG_HK1 = "Bạn đã học xong ít nhất 1 học kỳ chính chưa?"
DA_HOC_XONG = "Đã học xong"
CHUA_XONG_HK1 = "Chưa (đang học học kỳ đầu tiên)"
CHUA_XONG = "Chưa"

# Các câu chỉ dùng để chuyển trang trên form
CAU_DONG_Y = "Bạn có đồng ý tham gia khảo sát với các điều kiện trên không?"
CAU_SO_MON = "Học kỳ đó bạn học tổng cộng bao nhiêu môn?"
CAU_MUON_CHI_TIET = "Bạn có muốn điền chi tiết từng môn của học kỳ chính gần nhất đã học xong không?"
CAU_DIEN_TIEP = "Bạn muốn điền tiếp môn khác hay dừng ở đây?"
CAU_GOP_Y = "Góp ý cho nhóm (nếu có)"

# Lựa chọn trả lời, chép từ khao_sat/tao_google_form.gs
MUC_VANG = ["Gần như không vắng (dưới 5% số buổi)", "Từ 5% đến dưới 10%",
            "Từ 10% đến 20%", "Trên 20%", "Không nhớ / không muốn trả lời"]
HOC_PHI = ["Đóng đủ, đúng hạn", "Đóng đủ nhưng trễ hạn", "Chưa đóng đủ trong học kỳ",
           "Được miễn học phí", "Không muốn trả lời"]
HOC_HE = ["Không học", "Chỉ học lại môn bị rớt", "Chỉ học thêm môn mới",
          "Cả học lại và học thêm môn mới"]
KET_QUA_MON = ["Đạt", "Không đạt (điểm F)", "Bị cấm thi", "Không muốn trả lời"]
VANG_LY_THUYET = ["Ít hoặc không vắng", "Khá nhiều nhưng chưa quá 20%", "Nhiều, trên 20%", "Không nhớ"]
VANG_THUC_HANH = ["Môn không có thực hành", "Không vắng buổi nào", "Có vắng từ 1 buổi trở lên", "Không nhớ"]
TINH_TRANG = ["Đang học", "Đang nghỉ học tạm thời", "Bị buộc thôi học", "Tự xin thôi học",
              "Đã tốt nghiệp", "Không muốn trả lời"]

# Ngưỡng hợp lý của số liệu, dùng khi kiểm tra
TC_HOC_KY_TOI_DA = 35       # số TC đạt trong một học kỳ chính (kể cả học lại)


def ten_cot(cau_goc, thu_tu):
    """Tên cột Google Form của câu hỏi lần thứ `thu_tu` (đánh số từ 1)."""
    return cau_goc if thu_tu == 1 else f"{cau_goc} {thu_tu}"


def cau_xong_hoc_ky(k):
    """Câu hỏi xác nhận đã học xong học kỳ chính thứ k."""
    return CAU_XONG_HK1 if k == 1 else f"Bạn đã học xong học kỳ chính thứ {k} chưa?"


def cac_cot_form():
    """Toàn bộ tên cột của file xlsx, đúng thứ tự Google Sheet xuất ra."""
    cot = ["Dấu thời gian", CAU_DONG_Y, "Năm nhập học", "Ngành học", "Hệ đào tạo"]
    for k in range(1, SO_HOC_KY_TOI_DA + 1):
        cot.append(cau_xong_hoc_ky(k))
        cot += [ten_cot(cau, k) for cau in CAU_HOC_KY]
    cot += [CAU_SO_MON, CAU_MUON_CHI_TIET]
    for m in range(1, SO_MON_TOI_DA + 1):
        cot += [ten_cot(cau, m) for cau in CAU_MON]
        if m < SO_MON_TOI_DA:
            cot.append(ten_cot(CAU_DIEN_TIEP, m))
    cot += ["Tình trạng học tập hiện tại",
            "Trong thời gian học, bạn đã từng nhận hình thức kỷ luật nào chưa?", CAU_GOP_Y]
    return cot


def doc_xlsx(duong_dan):
    """Đọc file xlsx của form, gán mã SV1, SV2... theo thứ tự dòng."""
    form = pd.read_excel(duong_dan)
    form.index = [f"SV{i + 1}" for i in range(len(form))]
    form.index.name = "ma_sv"
    return form


def tach_hoc_ky(form):
    """Bảng học kỳ: chỉ lấy các học kỳ sinh viên xác nhận đã học xong.

    Sinh viên trả lời lần lượt: học xong kỳ 1 chưa → số liệu kỳ 1 → học xong
    kỳ 2 chưa → ... nên dừng ở câu đầu tiên trả lời khác "Đã học xong".
    """
    cac_dong = []
    for ma_sv, sv in form.iterrows():
        for k in range(1, SO_HOC_KY_TOI_DA + 1):
            if sv.get(cau_xong_hoc_ky(k)) != DA_HOC_XONG:
                break
            dong = {"ma_sv": ma_sv, "hoc_ky": k}
            for cau, cot in CAU_HOC_KY.items():
                dong[cot] = sv.get(ten_cot(cau, k))
            cac_dong.append(dong)

    bang = pd.DataFrame(cac_dong, columns=["ma_sv", "hoc_ky", *CAU_HOC_KY.values()])
    bang[COT_SO_HOC_KY] = bang[COT_SO_HOC_KY].apply(pd.to_numeric, errors="coerce")
    return bang


def tach_mon(form, bang_hoc_ky):
    """Bảng môn: các môn sinh viên điền chi tiết, gắn với học kỳ gần nhất."""
    hoc_ky_cuoi = bang_hoc_ky.groupby("ma_sv")["hoc_ky"].max()

    cac_dong = []
    for ma_sv, sv in form.iterrows():
        for m in range(1, SO_MON_TOI_DA + 1):
            mon = {cot: sv.get(ten_cot(cau, m)) for cau, cot in CAU_MON.items()}
            # Môn chưa điền thì cả số TC lẫn kết quả đều trống
            if pd.isna(mon["so_tc"]) and pd.isna(mon["ket_qua"]):
                continue
            cac_dong.append({"ma_sv": ma_sv, "hoc_ky": hoc_ky_cuoi.get(ma_sv),
                             "stt_mon": m, **mon})

    bang = pd.DataFrame(cac_dong, columns=["ma_sv", "hoc_ky", "stt_mon", *CAU_MON.values()])
    for cot in ["so_tc", "diem_gk", "ti_trong_gk"]:
        bang[cot] = pd.to_numeric(bang[cot], errors="coerce")
    return bang


def tach_sinh_vien(form):
    """Bảng sinh viên: thông tin chung, mỗi sinh viên một dòng."""
    bang = pd.DataFrame(index=form.index)
    for cau, cot in CAU_CHUNG.items():
        bang[cot] = form.get(cau)
    bang["nganh"] = bang["nganh"].astype("string").str.strip()
    bang["so_mon_hk_cuoi"] = pd.to_numeric(form.get(CAU_SO_MON), errors="coerce")
    return bang


def kiem_tra(bang_hoc_ky, sinh_vien):
    """Liệt kê lỗi số liệu của từng sinh viên.

    Trả về dict {ma_sv: [mô tả lỗi, ...]}; sinh viên không có lỗi thì danh
    sách rỗng. Quy tắc tín chỉ: TC đăng ký là lũy kế, học lại không cộng thêm
    nên TC đăng ký luôn >= TCTL, và cả hai không giảm theo học kỳ.
    """
    loi = {ma_sv: [] for ma_sv in sinh_vien.index}

    for ma_sv in sinh_vien.index:
        hk = bang_hoc_ky[bang_hoc_ky["ma_sv"] == ma_sv].sort_values("hoc_ky")
        if hk.empty:
            loi[ma_sv].append("không có học kỳ nào đã học xong")
            continue

        thieu = hk[hk[["tc_dat_hk", "tctl", "tc_dang_ky", "dtb_hk", "dtb_tl"]].isna().any(axis=1)]
        for k in thieu["hoc_ky"]:
            loi[ma_sv].append(f"HK{k}: thiếu số liệu TC/điểm")

        for _, d in hk.iterrows():
            k = d["hoc_ky"]
            if d["tc_dang_ky"] < d["tctl"]:
                loi[ma_sv].append(f"HK{k}: TC đăng ký ({d['tc_dang_ky']:g}) < TCTL ({d['tctl']:g})")
            if d["tc_dat_hk"] > TC_HOC_KY_TOI_DA:
                loi[ma_sv].append(f"HK{k}: TC đạt học kỳ = {d['tc_dat_hk']:g}, quá lớn")
            for cot, cao in [("dtb_hk", 4), ("dtb_tl", 4), ("drl", 100)]:
                if not pd.isna(d[cot]) and not 0 <= d[cot] <= cao:
                    loi[ma_sv].append(f"HK{k}: {cot} = {d[cot]:g} ngoài 0–{cao}")

        # Kỳ 1 chưa có gì tích luỹ trước đó nên TCTL phải bằng TC đạt kỳ 1
        hk1 = hk.iloc[0]
        if hk1["hoc_ky"] == 1 and hk1["tctl"] != hk1["tc_dat_hk"]:
            loi[ma_sv].append(f"HK1: TCTL ({hk1['tctl']:g}) khác TC đạt học kỳ "
                              f"({hk1['tc_dat_hk']:g}) — có thể điền số tích luỹ hiện tại")

        for cot in ["tctl", "tc_dang_ky"]:
            giam = hk[hk[cot].diff() < 0]
            for k in giam["hoc_ky"]:
                loi[ma_sv].append(f"HK{k}: {cot} giảm so với kỳ trước")

    return loi


def doc_form(duong_dan):
    """Đọc file form, trả về (sinh_vien, bang_hoc_ky, bang_mon).

    Bảng sinh viên có thêm cột `hop_le` và `loi` (chuỗi các lỗi, nối bằng "; ").
    """
    form = doc_xlsx(duong_dan)
    sinh_vien = tach_sinh_vien(form)
    bang_hoc_ky = tach_hoc_ky(form)
    bang_mon = tach_mon(form, bang_hoc_ky)

    loi = kiem_tra(bang_hoc_ky, sinh_vien)
    sinh_vien["hop_le"] = [not loi[ma_sv] for ma_sv in sinh_vien.index]
    sinh_vien["loi"] = ["; ".join(loi[ma_sv]) for ma_sv in sinh_vien.index]
    return sinh_vien, bang_hoc_ky, bang_mon


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    sinh_vien, bang_hoc_ky, bang_mon = doc_form(sys.argv[1])
    print(f"{len(sinh_vien)} sinh viên, {len(bang_hoc_ky)} dòng học kỳ, {len(bang_mon)} dòng môn")
    print(f"Hợp lệ: {', '.join(sinh_vien.index[sinh_vien['hop_le']])}\n")
    for ma_sv, sv in sinh_vien[~sinh_vien["hop_le"]].iterrows():
        print(f"{ma_sv}: {sv['loi']}")
    print("\nBảng học kỳ (5 dòng đầu):")
    print(bang_hoc_ky.head())
    print("\nBảng môn (5 dòng đầu):")
    print(bang_mon.head())
