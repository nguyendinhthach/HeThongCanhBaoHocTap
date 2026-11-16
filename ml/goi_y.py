"""
Gợi ý cải thiện (đề cương mục 2.2): những việc cụ thể, có con số, sinh viên
làm được để tránh nguy cơ mà mô hình báo.

Gợi ý tính bằng LUẬT từ số liệu và quy chế QĐ 600, không dùng học máy: con số
phải đúng tuyệt đối (điểm thi cần đạt, ngưỡng ĐTB), còn học máy lo phần dự
đoán. Không có việc gì cần làm thì trả list rỗng — không viết câu chung chung
kiểu "hãy cố gắng".

- goi_y_mon(): một môn đang học — điểm thi cuối kỳ cần đạt, mức vắng.
- goi_y_hoc_ky(): cảnh báo học tập / buộc thôi học ở học kỳ kế tiếp — ĐTB cần
  đạt, nợ tín chỉ, ĐTB đang giảm, số kỳ bị cảnh báo liên tiếp.
"""

import math

import numpy as np
import pandas as pd

import doc_form as form
from gan_nhan import (DIEM_DAT, NGUONG_DTB_HK, NO_TC_TOI_DA, NGUONG_DTB_TICH_LUY,
                      SO_LAN_CANH_BAO_THOI_HOC, gan_nhan_hoc_ky, trinh_do_nam)

DIEM_C = 5.5                 # Điều 13.5a: 5,5 trở lên là điểm C (2 trên thang 4)
TC_KY_TOI_MAC_DINH = 18      # số TC kỳ tới khi chưa có lịch sử để ước lượng
NO_TC_NHAC = 16              # nợ từ mức này là nhắc trước (cảnh báo khi > 24)
DTB_GIAM_NHAC = 0.5          # ĐTB học kỳ giảm từ mức này so với kỳ trước...
DTB_GIAM_CON_DUOI = 2.5      # ...và còn dưới mức này (dưới loại Khá) thì mới nhắc


def _so(x):
    """Số kiểu Việt Nam cho câu gợi ý, tối đa 2 chữ số lẻ: 4.3 -> "4,3", 1.53 -> "1,53", 4.0 -> "4"."""
    return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def diem_cuoi_ky_can_dat(diem_gk, ti_trong_gk, diem_muc_tieu=DIEM_DAT):
    """Điểm thi cuối kỳ tối thiểu (thang 10, làm tròn LÊN 0,1) để điểm học phần
    = tỉ trọng × giữa kỳ + (1 − tỉ trọng) × cuối kỳ đạt `diem_muc_tieu`.

    Trả về 0 nếu giữa kỳ đã đủ, None nếu thiếu số liệu. Có thể > 10 (không
    thể đạt) — bên gọi tự xử lý.
    """
    if diem_gk is None or ti_trong_gk is None or pd.isna(diem_gk) or pd.isna(ti_trong_gk):
        return None
    if not 0 < ti_trong_gk < 1:
        return None
    can = (diem_muc_tieu - ti_trong_gk * diem_gk) / (1 - ti_trong_gk)
    return max(0.0, math.ceil(round(can * 10, 6)) / 10)


def goi_y_mon(diem_gk, ti_trong_gk, vang_lt=None, vang_th=None):
    """Gợi ý cho một môn đang học (list chuỗi, có thể rỗng)."""
    goi_y = []
    if vang_lt == form.VANG_LY_THUYET[2]:
        goi_y.append("Vắng lý thuyết trên 20% thuộc diện bị cấm thi (QĐ 600, Điều 14.7): "
                     "liên hệ giảng viên ngay để biết còn được dự thi không.")
    elif vang_lt == form.VANG_LY_THUYET[1]:
        goi_y.append("Vắng lý thuyết đã khá nhiều: vắng quá 20% số giờ là bị cấm thi.")
    if vang_th == form.VANG_THUC_HANH[2]:
        goi_y.append("Có vắng buổi thực hành: quy chế yêu cầu dự đủ 100% giờ thực hành, "
                     "nên hỏi giảng viên về việc học bù.")

    can_qua = diem_cuoi_ky_can_dat(diem_gk, ti_trong_gk, DIEM_DAT)
    if can_qua is None:
        return goi_y
    if can_qua > 10:
        goi_y.append(f"Dù đạt 10 điểm thi cuối kỳ, điểm học phần vẫn dưới {_so(DIEM_DAT)}: "
                     "nên trao đổi với giảng viên và chuẩn bị kế hoạch học lại.")
        return goi_y
    if can_qua == 0:
        return goi_y            # giữa kỳ đã đủ qua môn: không cần nhắc thêm mốc điểm
    goi_y.append(f"Cần ít nhất {_so(can_qua)} điểm thi cuối kỳ để qua môn "
                 f"(điểm học phần từ {_so(DIEM_DAT)}).")
    can_c = diem_cuoi_ky_can_dat(diem_gk, ti_trong_gk, DIEM_C)
    if can_c is not None and can_c <= 10:
        goi_y.append(f"Đạt {_so(can_c)} điểm thi cuối kỳ thì môn được điểm C trở lên "
                     f"(điểm học phần từ {_so(DIEM_C)}).")
    return goi_y


def _tc_ky_toi(bang):
    """Ước lượng số TC kỳ tới: trung bình TC đạt các kỳ trước (ít nhất 10)."""
    tc = bang["tc_dat_hk"].dropna()
    return max(10.0, float(tc.mean())) if len(tc) else float(TC_KY_TOI_MAC_DINH)


def goi_y_hoc_ky(bang_hoc_ky, tc_ky_toi=None):
    """Gợi ý để không bị cảnh báo / buộc thôi học ở học kỳ kế tiếp.

    `bang_hoc_ky`: các học kỳ đã có điểm của MỘT sinh viên, cột như ml/
    (hoc_ky, tc_dat_hk, dtb_hk, tctl, tc_dang_ky, dtb_tl, ...). `tc_ky_toi`:
    số TC dự định học kỳ tới; bỏ trống thì ước lượng từ các kỳ trước.
    """
    if bang_hoc_ky is None or len(bang_hoc_ky) == 0:
        return []
    bang = gan_nhan_hoc_ky(bang_hoc_ky.assign(ma_sv=bang_hoc_ky.get("ma_sv", "SV1")))
    cuoi = bang.iloc[-1]
    if pd.isna(cuoi["dtb_tl"]) or pd.isna(cuoi["tctl"]):
        return []
    goi_y = []

    lien_tiep = 0 if pd.isna(cuoi["so_lan_canh_bao_lien_tiep"]) else int(cuoi["so_lan_canh_bao_lien_tiep"])
    if lien_tiep >= SO_LAN_CANH_BAO_THOI_HOC - 1:
        goi_y.append(f"Đã bị cảnh báo {lien_tiep} kỳ liên tiếp (tự xét theo quy chế): bị cảnh báo thêm "
                     "kỳ tới là thuộc diện buộc thôi học (Điều 18.2a). Nên gặp cố vấn học tập ngay.")
    elif lien_tiep == 1:
        goi_y.append("Kỳ vừa rồi đã bị cảnh báo (tự xét theo quy chế): bị cảnh báo 3 kỳ liên tiếp "
                     "là thuộc diện buộc thôi học.")

    # ĐTB tích luỹ chỉ tính môn đạt (Điều 15.4): kỳ tới đạt T tín chỉ với ĐTB g thì
    # ĐTB tích luỹ mới = (dtb_tl × tctl + g × T) / (tctl + T) phải >= ngưỡng trình độ mới
    tc = float(tc_ky_toi) if tc_ky_toi else _tc_ky_toi(bang)
    nguong = NGUONG_DTB_TICH_LUY[trinh_do_nam(cuoi["tctl"] + tc)]
    can = (nguong * (cuoi["tctl"] + tc) - cuoi["dtb_tl"] * cuoi["tctl"]) / tc
    if cuoi["dtb_tl"] < nguong + 0.3 and can > 1:
        goi_y.append(f"ĐTB tích luỹ {_so(round(cuoi['dtb_tl'], 2))} đang sát ngưỡng cảnh báo {_so(nguong)}: "
                     f"kỳ tới (khoảng {_so(round(tc))} TC) cần ĐTB các môn đạt từ {_so(math.ceil(can * 10) / 10)} "
                     "(thang 4) trở lên.")

    no_tc = cuoi["tc_dang_ky"] - cuoi["tctl"]
    if no_tc > NO_TC_TOI_DA:
        goi_y.append(f"Đang nợ {_so(no_tc)} tín chỉ, quá mức {NO_TC_TOI_DA} của quy chế: ưu tiên đăng ký "
                     "học lại các môn nợ để giảm nợ.")
    elif no_tc >= NO_TC_NHAC:
        goi_y.append(f"Đang nợ {_so(no_tc)} tín chỉ, nợ trên {NO_TC_TOI_DA} là bị cảnh báo: "
                     "nên ưu tiên học lại các môn nợ.")

    if cuoi["dtb_hk"] < NGUONG_DTB_HK + 0.5:
        goi_y.append(f"ĐTB học kỳ vừa rồi chỉ {_so(round(cuoi['dtb_hk'], 2))}: dưới {_so(NGUONG_DTB_HK)} là bị "
                     "cảnh báo; nên giảm số tín chỉ đăng ký kỳ tới để tập trung.")
    elif len(bang) >= 2 and cuoi["dtb_hk"] < DTB_GIAM_CON_DUOI:
        # Giảm mà vẫn loại Khá trở lên (vd 3,38 -> 2,63) thì chưa đáng lo, không nhắc
        giam = bang.iloc[-2]["dtb_hk"] - cuoi["dtb_hk"]
        if not np.isnan(giam) and giam >= DTB_GIAM_NHAC:
            goi_y.append(f"ĐTB học kỳ giảm {_so(round(giam, 2))} so với kỳ trước: xem lại các môn làm "
                         "điểm giảm và cách sắp xếp thời gian học.")
    return goi_y
