# Hệ thống Cảnh báo Sớm Nguy cơ Học tập

Đồ án tốt nghiệp — Ngành Kỹ thuật phần mềm, Trường Đại học Đà Lạt.

## Giới thiệu

Hệ thống hỗ trợ sinh viên tự theo dõi tình hình học tập và cảnh báo sớm nguy
cơ trượt môn, bị cảnh báo học vụ hoặc thôi học — dựa trên mô hình học máy
được huấn luyện từ dữ liệu học tập (điểm các học kỳ, chuyên cần, tín chỉ,
điểm rèn luyện...). Ngoài việc cảnh báo, hệ thống còn giải thích lý do dẫn
đến nguy cơ và gợi ý hướng cải thiện cụ thể cho từng sinh viên.

## Thông tin đồ án

- **Đề tài:** Xây dựng hệ thống cảnh báo sớm nguy cơ học tập của sinh viên
  bằng học máy
- **GVHD:** Thái Duy Quý
- **Nhóm thực hiện:**
  - Nguyễn Đình Thạch — 2314506 — CTK47B
  - Phan Thành Huy — 2312634 — CTK47B

## Công nghệ sử dụng

- **Ngôn ngữ:** Python
- **Giao diện:** Streamlit
- **Học máy:** Scikit-learn, XGBoost/LightGBM, SHAP
- **Backend:** FastAPI/Flask, APScheduler (tác vụ định kỳ)
- **Cơ sở dữ liệu:** SQL Server

## Trạng thái hiện tại

🚧 Bốn màn hình đã chạy thật trên cơ sở dữ liệu: Đăng nhập/Đăng ký,
Dashboard, Thêm/cập nhật môn học, Cảnh báo & Mục tiêu.

**Đã xong:** đăng ký và đăng nhập (mật khẩu băm bcrypt), nhập/sửa/xoá môn học
và điểm thành phần, tính GPA hai thang điểm, biểu đồ xu hướng, quy tắc đếm
lần học. Dữ liệu lưu trong SQL Server, mỗi tài khoản chỉ thấy dữ liệu của
mình.

**Chưa xong:** mô hình học máy. Mức nguy cơ, lý do cảnh báo, gợi ý cải thiện
và % khả năng đạt mục tiêu vẫn là số liệu cố định trong `ui/data.py` — chỗ
lưu trong cơ sở dữ liệu đã dựng sẵn nhưng chưa có gì ghi vào. Tác vụ định kỳ
và gửi email cũng chưa làm.

Quy tắc nghiệp vụ được mô tả trong [docs/SPEC.md](docs/SPEC.md).

## Cài đặt và chạy

Yêu cầu: **Python 3.9 trở lên** (nhóm đang dùng 3.14).

Ngoài ra cần **SQL Server** (nhóm dùng bản 2022 Developer, miễn phí) và
**ODBC Driver 17 for SQL Server**.

```bash
# 1. Tải mã nguồn
git clone https://github.com/nguyendinhthach/HeThongCanhBaoHocTap.git
cd HeThongCanhBaoHocTap

# 2. (Khuyến nghị) Tạo môi trường ảo riêng cho dự án
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Cài thư viện
python -m pip install -r requirements.txt

# 4. Chạy ứng dụng
python -m streamlit run app.py
```

### Dựng cơ sở dữ liệu

Chạy hai tệp SQL theo đúng thứ tự — bằng SSMS (mở tệp rồi nhấn F5) hoặc bằng
dòng lệnh:

```bash
sqlcmd -S localhost -E -i db/hethongcanhbao.sql   # tạo database và các bảng
sqlcmd -S localhost -E -i db/du_lieu_mau.sql      # nạp tài khoản demo + 11 môn
```

Tài khoản demo: **demo@dlu.edu.vn** / **demo1234**. Hoặc bấm "Đăng ký" trên
giao diện để tạo tài khoản trắng.

Mặc định kết nối tới SQL Server trên chính máy đang chạy, dùng xác thực
Windows nên không cần mật khẩu. Muốn trỏ sang máy khác thì đặt biến môi
trường `HT_DB_SERVER`, hoặc `HT_DB_URL` nếu cần chuỗi kết nối riêng.

Trình duyệt sẽ tự mở tại <http://localhost:8501>. Nhấn `Ctrl+C` trong
terminal để dừng.

> **Lưu ý:** dùng `python -m streamlit run app.py`, không phải
> `streamlit run app.py`. Nếu thư mục `Scripts` của Python không nằm trong
> biến môi trường PATH, gõ trực tiếp `streamlit` sẽ báo lỗi *command not
> found*.

Muốn đổi cổng: `python -m streamlit run app.py --server.port 8600`

## Cấu trúc thư mục

```
app.py                điểm vào ứng dụng, sidebar và điều hướng
requirements.txt      thư viện cần cài
.streamlit/           cấu hình giao diện Streamlit
docs/SPEC.md          đặc tả quy tắc nghiệp vụ
docs/mockups/         bản thiết kế gốc (không đưa lên git)
db/
  hethongcanhbao.sql  tạo database và 6 bảng
  du_lieu_mau.sql     tài khoản demo và 11 môn mẫu
  truy_van_kiem_tra.sql  truy vấn xem/đối chiếu dữ liệu bằng tay
  ket_noi.py          engine SQLAlchemy dùng chung
  repo.py             toàn bộ câu lệnh SQL của ứng dụng
  bao_mat.py          băm và kiểm tra mật khẩu
ui/
  tokens.py           màu và kích thước lấy từ mockup
  styles.py           CSS toàn cục cho widget Streamlit
  blocks.py           khối HTML dùng chung (thẻ chỉ số, bảng, nhãn)
  rules.py            quy tắc tính điểm, GPA, quy đổi thang
  phien.py            trạng thái đăng nhập, nạp dữ liệu từ CSDL
  data.py             cấu hình hiển thị và số liệu còn tạm cố định
  screens/            bốn màn hình của ứng dụng
```

