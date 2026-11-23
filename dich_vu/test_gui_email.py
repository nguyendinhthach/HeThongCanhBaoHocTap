import unittest
from unittest.mock import patch

from dich_vu import cau_hinh, gui_email


class GuiEmailTests(unittest.TestCase):
    def test_gui_email_uses_configured_smtp_and_tls(self):
        cau_hinh_smtp = {
            "host": "smtp.example.test", "port": 587, "user": "team@example.test",
            "mat_khau": "app-password", "tu": "alerts@example.test",
        }
        with patch.object(cau_hinh, "smtp", return_value=cau_hinh_smtp), \
                patch.object(gui_email.smtplib, "SMTP") as smtp_factory:
            smtp = smtp_factory.return_value.__enter__.return_value

            gui_email.gui_email("student@example.test", "Tiêu đề", "Nội dung")

            smtp_factory.assert_called_once_with("smtp.example.test", 587, timeout=20)
            smtp.starttls.assert_called_once()
            smtp.login.assert_called_once_with("team@example.test", "app-password")
            thu = smtp.send_message.call_args.args[0]
            self.assertEqual(thu["To"], "student@example.test")
            self.assertEqual(thu["Subject"], "Tiêu đề")
            self.assertEqual(thu.get_content().strip(), "Nội dung")

    def test_gui_email_reports_missing_credentials(self):
        cau_hinh_smtp = {
            "host": "smtp.example.test", "port": 587, "user": "", "mat_khau": "", "tu": "",
        }
        with patch.object(cau_hinh, "smtp", return_value=cau_hinh_smtp), \
                patch.object(gui_email.smtplib, "SMTP") as smtp_factory:
            with self.assertRaisesRegex(RuntimeError, "HT_SMTP_USER"):
                gui_email.gui_email("student@example.test", "Tiêu đề", "Nội dung")

            smtp_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
