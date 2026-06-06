"""Aufbau des Eingabeformulars für eine Adresse."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.pages.adressen.constants import FIELD_LABELS, WOCHENTAGE


def render_address_form(
	validate_phone: Callable[[Any], str | None],
	on_new: Callable[[], None],
	on_save: Callable[[], None],
) -> dict[str, Any]:
	"""Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück."""

	controls: dict[str, Any] = {}

	with ui.grid(columns=2).classes('w-full gap-2'):
		controls['anrede'] = ui.select(
			['Herr', 'Frau', 'Diverse'],
			label=FIELD_LABELS['anrede']['text'],
		).props('dense options-dense').classes('w-full')
		controls['titel'] = ui.select(
			['Dr.', 'Prof.', 'Prof. Dr.'],
			label=FIELD_LABELS['titel']['text'],
		).props('dense options-dense').classes('w-full')

	with ui.grid(columns=2).classes('w-full gap-2'):
		controls['vorname'] = ui.input(FIELD_LABELS['vorname']['text']).classes('w-full').props('dense')
		controls['nachname'] = ui.input(FIELD_LABELS['nachname']['text']).classes('w-full').props('dense')
	controls['zusatz'] = ui.textarea(FIELD_LABELS['zusatz']['text']).classes('w-full').props('autogrow dense')
	controls['adresse'] = ui.textarea(FIELD_LABELS['adresse']['text']).classes('w-full').props('autogrow dense')

	with ui.grid(columns=2).classes('w-full gap-2'):
		controls['ort'] = ui.input(FIELD_LABELS['ort']['text']).props('dense').classes('w-full')
		controls['geboren'] = ui.input(FIELD_LABELS['geboren']['text']).props('type=date dense').classes('w-full')
		controls['festnetz'] = ui.input(
			FIELD_LABELS['festnetz']['text'],
			validation=validate_phone,
		).props('dense').classes('w-full')
		controls['handy'] = ui.input(
			FIELD_LABELS['handy']['text'],
			validation=validate_phone,
		).props('dense').classes('w-full')
		controls['email'] = ui.input(FIELD_LABELS['email']['text']).props('type=email dense').classes('w-full')
		controls['www'] = ui.input(FIELD_LABELS['www']['text']).props('dense').classes('w-full')

	controls['nichtWochentag'] = ui.select(
		WOCHENTAGE,
		label=FIELD_LABELS['nichtWochentag']['text'],
		multiple=True,
		clearable=True,
	).props('dense options-dense use-chips').classes('w-full')

	with ui.grid(columns=2).classes('w-full gap-2'):
		controls['beruf'] = ui.input(FIELD_LABELS['beruf']['text']).props('dense').classes('w-full')
		controls['hobby'] = ui.input(FIELD_LABELS['hobby']['text']).props('dense').classes('w-full')

	controls['faehigkeiten'] = ui.textarea(
		FIELD_LABELS['faehigkeiten']['text'],
	).classes('w-full').props('autogrow dense')

	with ui.row().classes('w-full justify-end gap-2'):
		ui.button('Neu', icon='add', on_click=on_new).props('flat no-caps dense').classes(
			'text-slate-700 bg-slate-100 px-3'
		)
		ui.button('Speichern', icon='save', on_click=on_save).props('no-caps dense').classes(
			'bg-primary text-white px-3'
		)

	return controls
