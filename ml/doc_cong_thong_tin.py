"""
Đọc kết quả học tập dán từ cổng thông tin sinh viên (online.dlu.edu.vn).

Trường không có nút xuất hay API, nên sinh viên mở trang "Xem điểm", nhấn
Ctrl+A rồi Ctrl+C, dán vào hệ thống. Văn bản dán có dạng:

    Năm học:2023-2024
    Học kỳ: HK01
    1	20CT1101	Nhập môn ngành CNTT	3	5.8	2.0	C
    Chi tiết học phần: 20CT1101 - Nhập môn ngành CNTT        (chỉ khi đã mở mũi tên)
    1	Điểm Thi giữa học phần	HS1	8.5
    2	Điểm thi lý thuyết	60%	4.0
    - Số TC đạt học kỳ: 13
    - Điểm TB học kỳ (hệ 4): 2.46
    - Điểm rèn luyện: 80
    - Tổng số TC tích lũy/ Số TC đăng ký: 13/13
    - Điểm TB tích lũy toàn khóa (hệ 4): 2.46

File này chuyển văn bản đó về ĐÚNG 3 bảng mà doc_form.doc_form() trả về
(sinh viên, học kỳ, môn), nên dac_trung.py, mo_hinh_cuoi.du_doan() và mô
hình đã train dùng lại nguyên. Số liệu tổng kết lấy y như trường tính, không
tự tính lại GPA.

- Học kỳ đã có tổng kết → một dòng bảng học kỳ (đánh số 1, 2, ... theo thứ tự).
- Học kỳ đang học (chưa có điểm, tổng kết trống) → các môn của nó vào bảng
  môn, để dự đoán trượt môn; nếu không có thì bảng môn là học kỳ gần nhất.
- Bỏ môn có dấu "*" (Giáo dục quốc phòng, Giáo dục thể chất) và môn 0 tín
  chỉ (Sinh hoạt công dân) — trường cũng không tính chúng.
- Không đọc họ tên, mã sinh viên: mã trong bảng luôn là "SV1".
- Trang không có mức vắng, học phí → ghi "Không nhớ / không muốn trả lời"
  như sinh viên bỏ qua câu đó trên form (mức vắng thành ô trống + cột "_thieu").
- Điểm giữa kỳ chỉ có ở môn đã mở "Chi tiết" và đã có điểm; môn chưa có thì
  mo_hinh_cuoi.du_doan() không dự đoán trượt môn cho môn đó.

Chạy:  python ml/doc_cong_thong_tin.py file.txt      # văn bản đã dán ra file
       python ml/doc_cong_thong_tin.py --clipboard   # lấy thẳng từ clipboard
"""

import re
import sys

import numpy as np
import pandas as pd

import doc_form as form
from mo_phong import NGANH_KY_SU


MA_SV = "SV1"

# Các dòng tổng kết mô hình cần, đúng chữ trên trang
DONG_TONG_KET = ["Số TC đạt học kỳ", "Điểm TB học kỳ (hệ 4)", "Điểm rèn luyện",
                 "Tổng số TC tích lũy/ Số TC đăng ký", "Điểm TB tích lũy toàn khóa (hệ 4)"]

# Mã ngành trong mã chương trình đào tạo (vd. "CQ23CT-PM": chính quy, khoá 23,
# ngành CT, chuyên ngành PM). Bổ sung khi gặp mã ngành khác.
NGANH_THEO_MA = {"CT": "Công nghệ thông tin"}

_NAM_HOC = re.compile(r"^Năm học:\s*(\d{4})\s*-\s*(\d{4})")
_HOC_KY = re.compile(r"^Học kỳ:\s*HK0*(\d+)")
_CHI_TIET = re.compile(r"^Chi tiết học phần:\s*(\S+)")
_TONG_KET = re.compile(r"^-\s*(.+?)\s*:\s*(.*)$")
_CHUONG_TRINH = re.compile(r"^[A-Z]{2}(\d{2})([A-Z]{2,})-?")


def _so(chuoi):
    """'7.5' -> 7.5; chuỗi rỗng / không phải số -> NaN."""
    try:
        return float(chuoi.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return np.nan


def phan_tich(van_ban):
    """Văn bản dán -> (thông tin chung, danh sách học kỳ theo thứ tự trên trang).

    Mỗi học kỳ: {"nam", "ky", "mon": [...], "tong_ket": {tên dòng: chuỗi}}.
    Mỗi môn: {"ma", "ten", "so_tc", "diem_10", "diem_4", "diem_chu", "thanh_phan": [...]}.
    """
    thong_tin, cac_hoc_ky = {}, []
    nam = hoc_ky = mon_chi_tiet = None
    dong_truoc = ""

    for dong in van_ban.splitlines():
        dong = dong.rstrip("\r")
        sach = dong.strip()
        if dong_truoc == "Chương trình đào tạo" and sach:
            thong_tin["chuong_trinh"] = sach
        if sach:
            dong_truoc = sach

        if m := _NAM_HOC.match(sach):
            nam = int(m.group(1))
            continue
        if m := _HOC_KY.match(sach):
            hoc_ky = {"nam": nam, "ky": int(m.group(1)), "mon": [], "tong_ket": {}}
            cac_hoc_ky.append(hoc_ky)
            mon_chi_tiet = None
            continue
        if hoc_ky is None:
            continue
        if m := _CHI_TIET.match(sach):
            ma = m.group(1)
            mon_chi_tiet = next((mn for mn in reversed(hoc_ky["mon"]) if mn["ma"] == ma), None)
            continue
        if m := _TONG_KET.match(sach):
            hoc_ky["tong_ket"][m.group(1)] = m.group(2).strip()
            mon_chi_tiet = None
            continue

        cot = [c.strip() for c in dong.split("\t")]
        if len(cot) < 4 or not cot[0].isdigit():
            continue
        if mon_chi_tiet is not None and cot[1].startswith("Điểm"):
            # Dòng điểm thành phần: STT, tên, trọng số, điểm lần 1..3 (lấy lần cao nhất)
            diem = [d for d in map(_so, cot[3:6]) if not np.isnan(d)]
            mon_chi_tiet["thanh_phan"].append(
                {"ten": cot[1], "trong_so": cot[2], "diem": max(diem) if diem else np.nan})
            continue
        so_tc = _so(cot[3])
        if np.isnan(so_tc):
            continue
        hoc_ky["mon"].append({
            "ma": cot[1], "ten": cot[2], "so_tc": so_tc,
            "diem_10": _so(cot[4]) if len(cot) > 4 else np.nan,
            "diem_4": _so(cot[5]) if len(cot) > 5 else np.nan,
            "diem_chu": cot[6] if len(cot) > 6 else "",
            "thanh_phan": [],
        })
        mon_chi_tiet = None
    return thong_tin, cac_hoc_ky


def _tinh_vao_tich_luy(mon):
    """Môn được trường tính tín chỉ / điểm trung bình: có TC và không có dấu '*'."""
    return mon["so_tc"] > 0 and not mon["ten"].rstrip().endswith("*")


def _diem_giua_ky(mon):
    """(điểm giữa kỳ, tỉ trọng giữa kỳ) từ chi tiết học phần, thiếu thì NaN.

    Trọng số giữa kỳ có khi ghi "30%", có khi ghi "HS1" (hệ số): khi đó tỉ trọng
    = 100% − trọng số của các thành phần còn lại.
    """
    giua_ky = next((tp for tp in mon["thanh_phan"] if "giữa" in tp["ten"].lower()), None)
    if giua_ky is None:
        return np.nan, np.nan
    if giua_ky["trong_so"].endswith("%"):
        return giua_ky["diem"], _so(giua_ky["trong_so"][:-1]) / 100
    con_lai = [_so(tp["trong_so"][:-1]) for tp in mon["thanh_phan"]
               if tp is not giua_ky and tp["trong_so"].endswith("%")]
    ti_trong = 1 - sum(con_lai) / 100 if con_lai else np.nan
    return giua_ky["diem"], ti_trong


def _he_dao_tao(chuong_trinh):
    """(năm nhập học, ngành, hệ đào tạo) suy từ mã chương trình; không rõ thì NaN."""
    m = _CHUONG_TRINH.match(chuong_trinh or "")
    if not m:
        return np.nan, np.nan, np.nan
    nganh = NGANH_THEO_MA.get(m.group(2), np.nan)
    he = np.nan if pd.isna(nganh) else ("Kỹ sư (4,5 năm)" if nganh in NGANH_KY_SU else "Cử nhân (4 năm)")
    return 2000 + int(m.group(1)), nganh, he


def doc_van_ban(van_ban):
    """Văn bản dán -> (sinh_vien, bang_hoc_ky, bang_mon), cùng dạng doc_form.doc_form()."""
    thong_tin, cac_hoc_ky = phan_tich(van_ban)
    if not cac_hoc_ky:
        raise ValueError("Không tìm thấy học kỳ nào: hãy sao chép toàn bộ trang 'Xem điểm' "
                         "(Ctrl+A, Ctrl+C) của cổng thông tin sinh viên.")

    da_xong = [hk for hk in cac_hoc_ky if _co_tong_ket(hk)]
    dang_hoc = [hk for hk in cac_hoc_ky if hk not in da_xong]

    cac_dong = []
    for k, hk in enumerate(da_xong, start=1):
        tk = hk["tong_ket"]
        tctl, _, tc_dang_ky = tk.get("Tổng số TC tích lũy/ Số TC đăng ký", "").partition("/")
        cac_dong.append({
            "ma_sv": MA_SV, "hoc_ky": k,
            "tc_dat_hk": _so(tk.get("Số TC đạt học kỳ", "")),
            "dtb_hk": _so(tk.get("Điểm TB học kỳ (hệ 4)", "")),
            "tctl": _so(tctl), "tc_dang_ky": _so(tc_dang_ky),
            "dtb_tl": _so(tk.get("Điểm TB tích lũy toàn khóa (hệ 4)", "")),
            # Trang không có mức vắng, học phí: ghi đúng lựa chọn "không trả lời" của
            # form (mô hình đã gặp lúc train) thay vì bỏ trống mọi cột one-hot học phí
            "muc_vang": form.MUC_VANG[4], "hoc_phi": form.HOC_PHI[4],
            "drl": _so(tk.get("Điểm rèn luyện", "")),
            "hoc_he": np.nan,
        })
    bang_hoc_ky = pd.DataFrame(cac_dong, columns=["ma_sv", "hoc_ky", *form.CAU_HOC_KY.values()])

    # Bảng môn: học kỳ đang học (để dự đoán), không có thì học kỳ gần nhất đã xong
    if dang_hoc:
        hk_mon, so_hk = dang_hoc[-1], len(da_xong) + 1
    else:
        hk_mon, so_hk = da_xong[-1], len(da_xong)
    cac_mon = []
    for stt, mon in enumerate((m for m in hk_mon["mon"] if _tinh_vao_tich_luy(m)), start=1):
        diem_gk, ti_trong = _diem_giua_ky(mon)
        if np.isnan(mon["diem_10"]):
            ket_qua = np.nan                                   # chưa có điểm
        else:
            ket_qua = "Đạt" if mon["diem_10"] >= 4 else "Không đạt (điểm F)"
        cac_mon.append({"ma_sv": MA_SV, "hoc_ky": so_hk, "stt_mon": stt, "ten_mon": mon["ten"],
                        "so_tc": mon["so_tc"], "ket_qua": ket_qua, "diem_gk": diem_gk,
                        "ti_trong_gk": ti_trong, "vang_lt": np.nan, "vang_th": np.nan})
    bang_mon = pd.DataFrame(cac_mon, columns=["ma_sv", "hoc_ky", "stt_mon", *form.CAU_MON.values()])

    nam_nhap_hoc, nganh, he = _he_dao_tao(thong_tin.get("chuong_trinh"))
    if pd.isna(nam_nhap_hoc) and cac_hoc_ky[0]["nam"]:
        nam_nhap_hoc = cac_hoc_ky[0]["nam"]
    sinh_vien = pd.DataFrame({
        "nam_nhap_hoc": [nam_nhap_hoc], "nganh": [nganh], "he_dao_tao": [he],
        "tinh_trang": ["Đang học"], "ky_luat": [np.nan], "so_mon_hk_cuoi": [len(cac_mon)],
    }, index=pd.Index([MA_SV], name="ma_sv"))

    loi = form.kiem_tra(bang_hoc_ky, sinh_vien)
    sinh_vien["hop_le"] = [not loi[MA_SV]]
    sinh_vien["loi"] = ["; ".join(loi[MA_SV])]
    return sinh_vien, bang_hoc_ky, bang_mon


def ten_hoc_ky(van_ban):
    """{số thứ tự học kỳ như trong bảng: "HK1 2026–2027"}, kể cả kỳ đang học
    và kỳ kế tiếp sau kỳ cuối (nếu trang chưa có kỳ đang học)."""
    _, cac_hoc_ky = phan_tich(van_ban)
    da_xong = [hk for hk in cac_hoc_ky if _co_tong_ket(hk)]
    theo_thu_tu = da_xong + [hk for hk in cac_hoc_ky if hk not in da_xong][-1:]
    ten = {k: _ten_mot_ky(hk["ky"], hk["nam"]) for k, hk in enumerate(theo_thu_tu, start=1)}
    cuoi = theo_thu_tu[-1]
    if cuoi["nam"] is None:
        ten[len(theo_thu_tu) + 1] = "học kỳ kế tiếp"
        return ten
    nam, ky = (cuoi["nam"], 2) if cuoi["ky"] == 1 else (cuoi["nam"] + 1, 1)
    ten[len(theo_thu_tu) + 1] = _ten_mot_ky(ky, nam)
    return ten


def _co_tong_ket(hoc_ky):
    return not np.isnan(_so(hoc_ky["tong_ket"].get("Điểm TB học kỳ (hệ 4)", "")))


def _ten_mot_ky(ky, nam):
    return f"HK{ky}" if nam is None else f"HK{ky} {nam}–{nam + 1}"


def canh_bao_du_lieu(van_ban):
    """Dấu hiệu văn bản bị thiếu hoặc bị sửa nhầm, để báo trước khi dự đoán.

    Đây là những lỗi không làm bộ đọc dừng lại nhưng khiến số liệu sai mà không
    ai biết: mất dòng "Học kỳ", thiếu dòng tổng kết... Trả về list chuỗi.
    """
    _, cac_hoc_ky = phan_tich(van_ban)
    canh_bao = []
    if cac_hoc_ky and cac_hoc_ky[0]["nam"] is None:
        canh_bao.append("Không thấy dòng 'Năm học' đầu tiên nên tên học kỳ có thể thiếu năm.")

    for truoc, sau in zip(cac_hoc_ky, cac_hoc_ky[1:]):
        if truoc["nam"] is None or sau["nam"] is None:
            continue
        # HK1 -> HK2 cùng năm, hoặc HK2 trở lên -> HK1 năm sau (HK1 -> HK1 là mất HK2)
        lien_tuc = (sau["nam"] == truoc["nam"] and sau["ky"] == truoc["ky"] + 1) or (
            sau["nam"] == truoc["nam"] + 1 and sau["ky"] == 1 and truoc["ky"] >= 2)
        if not lien_tuc:
            canh_bao.append(f"Sau {_ten_mot_ky(truoc['ky'], truoc['nam'])} là "
                            f"{_ten_mot_ky(sau['ky'], sau['nam'])}: có thể thiếu một học kỳ "
                            "(hoặc bạn đã nghỉ học kỳ đó).")

    for hk in cac_hoc_ky[:-1]:
        if not _co_tong_ket(hk):
            canh_bao.append(f"{_ten_mot_ky(hk['ky'], hk['nam'])} không có ĐTB học kỳ nên bị bỏ qua, "
                            "các học kỳ sau bị đánh số lùi lại.")
    for hk in filter(_co_tong_ket, cac_hoc_ky):
        thieu = [dong for dong in DONG_TONG_KET if not hk["tong_ket"].get(dong)]
        if thieu:
            canh_bao.append(f"{_ten_mot_ky(hk['ky'], hk['nam'])} thiếu dòng: {', '.join(thieu)}.")
    return canh_bao


def doc_file(duong_dan):
    """Đọc file .txt chứa văn bản đã dán (utf-8)."""
    with open(duong_dan, encoding="utf-8-sig") as f:
        return doc_van_ban(f.read())


def doc_clipboard():
    """Lấy văn bản đang có trong clipboard (đã Ctrl+C trang Xem điểm)."""
    import tkinter
    goc = tkinter.Tk()
    goc.withdraw()
    try:
        return goc.clipboard_get()
    finally:
        goc.destroy()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pd.set_option("display.width", 200)
    if len(sys.argv) < 2:
        sys.exit(__doc__.split("Chạy:")[1])
    van_ban = doc_clipboard() if sys.argv[1] == "--clipboard" else open(sys.argv[1], encoding="utf-8-sig").read()
    sinh_vien, bang_hoc_ky, bang_mon = doc_van_ban(van_ban)
    ten = ten_hoc_ky(van_ban)
    sv = sinh_vien.iloc[0]
    print(f"Đọc được: {len(bang_hoc_ky)} học kỳ đã có tổng kết, nhập học {sv['nam_nhap_hoc']}, "
          f"{sv['nganh']}, {sv['he_dao_tao']}" + ("" if sv["hop_le"] else f" — LỖI: {sv['loi']}"))
    # Trang không ghi kỳ nào bị cảnh báo: tự xét từng kỳ theo Điều 18.1 QĐ 600
    # (chưa xét được điều kiện rớt > 50% TC đăng ký trong kỳ)
    from gan_nhan import SO_LAN_CANH_BAO_THOI_HOC, gan_nhan_hoc_ky
    co_nhan = gan_nhan_hoc_ky(bang_hoc_ky)
    hien_thi = co_nhan.assign(
        hoc_ky=co_nhan["hoc_ky"].map(ten),
        canh_bao_tu_tinh=co_nhan["ly_do_canh_bao"].map(lambda ld: ld if ld else "không"))
    print(hien_thi[["hoc_ky", "tc_dat_hk", "dtb_hk", "tctl", "tc_dang_ky", "dtb_tl", "drl",
                    "canh_bao_tu_tinh"]].to_string(index=False))
    print("(canh_bao_tu_tinh: hệ thống tự xét theo Điều 18.1 QĐ 600 vì trang không ghi; "
          "không phải danh sách cảnh báo chính thức)")
    lien_tiep = int(co_nhan["so_lan_canh_bao_lien_tiep"].iloc[-1])

    # Dự đoán bằng mô hình đã lưu (nếu có). Văn bản có họ tên, MSSV nên chỉ ghi
    # ra file tạm để dùng chung đường đọc .txt của dac_trung, rồi xoá ngay.
    import os
    import tempfile
    import mo_hinh_cuoi
    tam = tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False)
    try:
        tam.write(van_ban)
        tam.close()
        cb, th, tm = (mo_hinh_cuoi.du_doan(tam.name, m) for m in ["canh_bao", "thoi_hoc", "truot_mon"])
        dong = cb.iloc[0]
        print(f"\n=== DỰ ĐOÁN CHO {ten[dong['du_doan_cho_hk']]} "
              f"(dựa trên dữ liệu đến {ten[dong['dua_tren_hk']]}) ===")
        d = cb.iloc[0]
        print(f"- Bị cảnh báo học tập: {'CÓ NGUY CƠ' if d['bao_dong'] else 'không'} "
              f"(điểm nguy cơ {d['xac_suat']:.2f})"
              + (f" — lý do: {'; '.join(d['ly_do'])}" if d["ly_do"] else ""))
        d = th.iloc[0]
        if lien_tiep < SO_LAN_CANH_BAO_THOI_HOC - 1:
            # Điều 18.2a: thôi học khi bị cảnh báo lần thứ 3 liên tiếp
            print(f"- Bị buộc thôi học: không thể xảy ra ở kỳ này — mới bị cảnh báo {lien_tiep} kỳ "
                  f"liên tiếp (tự tính), cần {SO_LAN_CANH_BAO_THOI_HOC - 1} kỳ liên tiếp trước đó")
        else:
            print(f"- Bị buộc thôi học: {'CÓ NGUY CƠ' if d['bao_dong'] else 'không'} "
                  f"(đã bị cảnh báo {lien_tiep} kỳ liên tiếp; điểm nguy cơ {d['xac_suat']:.2f})"
                  + (f" — lý do: {'; '.join(d['ly_do'])}" if d["ly_do"] else ""))
        print("- Trượt từng môn:")
        for _, d in tm.iterrows():
            if d["ghi_chu"]:
                ket_luan = d["ghi_chu"]
            else:
                ket_luan = ("CÓ NGUY CƠ" if d["bao_dong"] else "không") + f" (điểm nguy cơ {d['xac_suat']:.2f})"
                if d["ly_do"]:
                    ket_luan += f" — lý do: {'; '.join(d['ly_do'])}"
            print(f"    {d['ten_mon']}: {ket_luan}")
    except FileNotFoundError as loi:
        print(f"\n(Chưa dự đoán: {loi})")
    finally:
        os.remove(tam.name)
