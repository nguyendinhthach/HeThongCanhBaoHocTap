"""
Mô phỏng dữ liệu học tập của sinh viên, xuất đúng định dạng xlsx của Google Form.

Khảo sát thật chỉ có 9 câu trả lời, không ai bị cảnh báo hay thôi học, nên mô
hình không có ca dương để học. File này sinh sinh viên ảo bằng luật (không dùng
AI): mỗi sinh viên có năng lực ẩn, thói quen vắng học, điểm rèn luyện; chạy lần
lượt từng học kỳ chính:

  đăng ký môn mới + học lại môn nợ -> điểm từng môn -> cập nhật TCTL, TC đăng
  ký, nợ -> ĐTB học kỳ / tích luỹ -> xét cảnh báo (QĐ 600) -> học kỳ hè

và dừng khi sinh viên tốt nghiệp, bị buộc thôi học hoặc tới học kỳ hiện tại.
Cố định seed nên chạy lại ra đúng dữ liệu cũ.

File xuất có 4 sheet:
- sheet đầu: giống hệt file Google Form, đọc bằng doc_form.py như dữ liệu thật;
- "hoc_ky", "mon": cùng dữ liệu đó dạng dọc, chỉ để mở Excel xem cho dễ;
- "nhan_that": nhãn tính từ đầy đủ thông tin mô phỏng (kể cả số TC rớt trong
  kỳ mà form không hỏi), dùng để đối chiếu với nhãn gán từ form.

Chạy:  python ml/mo_phong.py --so-sv 1000 --seed 2026
"""

import argparse
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import doc_form as form
from gan_nhan import DIEM_DAT, SO_LAN_CANH_BAO_THOI_HOC, ly_do_canh_bao, quy_doi_thang_4


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_DAN_MAC_DINH = os.path.join(THU_MUC_GOC, "data", "mo_phong.xlsx")

# --- Bối cảnh khảo sát -------------------------------------------------------
# Khảo sát tháng 10/2026: sinh viên nhập học năm y đã học xong 2 × (2026 − y)
# học kỳ chính (tối đa 12, bằng số trang học kỳ của form). Thời gian tối đa
# gấp đôi chuẩn (16–18 học kỳ) nên trong 12 học kỳ không ai bị thôi học vì hết hạn.
NAM_KHAO_SAT = 2026
CAC_NAM_NHAP_HOC = [2020, 2021, 2022, 2023, 2024, 2025]
TI_LE_NAM_NHAP_HOC = [0.05, 0.10, 0.20, 0.25, 0.20, 0.20]

# Hệ đào tạo -> (số học kỳ chuẩn, tổng TC chương trình ít nhất, nhiều nhất).
# Giả định, không lấy từ quy chế (QĐ 600 chỉ quy định 4 / 4,5 năm, Điều 5.2a);
# mỗi sinh viên lấy ngẫu nhiên trong khoảng. Con số này chỉ quyết định lúc hết
# môn mới để đăng ký và lúc tốt nghiệp, không dùng trong luật gán nhãn.
HE_DAO_TAO = {"Cử nhân (4 năm)": (8, 125, 140), "Kỹ sư (4,5 năm)": (9, 150, 160)}

# 41 ngành đại học chính quy của Trường ĐH Đà Lạt, theo trang chính thức
# https://dlu.edu.vn/cac-nganh-dao-tao-chinh-quy/ (tra ngày 21/10/2026);
# mỗi sinh viên chọn ngẫu nhiên đều nhau.
CAC_NGANH = [
    "Sư phạm Toán học", "Sư phạm Vật lý", "Sư phạm Hóa học", "Sư phạm Sinh học",
    "Sư phạm Ngữ văn", "Sư phạm Lịch sử", "Sư phạm Tiếng Anh", "Sư phạm Tin học",
    "Giáo dục tiểu học", "Toán học", "Khoa học dữ liệu", "Công nghệ thông tin", "Vật lý học",
    "Công nghệ kỹ thuật điện tử - viễn thông", "Kỹ thuật hạt nhân",
    "Công nghệ kỹ thuật điều khiển và tự động hóa", "Hóa học", "Hóa dược",
    "Công nghệ kỹ thuật môi trường", "Sinh học", "Công nghệ sinh học", "Quản trị kinh doanh",
    "Kế toán", "Tài chính - Ngân hàng", "Công nghệ thực phẩm", "Nông học",
    "Công nghệ sau thu hoạch", "Luật", "Luật hình sự và tố tụng hình sự",
    "Quản trị dịch vụ du lịch và lữ hành", "Việt Nam học", "Đông phương học", "Quốc tế học",
    "Văn học", "Văn hóa du lịch", "Trung Quốc học", "Lịch sử", "Công tác xã hội",
    "Dân số và phát triển", "Xã hội học", "Ngôn ngữ Anh",
]
# Các ngành cấp bằng kỹ sư (cùng trang trên, cột "Tên gọi văn bằng"); còn lại cử nhân
NGANH_KY_SU = {
    "Khoa học dữ liệu", "Công nghệ thông tin", "Công nghệ kỹ thuật điện tử - viễn thông",
    "Kỹ thuật hạt nhân", "Công nghệ kỹ thuật điều khiển và tự động hóa",
    "Công nghệ thực phẩm", "Nông học", "Công nghệ sau thu hoạch",
}

# --- Đăng ký môn -------------------------------------------------------------
SO_TC_MON = [2, 3, 3, 3, 4]
TC_HK_TB, TC_HK_LECH = 18, 4        # TC môn mới mỗi học kỳ ~ 18 ± 4
TC_HK_IT_NHAT, TC_HK_NHIEU_NHAT = 10, 25
XS_HOC_LAI = 0.6                    # xác suất học lại mỗi môn nợ ở học kỳ chính

# --- Điểm --------------------------------------------------------------------
DIEM_TB = 7.4                       # điểm môn (thang 10) của sinh viên năng lực 0
DIEM_THEO_NANG_LUC = 1.2            # mỗi độ lệch chuẩn năng lực cộng thêm bấy nhiêu điểm
NHIEU_MON = 1.0                     # độ khó / may rủi từng môn
NHIEU_HOC_KY = 0.35                 # học kỳ tốt / xấu của từng sinh viên
XU_HUONG_LECH = 0.08                # tiến bộ hoặc sa sút dần theo học kỳ
THUONG_HOC_LAI = 0.3                # học lại thường khá hơn lần đầu
# Giả định về hành vi học tập (vắng nhiều thì học kém hơn), không phải cách
# giảng viên chấm điểm: mỗi 1% vắng làm giảm năng lực học kỳ bấy nhiêu
ANH_HUONG_VANG = 0.05
CAC_TI_TRONG_GK = [0.2, 0.3, 0.4, 0.5]
TI_LE_TI_TRONG_GK = [0.05, 0.2, 0.25, 0.5]

# --- Vắng học (Điều 14.7: vắng > 20% giờ lý thuyết hoặc thiếu buổi thực hành -> cấm thi)
VANG_TB, VANG_LECH = 3.5, 4           # % vắng trung bình của sinh viên
TI_LE_MON_CO_TH = 0.4

# --- Điểm rèn luyện, học phí, học kỳ hè -------------------------------------
DRL_TB, DRL_LECH = 82, 7
XS_THIEU_DRL = 0.05                 # sinh viên bỏ trống ô điểm rèn luyện
TI_LE_HOC_PHI = [0.86, 0.08, 0.01, 0.04, 0.01]
XS_HE_HOC_LAI = 0.4
XS_HE_MON_MOI = 0.3
XS_DIEN_CHI_TIET = 0.85
XS_VANG_KHONG_NHO = 0.03


def phan_loai_vang(vang):
    """% vắng của học kỳ -> lựa chọn "Mức vắng" trên form."""
    if vang < 5:
        return form.MUC_VANG[0]
    if vang < 10:
        return form.MUC_VANG[1]
    if vang <= 20:
        return form.MUC_VANG[2]
    return form.MUC_VANG[3]


def phan_loai_vang_ly_thuyet(vang):
    """% vắng lý thuyết của một môn -> lựa chọn trên form."""
    if vang < 8:
        return form.VANG_LY_THUYET[0]
    if vang <= 20:
        return form.VANG_LY_THUYET[1]
    return form.VANG_LY_THUYET[2]


def tao_mon_moi(rng, so_tc, ma_tiep):
    """Danh sách môn mới có tổng đúng `so_tc` TC; trả về (môn, mã kế tiếp)."""
    cac_mon = []
    while so_tc > 0:
        tc = min(int(rng.choice(SO_TC_MON)), so_tc)
        cac_mon.append({"ma": ma_tiep, "tc": tc})
        ma_tiep += 1
        so_tc -= tc
    return cac_mon, ma_tiep


def hoc_mot_mon(rng, mon, nang_luc_hk, vang_hk, hoc_lai):
    """Kết quả một môn: điểm giữa kỳ, điểm học phần, cấm thi..."""
    vang_lt = float(np.clip(vang_hk + rng.normal(0, 4), 0, 60))
    co_th = rng.random() < TI_LE_MON_CO_TH
    vang_th = co_th and rng.random() < 0.01 * max(vang_hk - 3, 0)
    cam_thi = vang_lt > 20 or vang_th

    ti_trong = float(rng.choice(CAC_TI_TRONG_GK, p=TI_LE_TI_TRONG_GK))
    muc = DIEM_TB + DIEM_THEO_NANG_LUC * nang_luc_hk + rng.normal(0, NHIEU_MON)
    if hoc_lai:
        muc += THUONG_HOC_LAI

    # Điểm giữa kỳ thường là điểm quá trình (chuyên cần, bài tập cá nhân / nhóm)
    # nên sinh viên bị cấm thi vẫn có. Cách chấm tuỳ giảng viên nên không áp
    # công thức riêng, chỉ lệch ngẫu nhiên quanh mức năng lực như điểm cuối kỳ.
    diem_gk = round(float(np.clip(muc + rng.normal(0, 0.8), 0, 10)), 1)
    if cam_thi:
        diem = 0.0   # Điều 13.4e: bị cấm thi nhận điểm 0
    else:
        diem_ck = round(float(np.clip(muc + rng.normal(0, 1.0), 0, 10)), 1)
        diem = round(ti_trong * diem_gk + (1 - ti_trong) * diem_ck, 1)

    return {**mon, "hoc_lai": hoc_lai, "diem_gk": diem_gk, "ti_trong_gk": ti_trong,
            "diem": diem, "diem_4": quy_doi_thang_4(diem), "dat": diem >= DIEM_DAT,
            "cam_thi": cam_thi, "vang_lt": vang_lt, "co_th": co_th, "vang_th": vang_th}


class SinhVienAo:
    """Trạng thái học tập của một sinh viên ảo qua từng học kỳ.

    Quy tắc tín chỉ (rút ra từ dữ liệu thật): TC đăng ký là lũy kế, mỗi môn
    chỉ tính một lần — học lại không cộng thêm; TCTL cộng khi môn đạt; nợ =
    TC đăng ký − TCTL = tổng TC các môn đang nợ.
    """

    def __init__(self, rng):
        self.rng = rng
        self.nam_nhap_hoc = int(rng.choice(CAC_NAM_NHAP_HOC, p=TI_LE_NAM_NHAP_HOC))
        self.nganh = str(rng.choice(CAC_NGANH))
        self.he = "Kỹ sư (4,5 năm)" if self.nganh in NGANH_KY_SU else "Cử nhân (4 năm)"
        self.so_hk_chuan, tc_it_nhat, tc_nhieu_nhat = HE_DAO_TAO[self.he]
        self.tong_tc = int(rng.integers(tc_it_nhat, tc_nhieu_nhat + 1))

        # Năng lực ẩn; sinh viên yếu hơn có xu hướng vắng nhiều hơn
        self.nang_luc = rng.normal()
        z_vang = -0.4 * self.nang_luc + np.sqrt(1 - 0.4 ** 2) * rng.normal()
        self.vang = float(np.clip(VANG_TB + VANG_LECH * z_vang, 0, 35))
        self.xu_huong = rng.normal(0, XU_HUONG_LECH)
        self.drl = DRL_TB + DRL_LECH * rng.normal() + 3 * self.nang_luc

        self.tc_dang_ky = 0
        self.tctl = 0
        self.diem_dat = {}       # mã môn -> (TC, điểm thang 4) của môn đã đạt
        self.no = {}             # mã môn -> TC của môn đang nợ
        self.ma_tiep = 0
        self.lan_canh_bao = 0
        self.tinh_trang = "Đang học"

        self.hoc_ky = []         # mỗi phần tử: số liệu một học kỳ chính
        self.mon_hk_cuoi = []    # kết quả từng môn của học kỳ chính gần nhất

    def dtb_tich_luy(self):
        """ĐTB tích luỹ: chỉ các môn đã đạt (Điều 15.4)."""
        if not self.diem_dat:
            return 0.0
        tong = sum(tc * d for tc, d in self.diem_dat.values())
        return round(tong / sum(tc for tc, _ in self.diem_dat.values()), 2)

    def ghi_ket_qua(self, kq):
        """Cập nhật TCTL, nợ sau khi có kết quả một môn."""
        if kq["dat"]:
            self.tctl += kq["tc"]
            self.diem_dat[kq["ma"]] = (kq["tc"], kq["diem_4"])
            self.no.pop(kq["ma"], None)
        else:
            self.no[kq["ma"]] = kq["tc"]

    def hoc(self, cac_mon_moi, cac_mon_lai, nang_luc_hk, vang_hk):
        """Học một đợt (học kỳ chính hoặc hè), trả về kết quả từng môn."""
        self.tc_dang_ky += sum(m["tc"] for m in cac_mon_moi)
        ket_qua = [hoc_mot_mon(self.rng, m, nang_luc_hk, vang_hk, False) for m in cac_mon_moi]
        ket_qua += [hoc_mot_mon(self.rng, m, nang_luc_hk, vang_hk, True) for m in cac_mon_lai]
        for kq in ket_qua:
            self.ghi_ket_qua(kq)
        return ket_qua

    def hoc_ky_chinh(self, k):
        """Mô phỏng học kỳ chính thứ k; trả về False nếu phải dừng sau kỳ này."""
        rng = self.rng
        cac_mon_lai = [{"ma": ma, "tc": tc} for ma, tc in self.no.items() if rng.random() < XS_HOC_LAI]
        tc_lai = sum(m["tc"] for m in cac_mon_lai)

        con_lai = self.tong_tc - self.tc_dang_ky
        muc_tieu = int(np.clip(round(rng.normal(TC_HK_TB, TC_HK_LECH)), TC_HK_IT_NHAT, TC_HK_NHIEU_NHAT))
        tc_moi = max(min(muc_tieu, con_lai, TC_HK_NHIEU_NHAT - tc_lai), 0)
        if tc_moi == 0 and not cac_mon_lai:
            # Đã đăng ký hết chương trình, chỉ còn môn nợ: bắt buộc học lại
            cac_mon_lai = [{"ma": ma, "tc": tc} for ma, tc in self.no.items()]
        cac_mon_moi, self.ma_tiep = tao_mon_moi(rng, tc_moi, self.ma_tiep)

        vang_hk = float(np.clip(self.vang + rng.normal(0, 3), 0, 40))
        nang_luc_hk = (self.nang_luc + self.xu_huong * (k - 1) + rng.normal(0, NHIEU_HOC_KY)
                       - ANH_HUONG_VANG * vang_hk)
        ket_qua = self.hoc(cac_mon_moi, cac_mon_lai, nang_luc_hk, vang_hk)

        tc_hk = sum(kq["tc"] for kq in ket_qua)
        tc_dat_hk = sum(kq["tc"] for kq in ket_qua if kq["dat"])
        dtb_hk = round(sum(kq["tc"] * kq["diem_4"] for kq in ket_qua) / tc_hk, 2)
        dtb_tl = self.dtb_tich_luy()
        no_tc = self.tc_dang_ky - self.tctl

        ly_do = ly_do_canh_bao(dtb_hk, dtb_tl, self.tctl, no_tc, ky_dau=k == 1,
                               tc_rot_hk=tc_hk - tc_dat_hk, tc_dang_ky_hk=tc_hk)
        self.lan_canh_bao = self.lan_canh_bao + 1 if ly_do else 0
        buoc_thoi_hoc = self.lan_canh_bao >= SO_LAN_CANH_BAO_THOI_HOC

        drl = float(np.clip(round(self.drl + rng.normal(0, 5) - 0.5 * max(vang_hk - 10, 0)), 30, 100))
        self.hoc_ky.append({
            "hoc_ky": k, "tc_dat_hk": tc_dat_hk, "dtb_hk": dtb_hk, "tctl": self.tctl,
            "tc_dang_ky": self.tc_dang_ky, "dtb_tl": dtb_tl,
            "muc_vang": (form.MUC_VANG[4] if rng.random() < XS_VANG_KHONG_NHO
                         else phan_loai_vang(vang_hk)),
            "hoc_phi": str(rng.choice(form.HOC_PHI, p=TI_LE_HOC_PHI)),
            "drl": np.nan if rng.random() < XS_THIEU_DRL else drl,
            "hoc_he": form.HOC_HE[0],
            # Nhãn thật — không xuất ra sheet form
            "tc_dang_ky_hk": tc_hk, "tc_rot_hk": tc_hk - tc_dat_hk, "no_tc": no_tc,
            "ly_do_canh_bao": "; ".join(ly_do), "canh_bao": int(bool(ly_do)),
            "so_lan_canh_bao_lien_tiep": self.lan_canh_bao, "buoc_thoi_hoc": int(buoc_thoi_hoc),
        })
        self.mon_hk_cuoi = ket_qua

        if buoc_thoi_hoc:
            self.tinh_trang = "Bị buộc thôi học"
            return False
        if self.tctl >= self.tong_tc:
            self.tinh_trang = "Đã tốt nghiệp"
            return False
        if k % 2 == 0:
            self.hoc_ky[-1]["hoc_he"] = self.hoc_ky_he(nang_luc_hk, vang_hk)
        return True

    def hoc_ky_he(self, nang_luc, vang):
        """Học kỳ hè sau học kỳ chính thứ 2, 4...; kết quả gộp vào số lũy kế
        của học kỳ chính sau (Điều 15.8), không tính vào TC đạt học kỳ."""
        rng = self.rng
        hoc_lai = bool(self.no) and rng.random() < XS_HE_HOC_LAI
        con_lai = self.tong_tc - self.tc_dang_ky
        mon_moi = con_lai > 0 and rng.random() < XS_HE_MON_MOI

        cac_mon_lai = [{"ma": ma, "tc": tc} for ma, tc in list(self.no.items())[:2]] if hoc_lai else []
        cac_mon_moi = []
        if mon_moi:
            cac_mon_moi, self.ma_tiep = tao_mon_moi(rng, min(int(rng.choice([3, 6])), con_lai), self.ma_tiep)
        self.hoc(cac_mon_moi, cac_mon_lai, nang_luc, vang)

        return form.HOC_HE[(1 if hoc_lai else 0) + (2 if mon_moi else 0)]

    def mo_phong(self):
        so_hk = min(2 * (NAM_KHAO_SAT - self.nam_nhap_hoc), form.SO_HOC_KY_TOI_DA)
        for k in range(1, so_hk + 1):
            if self.tctl >= self.tong_tc:
                # Đủ tín chỉ nhờ học kỳ hè vừa rồi
                self.tinh_trang = "Đã tốt nghiệp"
                break
            if not self.hoc_ky_chinh(k):
                break
        return self


def dong_form(sv, thoi_diem):
    """Một dòng của file Google Form cho sinh viên ảo."""
    rng = sv.rng
    dong = {"Dấu thời gian": thoi_diem, form.CAU_DONG_Y: "Tôi đồng ý tham gia",
            "Năm nhập học": sv.nam_nhap_hoc, "Ngành học": sv.nganh, "Hệ đào tạo": sv.he}

    cau_so_lieu = {cot: cau for cau, cot in form.CAU_HOC_KY.items()}
    for hk in sv.hoc_ky:
        k = hk["hoc_ky"]
        dong[form.cau_xong_hoc_ky(k)] = form.DA_HOC_XONG
        for cot, cau in cau_so_lieu.items():
            dong[form.ten_cot(cau, k)] = hk[cot]

    k_tiep = len(sv.hoc_ky) + 1
    if k_tiep <= form.SO_HOC_KY_TOI_DA:
        dong[form.cau_xong_hoc_ky(k_tiep)] = form.CHUA_XONG_HK1 if k_tiep == 1 else form.CHUA_XONG

    if sv.hoc_ky and len(sv.hoc_ky) < form.SO_HOC_KY_TOI_DA:
        dong[form.CAU_SO_MON] = len(sv.mon_hk_cuoi)
        dien = rng.random() < XS_DIEN_CHI_TIET
        dong[form.CAU_MUON_CHI_TIET] = "Có" if dien else "Không, bỏ qua phần này"
        cac_mon = sv.mon_hk_cuoi[:form.SO_MON_TOI_DA] if dien else []
        cau_mon = {cot: cau for cau, cot in form.CAU_MON.items()}
        for m, kq in enumerate(cac_mon, start=1):
            if kq["cam_thi"]:
                ket_qua = "Bị cấm thi"
            else:
                ket_qua = "Đạt" if kq["dat"] else "Không đạt (điểm F)"
            gia_tri = {
                "so_tc": kq["tc"], "ket_qua": ket_qua, "diem_gk": kq["diem_gk"],
                "ti_trong_gk": kq["ti_trong_gk"],
                "vang_lt": phan_loai_vang_ly_thuyet(kq["vang_lt"]),
                "vang_th": (form.VANG_THUC_HANH[0] if not kq["co_th"]
                            else form.VANG_THUC_HANH[2] if kq["vang_th"] else form.VANG_THUC_HANH[1]),
            }
            for cot, gt in gia_tri.items():
                dong[form.ten_cot(cau_mon[cot], m)] = gt
            if m < form.SO_MON_TOI_DA:
                dong[form.ten_cot(form.CAU_DIEN_TIEP, m)] = "Điền tiếp" if m < len(cac_mon) else "Dừng ở đây"

    dong["Tình trạng học tập hiện tại"] = sv.tinh_trang
    dong["Trong thời gian học, bạn đã từng nhận hình thức kỷ luật nào chưa?"] = (
        "Khiển trách" if rng.random() < 0.03 else "Chưa")
    return dong


def mo_phong(so_sv, seed):
    """Sinh `so_sv` sinh viên ảo; trả về (bảng form, bảng nhãn thật)."""
    rng = np.random.default_rng(seed)
    bat_dau = datetime(NAM_KHAO_SAT, 10, 16, 8, 0)

    cac_dong, cac_nhan = [], []
    for i in range(so_sv):
        sv = SinhVienAo(rng).mo_phong()
        thoi_diem = bat_dau + timedelta(minutes=int(rng.integers(0, 5 * 24 * 60)))
        cac_dong.append(dong_form(sv, thoi_diem))
        for hk in sv.hoc_ky:
            cac_nhan.append({"ma_sv": f"SV{i + 1}", "nang_luc": round(sv.nang_luc, 3), **hk})

    bang_form = pd.DataFrame(cac_dong).reindex(columns=form.cac_cot_form())
    cot_nhan = ["ma_sv", "hoc_ky", "nang_luc", "tc_dang_ky_hk", "tc_rot_hk", "no_tc",
                "ly_do_canh_bao", "canh_bao", "so_lan_canh_bao_lien_tiep", "buoc_thoi_hoc"]
    return bang_form, pd.DataFrame(cac_nhan)[cot_nhan]


def ghi_xlsx(bang_form, bang_nhan, duong_dan):
    """Ghi sheet form (đọc bằng doc_form.py) + các sheet phụ để xem bằng mắt.

    Sheet "hoc_ky" và "mon" là bảng dọc (1 dòng = 1 SV × 1 học kỳ / 1 môn),
    tách từ chính sheet form nên luôn khớp với nó; code không đọc hai sheet này.
    """
    co_ma_sv = bang_form.set_axis([f"SV{i + 1}" for i in range(len(bang_form))])
    bang_hoc_ky = form.tach_hoc_ky(co_ma_sv)
    bang_mon = form.tach_mon(co_ma_sv, bang_hoc_ky)

    os.makedirs(os.path.dirname(os.path.abspath(duong_dan)), exist_ok=True)
    with pd.ExcelWriter(duong_dan) as ghi:
        bang_form.to_excel(ghi, sheet_name="Câu trả lời biểu mẫu 1", index=False)
        bang_hoc_ky.to_excel(ghi, sheet_name="hoc_ky", index=False)
        bang_mon.to_excel(ghi, sheet_name="mon", index=False)
        bang_nhan.to_excel(ghi, sheet_name="nhan_that", index=False)


def tom_tat(bang_nhan, sinh_vien):
    """In vài con số để chỉnh tham số mô phỏng."""
    so_sv = len(sinh_vien)
    print(f"{so_sv} sinh viên, {len(bang_nhan)} dòng học kỳ")
    print(f"Tỉ lệ học kỳ bị cảnh báo: {bang_nhan['canh_bao'].mean():.1%}")
    print(f"Sinh viên từng bị cảnh báo: {bang_nhan.groupby('ma_sv')['canh_bao'].max().mean():.1%}")
    print("Tình trạng:")
    print(sinh_vien["tinh_trang"].value_counts().to_string())
    print("Lý do cảnh báo (một học kỳ có thể nhiều lý do):")
    print(bang_nhan["ly_do_canh_bao"].str.split("; ").explode().loc[lambda s: s != ""]
          .value_counts().to_string())


if __name__ == "__main__":
    tham_so = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    tham_so.add_argument("--so-sv", type=int, default=1000)
    tham_so.add_argument("--seed", type=int, default=2026)
    tham_so.add_argument("--ra", default=DUONG_DAN_MAC_DINH, help="file xlsx xuất ra")
    a = tham_so.parse_args()

    bang_form, bang_nhan = mo_phong(a.so_sv, a.seed)
    ghi_xlsx(bang_form, bang_nhan, a.ra)
    print(f"Đã ghi {a.ra}\n")

    sinh_vien, _, _ = form.doc_form(a.ra)
    tom_tat(bang_nhan, sinh_vien)
