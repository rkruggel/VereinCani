"""Aufbau des Eingabeformulars für eine Adresse."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.pages.adressen.constants import FIELD_LABELS, FORM_FIELDS


def create_form_control(field: str, validate_phone: Callable[[Any], str | None]) -> Any:
	"""Erzeugt das in den Feldmetadaten konfigurierte NiceGUI-Steuerelement."""

	definition = FIELD_LABELS[field]
	label = definition['text']
	control_type = definition['steuerelement']

	if control_type == 'select':
		return ui.select(definition['optionen'], label=label).props('dense options-dense').classes('w-full')
	if control_type == 'multiselect':
		return ui.select(
			definition['optionen'],
			label=label,
			multiple=True,
			clearable=True,
		).props('dense options-dense use-chips').classes('w-full')
	if control_type == 'textarea':
		return ui.textarea(label).props('autogrow dense').classes('w-full')

	validation = validate_phone if definition['type'] == 'telefon' else None
	input_props = 'dense'
	if definition['type'] == 'datum':
		input_props = 'type=date dense'
	elif definition['type'] == 'email':
		input_props = 'type=email dense'
	return ui.input(label, validation=validation).props(input_props).classes('w-full')


def render_address_form(
	validate_phone: Callable[[Any], str | None],
	on_new: Callable[[], None],
	on_save: Callable[[], None],
) -> dict[str, Any]:
	"""Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück."""

	with ui.column().classes('w-full gap-2'):
		controls = {
			field: create_form_control(field, validate_phone)
			for field in FORM_FIELDS
		}

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Neu', icon='add', on_click=on_new).props('flat no-caps dense').classes(
				'text-slate-700 bg-slate-100 px-3'
			)
			ui.button('Speichern', icon='save', on_click=on_save).props('no-caps dense').classes(
				'bg-primary text-white px-3'
			)

	return controls
