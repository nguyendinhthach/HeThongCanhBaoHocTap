"""Cấu hình từ biến môi trường HT_* (SPEC §12.7), đọc thêm file .env nếu có.

Biến đã đặt sẵn trong môi trường thắng giá trị trong .env (để test / máy
chấm đè được).
"""

import logging
import os
import secrets

from dotenv import load_dotenv

THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(THU_MUC_GOC, ".env"), override=False)

_log = logging.getLogger(__name__)
_khoa_tam = None


def jwt_secret() -> str:
    """Khoá ký token. Chưa đặt HT_JWT_SECRET thì sinh khoá tạm cho lần chạy này
    (khởi động lại API là mọi token cũ hết hiệu lực) và ghi cảnh báo."""
    global _khoa_tam
    khoa = os.environ.get("HT_JWT_SECRET")
    if khoa:
        if len(khoa.encode("utf-8")) < 32:
            # HS256 cần khoá từ 32 byte (RFC 7518 §3.2); khoá ngắn thì token dễ bị dò
            raise RuntimeError("HT_JWT_SECRET phải dài ít nhất 32 ký tự. Tạo khoá: "
                               "python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
        return khoa
    if _khoa_tam is None:
        _khoa_tam = secrets.token_urlsafe(48)
        _log.warning("Chưa đặt HT_JWT_SECRET trong .env: dùng khoá tạm, khởi động lại là phải đăng nhập lại.")
    return _khoa_tam


def jwt_het_han_gio() -> float:
    return float(os.environ.get("HT_JWT_HET_HAN_GIO", "8"))


def smtp() -> dict:
    """Thông số gửi email (tác vụ gửi hàng đợi dùng)."""
    return {
        "host": os.environ.get("HT_SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("HT_SMTP_PORT", "587")),
        "user": os.environ.get("HT_SMTP_USER", ""),
        "mat_khau": os.environ.get("HT_SMTP_APP_PASSWORD", ""),
        "tu": os.environ.get("HT_EMAIL_TU") or os.environ.get("HT_SMTP_USER", ""),
    }


def file_moc_hoc_ky() -> str:
    duong_dan = os.environ.get("HT_MOC_HOC_KY", "config/moc_hoc_ky.json")
    return duong_dan if os.path.isabs(duong_dan) else os.path.join(THU_MUC_GOC, duong_dan)
