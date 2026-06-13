"""Beitragsberechnung der VereinGUI-Anwendung."""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from src.pages.mitglieder.start import MITGLIEDER_DB
from src.pages.preise.preisstamm import PREISSTAMM


CALCULATION_OPTIONS = ['Beitrag', 'Kurse']


def render_beitraege_page() -> None:
	"""Erzeugt das Berechnungsfenster für Beiträge und Kurse."""

	result_rows = {'value': []}
	total = {'value': '0.00'}
	error_message = {'value': ''}
	calculated = {'value': False}

	with ui.card().classes('w-[800px] max-w-full p-4 gap-4 rounded-lg shadow-sm border border-slate-200'):
		ui.label('Beiträge berechnen').classes('text-lg font-semibold text-slate-900')
		ui.label('Auswahl treffen und Berechnung starten.').classes('text-sm text-slate-600')

		calculation_type = ui.select(
			CALCULATION_OPTIONS,
			label='Was soll berechnet werden?',
			value='Beitrag',
		).props('dense options-dense').classes('w-full')

		@ui.refreshable
		def render_results() -> None:
			if error_message['value']:
				ui.label(error_message['value']).classes('text-sm text-red-600')
				return
			if not result_rows['value']:
				text = 'Keine passenden Einträge gefunden.' if calculated['value'] else 'Noch keine Berechnung ausgeführt.'
				ui.label(text).classes('text-sm text-slate-500')
				return

			columns = [
				{'name': 'name', 'label': 'Mitglied', 'field': 'name', 'align': 'left'},
				{'name': 'grundlage', 'label': 'Grundlage', 'field': 'grundlage', 'align': 'left'},
				{'name': 'betrag', 'label': 'Betrag', 'field': 'betrag', 'align': 'right'},
			]
			ui.table(
				columns=columns,
				rows=result_rows['value'],
				row_key='id',
				pagination={'rowsPerPage': 0},
			).props('flat dense hide-bottom').classes('w-full')
			with ui.row().classes('w-full justify-end items-center gap-2'):
				ui.label('Summe').classes('text-sm font-medium text-slate-700')
				ui.label(f'{total["value"]} €').classes('text-base font-semibold text-slate-900')

		def calculate() -> None:
			error_message['value'] = ''
			try:
				members = MITGLIEDER_DB.list()
			except Exception as error:
				result_rows['value'] = []
				total['value'] = '0.00'
				calculated['value'] = True
				error_message['value'] = f'Mitglieder konnten nicht geladen werden: {error}'
				render_results.refresh()
				return

			try:
				if calculation_type.value == 'Kurse':
					rows = calculate_course_rows(members, PREISSTAMM.get_courses())
				else:
					rows = calculate_membership_rows(members, PREISSTAMM)
			except Exception as error:
				result_rows['value'] = []
				total['value'] = '0.00'
				calculated['value'] = True
				error_message['value'] = f'Berechnung fehlgeschlagen: {error}'
				render_results.refresh()
				return

			result_rows['value'] = rows
			total['value'] = sum_amounts(row['betrag'] for row in rows)
			calculated['value'] = True
			render_results.refresh()

		render_results()

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Berechnen', icon='calculate', on_click=calculate).props('no-caps dense')


def calculate_membership_rows(
	members: list[dict[str, Any]],
	preisstamm: Any,
) -> list[dict[str, str]]:
	"""Berechnet Vereinsbeiträge für Mitglieder mit Hundeverein-Mitgliedschaft."""

	rows = []
	for member in members:
		if not is_yes(member.get('hundevereinMitglied')):
			continue
		dogs = normalize_list(member.get('hunde'))
		amount = price_for_dog_count(preisstamm, len(dogs))
		rows.append({
			'id': str(member.get('id') or member.get('name') or len(rows)),
			'name': str(member.get('name') or '-'),
			'grundlage': f'{len(dogs)} Hund' if len(dogs) == 1 else f'{len(dogs)} Hunde',
			'betrag': amount,
		})
	return rows


def calculate_course_rows(
	members: list[dict[str, Any]],
	courses: list[dict[str, Any]],
) -> list[dict[str, str]]:
	"""Berechnet Kursbeträge aus Kursbesuchen und Preisstamm-Kursen."""

	course_prices = {
		str(course.get('kurs') or '').strip(): str(course.get('preis') or '').strip()
		for course in courses
		if str(course.get('kurs') or '').strip()
	}
	rows = []
	for member in members:
		for index, visit in enumerate(normalize_course_visits(member.get('kursbesuche'))):
			course_name = visit.get('kurs', '')
			amount = course_prices.get(course_name, '')
			rows.append({
				'id': f'{member.get("id") or member.get("name")}-{index}',
				'name': str(member.get('name') or '-'),
				'grundlage': course_visit_basis(visit),
				'betrag': amount,
			})
	return rows


def is_yes(value: Any) -> bool:
	"""Prüft Ja/Nein-Felder robust."""

	return str(value or '').strip().casefold() == 'ja'


def normalize_list(value: Any) -> list[Any]:
	"""Normalisiert Listenfelder aus der Datenbank."""

	if value in (None, ''):
		return []
	return value if isinstance(value, list) else [value]


def price_for_dog_count(preisstamm: Any, dog_count: int) -> str:
	"""Lädt den Preis passend zur Hundeanzahl."""

	try:
		return str(preisstamm.get_price(dog_count) or '')
	except Exception:
		return ''


def normalize_course_visits(value: Any) -> list[dict[str, str]]:
	"""Normalisiert Kursbesuche für die Kursberechnung."""

	if not isinstance(value, list):
		return []
	visits = []
	for row in value:
		if not isinstance(row, dict):
			continue
		course = str(row.get('kurs') or '').strip()
		date_from = str(row.get('datumVon') or row.get('datum') or '').strip()
		paid = row.get('bezahlt')
		if course or date_from or paid is not None:
			visits.append({
				'kurs': course,
				'datumVon': date_from,
				'bezahlt': paid_text(paid),
			})
	return visits


def course_visit_basis(visit: dict[str, str]) -> str:
	"""Formatiert eine Kursbesuchszeile für die Ergebnisliste."""

	parts = [
		visit.get('kurs', ''),
		visit.get('datumVon', ''),
		visit.get('bezahlt', ''),
	]
	return ' / '.join(part for part in parts if part)


def paid_text(value: Any) -> str:
	"""Formatiert den Bezahlstatus."""

	if value is None or value == '':
		return ''
	if isinstance(value, str):
		return 'bezahlt' if value.strip().casefold() == 'ja' else 'offen'
	return 'bezahlt' if bool(value) else 'offen'


def sum_amounts(values: Iterable[str]) -> str:
	"""Summiert Geldbeträge und ignoriert leere Werte."""

	total = Decimal('0.00')
	for value in values:
		text = str(value or '').strip().replace('€', '').replace(' ', '').replace(',', '.')
		if not text:
			continue
		try:
			total += Decimal(text)
		except InvalidOperation:
			continue
	return format(total.quantize(Decimal('0.01')), 'f')
