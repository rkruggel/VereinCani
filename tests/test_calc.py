"""
Tests für Formularberechnungen.
"""
import unittest
from unittest.mock import patch

from src.services.calc import berechne, kassenDiff, preisNachHunden


class CalcTest(unittest.TestCase):
	"""
	Bündelt Tests für die Formularberechnungen.
	"""
	def test_preis_nach_hunden_uses_published_prestamm_price(self) -> None:
		"""
		Prüft den Testfall: preis nach hunden uses published prestamm price.
		"""
		with patch('src.services.calc.PREISSTAMM.get_price', return_value='25.00') as get_price:
			self.assertEqual(preisNachHunden(['hund/1', 'hund/2', 'hund/3']), '25.00')
			get_price.assert_called_once_with(3)

	def test_preis_nach_hunden_returns_empty_for_none_or_unknown_count(self) -> None:
		"""
		Prüft den Testfall: preis nach hunden returns empty for none or unknown count.
		"""
		self.assertEqual(preisNachHunden([]), '')
		with patch('src.services.calc.PREISSTAMM.get_price', side_effect=ValueError):
			self.assertEqual(preisNachHunden(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']), '')

	def test_berechne_supports_preis_nach_hunden_formula(self) -> None:
		"""
		Prüft den Testfall: berechne supports preis nach hunden formula.
		"""
		with patch('src.services.calc.PREISSTAMM.get_price', return_value='10.00'):
			self.assertEqual(
				berechne('preisNachHunden(hunde)', {'hunde': ['hund/1']}),
				'10.00',
			)

	def test_berechne_supports_int_diff_formula(self) -> None:
		"""
		Prüft den Testfall: berechne supports int diff formula.
		"""
		self.assertEqual(
			berechne('intDiff(gewichtSoll, gewicht)', {'gewichtSoll': '28', 'gewicht': '25'}),
			3,
		)

	def test_kassen_diff_calculates_cash_formula(self) -> None:
		"""
		Prüft den Testfall: kassen diff calculates cash formula.
		"""
		self.assertEqual(kassenDiff('100,50', '20', '5.25', '2,75'), '83.00')
		self.assertEqual(
			berechne(
				'kassenDiff(einnahme, ausgabe, einnahmenC24, ausgabenC24)',
				{
					'einnahme': '100',
					'ausgabe': '25',
					'einnahmenC24': '10',
					'ausgabenC24': '5',
				},
			),
			'80.00',
		)

	def test_berechne_supports_gewicht_ok_formula(self) -> None:
		"""
		Prüft den Testfall: berechne supports gewicht ok formula.
		"""
		self.assertEqual(
			berechne('gewichtOk(gewichtSoll, gewicht)', {'gewichtSoll': '28', 'gewicht': '28'}),
			'Ja',
		)
		self.assertEqual(
			berechne('gewichtOk(gewichtSoll, gewicht)', {'gewichtSoll': '28', 'gewicht': '25'}),
			'Nein',
		)


if __name__ == '__main__':
	unittest.main()
