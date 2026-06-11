"""CouchDB-Zugriff und Stammdatenseite für den Preisstamm."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from src.db.client import create_couch_database


PREISSTAMM_ID = 'preisstamm/hunde'
PREISSTAMM_COLLECTION = 'Preisstamm'
HUNDE_ANZAHLEN = range(1, 6)


class PreisstammRepository:
	"""Speichert die Preise für ein bis fünf Hunde in einem festen Dokument."""

	def __init__(self, database: Any | None = None) -> None:
		self._database = database

	def get(self) -> dict[int, str]:
		"""Lädt alle Hundepreise und ergänzt noch nicht gespeicherte Werte."""

		document = self._get_database().get_document(PREISSTAMM_ID) or {}
		prices = document.get('hundepreise') or {}
		return {
			count: str(prices.get(str(count), '') or '')
			for count in HUNDE_ANZAHLEN
		}

	def get_valid_from(self) -> str:
		"""Lädt das Datum, ab dem der Preisstamm gültig ist."""

		document = self._get_database().get_document(PREISSTAMM_ID) or {}
		return str(document.get('gueltig_ab') or '')

	def save(self, prices: dict[int, str], valid_from: Any) -> None:
		"""Speichert einen vollständigen und normalisierten Hundepreisstamm."""

		normalized = {
			str(count): normalize_price(prices.get(count, ''))
			for count in HUNDE_ANZAHLEN
		}
		self._get_database().put_document(
			PREISSTAMM_ID,
			{
				'gueltig_ab': normalize_valid_from(valid_from, field_label='Gültig ab'),
				'hundepreise': normalized,
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


def normalize_valid_from(value: Any, field_label: str = 'Gültig ab') -> str:
	"""Validiert das Gültigkeitsdatum und liefert das ISO-Datumsformat."""

	text = str(value or '').strip()
	if not text:
		raise ValueError(f'Das Feld {field_label} muss angegeben werden.')
	try:
		return date.fromisoformat(text).isoformat()
	except ValueError as error:
		raise ValueError(f'{field_label} muss ein gültiges Datum sein.') from error


PREISSTAMM = PreisstammRepository()


def render_preisstamm_page() -> None:
	"""Rendert die Stammdatenseite zur Pflege der fünf Hundepreise."""

	repository = PREISSTAMM
	inputs: dict[int, Any] = {}
	try:
		prices = repository.get()
		valid_from = repository.get_valid_from()
		load_error = None
	except Exception as error:
		prices = {count: '' for count in HUNDE_ANZAHLEN}
		valid_from = ''
		load_error = str(error)

	with ui.card().classes('w-[640px] max-w-full p-4 gap-4 rounded-lg shadow-sm border border-slate-200'):
		ui.label('Preisstamm').classes('text-lg font-semibold text-slate-900')
		ui.label('Der Mitgliedspreis ist nach Anzahl der Hunde gestaffelt.').classes('text-sm text-slate-600')
		if load_error is not None:
			ui.label(f'CouchDB konnte nicht geladen werden: {load_error}').classes(
				'text-sm text-red-600'
			)
		valid_from_input = ui.input('Gültig ab', value=valid_from).props(
			'type=date dense required'
		).classes('w-full')
		with ui.grid(columns=2).classes('w-full gap-2 max-sm:grid-cols-1'):
			for count in HUNDE_ANZAHLEN:
				label = f'Preis für {count} Hund' if count == 1 else f'Preis für {count} Hunde'
				price = prices[count]
				inputs[count] = ui.number(
					label,
					value=float(price) if price else None,
					min=0,
					step=0.01,
					precision=2,
					suffix='€',
					format='%.2f',
				).props('dense inputmode=decimal').classes('w-full')

		def save_prices() -> None:
			try:
				repository.save({
					count: inputs[count].value
					for count in HUNDE_ANZAHLEN
				}, valid_from_input.value)
			except ValueError as error:
				ui.notify(str(error), type='warning')
				return
			except Exception as error:
				ui.notify(f'Preisstamm konnte nicht gespeichert werden: {error}', type='negative')
				return
			ui.notify('Preisstamm wurde gespeichert.')

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Speichern', icon='save', on_click=save_prices).props('no-caps')
