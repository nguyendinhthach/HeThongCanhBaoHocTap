"""Dự đoán 3 mục tiêu cho lần cập nhật mới nhất, kèm gợi ý; lưu và xếp email
cảnh báo (SPEC §12.4 POST /du-doan, §12.6).

Tác vụ "dự đoán lại khi có mô hình mới" gọi đúng chay() này cho từng người.
"""

import os

import pandas as pd

import dac_trung
import doc_cong_thong_tin as cong
import goi_y
import mo_hinh_cuoi
from db import repo_canh_bao as repo
from dich_vu import LoiDuLieu, thong_bao
from gan_nhan import SO_LAN_CANH_BAO_THOI_HOC, gan_nhan_hoc_ky

_goi_da_tai = {}


def goi_mo_hinh(muc_tieu: str) -> dict:
    """Gói mô hình đã lưu (models/<muc_tieu>.joblib), giữ trong bộ nhớ; file đổi thì đọc lại."""
    duong_dan = os.path.join(mo_hinh_cuoi.THU_MUC_MO_HINH, f"{muc_tieu}.joblib")
    if not os.path.exists(duong_dan):
        raise LoiDuLieu("Chưa có mô hình đã train: chạy python ml/mo_hinh_cuoi.py trên máy chủ.")
    sua = os.path.getmtime(duong_dan)
    if _goi_da_tai.get(muc_tieu, (None,))[0] != sua:
        _goi_da_tai[muc_tieu] = (sua, mo_hinh_cuoi.tai(muc_tieu))
    return _goi_da_tai[muc_tieu][1]


def chay(user_id: int, xep_email: bool = True) -> dict:
    """Dự đoán cho lần cập nhật mới nhất của user_id, lưu, trả về ket_qua_moi_nhat().

    Xếp email cảnh báo khi kết quả "cao" mà lượt trước không "cao" (hoặc là lần
    đầu). Chưa có dữ liệu / dữ liệu không hợp lệ -> LoiDuLieu.
    """
    moi_nhat = repo.lan_cap_nhat_moi_nhat(user_id)
    if moi_nhat is None:
        raise LoiDuLieu("Chưa có dữ liệu học tập: hãy cập nhật kết quả học tập trước.")
    lcn = moi_nhat["id"]
    sinh_vien, hk, mon = repo.du_lieu_cho_ml(lcn)
    if not sinh_vien["hop_le"].iloc[0]:
        raise LoiDuLieu("Dữ liệu đã lưu chưa hợp lệ.", sinh_vien["loi"].iloc[0].split("; "))

    du_lieu = dac_trung.chuan_bi_du_lieu(sinh_vien, hk, mon)
    goi_cb, goi_tm = goi_mo_hinh("canh_bao"), goi_mo_hinh("truot_mon")
    cb = mo_hinh_cuoi.du_doan(None, "canh_bao", du_lieu=du_lieu).iloc[0]
    th = mo_hinh_cuoi.du_doan(None, "thoi_hoc", du_lieu=du_lieu).iloc[0]
    tm = mo_hinh_cuoi.du_doan(None, "truot_mon", du_lieu=du_lieu)

    # Tên học kỳ được dự đoán: kỳ kế tiếp kỳ cuối đã có điểm
    cuoi = moi_nhat["bang_hoc_ky"].iloc[-1]
    nam = None if pd.isna(cuoi["nam_bat_dau"]) else int(cuoi["nam_bat_dau"])
    ky = None if pd.isna(cuoi["ky_trong_nam"]) else int(cuoi["ky_trong_nam"])
    nam_toi, ky_toi = cong.ky_ke_tiep(nam, ky)
    cho = {"cho_thu_tu": int(cb["du_doan_cho_hk"]), "cho_ten": cong.ten_mot_ky(ky_toi, nam_toi)}
    ban_cb = {"phuong_phap": goi_cb["phuong_phap"], "phien_ban_mo_hinh": goi_cb["thoi_diem"],
              "nguong": goi_cb["nguong"]}

    lien_tiep = int(gan_nhan_hoc_ky(hk)["so_lan_canh_bao_lien_tiep"].fillna(0).iloc[-1])
    ket_qua = [{**cho, **ban_cb, "muc_tieu": "canh_bao", "diem_nguy_co": float(cb["xac_suat"]),
                "bao_dong": bool(cb["bao_dong"]), "muc_nguy_co": "cao" if cb["bao_dong"] else "thap",
                "ly_do": list(cb["ly_do"]), "goi_y": goi_y.goi_y_hoc_ky(hk)}]
    if lien_tiep < SO_LAN_CANH_BAO_THOI_HOC - 1:
        ket_qua.append({**cho, **ban_cb, "muc_tieu": "thoi_hoc", "diem_nguy_co": 0.0, "bao_dong": False,
                        "muc_nguy_co": "thap", "ly_do": [], "goi_y": [],
                        "ghi_chu": f"Chưa thể xảy ra ở kỳ này: mới bị cảnh báo {lien_tiep} kỳ liên tiếp "
                                   f"(tự xét theo quy chế), cần {SO_LAN_CANH_BAO_THOI_HOC - 1} kỳ liên tiếp."})
    else:
        ket_qua.append({**cho, **ban_cb, "muc_tieu": "thoi_hoc", "diem_nguy_co": float(th["xac_suat"]),
                        "bao_dong": bool(th["bao_dong"]), "muc_nguy_co": "cao" if th["bao_dong"] else "thap",
                        "ly_do": list(th["ly_do"]), "goi_y": [],
                        "ghi_chu": f"Đã bị cảnh báo {lien_tiep} kỳ liên tiếp (tự xét theo quy chế)."})

    mon_theo_stt = mon.set_index("stt_mon")
    for _, d in tm.iterrows():
        m = mon_theo_stt.loc[d["stt_mon"]]
        chua = pd.isna(d["xac_suat"])
        ket_qua.append({
            **cho, "muc_tieu": "truot_mon", "stt_mon": int(d["stt_mon"]),
            "diem_nguy_co": None if chua else float(d["xac_suat"]), "bao_dong": bool(d["bao_dong"]),
            "muc_nguy_co": "chua_du_doan" if chua else ("cao" if d["bao_dong"] else "thap"),
            "ly_do": list(d["ly_do"]), "ghi_chu": d["ghi_chu"] or None,
            "goi_y": goi_y.goi_y_mon(m["diem_gk"], m["ti_trong_gk"], m["vang_lt"], m["vang_th"]),
            "phuong_phap": goi_tm["phuong_phap"], "phien_ban_mo_hinh": goi_tm["thoi_diem"],
            "nguong": goi_tm["nguong"],
        })

    ids = repo.luu_du_doan(lcn, ket_qua)
    ket_qua_luu = repo.ket_qua_moi_nhat(user_id)
    ket_qua_luu["email_canh_bao"] = False
    if xep_email and ket_qua[0]["muc_nguy_co"] == "cao" and repo.muc_canh_bao_truoc(user_id, lcn) != "cao":
        hs = repo.ho_so_canh_bao(user_id)
        tieu_de, noi_dung = thong_bao.soan_email_canh_bao(hs["ho_ten"], ket_qua_luu)
        ket_qua_luu["email_canh_bao"] = repo.them_email(
            user_id, "canh_bao", tieu_de, noi_dung, du_doan_id=ids[0]) is not None
    return ket_qua_luu
