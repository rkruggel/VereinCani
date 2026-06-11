"""Tests für Formularberechnungen."""

import unittest
from unittest.mock import patch

from src.services.calc import berechne, preisNachHunden


class CalcTest(unittest.TestCase):
	def test_preis_nach_hunden_uses_published_prestamm_price(self) -> None:
		with patch('src.services.calc.PREISSTAMM.get_price', return_value='25.00') as get_price:
			self.assertEqual(preisNachHunden(['hund/1', 'hund/2', 'hund/3']), '25.00')
			get_price.assert_called_once_with(3)

	def test_preis_nach_hunden_returns_empty_for_none_or_unknown_count(self) -> None:
		self.assertEqual(preisNachHunden([]), '')
		with patch('src.services.calc.PREISSTAMM.get_price', side_effect=ValueError):
			self.assertEqual(preisNachHunden(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']), '')

	def test_berechne_supports_preis_nach_hunden_formula(self) -> None:
		with patch('src.services.calc.PREISSTAMM.get_price', return_value='10.00'):
			self.assertEqual(
				berechne('preisNachHunden(hunde)', {'hunde': ['hund/1']}),
				'10.00',
			)


if __name__ == '__main__':
	unittest.main()
