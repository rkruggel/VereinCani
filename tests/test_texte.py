"""Tests für Texte-Hilfsfunktionen."""

import unittest

from src.pages.texte.start import normalize_group_options


class TexteTest(unittest.TestCase):
	def test_normalize_group_options_removes_empty_and_duplicate_values(self) -> None:
		self.assertEqual(
			normalize_group_options([' Verein ', '', 'verein', 'Training']),
			['Training', 'Verein'],
		)


if __name__ == '__main__':
	unittest.main()
