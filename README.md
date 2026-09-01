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
- **Cơ sở dữ liệu:** PostgreSQL/SQL Server

## Trạng thái hiện tại

🚧 Đang ở giai đoạn dựng giao diện. Đã có bản chạy được với 4 màn hình:
Đăng nhập/Đăng ký, Dashboard, Thêm/cập nhật môn học, Cảnh báo & Mục tiêu.

Toàn bộ số liệu hiện là **dữ liệu tĩnh** trong `ui/data.py` — chưa có phần
tính toán nghiệp vụ, chưa nối cơ sở dữ liệu và chưa gắn mô hình học máy.
Phần điều hướng, chuyển tab, chọn thang điểm và chọn mục tiêu thì hoạt động
thật.

Quy tắc nghiệp vụ dự kiến được mô tả trong [docs/SPEC.md](docs/SPEC.md).

## Cài đặt và chạy

Yêu cầu: **Python 3.9 trở lên** (nhóm đang dùng 3.14).

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
ui/
  tokens.py           màu và kích thước lấy từ mockup
  styles.py           CSS toàn cục cho widget Streamlit
  blocks.py           khối HTML dùng chung (thẻ chỉ số, bảng, nhãn)
  data.py             dữ liệu hiển thị tĩnh
  screens/            bốn màn hình của ứng dụng
```

