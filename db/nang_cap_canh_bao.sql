/* ============================================================================
   HT_CANHBAOHOCTAP — Nâng cấp cho hệ thống cảnh báo sớm (bản 11/2026)
   Đặc tả: docs/SPEC.md §12

   Chạy SAU db\hethongcanhbao.sql, trên cơ sở dữ liệu đã có:
     sqlcmd -S localhost -E -i db\nang_cap_canh_bao.sql

   Script này CHỈ THÊM, không xoá bảng hay dữ liệu nào, và chạy lại nhiều lần
   vẫn an toàn (bảng / cột đã có thì bỏ qua). Bảng của giao diện cũ (mon_hoc,
   diem_thanh_phan, du_doan_canh_bao...) giữ nguyên để app.py cũ chạy tiếp cho
   tới khi giao diện mới thay xong.
   ============================================================================ */

USE HT_CANHBAOHOCTAP;
GO

-- Chỉ mục có điều kiện (UX_edg_moc) bắt buộc hai tuỳ chọn này; SSMS và pyodbc
-- bật sẵn nhưng sqlcmd thì không.
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


/* --- 1. nguoi_dung: thêm nhan_email, cho 4 cột của giao diện cũ được trống --
   Form đăng ký mới chỉ hỏi email, mật khẩu, họ tên: năm nhập học đọc được từ
   cổng thông tin. SQL Server không cho đổi cột đang bị ràng buộc CHECK /
   DEFAULT nên phải gỡ ràng buộc, đổi cột, rồi gắn lại. CHECK với giá trị NULL
   luôn qua nên ràng buộc cũ vẫn đúng cho dữ liệu cũ.
   -------------------------------------------------------------------------- */
IF COL_LENGTH('dbo.nguoi_dung', 'nhan_email') IS NULL
    ALTER TABLE dbo.nguoi_dung
        ADD nhan_email BIT NOT NULL CONSTRAINT DF_nguoi_dung_nhan_email DEFAULT (1);
GO

IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID('dbo.nguoi_dung') AND name = 'nien_khoa_tu' AND is_nullable = 0)
BEGIN
    ALTER TABLE dbo.nguoi_dung DROP CONSTRAINT CK_nguoi_dung_nien_khoa;
    ALTER TABLE dbo.nguoi_dung DROP CONSTRAINT CK_nguoi_dung_so_ky;
    ALTER TABLE dbo.nguoi_dung DROP CONSTRAINT CK_nguoi_dung_thang_diem;
    ALTER TABLE dbo.nguoi_dung DROP CONSTRAINT DF_nguoi_dung_thang_diem;

    ALTER TABLE dbo.nguoi_dung ALTER COLUMN nien_khoa_tu  INT NULL;
    ALTER TABLE dbo.nguoi_dung ALTER COLUMN nien_khoa_den INT NULL;
    ALTER TABLE dbo.nguoi_dung ALTER COLUMN so_ky_moi_nam INT NULL;
    ALTER TABLE dbo.nguoi_dung ALTER COLUMN thang_diem    INT NULL;

    ALTER TABLE dbo.nguoi_dung ADD
        CONSTRAINT DF_nguoi_dung_thang_diem DEFAULT (10) FOR thang_diem,
        CONSTRAINT CK_nguoi_dung_nien_khoa
            CHECK (nien_khoa_den > nien_khoa_tu AND nien_khoa_den - nien_khoa_tu <= 8),
        CONSTRAINT CK_nguoi_dung_so_ky      CHECK (so_ky_moi_nam IN (2, 3)),
        CONSTRAINT CK_nguoi_dung_thang_diem CHECK (thang_diem IN (4, 10));
END
GO


/* --- 2. lan_cap_nhat — mỗi lần sinh viên đưa dữ liệu vào là một bản ---------
   LƯU BẢN MỚI, không ghi đè: so được với lần trước (nguy cơ tăng hay giảm) và
   biết dự đoán cũ dựa trên số liệu nào. KHÔNG lưu văn bản gốc (có họ tên,
   MSSV), chỉ lưu các con số đã đọc.
   -------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.lan_cap_nhat') IS NULL
CREATE TABLE dbo.lan_cap_nhat (
    id            INT IDENTITY(1,1) NOT NULL,
    user_id       INT               NOT NULL,
    thoi_diem     DATETIME2(0)      NOT NULL CONSTRAINT DF_lcn_thoi_diem DEFAULT (SYSDATETIME()),
    nguon         VARCHAR(20)       NOT NULL,  -- cong_thong_tin / nhap_tay
    nam_nhap_hoc  INT               NULL,
    nganh         NVARCHAR(100)     NULL,
    he_dao_tao    NVARCHAR(50)      NULL,      -- 'Cử nhân (4 năm)' / 'Kỹ sư (4,5 năm)'

    CONSTRAINT PK_lan_cap_nhat PRIMARY KEY (id),
    CONSTRAINT FK_lcn_nguoi_dung FOREIGN KEY (user_id)
        REFERENCES dbo.nguoi_dung (id) ON DELETE CASCADE,
    CONSTRAINT CK_lcn_nguon CHECK (nguon IN ('cong_thong_tin', 'nhap_tay'))
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_lcn_moi_nhat')
    CREATE INDEX IX_lcn_moi_nhat ON dbo.lan_cap_nhat (user_id, thoi_diem DESC);
GO


/* --- 3. hoc_ky_tong_ket — các học kỳ đã có điểm của một lần cập nhật ---------
   Đúng các cột của bảng học kỳ trong ml/ (doc_form.py, doc_cong_thong_tin.py)
   để dac_trung.py dùng thẳng. muc_vang, hoc_phi lưu nguyên lựa chọn của form.
   -------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.hoc_ky_tong_ket') IS NULL
CREATE TABLE dbo.hoc_ky_tong_ket (
    id               INT IDENTITY(1,1) NOT NULL,
    lan_cap_nhat_id  INT               NOT NULL,
    thu_tu           INT               NOT NULL,  -- học kỳ chính thứ mấy: 1, 2, 3...
    nam_bat_dau      INT               NULL,      -- 2025 = năm học 2025–2026
    hoc_ky           INT               NULL,      -- 1, 2 (3 nếu trường có)
    tc_dat_hk        DECIMAL(5,1)      NOT NULL,
    dtb_hk           DECIMAL(4,2)      NOT NULL,  -- thang 4
    tctl             DECIMAL(5,1)      NOT NULL,
    tc_dang_ky       DECIMAL(5,1)      NOT NULL,
    dtb_tl           DECIMAL(4,2)      NOT NULL,  -- thang 4
    drl              DECIMAL(5,1)      NULL,
    muc_vang         NVARCHAR(60)      NULL,
    hoc_phi          NVARCHAR(60)      NULL,

    CONSTRAINT PK_hoc_ky_tong_ket PRIMARY KEY (id),
    CONSTRAINT FK_hktk_lan_cap_nhat FOREIGN KEY (lan_cap_nhat_id)
        REFERENCES dbo.lan_cap_nhat (id) ON DELETE CASCADE,
    CONSTRAINT UQ_hktk_thu_tu UNIQUE (lan_cap_nhat_id, thu_tu),
    CONSTRAINT CK_hktk_dtb CHECK (dtb_hk BETWEEN 0 AND 4 AND dtb_tl BETWEEN 0 AND 4),
    CONSTRAINT CK_hktk_tc  CHECK (tc_dat_hk >= 0 AND tctl >= 0 AND tc_dang_ky >= tctl),
    CONSTRAINT CK_hktk_drl CHECK (drl IS NULL OR drl BETWEEN 0 AND 100)
);
GO


/* --- 4. mon_dang_hoc — các môn của kỳ đang học (dự đoán trượt môn) ----------
   Điểm giữa kỳ, tỉ trọng có thể trống: chưa có điểm thì môn đó chưa dự đoán.
   -------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.mon_dang_hoc') IS NULL
CREATE TABLE dbo.mon_dang_hoc (
    id               INT IDENTITY(1,1) NOT NULL,
    lan_cap_nhat_id  INT               NOT NULL,
    stt              INT               NOT NULL,
    ma_mon           NVARCHAR(20)      NULL,
    ten_mon          NVARCHAR(200)     NOT NULL,
    so_tc            DECIMAL(4,1)      NOT NULL,
    diem_gk          DECIMAL(4,2)      NULL,      -- thang 10
    ti_trong_gk      DECIMAL(4,3)      NULL,      -- 0.4 = 40%
    vang_lt          NVARCHAR(60)      NULL,
    vang_th          NVARCHAR(60)      NULL,

    CONSTRAINT PK_mon_dang_hoc PRIMARY KEY (id),
    CONSTRAINT FK_mdh_lan_cap_nhat FOREIGN KEY (lan_cap_nhat_id)
        REFERENCES dbo.lan_cap_nhat (id) ON DELETE CASCADE,
    CONSTRAINT UQ_mdh_stt UNIQUE (lan_cap_nhat_id, stt),
    CONSTRAINT CK_mdh_so_tc   CHECK (so_tc >= 0),
    CONSTRAINT CK_mdh_diem_gk CHECK (diem_gk IS NULL OR diem_gk BETWEEN 0 AND 10),
    CONSTRAINT CK_mdh_ti_trong CHECK (ti_trong_gk IS NULL OR (ti_trong_gk > 0 AND ti_trong_gk < 1))
);
GO


/* --- 5. du_doan — mỗi kết quả là một dòng ------------------------------------
   Một lần dự đoán sinh: 1 dòng canh_bao, 1 dòng thoi_hoc, 1 dòng truot_mon cho
   MỖI môn đang học. Thay cho du_doan_canh_bao / du_doan_muc_tieu của thiết kế
   cũ (lưu % đã hiệu chỉnh và mục tiêu Giỏi/Khá — không còn dùng).

   mon_dang_hoc_id dùng NO ACTION: SQL Server không cho hai đường xoá dây
   chuyền (du_doan -> lan_cap_nhat và du_doan -> mon_dang_hoc -> lan_cap_nhat).
   Xoá một lần cập nhật vẫn xoá hết du_doan qua đường thứ nhất.
   -------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.du_doan') IS NULL
CREATE TABLE dbo.du_doan (
    id                 INT IDENTITY(1,1) NOT NULL,
    lan_cap_nhat_id    INT               NOT NULL,
    muc_tieu           VARCHAR(20)       NOT NULL,  -- canh_bao / thoi_hoc / truot_mon
    mon_dang_hoc_id    INT               NULL,      -- chỉ với truot_mon
    cho_thu_tu         INT               NOT NULL,  -- dự đoán cho học kỳ chính thứ mấy
    cho_ten            NVARCHAR(30)      NULL,      -- 'HK1 2026–2027'
    diem_nguy_co       DECIMAL(6,4)      NULL,      -- NULL = chưa dự đoán (thiếu điểm giữa kỳ)
    nguong             DECIMAL(6,4)      NOT NULL,  -- ngưỡng F2 của mô hình
    bao_dong           BIT               NOT NULL,
    muc_nguy_co        VARCHAR(20)       NOT NULL,  -- thap / trung_binh / cao / chua_du_doan
    ly_do_json         NVARCHAR(MAX)     NULL,      -- list chuỗi, từ SHAP; chỉ khi báo động
    goi_y_json         NVARCHAR(MAX)     NULL,
    ghi_chu            NVARCHAR(200)     NULL,
    phuong_phap        VARCHAR(30)       NOT NULL,  -- 'Random Forest', 'LightGBM'...
    phien_ban_mo_hinh  VARCHAR(30)       NOT NULL,  -- thời điểm train lưu trong file .joblib
    thoi_diem          DATETIME2(0)      NOT NULL CONSTRAINT DF_dd_thoi_diem DEFAULT (SYSDATETIME()),

    CONSTRAINT PK_du_doan PRIMARY KEY (id),
    CONSTRAINT FK_dd_lan_cap_nhat FOREIGN KEY (lan_cap_nhat_id)
        REFERENCES dbo.lan_cap_nhat (id) ON DELETE CASCADE,
    CONSTRAINT FK_dd_mon_dang_hoc FOREIGN KEY (mon_dang_hoc_id)
        REFERENCES dbo.mon_dang_hoc (id),
    CONSTRAINT CK_dd_muc_tieu CHECK (muc_tieu IN ('canh_bao', 'thoi_hoc', 'truot_mon')),
    -- Trượt môn thì phải chỉ ra môn nào; cảnh báo / thôi học thì không gắn môn
    CONSTRAINT CK_dd_mon CHECK ((muc_tieu = 'truot_mon' AND mon_dang_hoc_id IS NOT NULL) OR
                                (muc_tieu <> 'truot_mon' AND mon_dang_hoc_id IS NULL)),
    CONSTRAINT CK_dd_muc CHECK (muc_nguy_co IN ('thap', 'trung_binh', 'cao', 'chua_du_doan')),
    CONSTRAINT CK_dd_diem CHECK (diem_nguy_co IS NULL OR diem_nguy_co BETWEEN 0 AND 1),
    CONSTRAINT CK_dd_json CHECK (
        (ly_do_json IS NULL OR ISJSON(ly_do_json) = 1) AND
        (goi_y_json IS NULL OR ISJSON(goi_y_json) = 1))
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_dd_lan_cap_nhat')
    CREATE INDEX IX_dd_lan_cap_nhat ON dbo.du_doan (lan_cap_nhat_id, muc_tieu);
GO


/* --- 6. email_da_gui — hàng đợi email và lịch sử cảnh báo --------------------
   Mọi email đi qua bảng này: API / tác vụ chỉ THÊM dòng 'cho_gui', tác vụ gửi
   (5 phút một lần) gửi rồi đổi sang 'da_gui' hoặc 'loi' (thử tối đa 3 lần).
   "Nhắc tôi sau" là dòng loai = 'hen_nhac' có hen_gui = ngày hẹn.

   Chống gửi trùng nhắc theo mốc: mỗi (người, loại, mốc, lần nhắc) một dòng.
   du_doan_id NO ACTION cùng lý do như ở bảng du_doan.
   -------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.email_da_gui') IS NULL
CREATE TABLE dbo.email_da_gui (
    id              INT IDENTITY(1,1) NOT NULL,
    user_id         INT               NOT NULL,
    loai            VARCHAR(20)       NOT NULL,
    moc             NVARCHAR(60)      NULL,      -- 'HK1 2026–2027 giữa kỳ' (nhắc theo mốc)
    lan_nhac        TINYINT           NULL,      -- 1 hoặc 2
    du_doan_id      INT               NULL,      -- email cảnh báo: dự đoán nào
    trang_thai      VARCHAR(10)       NOT NULL CONSTRAINT DF_edg_trang_thai DEFAULT ('cho_gui'),
    hen_gui         DATETIME2(0)      NULL,      -- NULL = gửi ngay ở lượt sau
    so_lan_thu      TINYINT           NOT NULL CONSTRAINT DF_edg_so_lan_thu DEFAULT (0),
    tieu_de         NVARCHAR(200)     NOT NULL,
    noi_dung        NVARCHAR(MAX)     NOT NULL,
    noi_dung_loi    NVARCHAR(500)     NULL,
    thoi_diem_tao   DATETIME2(0)      NOT NULL CONSTRAINT DF_edg_tao DEFAULT (SYSDATETIME()),
    thoi_diem_gui   DATETIME2(0)      NULL,

    CONSTRAINT PK_email_da_gui PRIMARY KEY (id),
    CONSTRAINT FK_edg_nguoi_dung FOREIGN KEY (user_id)
        REFERENCES dbo.nguoi_dung (id) ON DELETE CASCADE,
    CONSTRAINT FK_edg_du_doan FOREIGN KEY (du_doan_id)
        REFERENCES dbo.du_doan (id),
    CONSTRAINT CK_edg_loai CHECK (loai IN ('nhac_giua_ky', 'nhac_cuoi_ky', 'hen_nhac',
                                           'canh_bao', 'mo_hinh_moi')),
    CONSTRAINT CK_edg_trang_thai CHECK (trang_thai IN ('cho_gui', 'da_gui', 'loi')),
    -- Đã gửi thì phải có thời điểm gửi, và ngược lại
    CONSTRAINT CK_edg_gui CHECK ((trang_thai = 'da_gui' AND thoi_diem_gui IS NOT NULL) OR
                                 (trang_thai <> 'da_gui' AND thoi_diem_gui IS NULL))
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_edg_moc')
    CREATE UNIQUE INDEX UX_edg_moc ON dbo.email_da_gui (user_id, loai, moc, lan_nhac)
        WHERE moc IS NOT NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_edg_hang_doi')
    CREATE INDEX IX_edg_hang_doi ON dbo.email_da_gui (trang_thai, hen_gui);
GO


/* ============================================================================
   SƠ ĐỒ QUAN HỆ (phần mới)

     nguoi_dung --< lan_cap_nhat --< hoc_ky_tong_ket
         |               |
         |               +--------< mon_dang_hoc
         |               |               | 1
         |               +--------< du_doan >-+  (truot_mon: một dòng mỗi môn)
         |                              | 1
         +--------------< email_da_gui >+       (email cảnh báo trỏ tới dự đoán)

   Xoá tài khoản thì xoá dây chuyền mọi bảng mới (CASCADE qua nguoi_dung và
   lan_cap_nhat).
   ============================================================================ */

PRINT N'Đã nâng cấp HT_CANHBAOHOCTAP cho hệ thống cảnh báo sớm.';
GO
