"""Các tác vụ email định kỳ theo SPEC §12.5."""

import json
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from db import repo_canh_bao as repo
from dich_vu import cau_hinh, du_doan, thong_bao
from dich_vu.gui_email import gui_email

_log = logging.getLogger(__name__)
_MUI_GIO = ZoneInfo("Asia/Ho_Chi_Minh")
# Mỗi học kỳ 2 giai đoạn nhắc (SPEC §12.5): (loại email, trường ngày bắt đầu,
# số lần, tên mốc, "xong" khi đủ điểm giữa kỳ hay phải có tổng kết học kỳ).
GIAI_DOAN = (
    ("nhac_giua_ky", "nhac_giua_ky", 3, "giữa kỳ", True),
    ("nhac_cuoi_ky", "nhac_sau_thi", 2, "sau thi", False),
)
# Các lần cách nhau CHU_KY_NGAY ngày. Mỗi lần chỉ xếp email trong
# NGAY_XEP_MOI_LAN ngày đầu (bù khi máy chủ tắt đúng ngày đó); quá thì bỏ qua,
# nên người đăng ký muộn không nhận các lần đã qua.
CHU_KY_NGAY = 15
NGAY_XEP_MOI_LAN = 3

def gui_hang_doi_email() -> int:
    """Gửi từng email đến hạn; cập nhật trạng thái theo kết quả SMTP."""
    da_gui = 0
    for email in repo.email_den_han():
        try:
            gui_email(email["den"], email["tieu_de"], email["noi_dung"])
        except Exception as loi:
            repo.danh_dau_loi(email["id"], f"{type(loi).__name__}: {loi}")
            _log.exception("Gửi email trong hàng đợi thất bại (id=%s).", email["id"])
        else:
            repo.danh_dau_da_gui(email["id"])
            da_gui += 1
    return da_gui


def _doc_moc_hoc_ky() -> list[dict]:
    with open(cau_hinh.file_moc_hoc_ky(), encoding="utf-8") as tep:
        moc_hoc_ky = json.load(tep)
    if not isinstance(moc_hoc_ky, list):
        raise ValueError("config/moc_hoc_ky.json phải chứa một danh sách các mốc.")

    for vi_tri, hk in enumerate(moc_hoc_ky):
        if not isinstance(hk, dict):
            raise ValueError(f"Học kỳ thứ {vi_tri + 1} phải là một object JSON.")
        if not isinstance(hk.get("hoc_ky"), str) or not hk["hoc_ky"].strip():
            raise ValueError(f"Học kỳ thứ {vi_tri + 1} thiếu tên 'hoc_ky'.")
        ten = hk["hoc_ky"]
        if not isinstance(hk.get("nam_bat_dau"), int) or hk.get("ky") not in (1, 2, 3):
            raise ValueError(f"Học kỳ {ten!r} cần 'nam_bat_dau' (số năm) và 'ky' (1, 2 hoặc 3).")
        for _, truong, *_ in GIAI_DOAN:
            try:
                date.fromisoformat(hk[truong])
            except (KeyError, TypeError, ValueError) as loi:
                raise ValueError(f"'{truong}' của học kỳ {ten!r} phải là ngày YYYY-MM-DD.") from loi
        so_ngay_giua_ky = GIAI_DOAN[0][2] * CHU_KY_NGAY
        if date.fromisoformat(hk["nhac_sau_thi"]) < date.fromisoformat(hk["nhac_giua_ky"]) +                 timedelta(days=so_ngay_giua_ky):
            raise ValueError(f"Học kỳ {ten!r}: 'nhac_sau_thi' phải sau 'nhac_giua_ky' "
                             f"ít nhất {so_ngay_giua_ky} ngày.")
    return moc_hoc_ky


def _noi_dung(loai: str, hoc_ky: str) -> tuple[str, str]:
    if loai == "nhac_giua_ky":
        return (f"Nhắc cập nhật điểm giữa kỳ: {hoc_ky}",
                f"Bạn chưa nhập đủ điểm giữa kỳ của {hoc_ky}. Khi đã có điểm giữa kỳ môn nào, "
                f"hãy cập nhật để xem cảnh báo sớm và gợi ý cải thiện.{thong_bao.DONG_CUOI}")
    return (f"Nhắc cập nhật kết quả học kỳ: {hoc_ky}",
            f"Kỳ thi {hoc_ky} đã kết thúc. Khi điểm học kỳ đã có trên cổng thông tin, "
            f"hãy cập nhật để xem cảnh báo cho học kỳ tới.{thong_bao.DONG_CUOI}")


def nhac_theo_moc(ngay_hom_nay: date | None = None) -> int:
    """Nhắc người chưa nhập xong điểm (SPEC §12.5), tối đa 5 email / học kỳ.

    Nửa đầu học kỳ chưa có điểm nên không nhắc. Mỗi học kỳ:
    - giữa kỳ: 3 lần từ nhac_giua_ky, cách 15 ngày; "xong" khi lần cập nhật từ
      nhac_giua_ky có môn nào cũng đủ điểm giữa kỳ;
    - sau thi: 2 lần từ nhac_sau_thi, cách 15 ngày; "xong" khi đã có tổng kết
      của học kỳ đó.
    Không gửi cho ai tắt nhận email (repo.nguoi_chua_nhap_xong). Trùng
    (người, loại, mốc, lần) thì repo.them_email tự bỏ qua.
    """
    hom_nay = ngay_hom_nay or datetime.now(_MUI_GIO).date()
    da_xep = 0
    for hk in _doc_moc_hoc_ky():
        for loai, truong, so_lan, ten_moc, xong_khi_du_gk in GIAI_DOAN:
            bat_dau = date.fromisoformat(hk[truong])
            so_ngay = (hom_nay - bat_dau).days
            if not 0 <= so_ngay < so_lan * CHU_KY_NGAY or so_ngay % CHU_KY_NGAY >= NGAY_XEP_MOI_LAN:
                continue
            lan = so_ngay // CHU_KY_NGAY + 1
            tieu_de, noi_dung = _noi_dung(loai, hk["hoc_ky"])
            for user_id in repo.nguoi_chua_nhap_xong(hk["nam_bat_dau"], hk["ky"],
                                                     datetime.combine(bat_dau, time.min),
                                                     xong_khi_du_gk):
                if repo.them_email(user_id, loai, tieu_de, noi_dung,
                                   moc=f"{hk['hoc_ky']} {ten_moc}", lan_nhac=lan) is not None:
                    da_xep += 1
    return da_xep

def du_doan_lai_khi_co_mo_hinh_moi() -> int:
    """Dự đoán lại các lần cập nhật gần nhất khi mô hình cảnh báo được đổi."""
    phien_ban_moi = {
        muc_tieu: du_doan.goi_mo_hinh(muc_tieu)["thoi_diem"]
        for muc_tieu in ("canh_bao", "truot_mon")
    }
    phien_ban_trong_repo = repo.phien_ban_mo_hinh_gan_nhat()
    nguoi_dung = repo.lan_cap_nhat_moi_nhat_moi_nguoi()

    if phien_ban_trong_repo in phien_ban_moi.values():
        # Bù lại những người chưa cập nhật được nếu một lượt chạy trước bị lỗi giữa chừng.
        nguoi_dung = [
            (user_id, lan_cap_nhat_id)
            for user_id, lan_cap_nhat_id in nguoi_dung
            if _can_du_doan_lai(user_id, phien_ban_moi)
        ]

    that_bai = []
    for user_id, _ in nguoi_dung:
        try:
            du_doan.chay(user_id)
        except Exception as loi:
            that_bai.append(user_id)
            _log.exception("Dự đoán lại thất bại (user_id=%s).", user_id)
    if that_bai:
        raise RuntimeError(f"Không dự đoán lại được cho user_id: {that_bai}.")
    return len(nguoi_dung)


def _can_du_doan_lai(user_id: int, phien_ban_moi: dict[str, str]) -> bool:
    ket_qua = repo.ket_qua_moi_nhat(user_id)
    if not ket_qua:
        return True

    canh_bao = ket_qua.get("canh_bao")
    if not canh_bao or canh_bao.get("phien_ban_mo_hinh") != phien_ban_moi["canh_bao"]:
        return True

    return any(d["phien_ban_mo_hinh"] != phien_ban_moi["truot_mon"]
               for d in ket_qua.get("truot_mon", []))


def tao_scheduler() -> BackgroundScheduler:
    """Tạo một scheduler dùng múi giờ Việt Nam và không chạy trùng cùng job."""
    scheduler = BackgroundScheduler(timezone=_MUI_GIO)
    scheduler.add_job(gui_hang_doi_email, "interval", minutes=5, id="gui_hang_doi_email",
                      max_instances=1, coalesce=True)
    scheduler.add_job(nhac_theo_moc, "cron", hour=7, minute=0, id="nhac_theo_moc",
                      max_instances=1, coalesce=True)
    scheduler.add_job(du_doan_lai_khi_co_mo_hinh_moi, "cron", hour=2, minute=0,
                      id="du_doan_lai_khi_co_mo_hinh_moi", max_instances=1, coalesce=True)
    return scheduler
