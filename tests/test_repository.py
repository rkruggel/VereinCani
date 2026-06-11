"""Tests für die Sortierlogik des Popels-Repositorys."""

import unittest

from src.popelsapp.repository import sort_records, sortable_name


class SortRecordsTest(unittest.TestCase):
	def setUp(self) -> None:
		self.records = [
			{'id': '1', 'name': 'Anna Müller'},
			{'id': '2', 'name': 'Clara Schmidt'},
			{'id': '3', 'name': 'Berta Müller'},
			{'id': '4', 'name': 'Madonna'},
			{'id': '5', 'name': 'Karl Heinz Schmidt'},
		]

	def test_name_ascending_uses_last_part_then_first_parts(self) -> None:
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
		records = [
			{'hundename': 'Zora'},
			{'hundename': 'Alma'},
		]

		result = sort_records(records, ['hundename:asc'], ['hundename'])

		self.assertEqual([record['hundename'] for record in result], ['Alma', 'Zora'])

	def test_name_split_uses_last_part_as_last_name(self) -> None:
		self.assertEqual(sortable_name('  Karl   Heinz Schmidt  '), ('schmidt', 'karl heinz'))
		self.assertEqual(sortable_name('Madonna'), ('madonna', ''))
		self.assertEqual(sortable_name(''), ('', ''))


if __name__ == '__main__':
	unittest.main()
