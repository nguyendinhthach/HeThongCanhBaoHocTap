"""Tầng dữ liệu: kết nối SQL Server và các hàm đọc/ghi.

Giao diện không viết câu lệnh SQL nào — chỉ gọi hàm trong db/repo.py. Nhờ vậy
đổi tên cột hay đổi hệ quản trị chỉ phải sửa ở đây, và tác vụ định kỳ với API
sau này dùng lại đúng các hàm đó thay vì chép lại truy vấn.
"""
