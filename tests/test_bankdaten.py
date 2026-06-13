"""
Tests für Bankdaten-Hilfsfunktionen.
"""
import unittest

from src.pages.bankdaten.start import embedded_bankdata_document, format_bankdaten_summary


class BankdatenTest(unittest.TestCase):
	"""
	Bündelt Tests für Bankdaten-Hilfsfunktionen.
	"""
	def test_format_bankdaten_summary_joins_present_fields(self) -> None:
		"""
		Prüft den Testfall: format bankdaten summary joins present fields.
		"""
		self.assertEqual(
			format_bankdaten_summary({
				'kreditinstitut': 'Musterbank',
				'iban': 'DE89 3704 0044 0532 0130 00',
				'mandat': '',
			}),
			'Musterbank / DE89 3704 0044 0532 0130 00',
		)

	def test_embedded_bankdata_document_keeps_bankdata_fields(self) -> None:
		"""
		Prüft den Testfall: embedded bankdata document keeps bankdata fields.
		"""
		self.assertEqual(
			embedded_bankdata_document({
				'id': 'bankdaten/1',
				'mitglied': 'mitglieder/1',
				'kontoinhaber': 'Anna Alt',
				'kreditinstitut': '',
				'iban': 'DE89 3704 0044 0532 0130 00',
				'mandat': '2026-01-01',
			}),
			{
				'iban': 'DE89 3704 0044 0532 0130 00',
				'mandat': '2026-01-01',
			},
		)


if __name__ == '__main__':
	unittest.main()
