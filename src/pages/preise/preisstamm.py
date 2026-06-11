"""CouchDB-Zugriff und Stammdatenseite für den Preisstamm."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from src.db.client import create_couch_database


PREISSTAMM_ID = 'preisstamm/hunde'
PREISSTAMM_COLLECTION = 'Preisstamm'
HUNDE_ANZAHLEN = range(1, 6)
COURSE_INTERVAL_OPTIONS = ['einmalig', 'Tag', 'Woche', 'Monat', 'Jahr']
EMPTY_COURSE = {'kurs': '', 'preis': '', 'dauer': '', 'einheit': 'einmalig'}


class PreisstammRepository:
	"""Speichert die Preise für ein bis fünf Hunde in einem festen Dokument."""

	def __init__(self, database: Any | None = None) -> None:
		self._database = database

	def get(self) -> dict[int, str]:
		"""Lädt alle Hundepreise und ergänzt noch nicht gespeicherte Werte."""

		return prices_from_document(self.get_document())

	def get_valid_from(self) -> str:
		"""Lädt das Datum, ab dem der Preisstamm gültig ist."""

		return valid_from_document(self.get_document())

	def get_courses(self) -> list[dict[str, str]]:
		"""Lädt die gespeicherten Kurspreise aus dem Preisstamm."""

		return courses_from_document(self.get_document())

	def get_document(self) -> dict[str, Any]:
		"""Lädt das feste Preisstamm-Dokument genau einmal."""

		return self._get_database().get_document(PREISSTAMM_ID) or {}

	def save(
		self,
		prices: dict[int, str],
		valid_from: Any,
		courses: list[dict[str, Any]] | None = None,
	) -> None:
		"""Speichert einen vollständigen und normalisierten Hundepreisstamm."""

		normalized = {
			str(count): normalize_price(prices.get(count, ''))
			for count in HUNDE_ANZAHLEN
		}
		normalized_courses = normalize_courses(courses or [], allow_empty=True)
		self._get_database().put_document(
			PREISSTAMM_ID,
			{
				'gueltig_ab': normalize_valid_from(valid_from, field_label='Gültig ab'),
				'hundepreise': normalized,
				'kurse': normalized_courses,
			},
			PREISSTAMM_COLLECTION,
		)

	def get_price(self, dog_count: int) -> str:
		"""Liefert den gespeicherten Preis für eine konkrete Hundeanzahl."""

		if dog_count not in HUNDE_ANZAHLEN:
			raise ValueError('Die Hundeanzahl muss zwischen 1 und 5 liegen.')
		return self.get()[dog_count]

	def _get_database(self):
		if self._database is None:
			self._database = create_couch_database()
		return self._database


def normalize_price(value: Any) -> str:
	"""Normalisiert einen nicht-negativen Geldbetrag auf zwei Nachkommastellen."""

	text = str(value or '').strip().replace('€', '').replace(' ', '').replace(',', '.')
	if not text:
		raise ValueError('Alle Preise müssen angegeben werden.')
	try:
		price = Decimal(text)
	except InvalidOperation as error:
		raise ValueError(f'Ungültiger Preis: {value}') from error
	if not price.is_finite() or price < 0:
		raise ValueError(f'Ungültiger Preis: {value}')
	return format(price.quantize(Decimal('0.01')), 'f')


def number_input_value(value: Any) -> float | None:
	"""Bereitet gespeicherte Preiswerte für NiceGUI-Zahlenfelder vor."""

	text = str(value or '').strip()
	if not text:
		return None
	return float(normalize_price(text))


def normalize_valid_from(value: Any, field_label: str = 'Gültig ab') -> str:
	"""Validiert das Gültigkeitsdatum und liefert das ISO-Datumsformat."""

	text = str(value or '').strip()
	if not text:
		raise ValueError(f'Das Feld {field_label} muss angegeben werden.')
	try:
		return date.fromisoformat(text).isoformat()
	except ValueError as error:
		raise ValueError(f'{field_label} muss ein gültiges Datum sein.') from error


def normalize_course_interval(value: Any) -> str:
	"""Normalisiert die Einheit einer Kursdauer auf eine auswählbare Option."""

	text = str(value or 'einmalig').strip()
	for option in COURSE_INTERVAL_OPTIONS:
		if text.casefold() == option.casefold():
			return option
	raise ValueError(f'Ungültige Einheit: {text}')


def normalize_courses(
	courses: list[dict[str, Any]],
	*,
	allow_empty: bool = False,
) -> list[dict[str, str]]:
	"""Normalisiert Kurszeilen und verwirft vollständig leere Zeilen."""

	normalized = []
	for row in courses:
		course = str(row.get('kurs') or '').strip()
		price = row.get('preis')
		duration = str(row.get('dauer') or '').strip()
		interval = str(row.get('einheit') or 'einmalig').strip()
		if not course and price in (None, '') and not duration:
			continue
		missing_fields = []
		if not course:
			missing_fields.append('Kurs')
		if price in (None, ''):
			missing_fields.append('Preis')
		if not duration:
			missing_fields.append('Dauer')
		if not interval:
			missing_fields.append('Einheit')
		if missing_fields:
			raise ValueError(f'Kurszeile unvollständig: {", ".join(missing_fields)} fehlt.')
		interval = normalize_course_interval(interval)
		normalized.append({
			'kurs': course,
			'preis': normalize_price(price),
			'dauer': duration,
			'einheit': interval,
		})
	if not normalized and not allow_empty:
		raise ValueError('Mindestens ein Kurs muss angegeben werden.')
	return normalized


def prices_from_document(document: dict[str, Any]) -> dict[int, str]:
	"""Liest die Hundepreise aus einem Preisstamm-Dokument."""

	prices = document.get('hundepreise') or {}
	return {
		count: normalize_price(prices.get(str(count))) if prices.get(str(count)) not in (None, '') else ''
		for count in HUNDE_ANZAHLEN
	}


def valid_from_document(document: dict[str, Any]) -> str:
	"""Liest das Gültigkeitsdatum aus einem Preisstamm-Dokument."""

	return str(document.get('gueltig_ab') or '')


def courses_from_document(document: dict[str, Any]) -> list[dict[str, str]]:
	"""Liest die Kurszeilen aus einem Preisstamm-Dokument."""

	return normalize_courses(document.get('kurse') or [], allow_empty=True)


PREISSTAMM = PreisstammRepository()


def render_preisstamm_page() -> None:
	"""Rendert die Stammdatenseite zur Pflege der fünf Hundepreise."""

	repository = PREISSTAMM
	inputs: dict[int, Any] = {}
	course_inputs: list[dict[str, Any]] = []
	try:
		document = repository.get_document()
		load_error = None
	except Exception as error:
		document = {}
		load_error = f'CouchDB konnte nicht geladen werden: {error}'

	try:
		prices = prices_from_document(document)
	except Exception as error:
		prices = {count: '' for count in HUNDE_ANZAHLEN}
		load_error = f'Hundepreise konnten nicht geladen werden: {error}'

	try:
		valid_from = valid_from_document(document)
	except Exception as error:
		valid_from = ''
		load_error = f'Gültigkeitsdatum konnte nicht geladen werden: {error}'

	try:
		course_rows = {'value': courses_from_document(document) or [EMPTY_COURSE.copy()]}
	except Exception as error:
		course_rows = {'value': [EMPTY_COURSE.copy()]}
		load_error = f'Kurse konnten nicht geladen werden: {error}'

	with ui.card().classes('w-[800px] max-w-full p-4 gap-4 rounded-lg shadow-sm border border-slate-200'):
		ui.label('Preisstamm').classes('text-lg font-semibold text-slate-900')
		ui.label('Der Mitgliedspreis ist nach Anzahl der Hunde gestaffelt.').classes('text-sm text-slate-600')
		if load_error is not None:
			ui.label(load_error).classes('text-sm text-red-600')
		valid_from_input = ui.input('Gültig ab', value=valid_from).props(
			'type=date dense required'
		).classes('w-full')
		with ui.grid(columns=2).classes('w-full gap-2 max-sm:grid-cols-1'):
			for count in HUNDE_ANZAHLEN:
				label = f'Preis für {count} Hund' if count == 1 else f'Preis für {count} Hunde'
				price = prices[count]
				inputs[count] = ui.number(
					label,
					value=number_input_value(price),
					min=0,
					step=0.01,
					precision=2,
					suffix='€',
					format='%.2f',
				).props('dense inputmode=decimal').classes('w-full')

		ui.separator().classes('w-full')

		def sync_course_rows() -> None:
			if not course_inputs:
				return
			course_rows['value'] = [
				{
					'kurs': str(controls['kurs'].value or ''),
					'preis': controls['preis'].value,
					'dauer': str(controls['dauer'].value or ''),
					'einheit': str(controls['einheit'].value or 'einmalig'),
				}
				for controls in course_inputs
			]

		def add_course_row(after_index: int | None = None) -> None:
			sync_course_rows()
			insert_at = len(course_rows['value']) if after_index is None else after_index + 1
			course_rows['value'].insert(insert_at, EMPTY_COURSE.copy())
			render_course_rows.refresh()

		def delete_course_row(index: int) -> None:
			sync_course_rows()
			if 0 <= index < len(course_rows['value']):
				course_rows['value'].pop(index)
			if not course_rows['value']:
				course_rows['value'].append(EMPTY_COURSE.copy())
			render_course_rows.refresh()

		@ui.refreshable
		def render_course_rows() -> None:
			course_inputs.clear()
			for index, row in enumerate(course_rows['value']):
				with ui.row().classes('w-full items-start gap-2 max-sm:flex-col'):
					course_control = ui.input('Kurs', value=row.get('kurs', '')).props(
						'dense'
					).classes('flex-1 min-w-[10rem] max-sm:w-full')
					price = row.get('preis')
					price_control = ui.number(
						'Preis',
						value=number_input_value(price),
						min=0,
						step=0.01,
						precision=2,
						suffix='€',
						format='%.2f',
					).props('dense inputmode=decimal').classes('w-36 max-sm:w-full')
					duration_control = ui.input('Dauer', value=row.get('dauer', '')).props(
						'dense'
					).classes('w-36 max-sm:w-full')
					interval_control = ui.select(
						COURSE_INTERVAL_OPTIONS,
						label='Einheit',
						value=normalize_course_interval(row.get('einheit')),
					).props('dense').classes('w-36 max-sm:w-full')
					course_inputs.append({
						'kurs': course_control,
						'preis': price_control,
						'dauer': duration_control,
						'einheit': interval_control,
					})
					with ui.row().classes('gap-1 pt-1 max-sm:pt-0'):
						ui.button(
							icon='delete',
							on_click=lambda row_index=index: delete_course_row(row_index),
						).props('flat round dense color=negative').tooltip('Zeile löschen')
						ui.button(
							icon='add',
							on_click=lambda row_index=index: add_course_row(row_index),
						).props('flat round dense').tooltip('Neue Zeile hinzufügen')

		render_course_rows()

		def save_prices() -> None:
			sync_course_rows()
			try:
				repository.save({
					count: inputs[count].value
					for count in HUNDE_ANZAHLEN
				}, valid_from_input.value, course_rows['value'])
			except ValueError as error:
				ui.notify(str(error), type='warning')
				return
			except Exception as error:
				ui.notify(f'Preisstamm konnte nicht gespeichert werden: {error}', type='negative')
				return
			ui.notify('Preisstamm wurde gespeichert.')

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Speichern', icon='save', on_click=save_prices).props('no-caps')
