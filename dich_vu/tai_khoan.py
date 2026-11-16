"""Đăng ký, đăng nhập và token JWT (SPEC §12.4).

Mật khẩu băm bằng bcrypt như giao diện cũ (db/bao_mat.py). Token ký HS256,
chứa user_id ở "sub", hết hạn sau HT_JWT_HET_HAN_GIO giờ.
"""

import re
from datetime import datetime, timedelta, timezone

import jwt

from db import bao_mat
from db import repo_canh_bao as repo
from dich_vu import LoiDuLieu, LoiTrung, LoiXacThuc, cau_hinh

MAT_KHAU_TOI_THIEU = 8
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def dang_ky(email: str, mat_khau: str, ho_ten: str) -> dict:
    """Tạo tài khoản, trả về hồ sơ. Email sai / mật khẩu ngắn -> LoiDuLieu; trùng -> LoiTrung."""
    email, ho_ten = email.strip(), ho_ten.strip()
    loi = []
    if not _EMAIL.match(email):
        loi.append("Email không hợp lệ.")
    if len(mat_khau) < MAT_KHAU_TOI_THIEU:
        loi.append(f"Mật khẩu cần ít nhất {MAT_KHAU_TOI_THIEU} ký tự.")
    if not ho_ten:
        loi.append("Chưa nhập họ tên.")
    if loi:
        raise LoiDuLieu("Thông tin đăng ký chưa hợp lệ.", loi)
    try:
        user_id = repo.tao_tai_khoan_moi(email, bao_mat.bam(mat_khau), ho_ten)
    except ValueError as e:
        raise LoiTrung("Email này đã được đăng ký.") from e
    return repo.ho_so_canh_bao(user_id)


def dang_nhap(email: str, mat_khau: str) -> str:
    """Trả về token JWT. Sai email hoặc mật khẩu đều báo cùng một câu (không lộ email nào có tài khoản)."""
    tk = repo.tai_khoan_theo_email(email)
    if tk is None or not bao_mat.kiem_tra(mat_khau, tk["mat_khau_hash"]):
        raise LoiXacThuc("Email hoặc mật khẩu không đúng.")
    het_han = datetime.now(timezone.utc) + timedelta(hours=cau_hinh.jwt_het_han_gio())
    return jwt.encode({"sub": str(tk["id"]), "exp": het_han}, cau_hinh.jwt_secret(), algorithm="HS256")


def user_id_tu_token(token: str) -> int:
    """Kiểm token, trả về user_id. Hết hạn / sai chữ ký / tài khoản đã xoá -> LoiXacThuc."""
    try:
        user_id = int(jwt.decode(token, cau_hinh.jwt_secret(), algorithms=["HS256"])["sub"])
    except jwt.ExpiredSignatureError as e:
        raise LoiXacThuc("Phiên đăng nhập đã hết hạn, hãy đăng nhập lại.") from e
    except (jwt.InvalidTokenError, KeyError, ValueError) as e:
        raise LoiXacThuc("Token không hợp lệ.") from e
    if repo.ho_so_canh_bao(user_id) is None:
        raise LoiXacThuc("Tài khoản không còn tồn tại.")
    return user_id
