USE HT_CANHBAOHOCTAP;
GO

SET NOCOUNT ON;

-- 1. Xoá dữ liệu các sinh viên mẫu cũ (đuôi @dlu.edu.vn)
DELETE FROM dbo.diem_thanh_phan WHERE mon_hoc_id IN (SELECT id FROM dbo.mon_hoc WHERE user_id IN (SELECT id FROM dbo.nguoi_dung WHERE email LIKE '%@dlu.edu.vn'));
DELETE FROM dbo.mon_hoc WHERE user_id IN (SELECT id FROM dbo.nguoi_dung WHERE email LIKE '%@dlu.edu.vn');
DELETE FROM dbo.nguoi_dung WHERE email LIKE '%@dlu.edu.vn';

-- 2. Khai báo mã loại thành phần
DECLARE @lt_cc INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'chuyen_can');
DECLARE @lt_gk INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'giua_ky');
DECLARE @lt_ck INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'cuoi_ky');

-- 3. Bảng tạm chứa thông tin 10 Sinh viên mẫu
DECLARE @SinhVien TABLE (
    id INT IDENTITY(1,1),
    ho_ten NVARCHAR(100),
    email NVARCHAR(100),
    muc_tieu VARCHAR(20),
    base_score FLOAT,
    fail_rate INT
);

INSERT INTO @SinhVien (ho_ten, email, muc_tieu, base_score, fail_rate) VALUES
(N'Nguyễn Văn An', 'an.nguyen23@dlu.edu.vn', 'gioi', 8.8, 0),
(N'Trần Thị Bình', 'binh.tran23@dlu.edu.vn', 'gioi', 8.2, 0),
(N'Lê Hoàng Cường', 'cuong.le23@dlu.edu.vn', 'kha', 7.4, 2),
(N'Phạm Minh Đức', 'duc.pham23@dlu.edu.vn', 'kha', 7.0, 5),
(N'Võ Thiện Em', 'em.vo23@dlu.edu.vn', 'kha', 6.8, 5),
(N'Đặng Thu Phương', 'phuong.dang23@dlu.edu.vn', 'kha', 6.2, 10),
(N'Hoàng Quốc Gia', 'gia.hoang23@dlu.edu.vn', 'qua_mon', 5.5, 20),
(N'Bùi Tấn Hải', 'hai.bui23@dlu.edu.vn', 'qua_mon', 4.5, 35),
(N'Ngô Mai Hương', 'huong.ngo23@dlu.edu.vn', 'qua_mon', 4.0, 40),
(N'Lý Khánh Khoa', 'khoa.ly23@dlu.edu.vn', 'gioi', 7.8, 5);

-- 4. Bảng tạm chứa danh mục 34 Môn học qua 8 học kỳ
DECLARE @MonHoc TABLE (
    id INT IDENTITY(1,1),
    nam INT,
    hk INT,
    ma NVARCHAR(20),
    ten NVARCHAR(200),
    tc INT
);

INSERT INTO @MonHoc (nam, hk, ma, ten, tc) VALUES
(2023, 1, N'CT1101', N'Lập trình cấu trúc (C++)', 3),
(2023, 1, N'CT1102', N'Công nghệ thông tin cơ bản', 3),
(2023, 1, N'LL1101', N'Triết học Mác-Lênin', 3),
(2023, 1, N'PL1101', N'Pháp luật đại cương', 2),
(2023, 2, N'CT1201', N'Lập trình hướng đối tượng (C#)', 3),
(2023, 2, N'CT1202', N'Bảo trì máy tính', 2),
(2023, 2, N'CT1203', N'Thiết kế đồ họa', 2),
(2023, 2, N'TN1201', N'Toán rời rạc', 3),
(2024, 1, N'TN2101', N'Toán cao cấp (B2)', 3),
(2024, 1, N'NN2101', N'Tiếng Anh chuyên ngành', 2),
(2024, 1, N'CT2101', N'Dữ liệu thuật giải', 3),
(2024, 1, N'KT2101', N'Nguyên lý kế toán', 2),
(2024, 2, N'CT2201', N'Mạng máy tính', 3),
(2024, 2, N'CT2202', N'Cơ sở dữ liệu', 3),
(2024, 2, N'CT2203', N'Hệ điều hành', 3),
(2024, 2, N'NV2201', N'Kỹ năng soạn thảo văn bản hành chính', 2),
(2025, 1, N'CT3101', N'Đồ án cơ sở', 2),
(2025, 1, N'CT3102', N'Phát triển ứng dụng desktop', 3),
(2025, 1, N'CT3103', N'Lập trình mạng', 3),
(2025, 1, N'CT3104', N'Thiết kế web', 3),
(2025, 2, N'CT3201', N'Phát triển ứng dụng web cơ bản', 3),
(2025, 2, N'CT3202', N'Lập trình Python', 3),
(2025, 2, N'CT3203', N'Phát triển ứng dụng game cơ bản', 3),
(2025, 2, N'CT3204', N'Công nghệ phần mềm', 3),
(2025, 2, N'CT3205', N'Phát triển ứng dụng di động', 3),
(2026, 1, N'CT4101', N'Phát triển ứng dụng web nâng cao', 3),
(2026, 1, N'CT4102', N'Đồ án chuyên ngành', 2),
(2026, 1, N'CT4103', N'Mẫu thiết kế', 3),
(2026, 1, N'CT4104', N'Phát triển ứng dụng game nâng cao', 3),
(2026, 1, N'CT4105', N'Kiểm thử phần mềm', 3),
(2026, 2, N'CT4201', N'Quản trị dự án Công nghệ Thông tin', 3),
(2026, 2, N'CT4202', N'Đồ án tốt nghiệp', 6),
(2026, 2, N'CT4203', N'Các phương pháp học máy', 3),
(2026, 2, N'CT4204', N'Phát triển ứng dụng mã nguồn mở', 3);

-- 5. Lặp để tạo dữ liệu tự động cho từng sinh viên
DECLARE @i INT = 1, @max_sv INT = (SELECT COUNT(*) FROM @SinhVien);
DECLARE @j INT, @max_mon INT = (SELECT COUNT(*) FROM @MonHoc);
DECLARE @curr_uid INT, @curr_mid INT;
DECLARE @sv_email NVARCHAR(100), @sv_name NVARCHAR(100), @sv_target VARCHAR(20), @sv_base FLOAT, @sv_fail INT;
DECLARE @m_nam INT, @m_hk INT, @m_ma NVARCHAR(20), @m_ten NVARCHAR(200), @m_tc INT;
DECLARE @rand_val INT, @cc DECIMAL(4,2), @gk DECIMAL(4,2), @ck DECIMAL(4,2), @loai_lan VARCHAR(20), @lan_hoc INT;

WHILE @i <= @max_sv
BEGIN
    SELECT @sv_name = ho_ten, @sv_email = email, @sv_target = muc_tieu, @sv_base = base_score, @sv_fail = fail_rate
    FROM @SinhVien WHERE id = @i;

    -- Thêm sinh viên (Dùng mật khẩu mã hoá chung của 'demo1234')
    INSERT INTO dbo.nguoi_dung (email, mat_khau_hash, ho_ten, nien_khoa_tu, nien_khoa_den, so_ky_moi_nam, thang_diem, muc_tieu)
    VALUES (@sv_email, '$2b$12$HSArfk/lPbnuuRR1ccDGjOjnV8f.LHNqMFnwOvuUWf1Hq.vkMkxHS', @sv_name, 2023, 2027, 2, 10, @sv_target);
    
    SET @curr_uid = SCOPE_IDENTITY();

    SET @j = 1;
    WHILE @j <= @max_mon
    BEGIN
        SELECT @m_nam = nam, @m_hk = hk, @m_ma = ma, @m_ten = ten, @m_tc = tc FROM @MonHoc WHERE id = @j;

        -- Tính xác suất ngẫu nhiên
        SET @rand_val = ABS(CHECKSUM(NEWID())) % 100;

        IF @rand_val < @sv_fail
        BEGIN
            -- Rớt môn / Cảnh báo học vụ
            SET @loai_lan = 'hoc_lai';
            SET @lan_hoc = 2;
            SET @cc = ROUND(4.0 + (ABS(CHECKSUM(NEWID())) % 25) / 10.0, 1);
            SET @gk = ROUND(2.0 + (ABS(CHECKSUM(NEWID())) % 25) / 10.0, 1);
            SET @ck = ROUND(1.0 + (ABS(CHECKSUM(NEWID())) % 25) / 10.0, 1);
        END
        ELSE
        BEGIN
            -- Học bình thường / Cải thiện
            IF @sv_base < 7.5 AND (ABS(CHECKSUM(NEWID())) % 100) < 8
            BEGIN
                SET @loai_lan = 'hoc_cai_thien';
                SET @lan_hoc = 2;
            END
            ELSE
            BEGIN
                SET @loai_lan = 'hoc_moi';
                SET @lan_hoc = 1;
            END

            -- Điểm thành phần phân bố quanh base_score
            SET @cc = ROUND(CASE WHEN @sv_base + 1.0 > 10.0 THEN 10.0 ELSE @sv_base + 1.0 - (ABS(CHECKSUM(NEWID())) % 10)/10.0 END, 1);
            SET @gk = ROUND(CASE WHEN @sv_base - 0.5 < 4.0 THEN 5.0 ELSE @sv_base - (ABS(CHECKSUM(NEWID())) % 15)/10.0 END, 1);
            SET @ck = ROUND(CASE WHEN @sv_base > 9.5 THEN 9.5 ELSE @sv_base + ((ABS(CHECKSUM(NEWID())) % 15) - 7)/10.0 END, 1);
            
            IF @cc > 10.0 SET @cc = 10.0; IF @cc < 5.0 SET @cc = 5.0;
            IF @gk > 10.0 SET @gk = 10.0; IF @gk < 4.0 SET @gk = 4.0;
            IF @ck > 10.0 SET @ck = 10.0; IF @ck < 4.0 SET @ck = 4.0;
        END

        INSERT INTO dbo.mon_hoc (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
        VALUES (@curr_uid, @m_nam, @m_hk, @m_ma, @m_ten, @m_tc, @lan_hoc, @loai_lan);
        
        SET @curr_mid = SCOPE_IDENTITY();

        INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
        (@curr_mid, @lt_cc, 10.00, @cc),
        (@curr_mid, @lt_gk, 30.00, @gk),
        (@curr_mid, @lt_ck, 60.00, @ck);

        SET @j = @j + 1;
    END

    SET @i = @i + 1;
END

PRINT N'==> TẠO DỮ LIỆU MẪU 10 SINH VIÊN THÀNH CÔNG!';

SELECT * FROM HT_CANHBAOHOCTAP.dbo.nguoi_dung;
SELECT * FROM HT_CANHBAOHOCTAP.dbo.mon_hoc;