"""Reine Hilfsfunktionen für Suche, Sortierung und Wertdarstellung."""

import base64
import unicodedata
from typing import Any

from src.pages.adressen.constants import FIELD_LABELS, FORM_FIELDS


def image_data_url(content_type: str, data: bytes) -> str:
	"""Kodiert Binärdaten als Data-URL für die Bildvorschau im Browser."""

	encoded_data = base64.b64encode(data).decode('ascii')
	return f'data:{content_type};base64,{encoded_data}'


def validate_phone(value: Any) -> str | None:
	"""Validiert Telefonnummern und liefert bei Erfolg ``None`` zurück."""

	text = str(value or '')
	if all(character.isdigit() or character in {'+', ' '} for character in text):
		return None
	return 'Nur Zahlen, + und Leerzeichen erlaubt'


def normalize_sort_criteria(sortierungen: list[str]) -> list[str]:
	"""Entfernt ungültige und doppelte Sortierkriterien."""

	result: list[str] = []
	used_fields: set[str] = set()
	for criterion in sortierungen:
		field, separator, direction = criterion.partition(':')
		if (
			separator
			and field in ('id', *FORM_FIELDS)
			and direction in {'asc', 'desc'}
			and field not in used_fields
		):
			result.append(criterion)
			used_fields.add(field)
	return result


def cycle_sort_criterion(sortierungen: list[str], field: str) -> list[str]:
	"""Schaltet ein Feld zwischen aufsteigend, absteigend und nicht sortiert um."""

	result = list(sortierungen)
	for index, criterion in enumerate(result):
		selected_field, _separator, direction = criterion.partition(':')
		if selected_field != field:
			continue
		if direction == 'asc':
			result[index] = f'{field}:desc'
		else:
			result.pop(index)
		return result
	result.append(f'{field}:asc')
	return result


def normalize_search_text(value: Any) -> str:
	"""Normalisiert einen Wert für eine akzent- und großschreibungsfreie Suche."""

	if isinstance(value, list):
		value = ' '.join(str(item) for item in value)
	text = unicodedata.normalize('NFKD', str(value or ''))
	return ''.join(character for character in text if not unicodedata.combining(character)).casefold()


def filter_records(records: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
	"""Filtert Adressen nach Suchbegriffen, die über mehrere Felder verteilt sein dürfen."""

	search_terms = normalize_search_text(query).split()
	if not search_terms:
		return records
	result = []
	for record in records:
		searchable_text = ' '.join(
			normalize_search_text(record.get(field))
			for field in ('id', *FORM_FIELDS)
		)
		if all(term in searchable_text for term in search_terms):
			result.append(record)
	return result


def display_value(record: dict[str, Any], field: str) -> str:
	"""Formatiert einen Feldwert für die kompakte Anzeige in einer Adresskarte."""

	value = record[field]
	if FIELD_LABELS[field]['type'] == 'liste':
		return ', '.join(value) if value else '-'
	return str(value or '-')
