import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

THU_MUC_GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(THU_MUC_GOC / "ml"))

from db import repo_canh_bao as repo
from dich_vu import du_doan, tac_vu_canh_bao


class TacVuCanhBaoTests(unittest.TestCase):
    def test_gui_hang_doi_email_danh_dau_thanh_cong_va_that_bai(self):
        emails = [
            {"id": 1, "den": "a@example.test", "tieu_de": "a", "noi_dung": "a"},
            {"id": 2, "den": "b@example.test", "tieu_de": "b", "noi_dung": "b"},
        ]
        trang_thai = []

        def gui(den, *_):
            if den == "b@example.test":
                raise OSError("SMTP không kết nối")

        with patch.object(repo, "email_den_han", return_value=emails), \
                patch.object(tac_vu_canh_bao, "gui_email", side_effect=gui), \
                patch.object(repo, "danh_dau_da_gui",
                             side_effect=lambda email_id: trang_thai.append(("gui", email_id))), \
                patch.object(repo, "danh_dau_loi",
                             side_effect=lambda email_id, loi: trang_thai.append(("loi", email_id, loi))), \
                self.assertLogs("dich_vu.tac_vu_canh_bao", level="ERROR"):
            self.assertEqual(tac_vu_canh_bao.gui_hang_doi_email(), 1)

        self.assertEqual(trang_thai[0], ("gui", 1))
        self.assertEqual(trang_thai[1][0:2], ("loi", 2))
        self.assertIn("SMTP không kết nối", trang_thai[1][2])

    def test_nhac_theo_moc_xep_lan_hai_sau_bay_ngay_va_bo_qua_moc_chua_co_ngay(self):
        with tempfile.TemporaryDirectory() as thu_muc:
            tep_moc = Path(thu_muc) / "moc_hoc_ky.json"
            tep_moc.write_text(json.dumps([
                {"moc": "HK1 giữa kỳ", "loai": "nhac_giua_ky", "bat_dau": "2026-10-01"},
                {"moc": "HK1 sau thi", "loai": "nhac_cuoi_ky", "bat_dau": None},
            ]), encoding="utf-8")
            duoc_xep = []

            def them_email(*args, **kwargs):
                duoc_xep.append((args[0], kwargs["moc"], kwargs["lan_nhac"]))
                return len(duoc_xep)

            with patch.object(tac_vu_canh_bao.cau_hinh, "file_moc_hoc_ky", return_value=str(tep_moc)), \
                    patch.object(repo, "nguoi_chua_cap_nhat_tu", return_value=[7]), \
                    patch.object(repo, "them_email", side_effect=them_email):
                so_luong = tac_vu_canh_bao.nhac_theo_moc(date(2026, 10, 8))

        self.assertEqual(so_luong, 2)
        self.assertEqual(duoc_xep, [(7, "HK1 giữa kỳ", 1), (7, "HK1 giữa kỳ", 2)])

    def test_nhac_theo_moc_khong_xep_truoc_ngay_bat_dau(self):
        with tempfile.TemporaryDirectory() as thu_muc:
            tep_moc = Path(thu_muc) / "moc_hoc_ky.json"
            tep_moc.write_text(json.dumps([
                {"moc": "HK1 giữa kỳ", "loai": "nhac_giua_ky", "bat_dau": "2026-10-01"},
            ]), encoding="utf-8")
            with patch.object(tac_vu_canh_bao.cau_hinh, "file_moc_hoc_ky", return_value=str(tep_moc)), \
                    patch.object(repo, "nguoi_chua_cap_nhat_tu") as truy_van:
                self.assertEqual(tac_vu_canh_bao.nhac_theo_moc(date(2026, 9, 30)), 0)

        truy_van.assert_not_called()

    def test_du_doan_lai_cho_tat_ca_khi_phien_ban_toan_cuc_khac(self):
        da_chay = []
        with patch.object(du_doan, "goi_mo_hinh", return_value={"thoi_diem": "2026-10-01"}), \
                patch.object(repo, "phien_ban_mo_hinh_gan_nhat", return_value="2026-09-01"), \
                patch.object(repo, "lan_cap_nhat_moi_nhat_moi_nguoi", return_value=[(1, 11), (2, 22)]), \
                patch.object(du_doan, "chay", side_effect=lambda user_id: da_chay.append(user_id)):
            so_luong = tac_vu_canh_bao.du_doan_lai_khi_co_mo_hinh_moi()

        self.assertEqual(so_luong, 2)
        self.assertEqual(da_chay, [1, 2])

    def test_du_doan_lai_bu_nguoi_dung_con_lai_sau_that_bai_giua_chung(self):
        da_chay = []

        def ket_qua_moi_nhat(user_id):
            phien_ban = "2026-10-01" if user_id == 1 else "2026-09-01"
            return {"canh_bao": {"phien_ban_mo_hinh": phien_ban}}

        with patch.object(du_doan, "goi_mo_hinh", side_effect=lambda _: {"thoi_diem": "2026-10-01"}), \
                patch.object(repo, "phien_ban_mo_hinh_gan_nhat", side_effect=["2026-09-01", "2026-10-01"]), \
                patch.object(repo, "lan_cap_nhat_moi_nhat_moi_nguoi", return_value=[(1, 11), (2, 22)]), \
                patch.object(repo, "ket_qua_moi_nhat", side_effect=ket_qua_moi_nhat), \
                patch.object(du_doan, "chay", side_effect=[None, OSError("lỗi mô hình")]) as chay:
            with self.assertLogs("dich_vu.tac_vu_canh_bao", level="ERROR"):
                with self.assertRaisesRegex(RuntimeError, "user_id: \\[2\\]"):
                    tac_vu_canh_bao.du_doan_lai_khi_co_mo_hinh_moi()

            chay.side_effect = lambda user_id: da_chay.append(user_id)
            so_luong = tac_vu_canh_bao.du_doan_lai_khi_co_mo_hinh_moi()

        self.assertEqual(so_luong, 1)
        self.assertEqual(da_chay, [2])

    def test_khong_chay_lai_lien_tuc_khi_phien_ban_hai_model_khac_nhau(self):
        goi_mo_hinh = {
            "canh_bao": {"thoi_diem": "2026-10-01"},
            "truot_mon": {"thoi_diem": "2026-10-02"},
        }
        ket_qua = {
            "canh_bao": {"phien_ban_mo_hinh": "2026-10-01"},
            "truot_mon": [{"phien_ban_mo_hinh": "2026-10-02"}],
        }
        with patch.object(du_doan, "goi_mo_hinh", side_effect=lambda muc_tieu: goi_mo_hinh[muc_tieu]), \
                patch.object(repo, "phien_ban_mo_hinh_gan_nhat", return_value="2026-10-02"), \
                patch.object(repo, "lan_cap_nhat_moi_nhat_moi_nguoi", return_value=[(1, 11)]), \
                patch.object(repo, "ket_qua_moi_nhat", return_value=ket_qua), \
                patch.object(du_doan, "chay") as chay:
            self.assertEqual(tac_vu_canh_bao.du_doan_lai_khi_co_mo_hinh_moi(), 0)

        chay.assert_not_called()

    def test_nhac_theo_moc_bao_loi_neu_ngay_khong_dung_dinh_dang(self):
        with tempfile.TemporaryDirectory() as thu_muc:
            tep_moc = Path(thu_muc) / "moc_hoc_ky.json"
            tep_moc.write_text(json.dumps([
                {"moc": "HK1 giữa kỳ", "loai": "nhac_giua_ky", "bat_dau": "ngay-khong-hop-le"},
            ]), encoding="utf-8")
            with patch.object(tac_vu_canh_bao.cau_hinh, "file_moc_hoc_ky", return_value=str(tep_moc)):
                with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                    tac_vu_canh_bao.nhac_theo_moc(date(2026, 10, 8))


if __name__ == "__main__":
    unittest.main()
