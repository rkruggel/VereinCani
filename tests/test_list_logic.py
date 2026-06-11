"""Tests für die Darstellung der Kartenüberschrift."""

import unittest

from src.popelsapp import load_popels_config
from src.popelsapp.list_logic import format_heading_value, record_heading


class RecordHeadingTest(unittest.TestCase):
	def test_sorted_name_is_displayed_last_name_first(self) -> None:
		self.assertEqual(
			format_heading_value('name', 'Karl Heinz Schmidt', True),
			'Schmidt, Karl Heinz',
		)

	def test_unsorted_name_keeps_stored_display_order(self) -> None:
		self.assertEqual(
			format_heading_value('name', 'Karl Heinz Schmidt', False),
			'Karl Heinz Schmidt',
		)

	def test_single_name_is_unchanged(self) -> None:
		self.assertEqual(format_heading_value('name', 'Madonna', True), 'Madonna')

	def test_record_heading_formats_only_name(self) -> None:
		config = load_popels_config('persoenlich.yaml')
		record = {'titel': 'Dr.', 'name': 'Anna Müller'}

		self.assertEqual(
			record_heading(config, record, name_last_first=True),
			'Dr. Müller, Anna',
		)


if __name__ == '__main__':
	unittest.main()
