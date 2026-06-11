"""Reine Hilfsfunktionen für Suche, Sortierung und Wertdarstellung."""

import base64
import html
import re
import unicodedata
from typing import Any

from src.popelsapp import PopelsConfig


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
	config: PopelsConfig,
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


def searchable_value(config: PopelsConfig, field: str, value: Any) -> str:
	"""Bereitet einen Feldwert entsprechend seiner Konfiguration für die Suche auf."""

	if config.page(field).get('steuerelement') == 'editor':
		value = html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))
	return normalize_search_text(value)


def filter_records(
	config: PopelsConfig,
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


def display_value(config: PopelsConfig, record: dict[str, Any], field: str) -> str:
	"""Formatiert einen Feldwert für die kompakte Anzeige in einer Popels-Karte."""

	value = record[field]
	if config.field_labels[field]['type'] == 'liste':
		return ', '.join(value) if value else '-'
	return str(value or '-')


def content_available(config: PopelsConfig, field: str, value: Any) -> bool:
	"""Prüft, ob ein Inhaltsfeld tatsächlich nutzbaren Inhalt enthält."""

	if config.page(field).get('steuerelement') != 'editor':
		return bool(value)
	text = html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))
	text = text.replace('\xa0', ' ')
	return bool(text.strip())


def record_heading(
	config: PopelsConfig,
	record: dict[str, Any],
	visible_fields: set[str] | None = None,
	*,
	fallback_to_id: bool = True,
	name_last_first: bool = False,
) -> str:
	"""Erzeugt die Überschrift aus numerisch markierten Feldern."""

	heading_fields = sorted(
		(
			(config.field_position(field, 'formHeaderPos'), field)
			for field in config.field_labels
			if config.field_position(field, 'formHeaderPos') is not None
			and (
				not config.is_list_field(field)
				or visible_fields is None
				or field in visible_fields
			)
		),
	)
	values = [
		format_heading_value(field, record.get(field), name_last_first)
		for _position, field in heading_fields
		if str(record.get(field) or '').strip()
	]
	heading = ' '.join(values)
	if heading or not fallback_to_id:
		return heading
	return str(record.get('id') or '')


def format_heading_value(field: str, value: Any, name_last_first: bool) -> str:
	"""Formatiert den Namen in sortierten Listen passend zur Nachnamensreihenfolge."""

	text = str(value or '').strip()
	if field != 'name' or not name_last_first:
		return text
	parts = text.split()
	if len(parts) < 2:
		return text
	return f'{parts[-1]}, {" ".join(parts[:-1])}'
