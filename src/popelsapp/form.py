"""Aufbau eines aus Felddefinitionen erzeugten Popels-Formulars."""

from collections.abc import Callable
from typing import Any

from nicegui import events, ui

from src.popelsapp import PopelsConfig
from src.services.calc import berechne


class RelatedRecordChips:
	"""Zeigt Datensatznamen als Chips und liefert intern deren stabile IDs."""

	def __init__(
		self,
		label: str,
		options: dict[str, str],
		on_select: Callable[[str], None] | None = None,
	) -> None:
		self._id_to_label = dict(options)
		self._label_to_id = {option_label: record_id for record_id, option_label in options.items()}
		self._element = ui.input_chips(label, clearable=True).props('dense options-dense')
		self._element._props['options'] = list(self._label_to_id)  # pylint: disable=protected-access
		self._element._props['hide-dropdown-icon'] = False  # pylint: disable=protected-access
		self._element._props.pop('new-value-mode', None)  # pylint: disable=protected-access
		if on_select is not None:
			self._element.on(
				'click.capture',
				lambda event: self._select_chip(event, on_select),
				js_handler='''
					(event) => {
						if (event.target.closest('.q-chip__icon--remove')) return;
						const chip = event.target.closest('.q-chip');
						const content = chip?.querySelector('.q-chip__content');
						if (!content) return;
						event.preventDefault();
						event.stopPropagation();
						event.currentTarget.querySelectorAll('.q-chip').forEach(item => {
							item.style.backgroundColor = '';
							item.style.color = '';
						});
						chip.style.backgroundColor = 'var(--q-primary)';
						chip.style.color = 'white';
						emit(content.innerText.trim());
					}
				''',
			)
		self._element.classes('w-full')

	@property
	def value(self) -> list[str]:
		"""Liefert die IDs der aktuell dargestellten Datensatz-Chips."""

		return [
			self._label_to_id[label]
			for label in self._element.value
			if label in self._label_to_id
		]

	@value.setter
	def value(self, record_ids: list[str] | None) -> None:
		labels = []
		for record_id in record_ids or []:
			if record_id in self._id_to_label:
				labels.append(self._id_to_label[record_id])
			elif record_id in self._label_to_id:
				labels.append(record_id)
			else:
				self._id_to_label[record_id] = record_id
				self._label_to_id[record_id] = record_id
				labels.append(record_id)
		self._element._props['options'] = list(self._label_to_id)  # pylint: disable=protected-access
		self._element.value = labels

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert das zugrunde liegende Chip-Feld."""

		self._element.set_enabled(value)

	def _select_chip(
		self,
		event: events.GenericEventArguments,
		on_select: Callable[[str], None],
	) -> None:
		record_id = self._label_to_id.get(str(event.args or ''))
		if record_id is not None:
			on_select(record_id)


class FreeInputChips:
	"""Zeigt frei eingebbare Mehrfachwerte als Chips."""

	def __init__(self, label: str) -> None:
		self._values: list[str] = []
		self._enabled = True
		autofill_key = ''.join(character for character in label.lower() if character.isalnum()) or 'wert'
		with ui.column().classes('w-full gap-1'):
			with ui.row().classes('w-full gap-1 items-start'):
				self._input = ui.input(label).props(
					f'dense autocomplete="new-password" name="vereincani_{autofill_key}_frei" '
					'autocorrect="off" autocapitalize="off" spellcheck="false"'
				).classes('flex-1')
				self._add_button = ui.button(
					icon='add',
					on_click=self._add_current_value,
				).props('flat round dense').classes('text-primary')
			self._input.on('keydown.enter', self._add_current_value)

			@ui.refreshable
			def render_values() -> None:
				if not self._values:
					return
				with ui.row().classes('w-full gap-1 flex-wrap'):
					for index, value in enumerate(self._values):
						with ui.row().classes('items-center gap-1 rounded-full bg-slate-100 px-2 py-1'):
							ui.label(value).classes('text-sm text-slate-700')
							delete_button = ui.button(
								icon='close',
								on_click=lambda selected_index=index: self._remove_value(selected_index),
							).props('flat round dense size=xs').classes('text-slate-500')
							delete_button.set_enabled(self._enabled)

			self._render_values = render_values
			self._render_values()

	@property
	def value(self) -> list[str]:
		"""Liefert die eingegebenen Chip-Werte ohne leere Einträge."""

		current_value = str(self._input.value or '').strip()
		if current_value and current_value not in self._values:
			return [*self._values, current_value]
		return list(self._values)

	@value.setter
	def value(self, values: list[str] | str | None) -> None:
		if values in (None, ''):
			self._values = []
			self._render_values.refresh()
			return
		raw_values = values if isinstance(values, list) else [values]
		self._values = [
			str(item).strip()
			for item in raw_values
			if str(item).strip()
		]
		self._render_values.refresh()

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert das zugrunde liegende Mehrfachfeld."""

		self._enabled = value
		self._input.set_enabled(value)
		self._add_button.set_enabled(value)
		self._render_values.refresh()

	def _add_current_value(self, *_args: Any) -> None:
		text = str(self._input.value or '').strip()
		if not text:
			return
		self._values.append(text)
		self._input.value = ''
		self._render_values.refresh()

	def _remove_value(self, index: int) -> None:
		if 0 <= index < len(self._values):
			self._values.pop(index)
		self._render_values.refresh()


class RelatedRecordSelect:
	"""Zeigt genau einen verknüpften Datensatz als Select und liefert dessen stabile ID."""

	def __init__(
		self,
		label: str,
		options: dict[str, str],
		on_select: Callable[[str], None] | None = None,
	) -> None:
		self._id_to_label = dict(options)
		self._label_to_id = {option_label: record_id for record_id, option_label in options.items()}
		self._element = ui.select(list(self._label_to_id), label=label, clearable=True).props(
			'dense options-dense'
		).classes('w-full')
		if on_select is not None:
			self._element.on_value_change(lambda _event: self._notify_selection(on_select))

	@property
	def value(self) -> str:
		"""Liefert die ID des aktuell ausgewählten Datensatzes."""

		label = self._element.value
		return self._label_to_id.get(label, label or '')

	@value.setter
	def value(self, record_id: str | None) -> None:
		if record_id in (None, ''):
			self._element.value = None
			return
		if record_id in self._id_to_label:
			self._element.value = self._id_to_label[record_id]
			return
		if record_id in self._label_to_id:
			self._element.value = record_id
			return
		text = str(record_id)
		self._id_to_label[text] = text
		self._label_to_id[text] = text
		self._element._props['options'] = list(self._label_to_id)  # pylint: disable=protected-access
		self._element.value = text

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert das zugrunde liegende Select-Feld."""

		self._element.set_enabled(value)

	def _notify_selection(self, on_select: Callable[[str], None]) -> None:
		record_id = self.value
		if record_id:
			on_select(record_id)


class CommaSeparatedListInput:
	"""Bearbeitet Listenwerte als kommagetrennte Eingabezeile."""

	def __init__(self, label: str) -> None:
		self._element = ui.input(label).props(
			'dense autocomplete="off"'
		).classes('w-full')

	@property
	def value(self) -> list[str]:
		"""Liefert die kommagetrennten Eingaben als Liste."""

		return [
			item.strip()
			for item in str(self._element.value or '').split(',')
			if item.strip()
		]

	@value.setter
	def value(self, values: list[str] | str | None) -> None:
		if values in (None, ''):
			self._element.value = ''
			return
		if isinstance(values, list):
			self._element.value = ', '.join(str(item) for item in values if str(item).strip())
			return
		self._element.value = str(values)

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert das zugrunde liegende Eingabefeld."""

		self._element.set_enabled(value)

	def on_value_change(self, handler: Callable[[Any], None]) -> None:
		"""Leitet Value-Change-Events an das Eingabefeld weiter."""

		self._element.on_value_change(handler)


def create_form_control(
	config: PopelsConfig,
	field: str,
	validate_phone: Callable[[Any], str | None],
	context: dict[str, Any] | None = None,
) -> Any:
	"""Erzeugt das in den Feldmetadaten konfigurierte NiceGUI-Steuerelement."""

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
	elif definition['type'] == 'liste':
		control = CommaSeparatedListInput(label)
	else:
		validation = validate_phone if definition['type'] == 'telefon' else None
		input_props = 'dense autocomplete="off"'
		if definition['type'] == 'datum':
			input_props = 'type=date dense autocomplete="off"'
		elif definition['type'] == 'email':
			input_props = 'type=email dense autocomplete="off"'
		elif config.key == 'mitglieder' and field == 'preis':
			input_props = f'{input_props} suffix="€"'
		if page_definition.get('pflichtfeld'):
			input_props += ' required'
		control = ui.input(label, validation=validation).props(input_props).classes('w-full')

	if page_definition.get('gesperrt', False):
		control.set_enabled(False)
	return control


def render_popels_form(
	config: PopelsConfig,
	validate_phone: Callable[[Any], str | None],
	on_new: Callable[[], None],
	on_save: Callable[[], None],
	control_contexts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück."""

	control_contexts = control_contexts or {}
	with ui.column().classes('w-full gap-2'):
		controls = {}
		for fields in group_form_fields(config):
			if len(fields) == 1:
				field = fields[0]
				controls[field] = create_form_control(
					config,
					field,
					validate_phone,
					control_contexts.get(field),
				)
				continue
			with ui.row().classes('w-full gap-2 items-start max-sm:flex-col'):
				for field in fields:
					with ui.column().classes('flex-1 min-w-0'):
						controls[field] = create_form_control(
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
	"""Berechnet alle mit ``berechnen`` konfigurierten Formularfelder neu."""

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
	"""Aktualisiert berechnete Felder, sobald sich ein Eingabewert ändert."""

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
	"""Gruppiert Formularfelder anhand ihrer horizontalen Position."""

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
