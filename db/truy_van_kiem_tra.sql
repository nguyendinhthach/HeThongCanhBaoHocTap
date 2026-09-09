/* ============================================================================
   HT_CANHBAOHOCTAP — Truy vấn kiểm tra thủ công

   Không phải phần của hệ thống. Đây là các câu lệnh để mở SSMS xem nhanh dữ
   liệu đang có, hoặc đối chiếu khi nghi ngờ giao diện hiển thị sai.

   Câu lệnh đọc/ghi thật của ứng dụng nằm trong db/repo.py, vì chúng cần tham
   số động (user_id, mã môn, điểm...) mà một tệp .sql tĩnh không nhận được.

   Cách dùng: bôi đen đoạn cần chạy rồi nhấn F5. Các câu ở đây chỉ đọc, không
   sửa gì, chạy bao nhiêu lần cũng được.
   ============================================================================ */

USE HT_CANHBAOHOCTAP;
GO


/* --- Xem toàn bộ dữ liệu từng bảng --------------------------------------- */
SELECT * FROM dbo.nguoi_dung;
SELECT * FROM dbo.loai_thanh_phan ORDER BY thu_tu;
SELECT * FROM dbo.mon_hoc;
SELECT * FROM dbo.diem_thanh_phan;
SELECT * FROM dbo.du_doan_canh_bao;
SELECT * FROM dbo.du_doan_muc_tieu;
GO


/* --- Số dòng mỗi bảng ----------------------------------------------------- */
           SELECT 'nguoi_dung'       AS bang, COUNT(*) AS so_dong FROM dbo.nguoi_dung
UNION ALL  SELECT 'loai_thanh_phan',  COUNT(*) FROM dbo.loai_thanh_phan
UNION ALL  SELECT 'mon_hoc',          COUNT(*) FROM dbo.mon_hoc
UNION ALL  SELECT 'diem_thanh_phan',  COUNT(*) FROM dbo.diem_thanh_phan
UNION ALL  SELECT 'du_doan_canh_bao', COUNT(*) FROM dbo.du_doan_canh_bao
UNION ALL  SELECT 'du_doan_muc_tieu', COUNT(*) FROM dbo.du_doan_muc_tieu;
GO


/* --- Bảng điểm đầy đủ của một sinh viên ----------------------------------
   Ghép ba bảng lại thành dạng dễ đọc như bảng điểm giấy.
   -------------------------------------------------------------------------- */
SELECT  m.nam_bat_dau, m.hoc_ky, m.ma_mon, m.ten_mon, m.so_tin_chi,
        m.lan_hoc, m.loai_lan_hoc,
        l.ten AS thanh_phan, d.trong_so_phan_tram, d.diem
FROM        dbo.mon_hoc          m
JOIN        dbo.diem_thanh_phan  d ON d.mon_hoc_id         = m.id
JOIN        dbo.loai_thanh_phan  l ON l.id                 = d.loai_thanh_phan_id
JOIN        dbo.nguoi_dung       u ON u.id                 = m.user_id
WHERE   u.email = N'demo@dlu.edu.vn'
ORDER BY m.nam_bat_dau, m.hoc_ky, m.ma_mon, l.thu_tu;
GO


/* --- Điểm tổng kết và GPA từng học kỳ ------------------------------------
   Đây là câu dùng để ĐỐI CHIẾU với các thẻ chỉ số trên Dashboard. Cách tính
   phải khớp ui/rules.py: điểm mỗi môn làm tròn 1 chữ số TRƯỚC, rồi mới lấy
   trung bình có trọng số theo tín chỉ. Làm ngược lại sẽ ra số khác.

   Với dữ liệu mẫu, kết quả đúng phải là 6.58 / 6.26 / 7.07.
   -------------------------------------------------------------------------- */
WITH diem_mon AS (
    SELECT  m.id, m.nam_bat_dau, m.hoc_ky, m.ma_mon, m.ten_mon, m.so_tin_chi,
            ROUND(ROUND(SUM(d.trong_so_phan_tram * d.diem)
                      / SUM(d.trong_so_phan_tram), 2), 1) AS diem,
            SUM(d.trong_so_phan_tram) AS tong_trong_so
    FROM        dbo.mon_hoc         m
    JOIN        dbo.diem_thanh_phan d ON d.mon_hoc_id = m.id
    WHERE   d.diem IS NOT NULL          -- chỉ tính phần trọng số đã có điểm
    GROUP BY m.id, m.nam_bat_dau, m.hoc_ky, m.ma_mon, m.ten_mon, m.so_tin_chi
)
SELECT  nam_bat_dau, hoc_ky,
        COUNT(*)                                              AS so_mon,
        SUM(so_tin_chi)                                       AS tin_chi,
        CAST(SUM(diem * so_tin_chi) / SUM(so_tin_chi)
             AS DECIMAL(4,2))                                 AS gpa10,
        SUM(CASE WHEN diem < 4.0 THEN 1 ELSE 0 END)           AS mon_diem_e
FROM    diem_mon
GROUP BY nam_bat_dau, hoc_ky
ORDER BY nam_bat_dau, hoc_ky;
GO


/* --- Cấu trúc: quan hệ khoá ngoại giữa các bảng --------------------------
   Cho ra đúng sơ đồ quan hệ ghi ở cuối db/hethongcanhbao.sql — tiện chụp
   màn hình đưa vào báo cáo.
   -------------------------------------------------------------------------- */
SELECT  f.name                                  AS khoa_ngoai,
        OBJECT_NAME(f.parent_object_id)         AS bang_con,
        OBJECT_NAME(f.referenced_object_id)     AS bang_cha,
        f.delete_referential_action_desc        AS khi_xoa_ban_ghi_cha
FROM    sys.foreign_keys f
ORDER BY bang_con;
GO


/* --- Cấu trúc: cột của một bảng ------------------------------------------ */
SELECT  COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
        NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_DEFAULT
FROM    INFORMATION_SCHEMA.COLUMNS
WHERE   TABLE_NAME = 'mon_hoc'          -- đổi tên bảng ở đây
ORDER BY ORDINAL_POSITION;
GO
