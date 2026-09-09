"""Băm và kiểm tra mật khẩu.

Tách riêng khỏi repo để chỗ nào cần cũng gọi được, và để khi đổi thuật toán
băm thì chỉ sửa một tệp.
"""

import bcrypt

# Chi phí băm. Mỗi đơn vị tăng gấp đôi thời gian tính. 12 là mức khuyến nghị
# hiện nay: đủ chậm để dò mật khẩu hàng loạt không khả thi, nhưng người dùng
# đăng nhập vẫn không thấy chờ.
_CHI_PHI = 12


def bam(mat_khau: str) -> str:
    """Băm mật khẩu, trả về chuỗi lưu thẳng vào cột mat_khau_hash.

    Chuỗi kết quả đã chứa sẵn muối (salt) bên trong nên không cần cột riêng.
    """
    return bcrypt.hashpw(mat_khau.encode("utf-8"),
                         bcrypt.gensalt(_CHI_PHI)).decode("ascii")


def kiem_tra(mat_khau: str, chuoi_bam: str) -> bool:
    """Mật khẩu có khớp với chuỗi băm đã lưu không."""
    if not chuoi_bam:
        return False
    try:
        return bcrypt.checkpw(mat_khau.encode("utf-8"),
                              chuoi_bam.encode("ascii"))
    except ValueError:
        # Chuỗi trong CSDL không đúng định dạng bcrypt — ví dụ tài khoản demo
        # nạp bằng db/du_lieu_mau.sql. Coi như sai mật khẩu, không cho vào.
        return False
