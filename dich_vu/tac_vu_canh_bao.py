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
_LOAI_NHAC = {"nhac_giua_ky", "nhac_cuoi_ky"}


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

    for vi_tri, moc in enumerate(moc_hoc_ky):
        if not isinstance(moc, dict):
            raise ValueError(f"Mốc thứ {vi_tri + 1} phải là một object JSON.")
        if not isinstance(moc.get("moc"), str) or not moc["moc"].strip():
            raise ValueError(f"Mốc thứ {vi_tri + 1} thiếu tên 'moc'.")
        if moc.get("loai") not in _LOAI_NHAC:
            raise ValueError(f"Mốc {moc['moc']!r} có 'loai' không hợp lệ.")
        if "bat_dau" not in moc:
            raise ValueError(f"Mốc {moc['moc']!r} thiếu trường 'bat_dau'.")
        ngay_bat_dau = moc.get("bat_dau")
        if ngay_bat_dau is not None:
            if not isinstance(ngay_bat_dau, str):
                raise ValueError(f"'bat_dau' của mốc {moc['moc']!r} phải là YYYY-MM-DD hoặc null.")
            try:
                date.fromisoformat(ngay_bat_dau)
            except ValueError as loi:
                raise ValueError(f"'bat_dau' của mốc {moc['moc']!r} không phải ngày YYYY-MM-DD.") from loi
    return moc_hoc_ky


def nhac_theo_moc(ngay_hom_nay: date | None = None) -> int:
    """Xếp nhắc lần 1 đúng mốc và lần 2 sau 7 ngày; dữ liệu trùng do repo chặn."""
    hom_nay = ngay_hom_nay or datetime.now(_MUI_GIO).date()
    da_xep = 0
    for moc in _doc_moc_hoc_ky():
        if moc["bat_dau"] is None:
            _log.warning("Bỏ qua mốc %r vì chưa cấu hình ngày bat_dau.", moc["moc"])
            continue

        bat_dau = date.fromisoformat(moc["bat_dau"])
        if hom_nay < bat_dau:
            continue

        bat_dau_datetime = datetime.combine(bat_dau, time.min)
        for user_id in repo.nguoi_chua_cap_nhat_tu(bat_dau_datetime):
            noi_dung = (f"Đã đến mốc {moc['moc']}. Hãy cập nhật kết quả học tập để xem cảnh báo "
                        f"sớm và các gợi ý cải thiện.{thong_bao.DONG_CUOI}")
            if repo.them_email(user_id, moc["loai"], f"Nhắc cập nhật kết quả học tập: {moc['moc']}",
                               noi_dung, moc=moc["moc"], lan_nhac=1) is not None:
                da_xep += 1

            if hom_nay >= bat_dau + timedelta(days=7):
                noi_dung_lan_hai = (f"Đây là lần nhắc thứ hai cho mốc {moc['moc']}. Nếu chưa cập nhật, "
                                    f"hãy nhập kết quả học tập để xem cảnh báo sớm.{thong_bao.DONG_CUOI}")
                if repo.them_email(user_id, moc["loai"], f"Nhắc lần 2: {moc['moc']}",
                                   noi_dung_lan_hai, moc=moc["moc"], lan_nhac=2) is not None:
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
