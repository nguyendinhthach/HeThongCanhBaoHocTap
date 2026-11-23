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
# Lần 1 xếp trong CUA_SO_NGAY ngày đầu kể từ mốc, lần 2 trong CUA_SO_NGAY ngày
# tiếp theo; quá 2 cửa sổ thì mốc đã qua, bỏ qua (không gửi nhắc mốc cũ).
CUA_SO_NGAY = 7


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


def _ngay_nhac_lan_1(user_id: int, moc: dict) -> date | None:
    """Ngày đã xếp nhắc lần 1 của mốc này cho người này; chưa có thì None."""
    for email in repo.lich_su_email(user_id, 200):
        if email["loai"] == moc["loai"] and email["moc"] == moc["moc"] and email["lan_nhac"] == 1:
            return email["thoi_diem_tao"].date()
    return None


def nhac_theo_moc(ngay_hom_nay: date | None = None) -> int:
    """Nhắc người chưa cập nhật từ ngày mốc (SPEC §12.5), tối đa 2 lần mỗi mốc:

    - ngày 0..6 kể từ mốc: nhắc lần 1;
    - ngày 7..13: nhắc lần 2 cho ai đã nhận lần 1 từ 7 ngày trở lên; người mới
      (chưa nhận lần 1, ví dụ vừa đăng ký) nhận lần 1 muộn, không có lần 2;
    - từ ngày 14: mốc đã qua, bỏ qua — không gửi dồn nhắc của mốc cũ.
    Trùng (người, loại, mốc, lần) thì repo.them_email tự bỏ qua.
    """
    hom_nay = ngay_hom_nay or datetime.now(_MUI_GIO).date()
    da_xep = 0
    for moc in _doc_moc_hoc_ky():
        if moc["bat_dau"] is None:
            _log.warning("Bỏ qua mốc %r vì chưa cấu hình ngày bat_dau.", moc["moc"])
            continue

        bat_dau = date.fromisoformat(moc["bat_dau"])
        so_ngay = (hom_nay - bat_dau).days
        if not 0 <= so_ngay < 2 * CUA_SO_NGAY:
            continue

        bat_dau_datetime = datetime.combine(bat_dau, time.min)
        for user_id in repo.nguoi_chua_cap_nhat_tu(bat_dau_datetime):
            lan_nhac = 1
            if so_ngay >= CUA_SO_NGAY:
                ngay_lan_1 = _ngay_nhac_lan_1(user_id, moc)
                if ngay_lan_1 is not None:
                    if hom_nay - ngay_lan_1 < timedelta(days=CUA_SO_NGAY):
                        continue                    # lần 1 còn mới (nhận muộn): chưa nhắc lại
                    lan_nhac = 2
            if lan_nhac == 1:
                tieu_de = f"Nhắc cập nhật kết quả học tập: {moc['moc']}"
                noi_dung = (f"Đã đến mốc {moc['moc']}. Hãy cập nhật kết quả học tập để xem cảnh báo "
                            f"sớm và các gợi ý cải thiện.{thong_bao.DONG_CUOI}")
            else:
                tieu_de = f"Nhắc lần 2: {moc['moc']}"
                noi_dung = (f"Đây là lần nhắc thứ hai cho mốc {moc['moc']}. Nếu chưa cập nhật, "
                            f"hãy nhập kết quả học tập để xem cảnh báo sớm.{thong_bao.DONG_CUOI}")
            if repo.them_email(user_id, moc["loai"], tieu_de, noi_dung,
                               moc=moc["moc"], lan_nhac=lan_nhac) is not None:
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
