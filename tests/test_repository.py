"""
Tests für die Sortierlogik des Popels-Repositorys.
"""
import unittest

from src.pages.kasse.start import CONFIG as KASSE_CONFIG, Kassenbuchung
from src.popelsapp.repository import normalize_bankdata_value, normalize_euro_value, normalize_iban_value, sort_records, sortable_name
from src.popelsapp.repository import CouchPopelsDatabase


class SortRecordsTest(unittest.TestCase):
	"""
	Bündelt Tests für Sortierung und Normalisierung im Repository.
	"""
	def setUp(self) -> None:
		"""
		Bereitet gemeinsame Testdaten für die folgenden Tests vor.
		"""
		self.records = [
			{'id': '1', 'name': 'Anna Müller'},
			{'id': '2', 'name': 'Clara Schmidt'},
			{'id': '3', 'name': 'Berta Müller'},
			{'id': '4', 'name': 'Madonna'},
			{'id': '5', 'name': 'Karl Heinz Schmidt'},
		]

	def test_name_ascending_uses_last_part_then_first_parts(self) -> None:
		"""
		Prüft den Testfall: name ascending uses last part then first parts.
		"""
		result = sort_records(self.records, ['name:asc'], ['name'])

		self.assertEqual(
			[record['name'] for record in result],
			[
				'Madonna',
				'Anna Müller',
				'Berta Müller',
				'Clara Schmidt',
				'Karl Heinz Schmidt',
			],
		)

	def test_name_descending_reverses_last_and_first_name_order(self) -> None:
		"""
		Prüft den Testfall: name descending reverses last and first name order.
		"""
		result = sort_records(self.records, ['name:desc'], ['name'])

		self.assertEqual(
			[record['name'] for record in result],
			[
				'Karl Heinz Schmidt',
				'Clara Schmidt',
				'Berta Müller',
				'Anna Müller',
				'Madonna',
			],
		)

	def test_other_fields_keep_the_standard_sorting(self) -> None:
		"""
		Prüft den Testfall: other fields keep the standard sorting.
		"""
		records = [
			{'hundename': 'Zora'},
			{'hundename': 'Alma'},
		]

		result = sort_records(records, ['hundename:asc'], ['hundename'])

		self.assertEqual([record['hundename'] for record in result], ['Alma', 'Zora'])

	def test_name_split_uses_last_part_as_last_name(self) -> None:
		"""
		Prüft den Testfall: name split uses last part as last name.
		"""
		self.assertEqual(sortable_name('  Karl   Heinz Schmidt  '), ('schmidt', 'karl heinz'))
		self.assertEqual(sortable_name('Madonna'), ('madonna', ''))
		self.assertEqual(sortable_name(''), ('', ''))

	def test_normalize_iban_groups_uppercase_value(self) -> None:
		"""
		Prüft den Testfall: normalize iban groups uppercase value.
		"""
		self.assertEqual(
			normalize_iban_value('de89 3704-0044 0532 0130 00'),
			'DE89 3704 0044 0532 0130 00',
		)

	def test_normalize_euro_value_accepts_comma_and_currency_symbol(self) -> None:
		"""
		Prüft den Testfall: normalize euro value accepts comma and currency symbol.
		"""
		self.assertEqual(normalize_euro_value('12,5 €'), '12.50')
		self.assertEqual(normalize_euro_value(''), '')

	def test_normalize_bankdata_value_keeps_embedded_document_shape(self) -> None:
		"""
		Prüft den Testfall: normalize bankdata value keeps embedded document shape.
		"""
		self.assertEqual(
			normalize_bankdata_value({
				'id': 'bankdaten/1',
				'mitglied': 'mitglieder/1',
				'kontoinhaber': 'Anna Alt',
				'kreditinstitut': 'Musterbank',
				'iban': 'de89370400440532013000',
				'mandat': '',
			}),
			{
				'kreditinstitut': 'Musterbank',
				'iban': 'DE89 3704 0044 0532 0130 00',
			},
		)

	def test_normalized_kasse_document_contains_calculated_diff(self) -> None:
		"""
		Prüft den Testfall: normalized kasse document contains calculated diff.
		"""
		database = CouchPopelsDatabase(KASSE_CONFIG, Kassenbuchung)

		record = database._normalize_document({  # pylint: disable=protected-access
			'_id': 'kasse/1',
			'einnahme': '100',
			'ausgabe': '20',
			'einnahmenC24': '5',
			'ausgabenC24': '2',
		})

		self.assertEqual(record['diff'], '83.00')


if __name__ == '__main__':
	unittest.main()
