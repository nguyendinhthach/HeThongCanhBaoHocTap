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

MUC_TIEU = ("canh_bao", "thoi_hoc", "truot_mon")


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
    raise NotImplementedError("Bước 2: chưa viết")


def nguy_co_thoi_hoc(nguy_co_canh_bao, so_lan_canh_bao_lien_tiep):
    """Nguy cơ buộc thôi học kỳ k+1 suy từ nguy cơ cảnh báo kỳ k+1.

    Theo Điều 18.2a, chỉ sinh viên đã bị cảnh báo 2 kỳ liên tiếp (k−1, k) mới
    có thể bị buộc thôi học ở kỳ k+1, và bị khi bị cảnh báo tiếp; các sinh
    viên khác nguy cơ bằng 0.

    Tham số là hai pd.Series cùng chỉ số; trả về pd.Series xác suất.
    """
    raise NotImplementedError("Bước 2: chưa viết")
