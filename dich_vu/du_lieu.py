"""Đọc văn bản trang Xem điểm (xem trước) và lưu một lần cập nhật (SPEC §12.4).

Dạng dữ liệu trao đổi với API là JSON thuần (list dict, ô trống = null), ĐÚNG
tên cột như ml/; kết quả xem_truoc() gửi lại nguyên vẹn cho luu() được (sau
khi người dùng sửa).
"""

import numpy as np
import pandas as pd

import doc_cong_thong_tin as cong
import doc_form as form
from db import repo_canh_bao as repo
from dich_vu import LoiDuLieu

COT_HOC_KY = ["hoc_ky", "nam_bat_dau", "ky_trong_nam", "tc_dat_hk", "dtb_hk", "tctl",
              "tc_dang_ky", "dtb_tl", "drl", "muc_vang", "hoc_phi"]
COT_MON = ["stt_mon", "ten_mon", "so_tc", "diem_gk", "ti_trong_gk", "vang_lt", "vang_th"]
_SO_HOC_KY = ["tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl"]
_SO_MON = ["so_tc", "diem_gk", "ti_trong_gk"]
_LUA_CHON = {"muc_vang": form.MUC_VANG, "hoc_phi": form.HOC_PHI,
             "vang_lt": form.VANG_LY_THUYET, "vang_th": form.VANG_THUC_HANH}


def ve_json(bang: pd.DataFrame) -> list[dict]:
    """DataFrame -> list dict, NaN / NA thành None, số numpy thành số Python."""
    return [{k: (None if not isinstance(v, (list, dict)) and pd.isna(v) else
                 v.item() if isinstance(v, np.generic) else v) for k, v in dong.items()}
            for dong in bang.astype(object).to_dict("records")]


def xem_truoc(van_ban: str) -> dict:
    """Đọc văn bản, KHÔNG lưu. Văn bản không nhận ra -> LoiDuLieu.

    {"thong_tin": {"nam_nhap_hoc", "nganh", "he_dao_tao"},
     "hoc_ky": [{cột COT_HOC_KY..., "ten"}], "mon": [{cột COT_MON...}],
     "ky_mon": "HK1 2026–2027", "canh_bao_du_lieu": [...], "hop_le", "loi": [...]}
    """
    try:
        sinh_vien, bang_hoc_ky, bang_mon = cong.doc_van_ban(van_ban)
    except ValueError as e:
        raise LoiDuLieu(str(e)) from e
    nam_ky = cong.nam_ky_hoc_ky(van_ban)
    hk = bang_hoc_ky.assign(
        nam_bat_dau=bang_hoc_ky["hoc_ky"].map(lambda k: nam_ky[k][0]),
        ky_trong_nam=bang_hoc_ky["hoc_ky"].map(lambda k: nam_ky[k][1]))[COT_HOC_KY]
    hk["ten"] = [cong.ten_mot_ky(nam_ky[k][1], nam_ky[k][0]) for k in hk["hoc_ky"]]
    ky_mon = int(bang_mon["hoc_ky"].iloc[0]) if len(bang_mon) else None
    sv = sinh_vien.iloc[0]
    return {
        "thong_tin": {"nam_nhap_hoc": None if pd.isna(sv["nam_nhap_hoc"]) else int(sv["nam_nhap_hoc"]),
                      "nganh": None if pd.isna(sv["nganh"]) else sv["nganh"],
                      "he_dao_tao": None if pd.isna(sv["he_dao_tao"]) else sv["he_dao_tao"]},
        "hoc_ky": ve_json(hk),
        "mon": ve_json(bang_mon[COT_MON]),
        "ky_mon": cong.ten_mot_ky(*reversed(nam_ky[ky_mon])) if ky_mon in nam_ky else None,
        "canh_bao_du_lieu": cong.canh_bao_du_lieu(van_ban),
        "hop_le": bool(sv["hop_le"]),
        "loi": [l for l in sv["loi"].split("; ") if l],
    }


def _bang(dong: list[dict], cot: list[str], cot_so: list[str]) -> pd.DataFrame:
    bang = pd.DataFrame(dong, columns=cot).astype(object)
    bang[cot_so] = bang[cot_so].apply(pd.to_numeric, errors="coerce").astype(float)
    return bang


def luu(user_id: int, nguon: str, thong_tin: dict, hoc_ky: list[dict], mon: list[dict],
        muc_vang: str | None = None, hoc_phi: str | None = None) -> int:
    """Kiểm tra rồi lưu một lần cập nhật, trả về lan_cap_nhat_id.

    muc_vang / hoc_phi (không bắt buộc) ghi vào học kỳ gần nhất. Dữ liệu sai
    -> LoiDuLieu kèm danh sách chỗ sai, không lưu gì.
    """
    if nguon not in repo.NGUON:
        raise LoiDuLieu(f"Nguồn dữ liệu phải là một trong {repo.NGUON}.")
    if not hoc_ky:
        raise LoiDuLieu("Chưa có học kỳ nào đã có điểm.")
    hk = _bang(hoc_ky, COT_HOC_KY, _SO_HOC_KY)
    bang_mon = _bang(mon, COT_MON, _SO_MON)
    if muc_vang is not None:
        hk.loc[hk.index[-1], "muc_vang"] = muc_vang
    if hoc_phi is not None:
        hk.loc[hk.index[-1], "hoc_phi"] = hoc_phi

    loi = []
    for bang, cot_chon in [(hk, ["muc_vang", "hoc_phi"]), (bang_mon, ["vang_lt", "vang_th"])]:
        for cot in cot_chon:
            sai = set(bang[cot].dropna()) - set(_LUA_CHON[cot])
            if sai:
                loi.append(f"{cot}: giá trị không có trong lựa chọn của form: {sorted(sai)}")
    if bang_mon["so_tc"].isna().any():
        loi.append("Có môn chưa có số tín chỉ.")
    if not bang_mon["ti_trong_gk"].dropna().between(0, 1, inclusive="neither").all():
        loi.append("Tỉ trọng giữa kỳ phải nằm giữa 0 và 1 (ví dụ 0,4 là 40%).")
    if not bang_mon["diem_gk"].dropna().between(0, 10).all():
        loi.append("Điểm giữa kỳ phải từ 0 đến 10.")

    kiem = hk.assign(ma_sv="SV1", hoc_he=np.nan)
    kiem["hoc_ky"] = pd.to_numeric(kiem["hoc_ky"], errors="coerce")
    sv = pd.DataFrame(index=pd.Index(["SV1"], name="ma_sv"))
    loi += form.kiem_tra(kiem, sv)["SV1"]
    if loi:
        raise LoiDuLieu("Dữ liệu chưa hợp lệ, chưa lưu.", loi)
    return repo.luu_lan_cap_nhat(user_id, nguon, thong_tin or {}, hk, bang_mon)
