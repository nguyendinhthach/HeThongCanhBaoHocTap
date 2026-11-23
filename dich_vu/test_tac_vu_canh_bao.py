import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
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

    HK1 = {"hoc_ky": "HK1 2026–2027", "nam_bat_dau": 2026, "ky": 1,
           "nhac_giua_ky": "2026-10-15", "nhac_sau_thi": "2027-01-10"}

    def _chay_nhac(self, hom_nay, moc=None, nguoi=(7,), them_email=None):
        """Chạy nhac_theo_moc với file mốc tạm (mặc định chỉ HK1 2026–2027).
        Trả (số đã xếp, [(user_id, loai, moc, lan_nhac)]); self.truy_van = lời gọi
        nguoi_chua_nhap_xong."""
        with tempfile.TemporaryDirectory() as thu_muc:
            tep_moc = Path(thu_muc) / "moc_hoc_ky.json"
            tep_moc.write_text(json.dumps(moc or [self.HK1]), encoding="utf-8")
            duoc_xep = []

            def ghi(user_id, loai, *_, **kwargs):
                duoc_xep.append((user_id, loai, kwargs["moc"], kwargs["lan_nhac"]))
                return len(duoc_xep)

            with patch.object(tac_vu_canh_bao.cau_hinh, "file_moc_hoc_ky", return_value=str(tep_moc)),                     patch.object(repo, "nguoi_chua_nhap_xong", return_value=list(nguoi)) as truy_van,                     patch.object(repo, "them_email", side_effect=them_email or ghi):
                so_luong = tac_vu_canh_bao.nhac_theo_moc(hom_nay)
        self.truy_van = truy_van
        return so_luong, duoc_xep

    def test_nhac_dung_5_lan_moi_hoc_ky_va_dung_ngay(self):
        da_xep, ngay_xep = set(), []

        def them_email(user_id, loai, *_, moc, lan_nhac, **__):
            if (loai, moc, lan_nhac) in da_xep:
                return None                                   # trùng: chỉ mục UX_edg_moc chặn
            da_xep.add((loai, moc, lan_nhac))
            ngay_xep.append((ngay, loai, moc, lan_nhac))
            return len(da_xep)

        ngay = date(2026, 9, 1)
        while ngay < date(2027, 3, 1):
            self._chay_nhac(ngay, them_email=them_email)
            ngay += timedelta(days=1)
        self.assertEqual(ngay_xep, [
            (date(2026, 10, 15), "nhac_giua_ky", "HK1 2026–2027 giữa kỳ", 1),
            (date(2026, 10, 30), "nhac_giua_ky", "HK1 2026–2027 giữa kỳ", 2),
            (date(2026, 11, 14), "nhac_giua_ky", "HK1 2026–2027 giữa kỳ", 3),
            (date(2027, 1, 10), "nhac_cuoi_ky", "HK1 2026–2027 sau thi", 1),
            (date(2027, 1, 25), "nhac_cuoi_ky", "HK1 2026–2027 sau thi", 2),
        ])

    def test_nhac_khong_xep_ngoai_3_ngay_dau_moi_lan(self):
        # nửa đầu kỳ, giữa hai lần, sau lần giữa kỳ thứ 3, sau lần sau thi thứ 2; 23/11 = hôm nay
        for ngay in (date(2026, 10, 14), date(2026, 10, 18), date(2026, 11, 23),
                     date(2026, 11, 29), date(2027, 2, 9)):
            self.assertEqual(self._chay_nhac(ngay), (0, []), ngay)
            self.truy_van.assert_not_called()
        # máy chủ tắt ngày 15/10 -> 17/10 vẫn bù lần 1
        self.assertEqual(self._chay_nhac(date(2026, 10, 17))[1],
                         [(7, "nhac_giua_ky", "HK1 2026–2027 giữa kỳ", 1)])

    def test_nhac_giua_ky_xet_diem_gk_sau_thi_xet_tong_ket_hoc_ky(self):
        self._chay_nhac(date(2026, 10, 30))
        self.truy_van.assert_called_once_with(2026, 1, datetime(2026, 10, 15), True)
        self._chay_nhac(date(2027, 1, 25))
        self.truy_van.assert_called_once_with(2026, 1, datetime(2027, 1, 10), False)

    def test_nhac_bo_qua_nguoi_da_xong_va_email_trung(self):
        self.assertEqual(self._chay_nhac(date(2026, 10, 15), nguoi=[]), (0, []))
        self.assertEqual(self._chay_nhac(date(2026, 10, 16), nguoi=[7, 8],
                                         them_email=lambda *a, **k: None), (0, []))

    def test_nhac_bao_loi_cau_hinh_sai(self):
        sai = [
            {**self.HK1, "nhac_giua_ky": "ngay-khong-hop-le"},
            {**self.HK1, "nhac_sau_thi": None},
            {**self.HK1, "nhac_sau_thi": "2026-11-20"},       # chồng lên 3 lần nhắc giữa kỳ
            {**self.HK1, "ky": 4},
        ]
        for hk in sai:
            with self.assertRaises(ValueError, msg=hk):
                self._chay_nhac(date(2026, 10, 15), moc=[hk])

    def test_file_moc_hoc_ky_that_hop_le(self):
        self.assertEqual(len(tac_vu_canh_bao._doc_moc_hoc_ky()), 2)

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


if __name__ == "__main__":
    unittest.main()
