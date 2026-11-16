"""Soạn nội dung email và hẹn nhắc (SPEC §12.6).

Chỉ SOẠN và XẾP vào hàng đợi email_da_gui; việc gửi thật (SMTP) là của tác
vụ gửi hàng đợi. Nội dung là văn bản thuần, không ghi điểm nguy cơ dạng %.
"""

from datetime import datetime, timedelta

from db import repo_canh_bao as repo
from dich_vu import LoiDuLieu

SO_NGAY_HEN = (7, 14)
DONG_CUOI = ("\n\nKết quả chỉ để tham khảo, không thay thế quyết định học vụ của nhà trường.\n"
             "Muốn ngừng nhận email: tắt mục \"Nhận email cảnh báo\" trong trang tài khoản.")


def _dong(muc):
    return "\n".join(f"  - {m}" for m in muc)


def soan_email_canh_bao(ho_ten: str, ket_qua: dict) -> tuple[str, str]:
    """(tiêu đề, nội dung) email cảnh báo từ ket_qua_moi_nhat() của repo."""
    cb, th = ket_qua["canh_bao"], ket_qua["thoi_hoc"]
    tieu_de = f"Cảnh báo sớm: nguy cơ bị cảnh báo học tập ở {cb['cho_ten'] or 'học kỳ tới'}"
    phan = [f"Chào {ho_ten},\n",
            f"Theo dữ liệu bạn cập nhật, hệ thống ước lượng bạn có NGUY CƠ CAO bị cảnh báo học tập "
            f"ở {cb['cho_ten'] or 'học kỳ tới'}."]
    if th and th["muc_nguy_co"] == "cao":
        phan.append("Bạn đã bị cảnh báo 2 kỳ liên tiếp (tự xét theo quy chế): bị cảnh báo thêm kỳ này "
                    "là thuộc diện buộc thôi học.")
    if cb["ly_do"]:
        phan.append("\nLý do chính:\n" + _dong(cb["ly_do"]))
    if cb["goi_y"]:
        phan.append("\nGợi ý cải thiện:\n" + _dong(cb["goi_y"]))
    mon_nguy_co = [m for m in ket_qua["truot_mon"] if m["muc_nguy_co"] == "cao"]
    if mon_nguy_co:
        phan.append("\nMôn có nguy cơ trượt:\n" + _dong(
            f"{m['ten_mon']}" + (f": {' '.join(m['goi_y'])}" if m["goi_y"] else "") for m in mon_nguy_co))
    return tieu_de, "\n".join(phan) + DONG_CUOI


def hen_nhac(user_id: int, so_ngay: int) -> int:
    """"Nhắc tôi sau" so_ngay ngày (7 hoặc 14): xếp một email hen_nhac, trả về id."""
    if so_ngay not in SO_NGAY_HEN:
        raise LoiDuLieu(f"Chỉ hẹn nhắc sau {SO_NGAY_HEN[0]} hoặc {SO_NGAY_HEN[1]} ngày.")
    hs = repo.ho_so_canh_bao(user_id)
    noi_dung = (f"Chào {hs['ho_ten']},\n\nBạn đã hẹn hệ thống nhắc sau {so_ngay} ngày: nếu đã có điểm "
                "giữa kỳ (trên lớp hoặc trên cổng thông tin), hãy cập nhật kết quả học tập để xem dự "
                "đoán nguy cơ trượt môn." + DONG_CUOI)
    return repo.them_email(user_id, "hen_nhac", "Nhắc cập nhật kết quả học tập", noi_dung,
                           hen_gui=datetime.now() + timedelta(days=so_ngay))
