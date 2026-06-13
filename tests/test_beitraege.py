"""Tests für die Beitragsberechnung."""

import unittest

from src.pages.beitraege.start import (
	calculate_course_rows,
	calculate_membership_rows,
	sum_amounts,
)


class FakePreisstamm:
	def __init__(self) -> None:
		self.requests = []

	def get_price(self, dog_count: int) -> str:
		self.requests.append(dog_count)
		return {
			1: '10.00',
			2: '18.00',
		}[dog_count]


class BeitraegeTest(unittest.TestCase):
	def test_membership_rows_use_all_club_members_with_yes_value(self) -> None:
		preisstamm = FakePreisstamm()
		members = [
			{
				'id': 'm1',
				'name': 'Anna Alt',
				'hundevereinMitglied': 'Ja',
				'mitgliedSeit': '2025-04-01',
				'hunde': ['h1', 'h2'],
			},
			{
				'id': 'm2',
				'name': 'Karl Neu',
				'hundevereinMitglied': 'Ja',
				'mitgliedSeit': '2026-01-01',
				'hunde': ['h1'],
			},
			{
				'id': 'm3',
				'name': 'Gabi Gast',
				'hundevereinMitglied': 'Nein',
				'mitgliedSeit': '2024-01-01',
				'hunde': ['h1'],
			},
		]

		rows = calculate_membership_rows(members, preisstamm)

		self.assertEqual(rows, [
			{'id': 'm1', 'name': 'Anna Alt', 'grundlage': '2 Hunde', 'betrag': '18.00'},
			{'id': 'm2', 'name': 'Karl Neu', 'grundlage': '1 Hund', 'betrag': '10.00'},
		])
		self.assertEqual(preisstamm.requests, [2, 1])

	def test_course_rows_use_course_prices_from_prestamm(self) -> None:
		rows = calculate_course_rows(
			[
				{
					'id': 'm1',
					'name': 'Anna Alt',
					'kursbesuche': [
						{'kurs': 'Mantrailing', 'datumVon': '2026-04-29', 'bezahlt': True},
					],
				},
			],
			[
				{'kurs': 'Mantrailing', 'preis': '25.00'},
			],
		)

		self.assertEqual(rows, [
			{
				'id': 'm1-0',
				'name': 'Anna Alt',
				'grundlage': 'Mantrailing / 2026-04-29 / bezahlt',
				'betrag': '25.00',
			},
		])

	def test_sum_amounts_ignores_empty_values(self) -> None:
		self.assertEqual(sum_amounts(['10.00', '', '2,50']), '12.50')


if __name__ == '__main__':
	unittest.main()
