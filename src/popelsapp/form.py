"""Aufbau eines aus Felddefinitionen erzeugten Popels-Formulars."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.popelsapp import PopelsConfig


def create_form_control(
	config: PopelsConfig,
	field: str,
	validate_phone: Callable[[Any], str | None],
) -> Any:
	"""Erzeugt das in den Feldmetadaten konfigurierte NiceGUI-Steuerelement."""

	definition = config.field_labels[field]
	label = definition['text']
	control_type = definition['steuerelement']

	if control_type == 'select':
		props = 'dense options-dense'
		if definition.get('pflichtfeld'):
			props += ' required'
		return ui.select(definition['optionen'], label=label).props(props).classes('w-full')
	if control_type == 'multiselect':
		props = 'dense options-dense use-chips'
		if definition.get('pflichtfeld'):
			props += ' required'
		return ui.select(
			definition['optionen'],
			label=label,
			multiple=True,
			clearable=True,
		).props(props).classes('w-full')
	if control_type == 'textarea':
		props = 'autogrow dense'
		if definition.get('pflichtfeld'):
			props += ' required'
		return ui.textarea(label).props(props).classes('w-full')

	validation = validate_phone if definition['type'] == 'telefon' else None
	input_props = 'dense'
	if definition['type'] == 'datum':
		input_props = 'type=date dense'
	elif definition['type'] == 'email':
		input_props = 'type=email dense'
	if definition.get('pflichtfeld'):
		input_props += ' required'
	return ui.input(label, validation=validation).props(input_props).classes('w-full')


def render_popels_form(
	config: PopelsConfig,
	validate_phone: Callable[[Any], str | None],
	on_new: Callable[[], None],
	on_save: Callable[[], None],
) -> dict[str, Any]:
	"""Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück."""

	with ui.column().classes('w-full gap-2'):
		controls = {
			field: create_form_control(config, field, validate_phone)
			for field in config.form_fields
		}

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Neu', icon='add', on_click=on_new).props('flat no-caps dense').classes(
				'text-slate-700 bg-slate-100 px-3'
			)
			ui.button('Speichern', icon='save', on_click=on_save).props('no-caps dense').classes(
				'bg-primary text-white px-3'
			)

	return controls
