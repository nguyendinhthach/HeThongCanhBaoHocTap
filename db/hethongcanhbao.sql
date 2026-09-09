/* ============================================================================
   HT_CANHBAOHOCTAP — Lược đồ cơ sở dữ liệu
   Hệ thống cảnh báo sớm nguy cơ học tập của sinh viên

   Đồ án tốt nghiệp KTPM — Trường Đại học Đà Lạt
   Nguyễn Đình Thạch (2314506) · Phan Thành Huy (2312634)
   GVHD: TS. Thái Duy Quý

   Đặc tả nghiệp vụ đầy đủ: docs/SPEC.md
   Hệ quản trị: SQL Server 2022

   CÁCH CHẠY
     SSMS   : mở file, nhấn F5
     sqlcmd : sqlcmd -S localhost -E -i db\hethongcanhbao.sql

   CẢNH BÁO
     Phần "DỌN DẸP" bên dưới XOÁ TOÀN BỘ BẢNG cùng dữ liệu bên trong, để
     chạy lại script nhiều lần trong lúc phát triển. Khi hệ thống đã chứa
     dữ liệu thật thì phải xoá phần đó đi trước khi chạy.
   ============================================================================ */


/* --- 0. Tạo cơ sở dữ liệu -------------------------------------------------
   Vietnamese_CI_AS:
     - sắp xếp đúng thứ tự bảng chữ cái tiếng Việt khi ORDER BY tên môn
     - CI (case-insensitive): 'ct101' khớp 'CT101' khi so mã môn (SPEC §3.3)
     - AS (accent-sensitive) : 'Toán' khác 'Toan', không gộp nhầm hai chuỗi
   Collation mặc định của server là SQL_Latin1_General_CP1_CI_AS nên phải chỉ
   định rõ ở đây, không dựa vào mặc định.
   -------------------------------------------------------------------------- */
IF DB_ID('HT_CANHBAOHOCTAP') IS NULL
    CREATE DATABASE HT_CANHBAOHOCTAP COLLATE Vietnamese_CI_AS;
GO

USE HT_CANHBAOHOCTAP;
GO


/* --- 1. DỌN DẸP — xoá ngược thứ tự phụ thuộc khoá ngoại ------------------- */
DROP TABLE IF EXISTS dbo.du_doan_muc_tieu;
DROP TABLE IF EXISTS dbo.du_doan_canh_bao;
DROP TABLE IF EXISTS dbo.diem_thanh_phan;
DROP TABLE IF EXISTS dbo.mon_hoc;
DROP TABLE IF EXISTS dbo.loai_thanh_phan;
DROP TABLE IF EXISTS dbo.nguoi_dung;
GO


/* ============================================================================
   2. nguoi_dung — tài khoản và hồ sơ sinh viên   (SPEC §2, §2.1)
   ----------------------------------------------------------------------------
   Danh sách năm học KHÔNG lưu thành bảng riêng: các năm luôn liên tiếp nhau
   nên suy được từ niên khoá — năm học chạy từ nien_khoa_tu đến nien_khoa_den-1.
   Thao tác "Thêm năm học mới" trên giao diện chỉ là tăng nien_khoa_den lên 1.
   Học kỳ cũng vậy: mọi năm đều có so_ky_moi_nam kỳ như nhau.

   thang_diem và muc_tieu là lựa chọn hiển thị của sinh viên, lưu lại để không
   bị đặt lại về mặc định mỗi lần tải trang.
   ============================================================================ */
CREATE TABLE dbo.nguoi_dung (
    id              INT IDENTITY(1,1) NOT NULL,
    email           NVARCHAR(255)     NOT NULL,  -- đăng nhập, và là địa chỉ nhận cảnh báo (SPEC §8)
    mat_khau_hash   VARCHAR(100)      NOT NULL,  -- chuỗi bcrypt: chỉ ASCII nên đây là cột VARCHAR duy nhất
    ho_ten          NVARCHAR(100)     NOT NULL,
    nien_khoa_tu    INT               NOT NULL,  -- VD 2023
    nien_khoa_den   INT               NOT NULL,  -- VD 2027
    so_ky_moi_nam   INT               NOT NULL,
    thang_diem      INT               NOT NULL CONSTRAINT DF_nguoi_dung_thang_diem DEFAULT (10),
    muc_tieu        VARCHAR(20)       NULL,      -- SPEC §7; NULL = chưa chọn mục tiêu
    ngay_tao        DATETIME2(0)      NOT NULL CONSTRAINT DF_nguoi_dung_ngay_tao   DEFAULT (SYSDATETIME()),

    CONSTRAINT PK_nguoi_dung       PRIMARY KEY (id),
    CONSTRAINT UQ_nguoi_dung_email UNIQUE (email),
    CONSTRAINT CK_nguoi_dung_nien_khoa
        CHECK (nien_khoa_den > nien_khoa_tu AND nien_khoa_den - nien_khoa_tu <= 8),
    CONSTRAINT CK_nguoi_dung_so_ky      CHECK (so_ky_moi_nam IN (2, 3)),
    CONSTRAINT CK_nguoi_dung_thang_diem CHECK (thang_diem IN (4, 10)),
    CONSTRAINT CK_nguoi_dung_muc_tieu   CHECK (muc_tieu IN ('gioi', 'kha', 'qua_mon'))
);
GO


/* ============================================================================
   3. loai_thanh_phan — danh mục loại điểm thành phần   (SPEC §3.2)
   ----------------------------------------------------------------------------
   Tách thành bảng riêng thay vì ràng buộc CHECK vì đây là danh sách sinh viên
   CHỌN TỪ MENU, không gõ tự do: có thứ tự hiển thị, và về sau thêm loại mới
   chỉ cần chèn một dòng chứ không phải sửa cấu trúc bảng.

   Quan trọng với phần học máy: mọi sinh viên dùng chung đúng bộ loại này, nhờ
   vậy "điểm chuyên cần" của người này so sánh được với người kia (SPEC §4).
   ============================================================================ */
CREATE TABLE dbo.loai_thanh_phan (
    id      INT IDENTITY(1,1) NOT NULL,
    ma      VARCHAR(20)       NOT NULL,  -- mã ổn định, dùng trong code Python
    ten     NVARCHAR(50)      NOT NULL,  -- nhãn hiển thị trên giao diện
    thu_tu  INT               NOT NULL,  -- thứ tự trong menu chọn

    CONSTRAINT PK_loai_thanh_phan    PRIMARY KEY (id),
    CONSTRAINT UQ_loai_thanh_phan_ma UNIQUE (ma)
);
GO

INSERT INTO dbo.loai_thanh_phan (ma, ten, thu_tu) VALUES
    ('chuyen_can',   N'Chuyên cần',       1),
    ('bai_tap',      N'Bài tập',          2),
    ('thuc_hanh',    N'Thực hành',        3),
    ('giua_ky',      N'Kiểm tra giữa kỳ', 4),
    ('bai_tap_nhom', N'Bài tập nhóm',     5),
    ('cuoi_ky',      N'Thi cuối kỳ',      6),
    ('khac',         N'Khác',             7);
GO


/* ============================================================================
   4. mon_hoc — mỗi dòng là MỘT LẦN HỌC của một môn trong một học kỳ
                                                        (SPEC §3.1, §3.3, §3.5)
   ----------------------------------------------------------------------------
   Học lại không ghi đè dòng cũ mà thêm dòng mới, nên cùng một ma_mon có thể
   xuất hiện nhiều lần với lan_hoc khác nhau. Đó là lý do khoá chính phải là
   cột id riêng chứ không thể là mã môn.

   Ràng buộc UQ_mon_hoc_ky chặn việc thêm trùng một môn trong CÙNG một học kỳ —
   ngoài đời không ai đăng ký hai lần cùng môn trong một kỳ, nếu xảy ra thì là
   người dùng bấm lưu hai lần.
   ============================================================================ */
CREATE TABLE dbo.mon_hoc (
    id             INT IDENTITY(1,1) NOT NULL,
    user_id        INT               NOT NULL,
    nam_bat_dau    INT               NOT NULL,  -- 2025 nghĩa là năm học 2025–2026
    hoc_ky         INT               NOT NULL,
    ma_mon         NVARCHAR(20)      NOT NULL,  -- khoá định danh môn, dùng để đếm lần học
    ten_mon        NVARCHAR(200)     NOT NULL,  -- chỉ để hiển thị, không dùng so trùng
    so_tin_chi     INT               NOT NULL,
    lan_hoc        INT               NOT NULL CONSTRAINT DF_mon_hoc_lan_hoc       DEFAULT (1),
    loai_lan_hoc   VARCHAR(20)       NOT NULL,
    ngay_tao       DATETIME2(0)      NOT NULL CONSTRAINT DF_mon_hoc_ngay_tao      DEFAULT (SYSDATETIME()),
    ngay_cap_nhat  DATETIME2(0)      NOT NULL CONSTRAINT DF_mon_hoc_ngay_cap_nhat DEFAULT (SYSDATETIME()),

    CONSTRAINT PK_mon_hoc PRIMARY KEY (id),
    CONSTRAINT FK_mon_hoc_nguoi_dung FOREIGN KEY (user_id)
        REFERENCES dbo.nguoi_dung (id) ON DELETE CASCADE,
    CONSTRAINT UQ_mon_hoc_ky UNIQUE (user_id, nam_bat_dau, hoc_ky, ma_mon),
    CONSTRAINT CK_mon_hoc_hoc_ky  CHECK (hoc_ky IN (1, 2, 3)),
    -- Môn 0 tín chỉ vẫn hợp lệ, ví dụ Sinh hoạt công dân (SPEC §9.2)
    CONSTRAINT CK_mon_hoc_tin_chi CHECK (so_tin_chi >= 0),
    CONSTRAINT CK_mon_hoc_lan_hoc CHECK (lan_hoc >= 1),
    CONSTRAINT CK_mon_hoc_loai    CHECK (loai_lan_hoc IN ('hoc_moi', 'hoc_lai', 'hoc_cai_thien'))
);
GO

-- Đếm số lần đã học một môn (SPEC §3.3). Ràng buộc UQ_mon_hoc_ky không phục vụ
-- được truy vấn này vì nam_bat_dau và hoc_ky nằm chen giữa user_id và ma_mon.
CREATE INDEX IX_mon_hoc_ma_mon ON dbo.mon_hoc (user_id, ma_mon);
GO


/* ============================================================================
   5. diem_thanh_phan — các đầu điểm của một lần học   (SPEC §3.2, §3.4)
   ----------------------------------------------------------------------------
   diem để NULL khi chưa nhập, KHÔNG mặc định 0: điểm 0 là một kết quả thật,
   còn NULL nghĩa là chưa thi. Phân biệt được hai thứ này mới tính ra "điểm tạm
   tính" và tránh báo động giả cho môn chưa thi xong.

   Cố ý KHÔNG đặt ràng buộc duy nhất trên (mon_hoc_id, loai_thanh_phan_id):
   một môn có thể có nhiều cột điểm cùng loại, ví dụ hai bài kiểm tra 15%.

   Tổng trọng số theo môn phải bằng 100% — ràng buộc này kiểm ở tầng ứng dụng
   vì SQL Server không có CHECK tính trên nhóm dòng.
   ============================================================================ */
CREATE TABLE dbo.diem_thanh_phan (
    id                  INT IDENTITY(1,1) NOT NULL,
    mon_hoc_id          INT               NOT NULL,
    loai_thanh_phan_id  INT               NOT NULL,
    trong_so_phan_tram  DECIMAL(5,2)      NOT NULL,
    diem                DECIMAL(4,2)      NULL,

    CONSTRAINT PK_diem_thanh_phan PRIMARY KEY (id),
    CONSTRAINT FK_dtp_mon_hoc FOREIGN KEY (mon_hoc_id)
        REFERENCES dbo.mon_hoc (id) ON DELETE CASCADE,
    -- Không CASCADE: đang có môn dùng loại nào thì không cho xoá loại đó
    CONSTRAINT FK_dtp_loai FOREIGN KEY (loai_thanh_phan_id)
        REFERENCES dbo.loai_thanh_phan (id),
    CONSTRAINT CK_dtp_trong_so CHECK (trong_so_phan_tram > 0 AND trong_so_phan_tram <= 100),
    CONSTRAINT CK_dtp_diem     CHECK (diem IS NULL OR (diem >= 0 AND diem <= 10))
);
GO

CREATE INDEX IX_dtp_mon_hoc ON dbo.diem_thanh_phan (mon_hoc_id);
GO


/* ============================================================================
   6. du_doan_canh_bao — kết quả dự đoán và lịch sử cảnh báo   (SPEC §3.6)
   ----------------------------------------------------------------------------
   Mỗi lần tác vụ định kỳ chạy xong là THÊM một dòng, không sửa dòng cũ. Giữ
   lịch sử mới đối chiếu được, và về sau vẽ được diễn biến mức nguy cơ.

   Trang "Cảnh báo & Mục tiêu" đọc dòng mới nhất của sinh viên đang đăng nhập.

   da_gui_email để tránh gửi trùng: tác vụ định kỳ chỉ gửi khi mức nguy cơ khác
   lần trước, hoặc khi chưa từng gửi. Không có cột này thì cứ mỗi chu kỳ sinh
   viên lại nhận một email y hệt.
   ============================================================================ */
CREATE TABLE dbo.du_doan_canh_bao (
    id               INT IDENTITY(1,1) NOT NULL,
    user_id          INT               NOT NULL,
    thoi_diem        DATETIME2(0)      NOT NULL CONSTRAINT DF_du_doan_thoi_diem DEFAULT (SYSDATETIME()),
    muc_nguy_co      VARCHAR(20)       NOT NULL,
    ty_le_phan_tram  DECIMAL(5,2)      NOT NULL,  -- % khả năng bị cảnh báo học vụ
    ly_do_json       NVARCHAR(MAX)     NULL,      -- "Lý do chính", sinh từ SHAP (SPEC §5)
    goi_y_json       NVARCHAR(MAX)     NULL,      -- "Gợi ý cải thiện"
    da_gui_email     BIT               NOT NULL CONSTRAINT DF_du_doan_da_gui    DEFAULT (0),
    thoi_diem_gui    DATETIME2(0)      NULL,

    CONSTRAINT PK_du_doan_canh_bao PRIMARY KEY (id),
    CONSTRAINT FK_du_doan_nguoi_dung FOREIGN KEY (user_id)
        REFERENCES dbo.nguoi_dung (id) ON DELETE CASCADE,
    CONSTRAINT CK_du_doan_muc   CHECK (muc_nguy_co IN ('thap', 'trung_binh', 'cao')),
    CONSTRAINT CK_du_doan_ty_le CHECK (ty_le_phan_tram >= 0 AND ty_le_phan_tram <= 100),
    -- Đã gửi thì phải có mốc thời gian gửi, và ngược lại
    CONSTRAINT CK_du_doan_gui CHECK (
        (da_gui_email = 0 AND thoi_diem_gui IS NULL) OR
        (da_gui_email = 1 AND thoi_diem_gui IS NOT NULL)),
    CONSTRAINT CK_du_doan_json CHECK (
        (ly_do_json IS NULL OR ISJSON(ly_do_json) = 1) AND
        (goi_y_json IS NULL OR ISJSON(goi_y_json) = 1))
);
GO

-- Truy vấn thường dùng nhất: lấy bản dự đoán mới nhất của một sinh viên
CREATE INDEX IX_du_doan_moi_nhat ON dbo.du_doan_canh_bao (user_id, thoi_diem DESC);
GO


/* ============================================================================
   7. du_doan_muc_tieu — khả năng đạt từng mục tiêu học tập   (SPEC §7, §3.7)
   ----------------------------------------------------------------------------
   Mỗi bản dự đoán sinh ra ĐỦ BA dòng, một dòng cho mỗi mục tiêu. Phải đủ cả ba
   vì trang "Cảnh báo & Mục tiêu" cho sinh viên bấm đổi mục tiêu và con số phải
   đổi theo ngay, không chờ chạy lại mô hình.

   Tách thành bảng riêng thay vì thêm một cột JSON vào du_doan_canh_bao: đây là
   số liệu có cấu trúc cố định, để dạng bảng thì sau này truy vấn "khả năng đạt
   loại Khá thay đổi thế nào qua các kỳ" là một câu SELECT, còn để JSON thì phải
   bóc tách từng dòng.
   ============================================================================ */
CREATE TABLE dbo.du_doan_muc_tieu (
    id           INT IDENTITY(1,1) NOT NULL,
    du_doan_id   INT               NOT NULL,
    ma_muc_tieu  VARCHAR(20)       NOT NULL,  -- gioi / kha / qua_mon
    ty_le        DECIMAL(5,2)      NOT NULL,  -- % khả năng đạt được mục tiêu
    ghi_chu      NVARCHAR(500)     NULL,      -- câu nhận xét hiện dưới thanh %

    CONSTRAINT PK_du_doan_muc_tieu PRIMARY KEY (id),
    CONSTRAINT FK_ddmt_du_doan FOREIGN KEY (du_doan_id)
        REFERENCES dbo.du_doan_canh_bao (id) ON DELETE CASCADE,
    -- Một bản dự đoán không được có hai dòng cho cùng một mục tiêu
    CONSTRAINT UQ_ddmt_muc_tieu UNIQUE (du_doan_id, ma_muc_tieu),
    CONSTRAINT CK_ddmt_ma    CHECK (ma_muc_tieu IN ('gioi', 'kha', 'qua_mon')),
    CONSTRAINT CK_ddmt_ty_le CHECK (ty_le >= 0 AND ty_le <= 100)
);
GO


/* ============================================================================
   SƠ ĐỒ QUAN HỆ

     nguoi_dung
         | 1
         +--------< mon_hoc --------< diem_thanh_phan >-------- loai_thanh_phan
         |   n        1        n            n             1
         |
         +--------< du_doan_canh_bao --------< du_doan_muc_tieu
             n             1            n

     nguoi_dung       1 - n  mon_hoc           xoá tài khoản thì xoá theo (CASCADE)
     mon_hoc          1 - n  diem_thanh_phan   xoá môn thì xoá theo (CASCADE)
     loai_thanh_phan  1 - n  diem_thanh_phan   danh mục dùng chung, không cho xoá
                                               loại đang có môn sử dụng
     nguoi_dung       1 - n  du_doan_canh_bao  xoá tài khoản thì xoá theo (CASCADE)
     du_doan_canh_bao 1 - n  du_doan_muc_tieu  xoá bản dự đoán thì xoá theo (CASCADE)
   ============================================================================ */

PRINT N'Đã dựng xong lược đồ HT_CANHBAOHOCTAP.';
GO
