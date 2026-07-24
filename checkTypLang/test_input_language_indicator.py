import unittest

from input_language_indicator import language_label, tray_image


class LanguageLabelTest(unittest.TestCase):
    def test_known_languages(self):
        self.assertEqual(language_label(0x0412), "한")
        self.assertEqual(language_label(0x0412, True), "한")
        self.assertEqual(language_label(0x0412, False), "EN")
        self.assertEqual(language_label(0x0409), "EN")
        self.assertEqual(language_label(0x0411), "日")
        self.assertEqual(language_label(0x0804), "中")

    def test_unknown_language_uses_identifier(self):
        self.assertEqual(language_label(0x0436), "0436")

    def test_tray_icon_size(self):
        self.assertEqual(tray_image("한").size, (64, 64))


if __name__ == "__main__":
    unittest.main()
