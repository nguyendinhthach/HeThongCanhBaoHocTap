# Đặc tả kỹ thuật — Hệ thống cảnh báo sớm nguy cơ học tập của sinh viên

Đồ án tốt nghiệp KTPM — Đề tài #19 · GVHD: Thái Duy Quý
Nhóm: Nguyễn Đình Thạch, Phan Thành Huy

> Tài liệu này mô tả quy tắc nghiệp vụ và kiến trúc kỹ thuật để triển khai
> thật bằng Streamlit. Ảnh mockup đính kèm (nếu có) chỉ để tham khảo bố cục,
> không cần bám sát pixel — vì mockup dựng bằng HTML còn app thật dùng
> component chuẩn của Streamlit.

---

## 1. Phạm vi & đối tượng sử dụng

- Đối tượng dùng **duy nhất là sinh viên** — không có giao diện/vai trò dành
  cho giảng viên hay cố vấn học tập.
- Dữ liệu **huấn luyện mô hình ML**: bộ dữ liệu tổng hợp (synthetic) do nhóm
  tự sinh, dựa trên quy luật giả định hợp lý (không phải dữ liệu thật từ
  trường).
- Dữ liệu **vận hành thực tế**: do chính sinh viên tự nhập vào hệ thống.

## 2. Xác thực & hồ sơ người dùng

- Đăng ký/đăng nhập bằng **email + mật khẩu**.
- Trường thông tin cá nhân: **HoTen** — một thuộc tính duy nhất (không tách
  Họ/Tên riêng).
- Khi đăng ký, sinh viên nhập niên khoá (VD: 2023–2027) và chọn:
  - Số năm học dự kiến: 4 / 4.5 / 5 năm
  - Số học kỳ mỗi năm: 2 hoặc 3
  - Hệ thống tự sinh danh sách năm học/học kỳ tương ứng, nhưng **không giới
    hạn cứng** — sinh viên có thể thêm học kỳ mới thủ công sau này nếu học
    kéo dài hơn dự kiến ban đầu.

## 3. Cấu trúc dữ liệu môn học

### 3.1 Bảng môn học (mỗi dòng = một lần học của một môn, trong một học kỳ)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | UUID/PK | |
| user_id | FK | |
| nam_hoc | string | VD "2025-2026" |
| hoc_ky | int | 1, 2, (3) |
| ten_mon | string | |
| so_tin_chi | int | |
| lan_hoc | int | **Tự động đếm**, không cho sửa tay — xem mục 3.3 |
| loai_lan_hoc | enum (`hoc_moi`, `hoc_lai`, `hoc_cai_thien`) | Sinh viên chọn/xác nhận — xem mục 3.3 |

### 3.2 Bảng điểm thành phần (nhiều dòng cho một môn học — quan hệ 1-nhiều)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| mon_hoc_id | FK | |
| loai_thanh_phan | enum | Chuyên cần / Bài tập / Thực hành / Kiểm tra giữa kỳ / Bài tập nhóm / Thi cuối kỳ / Khác — chọn từ danh sách cố định, **không cho gõ tự do** (đảm bảo dữ liệu nhất quán giữa các sinh viên để dùng làm đặc trưng ML) |
| trong_so_phan_tram | float | Tổng các dòng của cùng 1 môn phải = 100% mới được lưu |
| diem | float, **nullable** | **Để trống nếu chưa nhập** — KHÔNG mặc định 0. Xem mục 3.4 |

### 3.3 Quy tắc "Lần học" — tự động, không cho sinh viên chọn tay

Khi sinh viên nhập **Tên môn học** trùng với môn đã tồn tại ở bất kỳ học kỳ
nào trước đó (không chỉ học kỳ đang chọn):

1. Hệ thống hiển thị cảnh báo: *"Môn này đã học ở [Học kỳ X, Năm Y] — đây có
   phải là học lại/học cải thiện?"*
2. Trường **`lan_hoc`** tự động = (số lần đã tồn tại của môn đó) + 1. Hiển
   thị dạng chỉ đọc, sinh viên không chỉnh tay được.
3. Trường **`loai_lan_hoc`** (Học lại / Học cải thiện) **gợi ý mặc định**
   dựa trên điểm tổng kết của lần học gần nhất cùng môn:
   - Nếu lần trước đã đủ điểm và **dưới ngưỡng đậu** (< 4.0 theo thang 10) →
     gợi ý mặc định "Học lại"
   - Nếu lần trước đã đủ điểm và **đạt ngưỡng đậu** → gợi ý mặc định "Học
     cải thiện"
   - Nếu lần trước **chưa đủ điểm để xác định** (còn thành phần trống) → để
     trống, bắt buộc sinh viên tự chọn
   - Sinh viên luôn có thể sửa lại gợi ý này nếu không đúng thực tế.
4. Bản ghi của (các) lần học trước **không bị sửa hay xoá** — chỉ tạo thêm
   một dòng mới, gắn với học kỳ hiện tại (theo giá trị "Kỳ học đang xem" ở
   sidebar tại thời điểm thêm).
5. Nếu tên môn không trùng với môn nào trước đó → `lan_hoc = 1`,
   `loai_lan_hoc = hoc_moi`.

### 3.4 Quy tắc tính điểm khi thành phần chưa nhập đủ

- Ô điểm của một thành phần **để trống nếu chưa nhập**, không tự động điền 0.
- **Điểm tạm tính của một môn** (một lần học cụ thể) = tổng có trọng số CHỈ
  trên các thành phần đã có điểm, kèm hiển thị rõ phần trăm trọng số đã tính
  được (VD: "Điểm tạm tính (dựa trên 40% trọng số đã có điểm): 6.8").
- Một môn chỉ được tính là **"hoàn tất"** (có điểm tổng kết chính thức) khi
  đã nhập đủ điểm cho 100% trọng số thành phần. Trước đó luôn hiển thị là
  "tạm tính".
- Chỉ số **"Môn nợ (< 4.0)" / cảnh báo nguy cơ trượt theo môn** chỉ tính trên
  các môn đã hoàn tất — không tính môn đang tạm tính (tránh báo động giả cho
  môn chưa thi xong).

> **Ngưỡng rớt môn thống nhất toàn hệ thống là 4.0** (thang 10). Dùng chung
> cho: gợi ý Học lại/Học cải thiện (muc 3.3), chỉ số "Môn nợ" ở Dashboard,
> cột cảnh báo nguy cơ trượt theo môn, và mục tiêu "Qua môn" (muc 7).

### 3.5 Quy tắc khi một môn có nhiều lần học — KHÔNG ghi đè, KHÔNG hồi tố

- Mỗi lần học là **một bản ghi độc lập**, gắn với đúng học kỳ diễn ra lần
  học đó. Bản ghi cũ **không bị sửa, không bị ghi đè**.
- Ví dụ: *Cơ sở dữ liệu phân tán* học kỳ 1 được 4.2 (Học lần 1); học cải
  thiện ở học kỳ 2 được 6.8 (Lần 2). Cả hai dòng cùng tồn tại — xem học kỳ 1
  thấy 4.2, xem học kỳ 2 thấy 6.8.
- **GPA từng học kỳ dùng đúng điểm của lần học trong kỳ đó** — không hồi tố.
  Nhờ vậy biểu đồ xu hướng phản ánh đúng lịch sử thật của sinh viên.

> **Còn để ngỏ:** GPA *tích luỹ toàn khoá* nên lấy điểm lần học nào (cao
> nhất / mới nhất) — cần tra quy chế của trường rồi chốt. Chưa ảnh hưởng
> giai đoạn dựng giao diện vì màn hình hiện chỉ hiển thị GPA theo học kỳ.

## 4. Đặc trưng (feature) đưa vào mô hình ML

- Điểm tổng kết mỗi môn: dùng **điểm cao nhất** theo quy tắc mục 3.5 (không
  dùng điểm lần học gần nhất).
- **Điểm chuyên cần**: tách riêng thành một đặc trưng độc lập (không gộp
  chung vào điểm tổng kết môn), vì đây là tín hiệu dự đoán nguy cơ mạnh và
  cần giữ ý nghĩa riêng.
- **Cờ "đã từng học lại/học cải thiện"** (có/không) cho mỗi môn: giữ lại làm
  đặc trưng riêng dù điểm cuối cùng đã cải thiện — vì bản thân việc từng
  trượt là tín hiệu nguy cơ.
- Xu hướng GPA qua các học kỳ liên tiếp (dùng cho cả cảnh báo tổng thể lẫn
  hiển thị biểu đồ).

## 5. Đánh giá mô hình

- Ưu tiên **Recall và F1-score**, không chỉ Accuracy — vì bỏ sót sinh viên
  có nguy cơ thật (false negative) nghiêm trọng hơn báo động nhầm.
- Có thành phần giải thích kết quả dự đoán (feature importance / SHAP) để
  sinh ra "Lý do chính" và "Gợi ý cải thiện" hiển thị cho sinh viên.

## 6. Phạm vi tính toán của từng loại cảnh báo (quan trọng — dễ nhầm)

| Loại cảnh báo | Phạm vi dữ liệu | Vị trí hiển thị |
|---|---|---|
| Nguy cơ trượt **theo từng môn** | Chỉ trong học kỳ đang chọn ở sidebar | Cột trong bảng "Danh sách môn học", trang Dashboard |
| Mức nguy cơ **tổng thể** (bị cảnh báo học vụ/thôi học) + Lý do chính + Gợi ý cải thiện | **Toàn bộ lịch sử** các học kỳ đã nhập, không phụ thuộc lựa chọn sidebar | Trang "Cảnh báo & Mục tiêu" |
| Biểu đồ "Xu hướng điểm trung bình học kỳ" | **Toàn bộ** các học kỳ đã có dữ liệu (điểm hiện tại theo sidebar được đánh dấu nổi bật trên biểu đồ) | Trang Dashboard |

Ở trang "Cảnh báo & Mục tiêu", sidebar **không hiển thị** khối "Kỳ học đang
xem" (vì trang này không phụ thuộc lựa chọn kỳ).

## 7. Mục tiêu học tập & gợi ý cải thiện

- Sinh viên chọn 1 mục tiêu: Đạt loại Giỏi (GPA ≥ 3.2) / Đạt loại Khá (GPA ≥
  2.5) / Qua môn (không nợ, môn < 4.0 theo thang 10 — điều chỉnh đúng theo
  thang điểm thật của trường khi triển khai).
- Hệ thống trả về % khả năng đạt mục tiêu đó dựa trên nhịp học hiện tại, và
  gợi ý định tính cần cải thiện gì (không bắt buộc phải tính chính xác tuyệt
  đối số điểm cần tăng ở bản đầu tiên — có thể làm ở mức định tính trước).

## 8. Cơ chế cảnh báo tự động (không phụ thuộc người dùng tự vào xem)

- Chạy tiến trình định kỳ (scheduled job) để tự động chạy lại dự đoán trên
  dữ liệu mới nhất mỗi sinh viên đã nhập.
- Khi phát hiện nguy cơ, **tự động gửi email** đến sinh viên — không chỉ
  hiển thị thụ động khi sinh viên tự truy cập web.

## 9. Chuyển đổi thang điểm hiển thị

- Toggle "Thang 10 / Thang 4" ở Dashboard: chỉ ảnh hưởng **cách hiển thị**
  (thẻ GPA, trục biểu đồ, cột điểm tổng kết trong bảng). Dữ liệu gốc luôn
  lưu theo **thang 10** — quy đổi sang thang 4 chỉ diễn ra ở tầng hiển thị.
- Bảng quy đổi (cài đặt tại `ui/grading.py::to_scale_4`):

| Thang 10 | ≥ 8.5 | ≥ 8.0 | ≥ 7.0 | ≥ 6.5 | ≥ 5.5 | ≥ 5.0 | ≥ 4.0 | < 4.0 |
|---|---|---|---|---|---|---|---|---|
| Thang 4 | 4.0 | 3.5 | 3.0 | 2.5 | 2.0 | 1.5 | 1.0 | 0.0 |

## 10. Công nghệ

- Ngôn ngữ: **Python** (toàn bộ, không dùng C#/JS).
- Giao diện: **Streamlit** — dùng component chuẩn (`st.form`, `st.selectbox`,
  `st.data_editor`, `st.metric`, `st.line_chart`/`st.plotly_chart`,
  `st.tabs`/sidebar để điều hướng). Biểu đồ xu hướng **bắt buộc dùng thư
  viện vẽ chuẩn** (không tự dựng bằng HTML/CSS) để đảm bảo có đủ trục X/Y,
  nhãn, chia độ đúng.
- Model: Scikit-learn / XGBoost / LightGBM, SHAP cho giải thích.
- Backend API: FastAPI hoặc Flask.
- Tác vụ định kỳ: APScheduler hoặc cron job.
- Gửi email: SMTP.
- Cơ sở dữ liệu: PostgreSQL hoặc SQL Server.

## 11. Các màn hình cần có (tối giản, không thêm ngoài danh sách)

1. **Đăng ký / Đăng nhập** — không nằm trong menu điều hướng chính; truy cập
   qua nút góc dưới sidebar khi chưa đăng nhập.
2. **Dashboard chính** — chọn năm học/học kỳ xem điểm; thẻ tổng quan (GPA,
   tín chỉ, môn dưới 5.0, mức nguy cơ tổng thể rút gọn); bảng danh sách môn
   học kèm cột nguy cơ trượt theo môn; biểu đồ xu hướng GPA toàn bộ lịch sử;
   toggle thang 10/4; nút "+ Thêm môn học".
3. **Thêm / cập nhật môn học** — mặc định thu gọn, chỉ hiện bảng "Môn học đã
   thêm trong học kỳ này" (sửa/xoá được) + nút "+ Thêm môn học" để xổ form.
   Form dùng đúng năm học/học kỳ theo sidebar, không nhập lại.
4. **Cảnh báo & Mục tiêu học tập** — mức nguy cơ tổng thể (toàn lịch sử) +
   lý do + gợi ý cải thiện; phần nhập mục tiêu học tập + % khả năng đạt.
