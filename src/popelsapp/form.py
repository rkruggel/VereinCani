"""Aufbau eines aus Felddefinitionen erzeugten Popels-Formulars."""

from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
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
					f'dense autocomplete="new-password" name="vereingui_{autofill_key}_frei" '
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


class IbanInput:
	"""Formatiert IBAN-Werte in Vierergruppen."""

	def __init__(self, label: str) -> None:
		self._element = ui.input(label).props(
			'dense autocomplete="off" autocapitalize="characters" spellcheck="false"'
		).classes('w-full')
		self._element.on_value_change(self._format_current_value)

	@property
	def value(self) -> str:
		return format_iban(self._element.value)

	@value.setter
	def value(self, value: Any) -> None:
		self._element.value = format_iban(value)

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert das zugrunde liegende Eingabefeld."""

		self._element.set_enabled(value)

	def on_value_change(self, handler: Callable[[Any], None]) -> None:
		"""Leitet Value-Change-Events an das Eingabefeld weiter."""

		self._element.on_value_change(handler)

	def classes(self, classes: str) -> None:
		"""Leitet CSS-Klassen an das Eingabefeld weiter."""

		self._element.classes(classes)

	def _format_current_value(self, _event: Any) -> None:
		formatted = format_iban(self._element.value)
		if self._element.value != formatted:
			self._element.value = formatted


def format_iban(value: Any) -> str:
	"""Bereinigt eine IBAN und gruppiert sie in Viererblöcke."""

	compact = ''.join(
		character
		for character in str(value or '').upper()
		if character.isalnum()
	)
	return ' '.join(compact[index:index + 4] for index in range(0, len(compact), 4))


class CourseBookingsInput:
	"""Bearbeitet gebuchte Kurse als Zeilen mit Kurs, Datum und Bezahlstatus."""

	EMPTY_ROW = {'kurs': '', 'datumVon': '', 'bezahlt': None}

	def __init__(self, label: str, options: list[Any] | None = None) -> None:
		self._label = label
		self._course_definitions = self._course_definitions_from_options(options or [])
		self._options = list(self._course_definitions)
		self._rows = [self.EMPTY_ROW.copy()]
		self._controls: list[dict[str, Any]] = []
		self._enabled = True
		with ui.column().classes('w-full gap-1'):
			ui.label(label).classes('text-sm font-medium text-slate-700')

			@ui.refreshable
			def render_rows() -> None:
				self._controls.clear()
				for index, row in enumerate(self._rows):
					with ui.row().classes('w-full items-start gap-1 flex-nowrap'):
						course_options = self._course_options(row.get('kurs'))
						if course_options:
							course_control = ui.select(
								course_options,
								label='Kursname',
								value=row.get('kurs') or None,
								clearable=True,
							).props('dense options-dense').classes('flex-1 min-w-[10rem]')
						else:
							course_control = ui.input('Kursname', value=row.get('kurs', '')).props(
								'dense autocomplete="off"'
							).classes('flex-1 min-w-[10rem]')
						date_from_control = ui.input('Datum von', value=row.get('datumVon', '')).props(
							'type=date dense autocomplete="off"'
						).classes('w-28 shrink-0')
						date_to_control = ui.input(
							'Datum bis',
							value=self._calculate_date_to(row.get('kurs'), row.get('datumVon')),
						).props('type=date dense autocomplete="off" readonly').classes('w-28 shrink-0')
						paid_control = ui.select(
							['Ja', 'Nein'],
							label='Bezahlt',
							value=paid_select_value(row.get('bezahlt')),
							clearable=True,
						).props('dense options-dense').classes('w-20 shrink-0')
						for control in (course_control, date_from_control, paid_control):
							control.set_enabled(self._enabled)
						if not self._enabled:
							date_to_control.set_enabled(False)
						self._controls.append({
							'kurs': course_control,
							'datumVon': date_from_control,
							'datumBis': date_to_control,
							'bezahlt': paid_control,
						})
						def update_date_to(
							_event: Any,
							course: Any = course_control,
							date_from: Any = date_from_control,
							date_to: Any = date_to_control,
						) -> None:
							date_to.value = self._calculate_date_to(course.value, date_from.value)

						course_control.on_value_change(update_date_to)
						date_from_control.on_value_change(update_date_to)
						with ui.row().classes('ml-auto gap-0 pt-1 shrink-0'):
							delete_button = ui.button(
								icon='delete',
								on_click=lambda row_index=index: self._delete_row(row_index),
							).props('flat round dense size=sm color=negative').tooltip('Zeile löschen')
							add_button = ui.button(
								icon='add',
								on_click=lambda row_index=index: self._add_row(row_index),
							).props('flat round dense size=sm').tooltip('Neue Zeile hinzufügen')
							delete_button.set_enabled(self._enabled)
							add_button.set_enabled(self._enabled)

			self._render_rows = render_rows
			self._render_rows()

	@property
	def value(self) -> list[dict[str, Any]]:
		"""Liefert nur ausgefüllte Kursbesuchszeilen."""

		self._sync_rows()
		return [
			row
			for row in self._rows
			if row['kurs'] or row['datumVon'] or row['bezahlt'] is not None
		]

	@value.setter
	def value(self, rows: list[dict[str, Any]] | None) -> None:
		normalized_rows = self._normalize_rows(rows)
		if not normalized_rows:
			self.clear()
			return
		self._rows = normalized_rows
		self._controls.clear()
		self._render_rows.refresh()

	def clear(self) -> None:
		"""Leert Kursbesuche und vorhandene Steuerelementwerte sichtbar."""

		self._rows = [self.EMPTY_ROW.copy()]
		for controls in self._controls:
			controls['kurs'].value = None
			controls['datumVon'].value = ''
			controls['datumBis'].value = ''
			controls['bezahlt'].value = None
		self._render_rows.refresh()

	def set_enabled(self, value: bool) -> None:
		"""Aktiviert oder deaktiviert die Kursbesuchszeilen."""

		self._enabled = value
		self._render_rows.refresh()

	def _sync_rows(self) -> None:
		if not self._controls:
			return
		self._rows = [
			{
				'kurs': str(controls['kurs'].value or '').strip(),
				'datumVon': str(controls['datumVon'].value or '').strip(),
				'bezahlt': paid_bool_value(controls['bezahlt'].value),
			}
			for controls in self._controls
		]

	def _add_row(self, after_index: int) -> None:
		self._sync_rows()
		self._rows.insert(after_index + 1, self.EMPTY_ROW.copy())
		self._render_rows.refresh()

	def _delete_row(self, index: int) -> None:
		self._sync_rows()
		if 0 <= index < len(self._rows):
			self._rows.pop(index)
		if not self._rows:
			self._rows.append(self.EMPTY_ROW.copy())
		self._render_rows.refresh()

	def _course_options(self, current_value: Any) -> list[str]:
		options = list(self._options)
		current_text = str(current_value or '').strip()
		if current_text and current_text not in options:
			options.append(current_text)
		return options

	def _calculate_date_to(self, course_name: Any, date_from: Any) -> str:
		course = self._course_definitions.get(str(course_name or '').strip())
		if course is None:
			return ''
		try:
			start = date.fromisoformat(str(date_from or '').strip())
		except ValueError:
			return ''
		duration = parse_positive_int(course.get('dauer'))
		unit = str(course.get('einheit') or 'einmalig').strip().casefold()
		if duration is None or unit == 'einmalig':
			return start.isoformat()
		if unit == 'tag':
			return (start + timedelta(days=duration)).isoformat()
		if unit == 'woche':
			return (start + timedelta(weeks=duration)).isoformat()
		if unit == 'monat':
			return add_months(start, duration).isoformat()
		if unit == 'jahr':
			return add_months(start, duration * 12).isoformat()
		return ''

	@staticmethod
	def _course_definitions_from_options(options: list[Any]) -> dict[str, dict[str, Any]]:
		definitions: dict[str, dict[str, Any]] = {}
		for option in options:
			if isinstance(option, dict):
				name = str(option.get('kurs') or '').strip()
				if name:
					definitions[name] = dict(option)
				continue
			name = str(option or '').strip()
			if name:
				definitions[name] = {'kurs': name}
		return definitions

	@classmethod
	def _normalize_rows(cls, rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
		if not isinstance(rows, list):
			return []
		normalized_rows = []
		for row in rows:
			if not isinstance(row, dict):
				continue
			date_from = str(row.get('datumVon') or row.get('datum') or '').strip()
			normalized_rows.append({
				'kurs': str(row.get('kurs') or '').strip(),
				'datumVon': date_from,
				'bezahlt': paid_bool_value(row.get('bezahlt')),
			})
		return normalized_rows


def paid_select_value(value: Any) -> str | None:
	"""Bereitet den gespeicherten Bezahlstatus für das Ja/Nein-Select vor."""

	if value is None or value == '':
		return None
	return 'Ja' if paid_bool_value(value) else 'Nein'


def paid_bool_value(value: Any) -> bool | None:
	"""Normalisiert Bezahlstatus aus Select oder gespeicherten Altdaten."""

	if value is None or value == '':
		return None
	if isinstance(value, str):
		return value.strip().casefold() == 'ja'
	return bool(value)


def parse_positive_int(value: Any) -> int | None:
	"""Liest eine positive Ganzzahl aus Preisstamm-Dauerwerten."""

	text = str(value or '').strip()
	if not text:
		return None
	try:
		number = int(text)
	except ValueError:
		return None
	return number if number > 0 else None


def add_months(value: date, months: int) -> date:
	"""Addiert Monate und klemmt den Tag an das Monatsende."""

	month_index = value.month - 1 + months
	year = value.year + month_index // 12
	month = month_index % 12 + 1
	month_lengths = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	day = min(value.day, month_lengths[month - 1])
	return date(year, month, day)


def is_leap_year(year: int) -> bool:
	"""Prüft, ob ein Jahr ein Schaltjahr ist."""

	return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def euro_input_value(value: Any) -> float | None:
	"""Bereitet gespeicherte Euro-Werte für ein Zahlenfeld vor."""

	text = str(value or '').strip()
	if not text:
		return None
	try:
		return float(normalize_euro_text(text))
	except ValueError:
		return None


def normalize_euro_text(value: Any) -> str:
	"""Normalisiert einen Euro-Betrag auf zwei Nachkommastellen."""

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
	"""Erzeugt ein Formularfeld mit optionaler Feldbeschreibung links daneben."""

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
	"""Erzeugt alle Formularfelder und gibt sie nach Feldnamen indiziert zurück."""

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
