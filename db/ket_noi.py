"""Kết nối tới SQL Server.

Cả ứng dụng dùng chung một engine của SQLAlchemy. Engine giữ sẵn một nhóm kết
nối (pool) và tái sử dụng, nên không được tạo mới ở mỗi lần gọi — Streamlit
chạy lại toàn bộ script sau mỗi thao tác của người dùng, tạo engine mỗi lần
thì chỉ vài phút là đầy kết nối tới server.
"""

import os
import urllib.parse

import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

SERVER_MAC_DINH = "localhost"
TEN_CSDL_MAC_DINH = "HT_CANHBAOHOCTAP"

# Thứ tự ưu tiên khi máy cài nhiều driver. Driver 18 bật mã hoá mặc định nên
# phải kèm TrustServerCertificate, còn 17 thì không cần.
_UU_TIEN = ("ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0")


def driver_odbc() -> str:
    """Driver ODBC tốt nhất đang có trên máy."""
    co_san = pyodbc.drivers()
    for ten in _UU_TIEN:
        if ten in co_san:
            return ten
    con_lai = [d for d in co_san if "SQL Server" in d]
    if not con_lai:
        raise RuntimeError(
            "Máy chưa cài driver ODBC cho SQL Server. Tải 'ODBC Driver 17 "
            "for SQL Server' từ trang của Microsoft rồi chạy lại.")
    return con_lai[-1]


def chuoi_ket_noi() -> str:
    """Chuỗi kết nối SQLAlchemy.

    Đặt biến môi trường HT_DB_URL để trỏ sang máy chủ khác (ví dụ lúc chấm
    đồ án trên máy của thầy); không đặt thì dùng SQL Server trên máy này với
    xác thực Windows, không cần mật khẩu.
    """
    rieng = os.environ.get("HT_DB_URL")
    if rieng:
        return rieng

    server = os.environ.get("HT_DB_SERVER", SERVER_MAC_DINH)
    ten_csdl = os.environ.get("HT_DB_NAME", TEN_CSDL_MAC_DINH)
    driver = driver_odbc()

    tham_so = (f"DRIVER={{{driver}}};SERVER={server};DATABASE={ten_csdl};"
               "Trusted_Connection=yes;")
    if "18" in driver:
        tham_so += "Encrypt=yes;TrustServerCertificate=yes;"

    return "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(tham_so)


_engine: Engine | None = None


def engine() -> Engine:
    """Engine dùng chung, tạo một lần rồi giữ lại."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            chuoi_ket_noi(),
            # Kết nối để lâu không dùng có thể đã bị server đóng; pre_ping thử
            # một nhịp trước khi giao ra, tránh lỗi ngay sau khi người dùng để
            # trang mở qua đêm.
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def kiem_tra() -> str:
    """Thử kết nối, trả về tên cơ sở dữ liệu đang nối tới.

    Dùng để báo lỗi sớm và rõ ràng thay vì để lỗi bật ra giữa lúc vẽ giao diện.
    """
    from sqlalchemy import text
    with engine().connect() as cn:
        return cn.execute(text("SELECT DB_NAME()")).scalar_one()
