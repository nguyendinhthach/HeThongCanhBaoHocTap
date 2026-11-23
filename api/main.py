"""API của hệ thống cảnh báo sớm (SPEC §12.4).

Chạy (từ thư mục gốc dự án, ĐÚNG 1 worker vì tác vụ định kỳ chạy chung tiến trình):
    python -m uvicorn api.main:app --port 8000
Tài liệu API tự sinh: http://localhost:8000/docs (thử trực tiếp được, như Postman).

Endpoint chỉ nhận / trả dữ liệu; logic ở dich_vu/. Đăng nhập trả token JWT;
các API còn lại gửi kèm header "Authorization: Bearer <token>".
"""

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from db import ket_noi
from db import repo_canh_bao as repo
from dich_vu import LoiNghiepVu, du_doan, du_lieu, tai_khoan, tac_vu_canh_bao, thong_bao


@asynccontextmanager
async def vong_doi(app: FastAPI):
    scheduler = tac_vu_canh_bao.tao_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=True)


app = FastAPI(title="Hệ thống cảnh báo sớm nguy cơ học tập", version="0.1.0", lifespan=vong_doi)
_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/dang-nhap")


@app.exception_handler(LoiNghiepVu)
async def _loi_nghiep_vu(request: Request, loi: LoiNghiepVu):
    headers = {"WWW-Authenticate": "Bearer"} if loi.ma_http == 401 else None
    return JSONResponse(status_code=loi.ma_http, headers=headers,
                        content={"detail": loi.thong_bao, "loi": loi.chi_tiet})


def nguoi_dung(token: str = Depends(_oauth2)) -> int:
    """user_id của người gửi token; sai / hết hạn -> 401."""
    return tai_khoan.user_id_tu_token(token)


# --- Dữ liệu vào ----------------------------------------------------------------
class DangKy(BaseModel):
    email: str
    mat_khau: str
    ho_ten: str


class CapNhatToi(BaseModel):
    nhan_email: bool


class VanBan(BaseModel):
    van_ban: str = Field(description="Toàn bộ chữ trang Xem điểm (Ctrl+A, Ctrl+C)")


class LanCapNhat(BaseModel):
    nguon: Literal["cong_thong_tin", "nhap_tay"] = "cong_thong_tin"
    thong_tin: dict = Field(default_factory=dict, description="nam_nhap_hoc, nganh, he_dao_tao")
    hoc_ky: list[dict] = Field(description="Các học kỳ đã có điểm, cột như /du-lieu/doc trả về")
    mon: list[dict] = Field(default_factory=list, description="Các môn đang học")
    muc_vang: str | None = Field(None, description="Lựa chọn mức vắng của form, ghi vào học kỳ gần nhất")
    hoc_phi: str | None = Field(None, description="Lựa chọn tình trạng học phí, ghi vào học kỳ gần nhất")


class HenNhac(BaseModel):
    so_ngay: Literal[7, 14]


# --- Tài khoản ------------------------------------------------------------------
@app.post("/auth/dang-ky", status_code=201, tags=["Tài khoản"])
def dang_ky(than: DangKy):
    return tai_khoan.dang_ky(than.email, than.mat_khau, than.ho_ten)


@app.post("/auth/dang-nhap", tags=["Tài khoản"])
def dang_nhap(form: OAuth2PasswordRequestForm = Depends()):
    """Form chuẩn OAuth2: username = email, password = mật khẩu."""
    return {"access_token": tai_khoan.dang_nhap(form.username, form.password), "token_type": "bearer"}


@app.get("/toi", tags=["Tài khoản"])
def toi(user_id: int = Depends(nguoi_dung)):
    return repo.ho_so_canh_bao(user_id)


@app.patch("/toi", tags=["Tài khoản"])
def sua_toi(than: CapNhatToi, user_id: int = Depends(nguoi_dung)):
    repo.dat_nhan_email(user_id, than.nhan_email)
    return repo.ho_so_canh_bao(user_id)


# --- Dữ liệu học tập ------------------------------------------------------------
@app.post("/du-lieu/doc", tags=["Dữ liệu"])
def doc_du_lieu(than: VanBan, user_id: int = Depends(nguoi_dung)):
    """Đọc văn bản trang Xem điểm để XEM TRƯỚC; không lưu gì."""
    return du_lieu.xem_truoc(than.van_ban)


@app.post("/du-lieu", status_code=201, tags=["Dữ liệu"])
def luu_du_lieu(than: LanCapNhat, user_id: int = Depends(nguoi_dung)):
    lcn_id = du_lieu.luu(user_id, than.nguon, than.thong_tin, than.hoc_ky, than.mon,
                         than.muc_vang, than.hoc_phi)
    return {"lan_cap_nhat_id": lcn_id}


@app.get("/du-lieu/moi-nhat", tags=["Dữ liệu"])
def du_lieu_moi_nhat(user_id: int = Depends(nguoi_dung)):
    moi = repo.lan_cap_nhat_moi_nhat(user_id)
    if moi is None:
        return None
    return {**moi, "bang_hoc_ky": du_lieu.ve_json(moi["bang_hoc_ky"]),
            "bang_mon": du_lieu.ve_json(moi["bang_mon"])}


# --- Dự đoán --------------------------------------------------------------------
@app.post("/du-doan", tags=["Dự đoán"])
def chay_du_doan(user_id: int = Depends(nguoi_dung)):
    """Dự đoán trên lần cập nhật mới nhất, lưu, xếp email cảnh báo nếu cần."""
    return du_doan.chay(user_id)


@app.get("/ket-qua/moi-nhat", tags=["Dự đoán"])
def ket_qua_moi_nhat(user_id: int = Depends(nguoi_dung)):
    return repo.ket_qua_moi_nhat(user_id)


@app.get("/ket-qua/lich-su", tags=["Dự đoán"])
def lich_su_ket_qua(muc_tieu: Literal["canh_bao", "thoi_hoc"] = "canh_bao", gioi_han: int = 20,
                    user_id: int = Depends(nguoi_dung)):
    return repo.lich_su_du_doan(user_id, muc_tieu, min(max(gioi_han, 1), 100))


# --- Nhắc và email ----------------------------------------------------------------
@app.post("/hen-nhac", status_code=201, tags=["Email"])
def hen_nhac(than: HenNhac, user_id: int = Depends(nguoi_dung)):
    return {"email_id": thong_bao.hen_nhac(user_id, than.so_ngay)}


@app.get("/email/lich-su", tags=["Email"])
def lich_su_email(gioi_han: int = 50, user_id: int = Depends(nguoi_dung)):
    return repo.lich_su_email(user_id, min(max(gioi_han, 1), 200))


# --- Hệ thống -------------------------------------------------------------------
@app.get("/suc-khoe", tags=["Hệ thống"])
def suc_khoe():
    """Trạng thái API, CSDL và mô hình đang dùng."""
    trang_thai = {"api": "ok"}
    try:
        trang_thai["csdl"] = ket_noi.kiem_tra()
    except Exception as loi:                       # báo lỗi rõ thay vì 500
        trang_thai["csdl"] = f"lỗi: {type(loi).__name__}"
    mo_hinh = {}
    for muc_tieu in ("canh_bao", "truot_mon"):
        try:
            goi = du_doan.goi_mo_hinh(muc_tieu)
            mo_hinh[muc_tieu] = {"phuong_phap": goi["phuong_phap"], "thoi_diem_train": goi["thoi_diem"]}
        except LoiNghiepVu as loi:
            mo_hinh[muc_tieu] = loi.thong_bao
    trang_thai["mo_hinh"] = mo_hinh
    return trang_thai
