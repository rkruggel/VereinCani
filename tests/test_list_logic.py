"""
Tests für die Darstellung der Kartenüberschrift.
"""
import unittest

from src.popelsapp import load_popels_config
from src.popelsapp.list_logic import format_heading_value, record_heading


class RecordHeadingTest(unittest.TestCase):
	"""
	Bündelt Tests für die Kartenüberschrift.
	"""
	def test_sorted_name_is_displayed_last_name_first(self) -> None:
		"""
		Prüft den Testfall: sorted name is displayed last name first.
		"""
		self.assertEqual(
			format_heading_value('name', 'Karl Heinz Schmidt', True),
			'Schmidt, Karl Heinz',
		)

	def test_unsorted_name_keeps_stored_display_order(self) -> None:
		"""
		Prüft den Testfall: unsorted name keeps stored display order.
		"""
		self.assertEqual(
			format_heading_value('name', 'Karl Heinz Schmidt', False),
			'Karl Heinz Schmidt',
		)

	def test_single_name_is_unchanged(self) -> None:
		"""
		Prüft den Testfall: single name is unchanged.
		"""
		self.assertEqual(format_heading_value('name', 'Madonna', True), 'Madonna')

	def test_record_heading_formats_only_name(self) -> None:
		"""
		Prüft den Testfall: record heading formats only name.
		"""
		config = load_popels_config('persoenlich.yaml')
		record = {'titel': 'Dr.', 'name': 'Anna Müller'}

		self.assertEqual(
			record_heading(config, record, name_last_first=True),
			'Dr. Müller, Anna',
		)


if __name__ == '__main__':
	unittest.main()
