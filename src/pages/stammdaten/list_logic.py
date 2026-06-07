"""Reine Hilfsfunktionen für Suche, Sortierung und Wertdarstellung."""

import base64
import html
import re
import unicodedata
from typing import Any

from src.pages.stammdaten import StammdatenConfig


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


def normalize_sort_criteria(
	config: StammdatenConfig,
	sortierungen: list[str],
) -> list[str]:
	"""Entfernt ungültige und doppelte Sortierkriterien."""

	result: list[str] = []
	used_fields: set[str] = set()
	for criterion in sortierungen:
		field, separator, direction = criterion.partition(':')
		if (
			separator
			and field in config.sort_fields
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


def searchable_value(config: StammdatenConfig, field: str, value: Any) -> str:
	"""Bereitet einen Feldwert entsprechend seiner Konfiguration für die Suche auf."""

	if config.field_labels[field]['steuerelement'] == 'editor':
		value = html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))
	return normalize_search_text(value)


def filter_records(
	config: StammdatenConfig,
	records: list[dict[str, Any]],
	query: str,
) -> list[dict[str, Any]]:
	"""Filtert Datensätze nach Begriffen, die über mehrere Felder verteilt sein dürfen."""

	search_terms = normalize_search_text(query).split()
	if not search_terms:
		return records
	result = []
	for record in records:
		searchable_text = ' '.join(
			searchable_value(config, field, record.get(field))
			for field in config.search_fields
		)
		if all(term in searchable_text for term in search_terms):
			result.append(record)
	return result


def display_value(config: StammdatenConfig, record: dict[str, Any], field: str) -> str:
	"""Formatiert einen Feldwert für die kompakte Anzeige in einer Stammdatenkarte."""

	value = record[field]
	if config.field_labels[field]['type'] == 'liste':
		return ', '.join(value) if value else '-'
	return str(value or '-')


def content_available(config: StammdatenConfig, field: str, value: Any) -> bool:
	"""Prüft, ob ein Inhaltsfeld tatsächlich nutzbaren Inhalt enthält."""

	if config.field_labels[field]['steuerelement'] != 'editor':
		return bool(value)
	text = html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))
	text = text.replace('\xa0', ' ')
	return bool(text.strip())


def record_heading(
	config: StammdatenConfig,
	record: dict[str, Any],
	visible_fields: set[str] | None = None,
	*,
	fallback_to_id: bool = True,
) -> str:
	"""Erzeugt die Überschrift aus numerisch markierten Feldern."""

	heading_fields = sorted(
		(
			(definition['formHeaderPos'], field)
			for field, definition in config.field_labels.items()
			if 'formHeaderPos' in definition
			and (visible_fields is None or field in visible_fields)
		),
	)
	values = [
		str(record.get(field) or '').strip()
		for _position, field in heading_fields
		if str(record.get(field) or '').strip()
	]
	heading = ' '.join(values)
	if heading or not fallback_to_id:
		return heading
	return str(record.get('id') or '')
