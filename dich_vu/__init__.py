"""Logic nghiệp vụ của hệ thống cảnh báo sớm (SPEC §12.2).

API (api/main.py) và tác vụ định kỳ đều gọi vào đây, không tự viết lại logic:
endpoint chỉ nhận / trả dữ liệu.

- cau_hinh:  đọc .env (HT_*).
- tai_khoan: đăng ký, đăng nhập, token JWT.
- du_lieu:   đọc văn bản trang Xem điểm (xem trước), lưu một lần cập nhật.
- du_doan:   dự đoán 3 mục tiêu + gợi ý, lưu, xếp email cảnh báo.
- thong_bao: soạn nội dung email, hẹn nhắc.
"""

import os
import sys

# Các module trong ml/ import nhau bằng tên trần (import dac_trung...)
_THU_MUC_ML = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
if _THU_MUC_ML not in sys.path:
    sys.path.insert(0, _THU_MUC_ML)


class LoiNghiepVu(Exception):
    """Lỗi do dữ liệu / thao tác của người dùng; API đổi thành mã HTTP tương ứng."""

    ma_http = 400

    def __init__(self, thong_bao, chi_tiet=None):
        super().__init__(thong_bao)
        self.thong_bao = thong_bao
        self.chi_tiet = chi_tiet or []


class LoiDuLieu(LoiNghiepVu):
    """Dữ liệu sai hoặc thiếu (HTTP 422)."""
    ma_http = 422


class LoiXacThuc(LoiNghiepVu):
    """Sai email / mật khẩu, token hết hạn hoặc không hợp lệ (HTTP 401)."""
    ma_http = 401


class LoiTrung(LoiNghiepVu):
    """Trùng dữ liệu đã có, ví dụ email đã đăng ký (HTTP 409)."""
    ma_http = 409
