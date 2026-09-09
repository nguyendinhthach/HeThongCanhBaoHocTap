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
- Bộ sinh dữ liệu mô phỏng phải xuất **đúng cấu trúc bảng ở mục 3** — cùng tên
  trường, cùng đơn vị, cùng khoảng giá trị hợp lệ. Đề cương §2.1 coi tính nhất
  quán giữa dữ liệu huấn luyện và dữ liệu sinh viên nhập là yêu cầu bắt buộc;
  sinh ra một tệp CSV theo ý riêng rồi ép cho khớp sau là làm ngược thứ tự.

### 1.1 Nằm ngoài phạm vi (đề cương có nêu, nhóm quyết định cắt)

- **Tỷ lệ vắng học** (đề cương §1). Điểm _chuyên cần_ — một loại điểm thành
  phần có ở hầu hết môn — vốn do giảng viên chấm dựa trên số buổi vắng, nên
  tín hiệu chuyên cần vẫn giữ nguyên, chỉ khác cách thu thập. Bắt sinh viên
  nhập thêm số buổi vắng là nhập trùng thứ đã nằm trong bảng điểm.
- **Điểm rèn luyện** (đề cương §1): không thu thập ở phiên bản này.

> Hai mục trên **phải ghi rõ trong báo cáo** ở phần giới hạn đề tài, kèm lý do,
> để đối chiếu được với đề cương lúc bảo vệ.

## 2. Xác thực & hồ sơ người dùng

- Đăng ký/đăng nhập bằng **email + mật khẩu**. Mật khẩu **lưu dạng băm**
  (bcrypt hoặc argon2), không bao giờ lưu dạng thô.
- Trường thông tin cá nhân: **HoTen** — một thuộc tính duy nhất (không tách
  Họ/Tên riêng).
- Khi đăng ký, sinh viên nhập niên khoá (VD: 2023–2027) và chọn:
  - Số năm học dự kiến: 4 / 4.5 / 5 năm
  - Số học kỳ mỗi năm: 2 hoặc 3
  - Hệ thống tự sinh danh sách năm học/học kỳ tương ứng, nhưng **không giới
    hạn cứng** — sinh viên có thể thêm học kỳ mới thủ công sau này nếu học
    kéo dài hơn dự kiến ban đầu.

### 2.1 Bảng người dùng

| Trường        | Kiểu                  | Ghi chú                                                              |
| ------------- | --------------------- | -------------------------------------------------------------------- |
| id            | INT IDENTITY, PK      |                                                                      |
| email         | NVARCHAR(255), UNIQUE | Dùng để đăng nhập và để gửi email cảnh báo (mục 8)                   |
| mat_khau_hash | VARCHAR(100)          | Chuỗi bcrypt — chỉ chứa ASCII nên đây là chỗ duy nhất dùng `VARCHAR` |
| ho_ten        | NVARCHAR(100)         | Một thuộc tính duy nhất, không tách Họ/Tên                           |
| nien_khoa_tu  | INT                   | VD `2023`                                                            |
| nien_khoa_den | INT                   | VD `2027`                                                            |
| so_ky_moi_nam | INT                   | 2 hoặc 3                                                             |
| thang_diem | INT | 10 hoặc 4 — lựa chọn ở toggle Dashboard, lưu lại để không bị đặt lại mỗi lần tải trang |
| muc_tieu | VARCHAR(20) | `gioi` / `kha` / `qua_mon` (mục 7); NULL = chưa chọn |
| ngay_tao      | DATETIME2             |                                                                      |

## 3. Cấu trúc dữ liệu môn học

### 3.1 Bảng môn học (mỗi dòng = một lần học của một môn, trong một học kỳ)

| Trường       | Kiểu                                         | Ghi chú                                                                                                                   |
| ------------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| id           | INT IDENTITY, PK                             |                                                                                                                           |
| user_id      | INT, FK → `nguoi_dung.id`                    |                                                                                                                           |
| nam_bat_dau  | int                                          | Năm bắt đầu của năm học: `2025` nghĩa là năm học 2025–2026. **Không lưu chuỗi** — xem ghi chú bên dưới                    |
| hoc_ky       | int                                          | 1, 2, (3)                                                                                                                 |
| ma_mon       | string                                       | **Khoá định danh môn**, bắt buộc — dùng để đếm lần học (xem 3.3). Chuẩn hoá trước khi lưu: bỏ khoảng trắng thừa, viết hoa |
| ten_mon      | string                                       | Chỉ để hiển thị, **không dùng để so trùng**                                                                               |
| so_tin_chi   | int                                          |                                                                                                                           |
| lan_hoc      | int                                          | **Tự động đếm**, không cho sửa tay — xem mục 3.3                                                                          |
| loai_lan_hoc | enum (`hoc_moi`, `hoc_lai`, `hoc_cai_thien`) | Sinh viên chọn/xác nhận — xem mục 3.3                                                                                     |

> **Vì sao lưu `nam_bat_dau` dạng số thay vì chuỗi "2025–2026":** nhãn năm học
> dùng en dash (`–`) chứ không phải dấu trừ (`-`), hai ký tự này nhìn gần giống
> nhau nên rất dễ lưu lẫn lộn rồi truy vấn không ra. Lưu một số nguyên thì so
> sánh, sắp xếp và tìm kỳ liền trước đều chính xác; chuỗi hiển thị do giao
> diện ghép lại từ `nam_bat_dau` và `nam_bat_dau + 1`.

### 3.2 Bảng điểm thành phần (nhiều dòng cho một môn học — quan hệ 1-nhiều)

| Trường             | Kiểu                   | Ghi chú                                                                                                                                                                                                             |
| ------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                 | INT IDENTITY, PK       |                                                                                                                                                                                                                     |
| mon_hoc_id         | INT, FK → `mon_hoc.id` | Xoá môn thì xoá theo (`ON DELETE CASCADE`)                                                                                                                                                                          |
| loai_thanh_phan_id | INT, FK → `loai_thanh_phan.id` | Chuyên cần / Bài tập / Thực hành / Kiểm tra giữa kỳ / Bài tập nhóm / Thi cuối kỳ / Khác — chọn từ danh sách cố định, **không cho gõ tự do** (đảm bảo dữ liệu nhất quán giữa các sinh viên để dùng làm đặc trưng ML). Tách thành bảng danh mục riêng thay vì ràng buộc CHECK vì cần thứ tự hiển thị trong menu, và thêm loại mới thì chỉ chèn một dòng |
| trong_so_phan_tram | float                  | Tổng các dòng của cùng 1 môn phải = 100% mới được lưu                                                                                                                                                               |
| diem               | float, **nullable**    | **Để trống nếu chưa nhập** — KHÔNG mặc định 0. Xem mục 3.4                                                                                                                                                          |

### 3.3 Quy tắc "Lần học" — tự động, không cho sinh viên chọn tay

Việc so trùng dựa trên **mã môn học** (`ma_mon`), không dựa trên tên môn.

> **Vì sao là mã môn:** tên gõ tay không đáng tin — "Lập trình Web", "lập
> trình web", "LT Web" là ba chuỗi khác nhau của cùng một môn, ngược lại hai
> môn khác nhau vẫn có thể trùng tên rút gọn. Mã môn do trường cấp, ổn định
> qua các học kỳ nên đếm lần học mới đúng.

Khi sinh viên nhập **Mã môn học** trùng với môn đã tồn tại ở bất kỳ học kỳ
nào trước đó (không chỉ học kỳ đang chọn):

1. Hệ thống hiển thị cảnh báo: _"Môn này đã học ở [Học kỳ X, Năm Y] — đây có
   phải là học lại/học cải thiện?"_
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
5. Nếu mã môn không trùng với môn nào trước đó → `lan_hoc = 1`,
   `loai_lan_hoc = hoc_moi`.
6. Tên môn của lần học mới **không cần trùng** với lần trước (trường có thể
   đổi cách viết tên); lấy tên sinh viên vừa nhập, không ghi đè bản ghi cũ.

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
- Ví dụ: _Cơ sở dữ liệu phân tán_ học kỳ 1 được 4.2 (Học lần 1); học cải
  thiện ở học kỳ 2 được 6.8 (Lần 2). Cả hai dòng cùng tồn tại — xem học kỳ 1
  thấy 4.2, xem học kỳ 2 thấy 6.8.
- **GPA từng học kỳ dùng đúng điểm của lần học trong kỳ đó** — không hồi tố.
  Nhờ vậy biểu đồ xu hướng phản ánh đúng lịch sử thật của sinh viên.

> **Còn để ngỏ:** GPA _tích luỹ toàn khoá_ nên lấy điểm lần học nào (cao
> nhất / mới nhất) — cần tra quy chế của trường rồi chốt. Chưa ảnh hưởng
> giai đoạn dựng giao diện vì màn hình hiện chỉ hiển thị GPA theo học kỳ.

### 3.6 Bảng kết quả dự đoán và lịch sử cảnh báo

Đề cương §3.4 yêu cầu cơ sở dữ liệu lưu cả _kết quả dự đoán_ lẫn _lịch sử
cảnh báo_, không chỉ dữ liệu học tập.

| Trường          | Kiểu                      | Ghi chú                                       |
| --------------- | ------------------------- | --------------------------------------------- |
| id              | INT IDENTITY, PK          |                                               |
| user_id         | INT, FK → `nguoi_dung.id` |                                               |
| thoi_diem       | DATETIME2                 | Lúc chạy dự đoán                              |
| muc_nguy_co | VARCHAR(20) | `thap` / `trung_binh` / `cao` — lưu mã, giao diện tự đổi ra nhãn tiếng Việt, cùng cách làm với `loai_lan_hoc` |
| ty_le_phan_tram | DECIMAL(5,2)              | % khả năng bị cảnh báo học vụ                 |
| ly_do_json      | NVARCHAR(MAX)             | Danh sách "Lý do chính", sinh từ SHAP (mục 5) |
| goi_y_json      | NVARCHAR(MAX)             | Danh sách "Gợi ý cải thiện"                   |
| da_gui_email    | BIT                       |                                               |
| thoi_diem_gui   | DATETIME2, nullable       |                                               |

- Mỗi lần tiến trình định kỳ (mục 8) chạy xong là **thêm một dòng mới**, không
  ghi đè dòng cũ. Nhờ vậy có lịch sử thật để đối chiếu, và về sau vẽ được diễn
  biến mức nguy cơ theo thời gian.
- Trang "Cảnh báo & Mục tiêu" đọc **dòng mới nhất** của sinh viên đang đăng nhập.
- Không đặt ràng buộc duy nhất trên (`mon_hoc_id`, `loai_thanh_phan_id`)
  ở bảng điểm thành phần: một môn có thể có nhiều cột điểm cùng loại, ví
  dụ hai bài kiểm tra 15%.
- `da_gui_email` để **tránh gửi trùng**: job chỉ gửi khi mức nguy cơ khác dòng
  liền trước, hoặc khi chưa từng gửi lần nào. Không có cột này thì cứ mỗi chu
  kỳ sinh viên lại nhận một email y hệt.

### 3.7 Bảng khả năng đạt mục tiêu

Trang "Cảnh báo & Mục tiêu" cho sinh viên bấm đổi mục tiêu và con số phải đổi
theo ngay, nên mỗi bản dự đoán phải sinh **đủ ba dòng** — một cho mỗi mục tiêu
ở mục 7 — chứ không chỉ mục tiêu đang chọn.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | INT IDENTITY, PK | |
| du_doan_id | INT, FK → `du_doan_canh_bao.id` | Xoá bản dự đoán thì xoá theo (`ON DELETE CASCADE`) |
| ma_muc_tieu | VARCHAR(20) | `gioi` / `kha` / `qua_mon` |
| ty_le | DECIMAL(5,2) | % khả năng đạt, hiển thị kèm thanh tiến độ |
| ghi_chu | NVARCHAR(500) | Câu nhận xét hiện dưới thanh % |

- Ràng buộc duy nhất trên (`du_doan_id`, `ma_muc_tieu`): một bản dự đoán không
  được có hai dòng cho cùng một mục tiêu.
- Tách thành bảng riêng thay vì thêm một cột JSON vào `du_doan_canh_bao` vì đây
  là số liệu có cấu trúc cố định. Để dạng bảng thì câu hỏi "khả năng đạt loại
  Khá thay đổi thế nào qua các kỳ" là một câu SELECT; để JSON thì phải bóc tách
  từng dòng mới so sánh được.

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

| Loại cảnh báo                                                                          | Phạm vi dữ liệu                                                                                      | Vị trí hiển thị                                     |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Nguy cơ trượt **theo từng môn**                                                        | Chỉ trong học kỳ đang chọn ở sidebar                                                                 | Cột trong bảng "Danh sách môn học", trang Dashboard |
| Mức nguy cơ **tổng thể** (bị cảnh báo học vụ/thôi học) + Lý do chính + Gợi ý cải thiện | **Toàn bộ lịch sử** các học kỳ đã nhập, không phụ thuộc lựa chọn sidebar                             | Trang "Cảnh báo & Mục tiêu"                         |
| Biểu đồ "Xu hướng điểm trung bình học kỳ"                                              | **Toàn bộ** các học kỳ đã có dữ liệu (điểm hiện tại theo sidebar được đánh dấu nổi bật trên biểu đồ) | Trang Dashboard                                     |

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

## 9. Thang điểm và chuyển đổi hiển thị

- Điểm **luôn nhập và lưu ở DH10** (thang 10). Điểm tổng kết môn làm tròn 1
  chữ số thập phân như học bạ. DH4 và điểm chữ chỉ là lớp quy đổi lúc hiển
  thị, **không lưu xuống cơ sở dữ liệu** — tránh lệch giữa hai bản.
- Toggle "DH10 / DH4" ở Dashboard chỉ đổi cách hiển thị (thẻ GPA, trục biểu
  đồ, cột điểm tổng kết). Ở DH4 hiển thị kèm điểm chữ, ví dụ `3.0 (B)`.
- Bảng quy đổi 5 bậc (cài đặt tại `ui/rules.py::to4` và `ui/rules.py::chu_cai`):

| DH10     | ≥ 8.5 | ≥ 7.0 | ≥ 5.5 | ≥ 4.0 | < 4.0 |
| -------- | ----- | ----- | ----- | ----- | ----- |
| Điểm chữ | A     | B     | C     | D     | **E** |
| DH4      | 4.0   | 3.0   | 2.0   | 1.0   | 0.0   |

### 9.1 Điểm trung bình học kỳ — tính riêng cho từng thang

Cả hai đều là trung bình có trọng số theo tín chỉ, tính **độc lập với nhau**:

```
DH10 = Σ(điểm DH10 của môn × TC) / Σ TC
DH4  = Σ(điểm DH4  của môn × TC) / Σ TC     ← quy đổi TỪNG MÔN trước
```

> **Không được** tính DH4 bằng cách quy đổi điểm trung bình DH10. `to4` là
> hàm bậc thang nên hai cách cho kết quả khác nhau. Đây là lỗi dễ mắc nhất
> ở phần này.

Đối chiếu với bảng điểm thật của sinh viên (2 học kỳ, khớp tuyệt đối):

| Học kỳ         | TC  | DH10 | DH4  | `to4(DH10)` — cách sai |
| -------------- | --- | ---- | ---- | ---------------------- |
| 2024–2025 HK01 | 18  | 8.19 | 3.50 | 3.00                   |
| 2024–2025 HK02 | 16  | 7.46 | 2.81 | 3.00                   |

### 9.2 Các trường hợp biên

- Ngưỡng lấy **bằng**: 7.0 là B (không phải C), 8.5 là A, 4.0 là D. Kiểm
  chứng bằng cặp 6.9 → C và 7.0 → B trong bảng điểm thật.
- Môn **điểm E** (< 4.0) vẫn tính vào GPA với DH4 = 0.0, **không** loại khỏi
  mẫu số. Đây là môn phải học lại.
- Môn **0 tín chỉ** (ví dụ Sinh hoạt công dân) không ảnh hưởng GPA vì trọng
  số bằng 0, nhưng vẫn hiện trong bảng môn học.
- Môn **chưa nhập đủ 100% trọng số thành phần** cho ra điểm _tạm tính_ (xem
  §3.4); điểm tạm tính không được dùng để kết luận đỗ/trượt, nên không tính
  vào chỉ số "Môn điểm E".

## 10. Công nghệ

- Ngôn ngữ: **Python** (toàn bộ, không dùng C#/JS).
- Giao diện: **Streamlit** — dùng component chuẩn (`st.form`, `st.selectbox`,
  `st.data_editor`, `st.metric`, `st.line_chart`/`st.plotly_chart`,
  `st.tabs`/sidebar để điều hướng). Biểu đồ xu hướng **bắt buộc dùng thư
  viện vẽ chuẩn** (không tự dựng bằng HTML/CSS) để đảm bảo có đủ trục X/Y,
  nhãn, chia độ đúng.
- Model: Scikit-learn / XGBoost / LightGBM, SHAP cho giải thích.
- Backend API: **FastAPI**.
- Tác vụ định kỳ: **APScheduler**.
- Gửi email: SMTP.
- Cơ sở dữ liệu: **SQL Server**, kết
  nối qua SQLAlchemy + `pyodbc` với ODBC Driver 17, xác thực Windows.
- Quản trị CSDL: SSMS — xem bảng, chạy truy vấn đối chiếu số liệu.
- Kiểm thử API: Postman.

> **Vì sao SQL Server chứ không phải PostgreSQL:** máy phát triển đã cài sẵn
> SQL Server và SSMS. Cả hai mốc trình bày đều chạy **local** — báo cáo tiến
> độ là chia sẻ màn hình qua Google Meet, báo cáo cuối kỳ là mở máy chạy trực
> tiếp — nên không cần triển khai lên cloud, thứ vốn là lợi thế duy nhất của
> PostgreSQL trong bối cảnh này. Nếu phát sinh nhu cầu cho người khác tự truy
> cập, mở đường hầm tạm (`cloudflared tunnel`) là đủ, không phải đổi CSDL.

### 10.1 Đường đi của dữ liệu — Streamlit không gọi qua HTTP

```
Streamlit  →  lớp repository (SQLAlchemy)  →  SQL Server
FastAPI    →  cùng lớp repository đó       →  SQL Server
```

- Thao tác CRUD môn học/điểm thành phần của giao diện đi **thẳng** xuống lớp
  repository, không vòng qua HTTP. Bọc thêm một tầng API cho phần này chỉ làm
  chậm và thêm một chỗ phải gỡ lỗi, trong khi ứng dụng chỉ có một loại người
  dùng và chạy chung một tiến trình.
- **FastAPI vẫn nằm trong phạm vi đồ án**: phục vụ tiến trình định kỳ (mục 8),
  gửi email cảnh báo, và gọi mô hình dự đoán — những phần chạy độc lập với
  phiên làm việc của sinh viên.
- Đây là quyết định **theo giai đoạn, không vĩnh viễn**. Đề cương §2.3 nói API
  phục vụ cả việc _lưu trữ dữ liệu_, còn §4.1 đặt mục tiêu nắm kiến trúc
  client–server; nên sau khi dữ liệu chạy thật, FastAPI sẽ bọc lên chính lớp
  repository đó thành API CRUD đầy đủ (kiểm thử bằng Postman theo §3.5), rồi
  chuyển Streamlit sang gọi HTTP. Vì mọi truy cập dữ liệu đã gom về một lớp,
  bước chuyển này là sửa một chỗ chứ không phải viết lại màn hình.
- Cả hai đi qua **cùng một lớp repository**, nên quy tắc nghiệp vụ chỉ được
  cài đặt một lần (`ui/rules.py` giữ nguyên vai trò tính toán, không biết dữ
  liệu đến từ đâu).

### 10.2 Quy ước riêng của SQL Server phải tuân thủ

- **Mọi cột chữ dùng `NVARCHAR`, không dùng `VARCHAR`**, và chuỗi hằng trong
  câu lệnh SQL phải có tiền tố `N` (`N'Chuyên cần'`). Bỏ sót là tên môn và
  loại thành phần tiếng Việt bị mất dấu — lỗi âm thầm, chỉ lộ ra khi đọc lại
  dữ liệu.
- **Điểm lưu `DECIMAL(4,2)`**, không dùng `FLOAT`: điểm thành phần và trọng số
  là số thập phân cố định, dùng dấu phẩy động sẽ ra những sai số kiểu
  `6.999999` khi cộng có trọng số.
- **Trọng số lưu `DECIMAL(5,2)`** với ràng buộc tổng theo môn = 100 kiểm ở
  tầng ứng dụng (SQL Server không có ràng buộc CHECK theo nhóm dòng).
- Chuỗi kết nối phát triển:
  `mssql+pyodbc://@localhost/<TenCSDL>?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes`

## 11. Các màn hình cần có (tối giản, không thêm ngoài danh sách)

1. **Đăng ký / Đăng nhập** — không nằm trong menu điều hướng chính; truy cập
   qua nút góc dưới sidebar khi chưa đăng nhập.
2. **Dashboard chính** — chọn năm học/học kỳ xem điểm; thẻ tổng quan (GPA,
   tín chỉ, môn điểm E (< 4.0), mức nguy cơ tổng thể rút gọn); bảng danh sách môn
   học kèm cột nguy cơ trượt theo môn; biểu đồ xu hướng GPA toàn bộ lịch sử;
   toggle DH10 / DH4; nút "+ Thêm môn học".
3. **Thêm / cập nhật môn học** — mặc định thu gọn, chỉ hiện bảng "Môn học đã
   thêm trong học kỳ này" (sửa/xoá được) + nút "+ Thêm môn học" để xổ form.
   Form dùng đúng năm học/học kỳ theo sidebar, không nhập lại.
4. **Cảnh báo & Mục tiêu học tập** — mức nguy cơ tổng thể (toàn lịch sử) +
   lý do + gợi ý cải thiện; phần nhập mục tiêu học tập + % khả năng đạt.
