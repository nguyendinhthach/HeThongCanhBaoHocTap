"""Gửi email qua SMTP theo cấu hình HT_SMTP_* trong .env."""

import smtplib
import ssl
from email.message import EmailMessage

from dich_vu import cau_hinh


def gui_email(den: str, tieu_de: str, noi_dung: str) -> None:
    """Gửi một email văn bản thuần; lỗi cấu hình/kết nối được báo cho caller."""
    smtp = cau_hinh.smtp()
    if not smtp["user"] or not smtp["mat_khau"] or not smtp["tu"]:
        raise RuntimeError("Cần cấu hình HT_SMTP_USER, HT_SMTP_APP_PASSWORD và HT_EMAIL_TU trong .env.")

    thu = EmailMessage()
    thu["From"] = smtp["tu"]
    thu["To"] = den
    thu["Subject"] = tieu_de
    thu.set_content(noi_dung)

    with smtplib.SMTP(smtp["host"], smtp["port"], timeout=20) as ket_noi:
        ket_noi.ehlo()
        ket_noi.starttls(context=ssl.create_default_context())
        ket_noi.ehlo()
        ket_noi.login(smtp["user"], smtp["mat_khau"])
        ket_noi.send_message(thu)
