"""Cấu hình hiển thị, dữ liệu mẫu và đặc trưng dự đoán trực tiếp.

Môn học và hồ sơ người dùng nay đọc từ SQL Server qua db/repo.py, không còn
nằm ở đây. Phần dữ liệu mẫu bên dưới chỉ còn một việc: sinh ra
db/du_lieu_mau.sql, để bộ số dùng lúc dựng giao diện được giữ nguyên làm mốc
đối chiếu. Dự đoán nguy cơ dùng lịch sử môn học thật trong phiên hiện tại và
không ghi kết quả vào cơ sở dữ liệu.
"""

from ui import rules
from ui import tokens as t

SEMESTERS = ["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"]


def semesters(so_ky: int) -> list[str]:
    """Học kỳ của một năm học.

    Học kỳ không phải thứ người dùng tạo ra: mọi năm đều có như nhau, số
    lượng lấy từ "Số học kỳ mỗi năm" chọn lúc đăng ký. Nhờ vậy không tồn tại
    cặp năm–kỳ không hợp lệ; kỳ chưa nhập môn chỉ là kỳ rỗng.
    """
    return SEMESTERS[:so_ky]


def years(khoa_from, khoa_to) -> list[str]:
    """Danh sách năm học suy từ niên khoá, dùng khi tạo tài khoản."""
    try:
        tu, den = int(khoa_from), int(khoa_to)
    except (TypeError, ValueError):
        return []
    if den <= tu or den - tu > 8:
        return []
    return [f"{y}–{y + 1}" for y in range(tu, den)]

SCREENS = {
    "dashboard": "Dashboard",
    "add": "Thêm / cập nhật môn học",
    "risk": "Cảnh báo & Mục tiêu",
}

# --- Dữ liệu mẫu -----------------------------------------------------------
# Port nguyên SEED của mockup, thêm mã môn học. Mã là khoá nhận diện môn (tên
# nhập tay không đáng tin), còn điểm thành phần dựng lại từ điểm mục tiêu bằng
# rules.mk_rows thay vì lưu điểm tổng kết.
#
# KHÔNG còn được ứng dụng dùng để hiển thị — chỉ dùng khi cần sinh lại
# db/du_lieu_mau.sql.
_SEED = [
    ("2024–2025", "Học kỳ 2", "20CT3101", "Công nghệ phần mềm", 3, 7.1,
     "Học lần 1"),
    ("2024–2025", "Học kỳ 2", "20CT2203", "Mạng máy tính", 3, 6.0,
     "Học lần 1"),
    ("2024–2025", "Học kỳ 2", "20TN1301", "Xác suất thống kê", 3, 4.8,
     "Học lại"),
    ("2024–2025", "Học kỳ 2", "20CT2301", "Lập trình web", 3, 8.4,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3201", "Trí tuệ nhân tạo", 3, 5.4,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3202", "Lập trình Python nâng cao", 3, 7.8,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT3203", "Cơ sở dữ liệu phân tán", 3, 4.2,
     "Học lại"),
    ("2025–2026", "Học kỳ 1", "20CT3204", "Kiểm thử phần mềm", 2, 6.5,
     "Học lần 1"),
    ("2025–2026", "Học kỳ 1", "20CT2104", "Tiếng Anh chuyên ngành 2", 2, 8.1,
     "Học cải thiện"),
    ("2026–2027", "Học kỳ 1", "20CT4901", "Đồ án tốt nghiệp", 6, 7.5,
     "Học lần 1"),
    ("2026–2027", "Học kỳ 1", "20CT4201", "Học máy ứng dụng", 3, 6.2,
     "Học lần 1"),
]


def seed_courses() -> list[dict]:
    """Bộ 11 môn mẫu, dùng để sinh db/du_lieu_mau.sql."""
    return [
        {"id": i + 1, "year": nam, "sem": ky, "code": ma, "name": ten,
         "credits": tc, "attempt": loai,
         "attempt_no": 1 if loai == "Học lần 1" else 2,
         "rows": rules.mk_rows(diem)}
        for i, (nam, ky, ma, ten, tc, diem, loai) in enumerate(_SEED)
    ]


def metrics(courses: list[dict], scale: int, tat_ca: list[dict],
            nam: str, ky: str, du_doan: dict | None = None) -> list[dict]:
    """Bốn thẻ chỉ số của kỳ đang xem; nhãn đổi theo thang điểm."""
    tk = rules.tom_tat(courses)
    delta, mau_delta = rules.so_sanh_ky_truoc(tat_ca, nam, ky, scale)
    gpa = rules.gpa_thang(tk, scale)
    if tk["tam_tinh"]:
        no_delta = f'Chỉ tính {len(courses) - tk["tam_tinh"]} môn đã đủ điểm'
    else:
        no_delta = "Phải học lại" if tk["truot"] else "Không có môn nợ"
    return [
        {"label": f"GPA học kỳ (DH{scale})",
         "value": f"{gpa:.2f}" if courses else "—",
         "color": t.TEXT, "delta": delta, "delta_color": mau_delta},
        {"label": "Tín chỉ đã đăng ký", "value": str(tk["tin_chi"]),
         "color": t.TEXT, "delta": f"{len(courses)} môn đang học",
         "delta_color": t.MUTED},
        {"label": ("Môn điểm E (học lại)" if scale == 4
                   else f"Môn dưới {t.GRADE_FAIL:.1f} (học lại)"),
         "value": str(tk["truot"]),
         "color": t.DANGER if tk["truot"] else t.SUCCESS,
         "delta": no_delta, "delta_color": t.MUTED},
        {"label": "Mức nguy cơ",
         "value": du_doan["muc_nguy_co"] if du_doan else "Chưa đủ dữ liệu",
         "color": (t.RISK_STYLES[du_doan["muc_nguy_co"]]["dot"]
                   if du_doan else t.MUTED),
         "delta": (f'{du_doan["ty_le"]:g}% xác suất kỳ tới'
                   if du_doan else "Cần ít nhất một học kỳ đủ điểm"),
         "delta_color": t.MUTED},
    ]


def course_footnote(courses: list[dict]) -> str:
    tk = rules.tom_tat(courses)
    return (f'{len(courses)} môn · {tk["tin_chi"]} tín chỉ trong học kỳ này · '
            'môn ghi "tạm tính" là chưa nhập đủ 100% trọng số điểm thành phần')


def dac_trung_canh_bao(courses: list[dict], khoa_from: int | str,
                       so_ky: int) -> tuple[dict | None, str | None]:
    """Tạo đặc trưng cho học kỳ gần nhất đã có điểm hoàn chỉnh.

    Các cột không lưu trong hồ sơ SQL được giữ thiếu hoặc gán nhóm "không trả
    lời", đúng với cách dữ liệu khảo sát được mã hoá khi huấn luyện.
    """
    from ml import gan_nhan

    try:
        nam_nhap_hoc = int(khoa_from)
    except (TypeError, ValueError) as loi:
        raise ValueError("Niên khoá bắt đầu không hợp lệ.") from loi
    if so_ky not in (2, 3):
        raise ValueError("Số học kỳ mỗi năm phải là 2 hoặc 3.")

    theo_ky: dict[tuple[int, int], list[dict]] = {}
    for mon in courses:
        try:
            nam = int(mon["year"][:4])
            ky = int("".join(c for c in mon["sem"] if c.isdigit()))
        except (KeyError, TypeError, ValueError) as loi:
            raise ValueError("Môn học thiếu năm hoặc học kỳ hợp lệ.") from loi
        if nam < nam_nhap_hoc or not 1 <= ky <= so_ky:
            raise ValueError(
                f'Học kỳ {mon["year"]} · {mon["sem"]} không khớp niên khoá '
                "hoặc số học kỳ trong hồ sơ."
            )
        theo_ky.setdefault((nam, ky), []).append(mon)

    cac_ky_day_du = []
    for (nam, ky), mon_trong_ky in sorted(theo_ky.items()):
        # Không đưa điểm tạm tính vào mô hình như thể học kỳ đã kết thúc.
        if not all(rules.du_trong_so(mon) and rules.diem_mon(mon) is not None
                   for mon in mon_trong_ky):
            continue
        tong_tin_chi = sum(mon["credits"] for mon in mon_trong_ky)
        if tong_tin_chi <= 0:
            continue
        hoc_ky = (nam - nam_nhap_hoc) * so_ky + ky
        cac_ky_day_du.append((hoc_ky, nam, ky, mon_trong_ky))

    if not cac_ky_day_du:
        return None, None

    lich_su = []
    canh_bao_lien_tiep = 0
    hoc_ky_truoc = None
    for hoc_ky, nam, ky, mon_trong_ky in cac_ky_day_du:
        if hoc_ky_truoc is not None and hoc_ky != hoc_ky_truoc + 1:
            canh_bao_lien_tiep = 0

        mon_den_ky_nay = [
            mon for mon in courses
            if (int(mon["year"][:4]), int("".join(
                c for c in mon["sem"] if c.isdigit()))) <= (nam, ky)
        ]
        dang_ky = {}
        for mon in mon_den_ky_nay:
            ma = mon.get("code") or mon["name"]
            # Học lại không tạo thêm một mã môn trong tổng tín chỉ đăng ký.
            if ma not in dang_ky or mon["credits"] > dang_ky[ma]["credits"]:
                dang_ky[ma] = mon

        # Dùng cùng quy tắc lấy lần điểm tốt nhất/môn với GPA tích luỹ của UI.
        tc_dang_ky = sum(mon["credits"] for mon in dang_ky.values())

        mon_tich_luy = rules.mon_tinh_tich_luy(mon_den_ky_nay)
        tk_tich_luy = rules.tom_tat(mon_tich_luy)
        tctl = sum(mon["credits"] for mon in mon_tich_luy
                   if rules.diem_mon(mon) >= gan_nhan.DIEM_DAT)
        no_tc = tc_dang_ky - tctl
        dtb_hk = rules.tom_tat(mon_trong_ky)["gpa4"]
        dtb_tl = tk_tich_luy["gpa4"]
        ly_do_canh_bao = gan_nhan.ly_do_canh_bao(
            dtb_hk, dtb_tl, tctl, no_tc, ky_dau=hoc_ky == 1)
        canh_bao = int(bool(ly_do_canh_bao))
        canh_bao_lien_tiep = (
            canh_bao_lien_tiep + 1 if canh_bao else 0
        )
        lich_su.append({
            "hoc_ky": hoc_ky,
            "tc_dat_hk": sum(
                mon["credits"] for mon in mon_trong_ky
                if rules.diem_mon(mon) >= gan_nhan.DIEM_DAT
            ),
            "dtb_hk": dtb_hk,
            "tctl": tctl,
            "no_tc": no_tc,
            "dtb_tl": dtb_tl,
            "trinh_do": gan_nhan.trinh_do_nam(tctl),
            "canh_bao": canh_bao,
            "so_lan_canh_bao_lien_tiep": canh_bao_lien_tiep,
        })
        hoc_ky_truoc = hoc_ky

    gan_nhat = lich_su[-1]
    co_hoc_ky_truoc = (
        len(lich_su) > 1
        and lich_su[-2]["hoc_ky"] == gan_nhat["hoc_ky"] - 1
    )
    dtb_hk_thay_doi = float("nan")
    if co_hoc_ky_truoc:
        dtb_hk_thay_doi = gan_nhat["dtb_hk"] - lich_su[-2]["dtb_hk"]

    # Các trường không có trong SQL phải theo đúng quy ước thiếu của tập train.
    dac_trung = {
        **gan_nhat,
        "drl": float("nan"),
        "ky_su": float("nan"),
        "muc_vang": float("nan"),
        "dtb_hk_thay_doi": dtb_hk_thay_doi,
        "drl_thieu": 1.0,
        "muc_vang_thieu": 1.0,
        "dtb_hk_thay_doi_thieu": float(not co_hoc_ky_truoc),
        "hoc_phi_dung_han": 0.0,
        "hoc_phi_tre_han": 0.0,
        "hoc_phi_chua_du": 0.0,
        "hoc_phi_mien": 0.0,
        "hoc_phi_khong_tra_loi": 1.0,
    }
    return dac_trung, f"{nam}–{nam + 1} · Học kỳ {ky}"


def du_doan_canh_bao(courses: list[dict], khoa_from: int | str,
                      so_ky: int) -> dict | None:
    """Tính xác suất và lý do SHAP trực tiếp, không lưu dự đoán."""
    dac_trung, hoc_ky = dac_trung_canh_bao(courses, khoa_from, so_ky)
    if dac_trung is None:
        return None

    import pandas as pd
    from ml import giai_thich

    mo_hinh, cot_huan_luyen = giai_thich.mo_hinh_tai("canh_bao")
    cot_thieu = set(cot_huan_luyen) - dac_trung.keys()
    if cot_thieu:
        raise ValueError(
            f"Chưa ánh xạ đủ đặc trưng cho mô hình: {sorted(cot_thieu)}"
        )
    X = pd.DataFrame(
        [{cot: dac_trung[cot] for cot in cot_huan_luyen}],
        columns=cot_huan_luyen,
    )
    ty_le = round(float(mo_hinh.predict_proba(X)[0, 1]) * 100, 1)
    return {
        "muc_nguy_co": rules.risk_label(ty_le),
        "ty_le": ty_le,
        "ly_do": giai_thich.ly_do(mo_hinh, X)[0],
        "hoc_ky": hoc_ky,
    }


# --- Thêm / cập nhật môn học ----------------------------------------------
# Bộ dòng mặc định khi mở form thêm môn mới: đủ 100% trọng số, chưa có điểm.
def form_rows_moi() -> list[dict]:
    return [
        {"loai": "Chuyên cần", "trong_so": 10, "diem": None},
        {"loai": "Kiểm tra giữa kỳ", "trong_so": 30, "diem": None},
        {"loai": "Thi cuối kỳ", "trong_so": 60, "diem": None},
    ]


# --- Cảnh báo & Mục tiêu ---------------------------------------------------
# Ngưỡng Giỏi/Khá lấy từ khung xếp loại học lực (rules._XEP_LOAI, SPEC §9.3)
# để chỉ có một chỗ giữ con số; so với GPA tích luỹ thang 4.
GOALS = {
    "Đạt loại Giỏi": {
        "pct": 24, "hint": f'GPA ≥ {rules.nguong_xep_loai("Giỏi"):.1f}',
        "note": "Cần điểm trung bình từ 8.5 trở lên ở 3 môn còn lại — khá khó "
                "với mức hiện tại.",
    },
    "Đạt loại Khá": {
        "pct": 61, "hint": f'GPA ≥ {rules.nguong_xep_loai("Khá"):.1f}',
        "note": "Khả thi nếu nâng điểm Trí tuệ nhân tạo lên ≥ 6.5 và giữ các "
                "môn còn lại.",
    },
    "Qua môn (không nợ)": {
        "pct": 88, "hint": "Không môn < 4.0",
        "note": "Chỉ cần đạt ≥ 5.0 điểm thi cuối kỳ môn Cơ sở dữ liệu phân "
                "tán.",
    },
}

FOOTER = ("Mockup Streamlit · Đồ án chuyên ngành Kỹ thuật phần mềm — Hệ thống "
          "cảnh báo sớm nguy cơ học tập của sinh viên")
