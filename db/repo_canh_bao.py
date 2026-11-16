"""Đọc và ghi dữ liệu cho hệ thống cảnh báo sớm — HỢP ĐỒNG HÀM (SPEC §12).

File này chốt tên hàm, tham số và kiểu trả về để làm song song: phần API
(dich_vu/, FastAPI, tác vụ định kỳ) viết code gọi theo đây ngay, phần bên
trong viết sau. Hiện mọi hàm báo NotImplementedError. Đổi chữ ký hàm thì báo
bên gọi; thêm tham số có giá trị mặc định thì không cần.

Bảng dùng: nguoi_dung, lan_cap_nhat, hoc_ky_tong_ket, mon_dang_hoc, du_doan,
email_da_gui (db/nang_cap_canh_bao.sql). Không dùng bảng của giao diện cũ.

Quy ước:
- Bảng học kỳ / môn truyền vào và trả ra là pandas DataFrame, ĐÚNG cột như
  ml/ đang dùng (doc_form.py, doc_cong_thong_tin.py), để đưa thẳng vào
  dac_trung.chuan_bi_du_lieu() và mo_hinh_cuoi.du_doan(du_lieu=...).
- Hàm ghi nhiều bảng chạy trong MỘT giao dịch: lỗi giữa chừng thì không ghi
  gì cả.
- Tài khoản tạo theo luồng mới có niên khoá trống nên các hàm hồ sơ cũ
  repo.ho_so() / repo.ho_so_theo_email() sẽ lỗi với họ: luồng mới dùng
  tai_khoan_theo_email() / ho_so_canh_bao() ở đây.
- Thời điểm là datetime theo giờ máy chủ SQL (SYSDATETIME()).
"""

from datetime import datetime

import pandas as pd

# Mức nguy cơ lưu trong du_doan.muc_nguy_co
MUC_NGUY_CO = ("thap", "trung_binh", "cao", "chua_du_doan")
# Loại email trong email_da_gui.loai
LOAI_EMAIL = ("nhac_giua_ky", "nhac_cuoi_ky", "hen_nhac", "canh_bao", "mo_hinh_moi")
SO_LAN_THU_TOI_DA = 3

_CHUA_VIET = "Hợp đồng hàm: phần bên trong viết ở nhánh feature/repo-canh-bao"


# --- Tài khoản ---------------------------------------------------------------
def tao_tai_khoan_moi(email: str, mat_khau_bam: str, ho_ten: str) -> int:
    """Tạo tài khoản theo form đăng ký mới (không niên khoá). Trả về user_id.

    Email đã có thì báo ValueError("email đã được dùng"). nhan_email mặc định 1.
    """
    raise NotImplementedError(_CHUA_VIET)


def tai_khoan_theo_email(email: str) -> dict | None:
    """Dùng cho đăng nhập: {"id", "email", "ho_ten", "mat_khau_hash", "nhan_email"}.

    Không có thì None. Email so không phân biệt hoa thường (collation của CSDL).
    """
    raise NotImplementedError(_CHUA_VIET)


def ho_so_canh_bao(user_id: int) -> dict | None:
    """{"id", "email", "ho_ten", "nhan_email", "ngay_tao"}; không có thì None."""
    raise NotImplementedError(_CHUA_VIET)


def dat_nhan_email(user_id: int, bat: bool) -> None:
    """Bật / tắt nhận email (PATCH /toi)."""
    raise NotImplementedError(_CHUA_VIET)


# --- Dữ liệu học tập (mỗi lần cập nhật là một bản mới, không ghi đè) ---------
def luu_lan_cap_nhat(user_id: int, nguon: str, thong_tin: dict,
                     bang_hoc_ky: pd.DataFrame, bang_mon: pd.DataFrame) -> int:
    """Lưu một lần cập nhật: 1 dòng lan_cap_nhat + các học kỳ + các môn đang học.

    nguon: "cong_thong_tin" hoặc "nhap_tay".
    thong_tin: {"nam_nhap_hoc", "nganh", "he_dao_tao"} (giá trị có thể None).
    bang_hoc_ky: cột như ml/ — hoc_ky (thứ tự 1, 2...), tc_dat_hk, dtb_hk,
        tctl, tc_dang_ky, dtb_tl, muc_vang, hoc_phi, drl; thêm nam_bat_dau,
        ky_trong_nam nếu biết (không có thì lưu NULL).
    bang_mon: cột như ml/ — stt_mon, ten_mon, so_tc, diem_gk, ti_trong_gk,
        vang_lt, vang_th; thêm ma_mon nếu biết. Có thể rỗng.
    Kiểm tra hợp lệ (doc_form.kiem_tra) là việc của bên gọi; CSDL vẫn chặn số
    sai miền bằng ràng buộc CHECK (báo lỗi, không ghi gì). Trả về lan_cap_nhat_id.
    """
    raise NotImplementedError(_CHUA_VIET)


def du_lieu_cho_ml(lan_cap_nhat_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(sinh_vien, bang_hoc_ky, bang_mon) của một lần cập nhật, ĐÚNG dạng
    doc_form.doc_form() trả về (ma_sv = "SV1", có cột hop_le, loi), để gọi:

        du_lieu = dac_trung.chuan_bi_du_lieu(*repo_canh_bao.du_lieu_cho_ml(lcn_id))
        mo_hinh_cuoi.du_doan(None, "canh_bao", du_lieu=du_lieu)

    Không có lần cập nhật đó thì LookupError.
    """
    raise NotImplementedError(_CHUA_VIET)


def lan_cap_nhat_moi_nhat(user_id: int) -> dict | None:
    """Lần cập nhật gần nhất (GET /du-lieu/moi-nhat, điền sẵn giao diện):

        {"id", "thoi_diem", "nguon", "thong_tin": {...},
         "bang_hoc_ky": DataFrame, "bang_mon": DataFrame}

    Chưa từng cập nhật thì None.
    """
    raise NotImplementedError(_CHUA_VIET)


def nguoi_chua_cap_nhat_tu(moc: datetime) -> list[int]:
    """user_id có nhan_email = 1 và KHÔNG có lần cập nhật nào từ `moc` trở đi
    (tác vụ 2: nhắc theo mốc). Gồm cả người chưa cập nhật lần nào."""
    raise NotImplementedError(_CHUA_VIET)


def lan_cap_nhat_moi_nhat_moi_nguoi() -> list[tuple[int, int]]:
    """[(user_id, lan_cap_nhat_id mới nhất)] của mọi người đã từng cập nhật
    (tác vụ 3: dự đoán lại khi có mô hình mới)."""
    raise NotImplementedError(_CHUA_VIET)


# --- Dự đoán ---------------------------------------------------------------
def luu_du_doan(lan_cap_nhat_id: int, ket_qua: list[dict]) -> list[int]:
    """Lưu các kết quả của một lần dự đoán, trả về id theo đúng thứ tự.

    Mỗi dict: {"muc_tieu": "canh_bao" | "thoi_hoc" | "truot_mon",
               "stt_mon": int | None (bắt buộc với truot_mon — tra ra mon_dang_hoc_id),
               "cho_thu_tu", "cho_ten", "diem_nguy_co" (None khi chưa dự đoán),
               "nguong", "bao_dong", "muc_nguy_co" (một trong MUC_NGUY_CO),
               "ly_do": list[str], "goi_y": list[str], "ghi_chu",
               "phuong_phap", "phien_ban_mo_hinh"}
    Ghi một giao dịch.
    """
    raise NotImplementedError(_CHUA_VIET)


def ket_qua_moi_nhat(user_id: int) -> dict | None:
    """Lần dự đoán gần nhất (GET /ket-qua/moi-nhat):

        {"lan_cap_nhat_id", "thoi_diem",
         "canh_bao": {cột như luu_du_doan, có "id"},
         "thoi_hoc": {...},
         "truot_mon": [{..., "ten_mon", "so_tc"}, ...]}

    Chưa từng dự đoán thì None.
    """
    raise NotImplementedError(_CHUA_VIET)


def lich_su_du_doan(user_id: int, muc_tieu: str = "canh_bao", gioi_han: int = 20) -> list[dict]:
    """Các lần dự đoán trước, mới nhất trước (GET /ket-qua/lich-su):
    [{"id", "thoi_diem", "cho_ten", "muc_nguy_co", "diem_nguy_co", "bao_dong"}]."""
    raise NotImplementedError(_CHUA_VIET)


def muc_canh_bao_truoc(user_id: int, tru_lan_cap_nhat_id: int) -> str | None:
    """muc_nguy_co của dự đoán "canh_bao" gần nhất TRƯỚC lần cập nhật đang xét
    (quy tắc gửi email §12.6: chỉ gửi khi lần này "cao" mà lần trước không).
    Chưa có lần trước thì None."""
    raise NotImplementedError(_CHUA_VIET)


def phien_ban_mo_hinh_gan_nhat() -> str | None:
    """phien_ban_mo_hinh của dự đoán mới nhất trong toàn hệ thống (tác vụ 3 so
    với thời điểm train trong models/*.joblib). Chưa có dự đoán nào thì None."""
    raise NotImplementedError(_CHUA_VIET)


# --- Email: hàng đợi và lịch sử cảnh báo ----------------------------------
def them_email(user_id: int, loai: str, tieu_de: str, noi_dung: str, *,
               moc: str | None = None, lan_nhac: int | None = None,
               du_doan_id: int | None = None, hen_gui: datetime | None = None) -> int | None:
    """Xếp một email vào hàng đợi (trạng thái "cho_gui"), trả về id.

    loai: một trong LOAI_EMAIL. Nhắc theo mốc truyền moc + lan_nhac; đã có
    (user_id, loai, moc, lan_nhac) rồi thì KHÔNG thêm, trả về None (chống trùng).
    "Nhắc tôi sau": loai="hen_nhac", hen_gui = ngày hẹn.
    Người dùng nhan_email = 0 vẫn thêm được; email_den_han() mới bỏ qua họ.
    """
    raise NotImplementedError(_CHUA_VIET)


def email_den_han(gioi_han: int = 50) -> list[dict]:
    """Email "cho_gui" có hen_gui trống hoặc đã đến hạn, của người nhan_email = 1,
    cũ nhất trước (tác vụ 1):
    [{"id", "user_id", "den" (email người nhận), "tieu_de", "noi_dung", "so_lan_thu"}]."""
    raise NotImplementedError(_CHUA_VIET)


def danh_dau_da_gui(email_id: int) -> None:
    """Trạng thái "da_gui", thoi_diem_gui = bây giờ."""
    raise NotImplementedError(_CHUA_VIET)


def danh_dau_loi(email_id: int, noi_dung_loi: str) -> str:
    """Tăng so_lan_thu; quá SO_LAN_THU_TOI_DA thì chuyển "loi", chưa quá thì vẫn
    "cho_gui" để lượt sau thử lại. Trả về trạng thái mới."""
    raise NotImplementedError(_CHUA_VIET)


def lich_su_email(user_id: int, gioi_han: int = 50) -> list[dict]:
    """Email của một người, mới nhất trước (GET /email/lich-su):
    [{"id", "loai", "tieu_de", "trang_thai", "thoi_diem_tao", "thoi_diem_gui"}]."""
    raise NotImplementedError(_CHUA_VIET)
