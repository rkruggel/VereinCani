"""Tests für Speicherung und Normalisierung des Preisstamms."""

import unittest

from src.pages.preise.preisstamm import (
	PREISSTAMM_COLLECTION,
	PREISSTAMM_ID,
	PreisstammRepository,
	number_input_value,
	normalize_course_interval,
	normalize_courses,
	normalize_price,
	normalize_valid_from,
	prices_from_document,
)


class FakeDatabase:
	def __init__(self) -> None:
		self.document = None
		self.saved = None

	def get_document(self, document_id: str):
		self.asserted_document_id = document_id
		return self.document

	def put_document(self, document_id: str, data: dict, collection: str) -> None:
		self.saved = (document_id, data, collection)


class PreisstammTest(unittest.TestCase):
	def test_normalize_price_accepts_german_decimal_separator(self) -> None:
		self.assertEqual(normalize_price('12,5'), '12.50')
		self.assertEqual(normalize_price('0 €'), '0.00')

	def test_normalize_price_rejects_missing_and_negative_values(self) -> None:
		with self.assertRaises(ValueError):
			normalize_price('')
		with self.assertRaises(ValueError):
			normalize_price('-1')

	def test_normalize_valid_from_requires_iso_date(self) -> None:
		self.assertEqual(normalize_valid_from('2026-07-01'), '2026-07-01')
		with self.assertRaises(ValueError):
			normalize_valid_from('')
		with self.assertRaises(ValueError):
			normalize_valid_from('01.07.2026')

	def test_save_writes_all_five_prices_to_fixed_document(self) -> None:
		database = FakeDatabase()
		repository = PreisstammRepository(database)

		repository.save(
			{count: str(count) for count in range(1, 6)},
			'2026-07-01',
			[
				{'kurs': 'Welpenkurs', 'preis': '12,5', 'dauer': '60', 'einheit': 'woche'},
			],
		)

		document_id, data, collection = database.saved
		self.assertEqual(document_id, PREISSTAMM_ID)
		self.assertEqual(collection, PREISSTAMM_COLLECTION)
		self.assertEqual(data['gueltig_ab'], '2026-07-01')
		self.assertEqual(data['hundepreise']['1'], '1.00')
		self.assertEqual(data['hundepreise']['5'], '5.00')
		self.assertEqual(len(data['hundepreise']), 5)
		self.assertEqual(data['kurse'], [
			{'kurs': 'Welpenkurs', 'preis': '12.50', 'dauer': '60', 'einheit': 'Woche'},
		])

	def test_get_fills_missing_prices(self) -> None:
		database = FakeDatabase()
		database.document = {'hundepreise': {'1': '10.00'}}

		prices = PreisstammRepository(database).get()

		self.assertEqual(prices[1], '10.00')
		self.assertEqual(prices[5], '')
		self.assertEqual(len(prices), 5)

	def test_prices_from_document_normalizes_german_decimal_separator(self) -> None:
		prices = prices_from_document({'hundepreise': {'1': '12,50'}})

		self.assertEqual(prices[1], '12.50')
		self.assertIsNone(number_input_value(''))
		self.assertEqual(number_input_value('12,50'), 12.5)

	def test_get_valid_from_supports_existing_documents_without_date(self) -> None:
		database = FakeDatabase()
		repository = PreisstammRepository(database)

		self.assertEqual(repository.get_valid_from(), '')
		database.document = {'gueltig_ab': '2026-07-01'}
		self.assertEqual(repository.get_valid_from(), '2026-07-01')

	def test_get_courses_supports_existing_documents_without_courses(self) -> None:
		database = FakeDatabase()
		repository = PreisstammRepository(database)

		self.assertEqual(repository.get_courses(), [])
		database.document = {
			'kurse': [
				{'kurs': 'Junghunde', 'preis': '25.00', 'dauer': '45 Minuten'},
			],
		}
		self.assertEqual(repository.get_courses(), [
			{'kurs': 'Junghunde', 'preis': '25.00', 'dauer': '45 Minuten', 'einheit': 'einmalig'},
		])

	def test_normalize_course_interval_accepts_changed_option_capitalization(self) -> None:
		self.assertEqual(normalize_course_interval('tag'), 'Tag')
		self.assertEqual(normalize_course_interval('Woche'), 'Woche')
		with self.assertRaises(ValueError):
			normalize_course_interval('quartal')

	def test_get_price_returns_requested_dog_price(self) -> None:
		database = FakeDatabase()
		database.document = {'hundepreise': {'3': '25.00'}}
		repository = PreisstammRepository(database)

		self.assertEqual(repository.get_price(3), '25.00')
		with self.assertRaises(ValueError):
			repository.get_price(6)

	def test_normalize_courses_skips_empty_rows_and_requires_complete_rows(self) -> None:
		self.assertEqual(
			normalize_courses([
				{'kurs': '', 'preis': None, 'dauer': ''},
				{'kurs': 'Agility', 'preis': '30', 'dauer': '90', 'einheit': 'tag'},
			], allow_empty=True),
			[
				{'kurs': 'Agility', 'preis': '30.00', 'dauer': '90', 'einheit': 'Tag'},
			],
		)
		with self.assertRaises(ValueError):
			normalize_courses([{'kurs': 'Agility', 'preis': '', 'dauer': ''}], allow_empty=True)
		with self.assertRaises(ValueError):
			normalize_courses([{'kurs': 'Agility', 'preis': '30', 'dauer': '90', 'einheit': 'quartal'}], allow_empty=True)


if __name__ == '__main__':
	unittest.main()
