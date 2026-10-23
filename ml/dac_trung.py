"""
Tạo đặc trưng (X), nhãn (y) và nhóm (mã sinh viên) cho 3 mục tiêu dự đoán.

Đây là "hợp đồng" giữa phần dữ liệu và phần mô hình: các file thuật toán
(Decision Tree, SVM, XGBoost, Random Forest, LightGBM) và phần đánh giá chỉ
gọi tao_du_lieu() rồi dùng X, y, nhom; không tự đọc form hay tính đặc trưng.
Bên trong file này thêm / bớt đặc trưng thoải mái, miễn giữ đúng hợp đồng.

    X, y, nhom = tao_du_lieu("canh_bao")

Ba mục tiêu (MUC_TIEU):

- "canh_bao":  1 dòng = 1 sinh viên ở cuối học kỳ k.
               y = 1 nếu bị cảnh báo học tập ở học kỳ k+1 (Điều 18.1 QĐ 600).
               Học kỳ cuối của mỗi sinh viên không có k+1 nên bị bỏ.
- "thoi_hoc":  cùng dòng với "canh_bao"; y = 1 nếu bị buộc thôi học ở học
               kỳ k+1 (Điều 18.2a). Rất ít ca dương, dùng để so sánh; cách
               chính là suy từ nguy cơ cảnh báo (xem nguy_co_thoi_hoc).
- "truot_mon": 1 dòng = 1 môn của học kỳ gần nhất, dự đoán sau giữa kỳ.
               y = 1 nếu "Không đạt (điểm F)" hoặc "Bị cấm thi"; bỏ dòng
               "Không muốn trả lời". Chỉ dùng lịch sử đến học kỳ k−1, không
               dùng số liệu tổng kết học kỳ k (đã chứa kết quả môn đang đoán).

Quy ước chung:
- Loại sinh viên không hợp lệ (doc_form: hop_le = False).
- Ô trống giữ là NaN, kèm cột "<tên>_thieu" (0/1); mô hình nào không nhận
  NaN (SVM, Random Forest) thì tự điền trong pipeline của mình.
- Chưa chuẩn hoá: SVM tự chuẩn hoá trong pipeline để không rò dữ liệu test.
- Không dùng ngành (dữ liệu mô phỏng chọn ngành ngẫu nhiên, không mang tín
  hiệu) và tạm không dùng học kỳ hè (có thể chưa biết lúc dự đoán).
- Chia train / test theo `nhom`, không chia ngẫu nhiên theo dòng: một sinh
  viên chỉ nằm trọn ở train hoặc ở test.
"""

import os
from functools import lru_cache

import pandas as pd

import doc_form as form
from gan_nhan import SO_LAN_CANH_BAO_THOI_HOC, gan_nhan_hoc_ky, gan_nhan_mon


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_DAN_MAC_DINH = os.path.join(THU_MUC_GOC, "data", "mo_phong.xlsx")

MUC_TIEU = ("canh_bao", "thoi_hoc", "truot_mon")

# Mức vắng theo thứ bậc; "Không nhớ / không muốn trả lời" coi là thiếu
THU_BAC_VANG = {muc: i for i, muc in enumerate(form.MUC_VANG[:4])}
HE_KY_SU = "Kỹ sư (4,5 năm)"
# Tên cột one-hot, cùng thứ tự với form.HOC_PHI
TEN_COT_HOC_PHI = ["dung_han", "tre_han", "chua_du", "mien", "khong_tra_loi"]

# Đặc trưng số lấy thẳng từ bảng học kỳ ở học kỳ k (đã có sau khi kỳ k kết thúc)
COT_HOC_KY_K = ["hoc_ky", "tc_dat_hk", "dtb_hk", "tctl", "no_tc", "dtb_tl", "trinh_do", "drl",
                "canh_bao", "so_lan_canh_bao_lien_tiep"]
# Cột có thể trống -> kèm cột "<tên>_thieu". Danh sách cố định để dữ liệu thật
# và mô phỏng luôn ra cùng một bộ cột, kể cả khi một file không có ô trống nào.
COT_CO_THE_THIEU = ["drl", "muc_vang", "dtb_hk_thay_doi"]

# --- Trượt môn ---------------------------------------------------------------
# Vắng lý thuyết theo thứ bậc (0: ít, 1: khá nhiều chưa quá 20%, 2: trên 20%)
THU_BAC_VANG_LT = {muc: i for i, muc in enumerate(form.VANG_LY_THUYET[:3])}
# Lịch sử đến học kỳ k−1 (lấy từ đặc trưng học kỳ của kỳ trước), đặt tiền tố "truoc_"
COT_LICH_SU = ["dtb_hk", "dtb_tl", "tctl", "no_tc", "trinh_do", "drl", "muc_vang",
               "canh_bao", "so_lan_canh_bao_lien_tiep"]
COT_MON_CO_THE_THIEU = ["diem_gk", "ti_trong_gk", "vang_lt", "vang_th", "truoc_drl", "truoc_muc_vang"]


def doc_du_lieu(duong_dan=None):
    """(bảng học kỳ, bảng môn) đã gán nhãn, chỉ gồm sinh viên hợp lệ.

    Bảng học kỳ có thêm cột he_dao_tao, sắp theo (ma_sv, hoc_ky). Mỗi file chỉ
    đọc một lần (đọc xlsx chậm); file đổi trên đĩa thì đọc lại.
    """
    duong_dan = os.path.abspath(duong_dan or DUONG_DAN_MAC_DINH)
    bang, mon = _doc_du_lieu(duong_dan, os.path.getmtime(duong_dan))
    return bang.copy(), mon.copy()


@lru_cache(maxsize=4)
def _doc_du_lieu(duong_dan, _thoi_diem_sua):
    sinh_vien, bang_hoc_ky, bang_mon = form.doc_form(duong_dan)
    hop_le = sinh_vien.index[sinh_vien["hop_le"]]
    bang = gan_nhan_hoc_ky(bang_hoc_ky[bang_hoc_ky["ma_sv"].isin(hop_le)])
    # gan_nhan_hoc_ky đã sắp theo (ma_sv, hoc_ky); merge "inner" giữ thứ tự đó
    bang = bang.merge(sinh_vien[["he_dao_tao"]], left_on="ma_sv", right_index=True)
    mon = gan_nhan_mon(bang_mon[bang_mon["ma_sv"].isin(hop_le)]).reset_index(drop=True)
    return bang, mon


def doc_bang_hoc_ky(duong_dan=None):
    """Bảng học kỳ đã gán nhãn của các sinh viên hợp lệ, kèm thông tin chung."""
    return doc_du_lieu(duong_dan)[0]


def dac_trung_hoc_ky(bang):
    """Đặc trưng của sinh viên ở cuối học kỳ k, mỗi dòng của `bang` một dòng.

    Chỉ dùng số liệu đến học kỳ k (dòng hiện tại và các dòng trước của cùng
    sinh viên). `bang` phải sắp theo (ma_sv, hoc_ky) như doc_bang_hoc_ky trả về.
    """
    X = bang[COT_HOC_KY_K].astype(float)
    X["ky_su"] = (bang["he_dao_tao"] == HE_KY_SU).astype(float)
    X["muc_vang"] = bang["muc_vang"].map(THU_BAC_VANG)

    # ĐTB học kỳ tăng / giảm so với kỳ trước; kỳ đầu không có kỳ trước nên trống
    X["dtb_hk_thay_doi"] = bang.groupby("ma_sv")["dtb_hk"].diff()

    # One-hot học phí theo danh sách lựa chọn của form (cột cố định)
    for lua_chon, ten in zip(form.HOC_PHI, TEN_COT_HOC_PHI):
        X[f"hoc_phi_{ten}"] = (bang["hoc_phi"] == lua_chon).astype(float)

    for cot in COT_CO_THE_THIEU:
        X[f"{cot}_thieu"] = X[cot].isna().astype(float)
    return X


def _canh_bao_ky_sau(duong_dan, cot_nhan):
    """Dữ liệu cho mục tiêu dự đoán ở học kỳ k+1 ("canh_bao", "thoi_hoc").

    Mỗi dòng = sinh viên ở cuối học kỳ k, nhãn = `cot_nhan` của học kỳ k+1.
    Học kỳ cuối của mỗi sinh viên không có k+1 nên bị bỏ (kể cả sinh viên đã
    tốt nghiệp / bị buộc thôi học), như các dòng mà nhãn kỳ sau bị trống.
    """
    bang = doc_bang_hoc_ky(duong_dan)
    X = dac_trung_hoc_ky(bang)

    ky_sau = bang.groupby("ma_sv")
    co_ky_sau = ky_sau["hoc_ky"].shift(-1) == bang["hoc_ky"] + 1
    nhan = ky_sau[cot_nhan].shift(-1)
    giu = co_ky_sau & nhan.notna()

    X = X[giu].reset_index(drop=True)
    y = nhan[giu].astype(int).reset_index(drop=True).rename(cot_nhan)
    nhom = bang.loc[giu, "ma_sv"].reset_index(drop=True)
    return X, y, nhom


def _truot_mon(duong_dan):
    """Dữ liệu cho mục tiêu trượt môn, dự đoán sau giữa kỳ.

    Mỗi dòng = một môn của học kỳ k (học kỳ gần nhất sinh viên điền chi tiết).
    Đặc trưng = thông tin của môn có được trước cuối kỳ + lịch sử đến học kỳ
    k−1. Không dùng số liệu tổng kết học kỳ k (ĐTB học kỳ, TC đạt học kỳ...)
    vì chúng đã chứa kết quả của chính môn đang dự đoán.
    """
    bang, mon = doc_du_lieu(duong_dan)
    mon = mon[mon["truot_mon"].notna()].reset_index(drop=True)   # bỏ "Không muốn trả lời"

    X = pd.DataFrame({
        "hoc_ky": mon["hoc_ky"].astype(float),
        "so_tc": mon["so_tc"],
        "diem_gk": mon["diem_gk"],
        "ti_trong_gk": mon["ti_trong_gk"],
        "vang_lt": mon["vang_lt"].map(THU_BAC_VANG_LT),
        # "Không nhớ" số buổi vắng thì môn vẫn có thực hành
        "co_thuc_hanh": (mon["vang_th"] != form.VANG_THUC_HANH[0]).astype(float),
        "vang_th": mon["vang_th"].map({form.VANG_THUC_HANH[0]: 0, form.VANG_THUC_HANH[1]: 0,
                                       form.VANG_THUC_HANH[2]: 1}),
    })

    # Lịch sử: đặc trưng học kỳ k−1, ghép vào môn của học kỳ k
    lich_su = dac_trung_hoc_ky(bang)[COT_LICH_SU].add_prefix("truoc_")
    lich_su["ma_sv"] = bang["ma_sv"]
    lich_su["hoc_ky"] = bang["hoc_ky"] + 1
    ghep = mon[["ma_sv", "hoc_ky"]].merge(lich_su, on=["ma_sv", "hoc_ky"], how="left")
    X = X.join(ghep.drop(columns=["ma_sv", "hoc_ky"]))
    X["ky_su"] = mon["ma_sv"].map(bang.groupby("ma_sv")["he_dao_tao"].first() == HE_KY_SU).astype(float)

    # Học kỳ 1 không có lịch sử: một cột đánh dấu chung cho cả nhóm "truoc_"
    X["lich_su_thieu"] = ghep["truoc_dtb_hk"].isna().astype(float).to_numpy()
    for cot in COT_MON_CO_THE_THIEU:
        X[f"{cot}_thieu"] = X[cot].isna().astype(float)

    y = mon["truot_mon"].astype(int).rename("truot_mon")
    return X, y, mon["ma_sv"]


def tao_du_lieu(muc_tieu, duong_dan=None):
    """Trả về (X, y, nhom) cho một mục tiêu.

    Tham số:
        muc_tieu:  một trong MUC_TIEU.
        duong_dan: file xlsx định dạng Google Form (thật hoặc mô phỏng);
                   bỏ trống thì dùng data/mo_phong.xlsx.

    Trả về:
        X:    pd.DataFrame, mỗi dòng một mẫu, mỗi cột một đặc trưng dạng số
              (đã mã hoá, có thể chứa NaN).
        y:    pd.Series 0/1, cùng chỉ số (index) với X.
        nhom: pd.Series mã sinh viên ("SV1", ...), cùng chỉ số với X.
    """
    if muc_tieu not in MUC_TIEU:
        raise ValueError(f"muc_tieu phải là một trong {MUC_TIEU}, nhận {muc_tieu!r}")
    if muc_tieu == "canh_bao":
        return _canh_bao_ky_sau(duong_dan, "canh_bao")
    if muc_tieu == "thoi_hoc":
        return _canh_bao_ky_sau(duong_dan, "buoc_thoi_hoc")
    return _truot_mon(duong_dan)


def nguy_co_thoi_hoc(nguy_co_canh_bao, so_lan_canh_bao_lien_tiep):
    """Nguy cơ buộc thôi học kỳ k+1 suy từ nguy cơ cảnh báo kỳ k+1.

    Theo Điều 18.2a, chỉ sinh viên đã bị cảnh báo 2 kỳ liên tiếp (k−1, k) mới
    có thể bị buộc thôi học ở kỳ k+1, và bị khi bị cảnh báo tiếp; các sinh
    viên khác nguy cơ bằng 0.

    Tham số là hai pd.Series cùng chỉ số (cột so_lan_canh_bao_lien_tiep của X
    "canh_bao"); trả về pd.Series xác suất.
    """
    sap_thoi_hoc = so_lan_canh_bao_lien_tiep >= SO_LAN_CANH_BAO_THOI_HOC - 1
    return nguy_co_canh_bao.where(sap_thoi_hoc, 0.0).rename("nguy_co_thoi_hoc")
