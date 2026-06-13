"""
Aufbau eines aus Felddefinitionen erzeugten Popels-Formulars.
"""
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from typing import Any

from nicegui import ui

from src.popelsapp import PopelsConfig
from src.popelsapp.controls import (
	CommaSeparatedListInput,
	CourseBookingsInput,
	EditableOptionsSelect,
	FreeInputChips,
	IbanInput,
	RelatedRecordChips,
	RelatedRecordSelect,
)
from src.services.calc import berechne


def euro_input_value(value: Any) -> float | None:
	"""
	Bereitet gespeicherte Euro-Werte für ein Zahlenfeld vor.
	"""
	text = str(value or '').strip()
	if not text:
		return None
	try:
		return float(normalize_euro_text(text))
	except ValueError:
		return None


def normalize_euro_text(value: Any) -> str:
	"""
	Normalisiert einen Euro-Betrag auf zwei Nachkommastellen.
	"""
	text = str(value or '').strip().replace('€', '').replace(' ', '').replace(',', '.')
	if not text:
		return ''
	try:
		amount = Decimal(text)
	except InvalidOperation as error:
		raise ValueError(f'Ungültiger Euro-Betrag: {value}') from error
	if not amount.is_finite():
		raise ValueError(f'Ungültiger Euro-Betrag: {value}')
	return format(amount.quantize(Decimal('0.01')), 'f')


def create_form_control(
	config: PopelsConfig,
	field: str,
	validate_phone: Callable[[Any], str | None],
	context: dict[str, Any] | None = None,
) -> Any:
	"""
	Erzeugt das in den Feldmetadaten konfigurierte NiceGUI-Steuerelement.
	"""
	definition = config.field_labels[field]
	page_definition = config.page(field)
	label = definition['text']
	control_type = page_definition['steuerelement']

	if control_type == 'input_chips':
		context = context or {}
		if 'options' in context:
			control = RelatedRecordChips(
				label,
				context.get('options', {}),
				context.get('on_select'),
			)
		else:
			control = FreeInputChips(label)
	elif control_type == 'select':
		context = context or {}
		if 'options' in context:
			control = RelatedRecordSelect(
				label,
				context.get('options', {}),
				context.get('on_select'),
			)
		else:
			props = 'dense options-dense'
			if page_definition.get('pflichtfeld'):
				props += ' required'
			control = ui.select(page_definition['optionen'], label=label).props(props).classes('w-full')
	elif control_type == 'editable_select':
		context = context or {}
		control = EditableOptionsSelect(
			label,
			context.get('options', []),
			context.get('on_options_change'),
			context.get('on_options_load'),
			context.get('on_option_rename'),
		)
	elif control_type == 'multiselect':
		props = 'dense options-dense use-chips'
		if page_definition.get('pflichtfeld'):
			props += ' required'
		control = ui.select(
			page_definition['optionen'],
			label=label,
			multiple=True,
			clearable=True,
		).props(props).classes('w-full')
	elif control_type == 'textarea':
		props = 'autogrow dense autocomplete="off"'
		if page_definition.get('pflichtfeld'):
			props += ' required'
		control = ui.textarea(label).props(props).classes('w-full')
	elif control_type in {'kursbuchungen', 'kursbesuche'}:
		context = context or {}
		control = CourseBookingsInput(label, context.get('options'))
	elif definition['type'] == 'iban':
		control = IbanInput(label)
	elif definition['type'] == 'euro':
		control = ui.number(
			label,
			value=euro_input_value(''),
			step=0.01,
			precision=2,
			suffix='€',
			format='%.2f',
		).props('dense inputmode=decimal autocomplete="off"').classes('w-full')
	elif definition['type'] == 'liste':
		control = CommaSeparatedListInput(label)
	else:
		validation = validate_phone if definition['type'] == 'telefon' else None
		input_props = 'dense autocomplete="off"'
		if definition['type'] == 'datum':
			input_props = 'type=date dense autocomplete="off"'
		elif definition['type'] == 'email':
			input_props = 'type=email dense autocomplete="off"'
		if page_definition.get('pflichtfeld'):
			input_props += ' required'
		control = ui.input(label, validation=validation).props(input_props).classes('w-full')

	if page_definition.get('gesperrt', False):
		control.set_enabled(False)
	return control


def create_form_control_with_description(
	config: PopelsConfig,
	field: str,
	validate_phone: Callable[[Any], str | None],
	context: dict[str, Any] | None = None,
) -> Any:
	"""
	Erzeugt ein Formularfeld mit optionaler Feldbeschreibung links daneben.
	"""
	definition = config.field_labels[field]
	page_definition = config.page(field)
	if page_definition.get('versteckt'):
		control = create_form_control(config, field, validate_phone, context)
		control.classes('hidden')
		return control

	description = str(definition.get('beschreibung') or '').strip()
	if not description:
		return create_form_control(config, field, validate_phone, context)

	with ui.row().classes('w-full gap-1 items-start'):
		with ui.dialog() as description_dialog, ui.card().classes('w-[380px] max-w-full gap-2'):
			ui.label(definition['text']).classes('text-base font-semibold text-slate-900')
			ui.label(description).classes('text-sm text-slate-700 whitespace-pre-wrap')
			with ui.row().classes('w-full justify-end'):
				ui.button('Schliessen', on_click=description_dialog.close).props('flat no-caps dense')
		ui.button(
			icon='info',
			on_click=description_dialog.open,
		).props('flat round dense size=sm').classes('mt-3 shrink-0 text-slate-500').tooltip('Feldbeschreibung')
		with ui.column().classes('flex-1 min-w-0'):
			return create_form_control(config, field, validate_phone, context)


def render_popels_form(
	config: PopelsConfig,
	validate_phone: Callable[[Any], str | None],
	on_new: Callable[[], None],
	on_save: Callable[[], None],
	control_contexts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""
	Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück.
	"""
	control_contexts = control_contexts or {}
	with ui.column().classes('w-full gap-2'):
		controls = {}
		for fields in group_form_fields(config):
			if len(fields) == 1:
				field = fields[0]
				controls[field] = create_form_control_with_description(
					config,
					field,
					validate_phone,
					control_contexts.get(field),
				)
				continue
			with ui.row().classes('w-full gap-2 items-start max-sm:flex-col'):
				for field in fields:
					with ui.column().classes('flex-1 min-w-0'):
						controls[field] = create_form_control_with_description(
							config,
							field,
							validate_phone,
							control_contexts.get(field),
						)

		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Neu', icon='add', on_click=on_new).props('flat no-caps dense').classes(
				'text-slate-700 bg-slate-100 px-3'
			)
			ui.button('Speichern', icon='save', on_click=on_save).props('no-caps dense').classes(
				'bg-primary text-white px-3'
			)

	bind_calculated_fields(config, controls)
	recalculate_form(config, controls)
	return controls


def recalculate_form(config: PopelsConfig, controls: dict[str, Any]) -> None:
	"""
	Berechnet alle mit ``berechnen`` konfigurierten Formularfelder neu.
	"""
	werte = {
		field: getattr(control, 'value', None)
		for field, control in controls.items()
	}
	for field in config.field_labels:
		formel = config.page(field).get('berechnen')
		control = controls.get(field)
		if not formel or control is None:
			continue

		try:
			ergebnis = berechne(formel, werte)
		except (TypeError, ValueError):
			ergebnis = ''

		if control.value != ergebnis:
			control.value = ergebnis
		werte[field] = ergebnis


def bind_calculated_fields(config: PopelsConfig, controls: dict[str, Any]) -> None:
	"""
	Aktualisiert berechnete Felder, sobald sich ein Eingabewert ändert.
	"""
	berechnete_felder = {
		field
		for field in config.field_labels
		if config.page(field).get('berechnen')
	}
	for field, control in controls.items():
		if field in berechnete_felder:
			continue

		on_value_change = getattr(control, 'on_value_change', None)
		if callable(on_value_change):
			on_value_change(lambda _event: recalculate_form(config, controls))


def group_form_fields(config: PopelsConfig) -> list[list[str]]:
	"""
	Gruppiert Formularfelder anhand ihrer horizontalen Position.
	"""
	groups: list[list[str]] = []
	current_group: list[str] = []
	expected_position = 1
	for field in config.form_fields:
		position = config.page(field).get('horizont', 1)
		if not isinstance(position, int) or isinstance(position, bool) or position < 1:
			position = 1
		if position == 1 or position != expected_position:
			if current_group:
				groups.append(current_group)
			current_group = [field]
			expected_position = 2
		else:
			current_group.append(field)
			expected_position += 1
	if current_group:
		groups.append(current_group)
	return groups
