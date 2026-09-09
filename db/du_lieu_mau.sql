/* ============================================================================
   HT_CANHBAOHOCTAP — Dữ liệu mẫu

   Sinh tự động từ ui/data.py (hàm seed_courses) — CHÍNH LÀ bộ dữ liệu tĩnh đã
   dùng lúc dựng giao diện. Giữ nguyên từng con số để sau khi chuyển sang đọc
   từ cơ sở dữ liệu, các chỉ số trên màn hình phải ra y hệt trước đó; lệch chỗ
   nào là biết ngay chỗ đó sai.

   Chạy SAU khi đã chạy db/hethongcanhbao.sql.
     sqlcmd -S localhost -E -i db\du_lieu_mau.sql

   Chạy lại nhiều lần được: xoá tài khoản demo cũ rồi nạp lại từ đầu.
   ============================================================================ */

USE HT_CANHBAOHOCTAP;
GO

/* Xoá tài khoản demo cũ nếu có. Khoá ngoại ON DELETE CASCADE sẽ tự xoá theo
   toàn bộ môn học, điểm thành phần và các bản dự đoán của tài khoản này. */
DELETE FROM dbo.nguoi_dung WHERE email = N'demo@dlu.edu.vn';
GO

DECLARE @uid INT, @mid INT;
DECLARE @lt_cc INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'chuyen_can');
DECLARE @lt_gk INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'giua_ky');
DECLARE @lt_ck INT = (SELECT id FROM dbo.loai_thanh_phan WHERE ma = 'cuoi_ky');

/* Tài khoản demo. Mật khẩu để dạng chuỗi thay thế, KHÔNG phải hash thật —
   sẽ sinh hash bcrypt đúng khi làm chức năng đăng nhập. Chuỗi này không khớp
   với bất kỳ mật khẩu nào nên không đăng nhập được, đó là chủ ý.
   Dùng email demo thay vì email thật của nhóm vì tệp này nằm trên GitHub. */
INSERT INTO dbo.nguoi_dung
    (email, mat_khau_hash, ho_ten, nien_khoa_tu, nien_khoa_den,
     so_ky_moi_nam, thang_diem, muc_tieu)
VALUES
    (N'demo@dlu.edu.vn', 'CHUA_CO_HASH_BCRYPT', N'Sinh viên Demo',
     2023, 2027, 2, 10, 'kha');
SET @uid = SCOPE_IDENTITY();

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2024, 2, N'20CT3101', N'Công nghệ phần mềm', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 8.10),
    (@mid, @lt_gk, 30.00, 6.60),
    (@mid, @lt_ck, 60.00, 7.20);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2024, 2, N'20CT2203', N'Mạng máy tính', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 7.00),
    (@mid, @lt_gk, 30.00, 5.50),
    (@mid, @lt_ck, 60.00, 6.10);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2024, 2, N'20TN1301', N'Xác suất thống kê', 3, 2, 'hoc_lai');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 5.80),
    (@mid, @lt_gk, 30.00, 4.30),
    (@mid, @lt_ck, 60.00, 4.90);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2024, 2, N'20CT2301', N'Lập trình web', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 9.40),
    (@mid, @lt_gk, 30.00, 7.90),
    (@mid, @lt_ck, 60.00, 8.50);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2025, 1, N'20CT3201', N'Trí tuệ nhân tạo', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 6.40),
    (@mid, @lt_gk, 30.00, 4.90),
    (@mid, @lt_ck, 60.00, 5.50);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2025, 1, N'20CT3202', N'Lập trình Python nâng cao', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 8.80),
    (@mid, @lt_gk, 30.00, 7.30),
    (@mid, @lt_ck, 60.00, 7.90);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2025, 1, N'20CT3203', N'Cơ sở dữ liệu phân tán', 3, 2, 'hoc_lai');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 5.20),
    (@mid, @lt_gk, 30.00, 3.70),
    (@mid, @lt_ck, 60.00, 4.30);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2025, 1, N'20CT3204', N'Kiểm thử phần mềm', 2, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 7.50),
    (@mid, @lt_gk, 30.00, 6.00),
    (@mid, @lt_ck, 60.00, 6.60);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2025, 1, N'20CT2104', N'Tiếng Anh chuyên ngành 2', 2, 2, 'hoc_cai_thien');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 9.10),
    (@mid, @lt_gk, 30.00, 7.60),
    (@mid, @lt_ck, 60.00, 8.20);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2026, 1, N'20CT4901', N'Đồ án tốt nghiệp', 6, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 8.50),
    (@mid, @lt_gk, 30.00, 7.00),
    (@mid, @lt_ck, 60.00, 7.60);

INSERT INTO dbo.mon_hoc
    (user_id, nam_bat_dau, hoc_ky, ma_mon, ten_mon, so_tin_chi, lan_hoc, loai_lan_hoc)
VALUES (@uid, 2026, 1, N'20CT4201', N'Học máy ứng dụng', 3, 1, 'hoc_moi');
SET @mid = SCOPE_IDENTITY();
INSERT INTO dbo.diem_thanh_phan (mon_hoc_id, loai_thanh_phan_id, trong_so_phan_tram, diem) VALUES
    (@mid, @lt_cc, 10.00, 7.20),
    (@mid, @lt_gk, 30.00, 5.70),
    (@mid, @lt_ck, 60.00, 6.30);

GO

PRINT N'Đã nạp xong dữ liệu mẫu.';
GO
