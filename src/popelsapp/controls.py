"""
Spezielle NiceGUI-Steuerelemente fuer Popels-Formulare.
"""
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from nicegui import events, ui


class RelatedRecordChips:
	"""
	Zeigt Datensatznamen als Chips und liefert intern deren stabile IDs.
	"""
	def __init__(
		self,
		label: str,
		options: dict[str, str],
		on_select: Callable[[str], None] | None = None,
	) -> None:
		"""
		Initialisiert das Chip-Feld mit ID-zu-Anzeige-Optionen.
		"""
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
		"""
		Liefert die IDs der aktuell dargestellten Datensatz-Chips.
		"""
		return [
			self._label_to_id[label]
			for label in self._element.value
			if label in self._label_to_id
		]

	@value.setter
	def value(self, record_ids: list[str] | None) -> None:
		"""
		Setzt die sichtbaren Chips anhand gespeicherter Datensatz-IDs.
		"""
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
		"""
		Aktiviert oder deaktiviert das zugrunde liegende Chip-Feld.
		"""
		self._element.set_enabled(value)

	def _select_chip(
		self,
		event: events.GenericEventArguments,
		on_select: Callable[[str], None],
	) -> None:
		"""
		Übersetzt den geklickten Chip-Text in eine ID und meldet sie zurück.
		"""
		record_id = self._label_to_id.get(str(event.args or ''))
		if record_id is not None:
			on_select(record_id)


class FreeInputChips:
	"""
	Zeigt frei eingebbare Mehrfachwerte als Chips.
	"""
	def __init__(self, label: str) -> None:
		"""
		Initialisiert Eingabezeile, Hinzufügen-Button und Chip-Anzeige.
		"""
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
				"""
				Zeichnet die aktuell eingegebenen freien Chip-Werte.
				"""
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
		"""
		Liefert die eingegebenen Chip-Werte ohne leere Einträge.
		"""
		current_value = str(self._input.value or '').strip()
		if current_value and current_value not in self._values:
			return [*self._values, current_value]
		return list(self._values)

	@value.setter
	def value(self, values: list[str] | str | None) -> None:
		"""
		Ersetzt die gespeicherten freien Chip-Werte.
		"""
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
		"""
		Aktiviert oder deaktiviert das zugrunde liegende Mehrfachfeld.
		"""
		self._enabled = value
		self._input.set_enabled(value)
		self._add_button.set_enabled(value)
		self._render_values.refresh()

	def _add_current_value(self, *_args: Any) -> None:
		"""
		Übernimmt den aktuellen Eingabetext als neuen Chip.
		"""
		text = str(self._input.value or '').strip()
		if not text:
			return
		self._values.append(text)
		self._input.value = ''
		self._render_values.refresh()

	def _remove_value(self, index: int) -> None:
		"""
		Entfernt einen freien Chip anhand seines Listenindex.
		"""
		if 0 <= index < len(self._values):
			self._values.pop(index)
		self._render_values.refresh()


class RelatedRecordSelect:
	"""
	Zeigt genau einen verknüpften Datensatz als Select und liefert dessen stabile ID.
	"""
	def __init__(
		self,
		label: str,
		options: dict[str, str],
		on_select: Callable[[str], None] | None = None,
	) -> None:
		"""
		Initialisiert ein Select mit Anzeigeoptionen und stabilen Datensatz-IDs.
		"""
		self._id_to_label = dict(options)
		self._label_to_id = {option_label: record_id for record_id, option_label in options.items()}
		self._element = ui.select(list(self._label_to_id), label=label, clearable=True).props(
			'dense options-dense'
		).classes('w-full')
		if on_select is not None:
			self._element.on_value_change(lambda _event: self._notify_selection(on_select))

	@property
	def value(self) -> str:
		"""
		Liefert die ID des aktuell ausgewählten Datensatzes.
		"""
		label = self._element.value
		return self._label_to_id.get(label, label or '')

	@value.setter
	def value(self, record_id: str | None) -> None:
		"""
		Setzt die Auswahl anhand einer gespeicherten Datensatz-ID.
		"""
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
		"""
		Aktiviert oder deaktiviert das zugrunde liegende Select-Feld.
		"""
		self._element.set_enabled(value)

	def _notify_selection(self, on_select: Callable[[str], None]) -> None:
		"""
		Meldet eine gültige Select-Auswahl an den externen Handler.
		"""
		record_id = self.value
		if record_id:
			on_select(record_id)


class EditableOptionsSelect:
	"""
	Select-Feld mit verwaltbaren Optionen.
	"""
	def __init__(
		self,
		label: str,
		options: list[str] | None = None,
		on_options_change: Callable[[list[str]], None] | None = None,
		on_options_load: Callable[[], list[str]] | None = None,
		on_option_rename: Callable[[str, str], None] | None = None,
	) -> None:
		"""
		Initialisiert Select, Optionsaktionen und Bearbeitungsdialog.
		"""
		self._options = normalize_editable_options(options or [])
		self._on_options_change = on_options_change
		self._on_options_load = on_options_load
		self._on_option_rename = on_option_rename
		self._enabled = True
		self._dialog_mode = {'value': 'add'}
		with ui.row().classes('w-full gap-1 items-start'):
			self._element = ui.select(
				self._options,
				label=label,
				clearable=True,
			).props('dense options-dense').classes('flex-1 min-w-0')
			with ui.fab('more_vert', direction='left').props('flat dense mini').classes('mt-1') as self._options_fab:
				ui.fab_action('add', on_click=lambda: self._open_option_dialog('add')).props('dense mini').tooltip('Wert hinzufügen')
				ui.fab_action('edit', on_click=lambda: self._open_option_dialog('edit')).props('dense mini').tooltip('Wert ändern')
				ui.fab_action('delete', on_click=self._delete_current_option, color='negative').props('dense mini').tooltip('Wert löschen')

		with ui.dialog() as option_dialog, ui.card().classes('w-[360px] max-w-full gap-3'):
			self._dialog_title = ui.label('Wert hinzufügen').classes('text-lg font-semibold text-slate-900')
			self._option_input = ui.input('Wert').props('dense autocomplete="off"').classes('w-full')
			with ui.row().classes('w-full justify-end gap-2'):
				ui.button('Abbrechen', on_click=option_dialog.close).props('flat no-caps dense')
				ui.button('Speichern', on_click=lambda: self._save_option_dialog(option_dialog)).props('no-caps dense')
		self._option_dialog = option_dialog

	@property
	def value(self) -> str:
		"""
		Liefert die aktuell ausgewählte Option als bereinigten Text.
		"""
		return str(self._element.value or '').strip()

	@value.setter
	def value(self, value: Any) -> None:
		"""
		Setzt die Auswahl und ergänzt unbekannte Werte als neue Option.
		"""
		text = str(value or '').strip()
		if not text:
			self._element.value = None
			return
		if text not in self._options:
			self._options.append(text)
			self._options = normalize_editable_options(self._options)
			self._refresh_options()
			self._persist_options()
		self._element.value = text

	def set_enabled(self, value: bool) -> None:
		"""
		Aktiviert oder deaktiviert Feld und Optionsaktionen.
		"""
		self._enabled = value
		self._element.set_enabled(value)
		self._options_fab.set_enabled(value)

	def on_value_change(self, handler: Callable[[Any], None]) -> None:
		"""
		Leitet Value-Change-Events an das Select weiter.
		"""
		self._element.on_value_change(handler)

	def classes(self, classes: str) -> None:
		"""
		Leitet CSS-Klassen an das Select weiter.
		"""
		self._element.classes(classes)

	def _open_option_dialog(self, mode: str) -> None:
		"""
		Öffnet den Dialog zum Hinzufügen oder Bearbeiten einer Option.
		"""
		if not self._enabled:
			return
		self._reload_options()
		current_value = self.value
		if mode == 'edit' and not current_value:
			ui.notify('Bitte zuerst einen Wert auswählen.', type='warning')
			return
		self._dialog_mode['value'] = mode
		self._dialog_title.set_text('Wert ändern' if mode == 'edit' else 'Wert hinzufügen')
		self._option_input.value = current_value if mode == 'edit' else ''
		self._option_dialog.open()
		ui.timer(0.1, lambda: self._option_input.run_method('focus'), once=True)

	def _save_option_dialog(self, dialog: Any) -> None:
		"""
		Speichert den Dialogwert als neue oder umbenannte Option.
		"""
		text = str(self._option_input.value or '').strip()
		if not text:
			ui.notify('Bitte einen Wert eingeben.', type='warning')
			return
		current_value = self.value
		renamed_value = current_value if self._dialog_mode['value'] == 'edit' and current_value in self._options else ''
		if self._dialog_mode['value'] == 'edit' and current_value in self._options:
			self._options = [text if option == current_value else option for option in self._options]
		else:
			self._options.append(text)
		self._options = normalize_editable_options(self._options)
		self._refresh_options()
		self._element.value = text
		self._persist_options()
		if renamed_value and renamed_value != text:
			self._rename_option(renamed_value, text)
		self._reload_options(text)
		dialog.close()

	def _delete_current_option(self) -> None:
		"""
		Löscht die aktuell ausgewählte Option aus der Optionsliste.
		"""
		if not self._enabled:
			return
		self._reload_options()
		current_value = self.value
		if not current_value:
			ui.notify('Bitte zuerst einen Wert auswählen.', type='warning')
			return
		self._options = [option for option in self._options if option != current_value]
		self._refresh_options()
		self._element.value = None
		self._persist_options()
		self._reload_options()

	def _refresh_options(self) -> None:
		"""
		Überträgt die interne Optionsliste in das sichtbare Select.
		"""
		current_value = self.value
		next_value = current_value if current_value in self._options else None
		self._element.set_options(list(self._options), value=next_value)

	def _reload_options(self, selected_value: str | None = None) -> None:
		"""
		Lädt Optionswerte über den optionalen externen Loader neu.
		"""
		if self._on_options_load is None:
			return
		current_value = selected_value if selected_value is not None else self.value
		try:
			self._options = normalize_editable_options(self._on_options_load())
		except Exception as error:
			ui.notify(f'Werte konnten nicht geladen werden: {error}', type='warning')
			return
		self._refresh_options()
		if current_value and current_value in self._options:
			self._element.value = current_value

	def _rename_option(self, old_value: str, new_value: str) -> None:
		"""
		Meldet eine Optionsumbenennung an den optionalen externen Handler.
		"""
		if self._on_option_rename is None:
			return
		try:
			self._on_option_rename(old_value, new_value)
		except Exception as error:
			ui.notify(f'Geänderte Werte konnten nicht übernommen werden: {error}', type='warning')

	def _persist_options(self) -> None:
		"""
		Speichert die aktuelle Optionsliste über den optionalen Callback.
		"""
		if self._on_options_change is not None:
			self._on_options_change(list(self._options))


def normalize_editable_options(options: list[Any]) -> list[str]:
	"""
	Normalisiert editierbare Select-Optionen eindeutig und sortiert.
	"""
	seen = set()
	result = []
	for option in options:
		text = str(option or '').strip()
		if not text or text.casefold() in seen:
			continue
		seen.add(text.casefold())
		result.append(text)
	return sorted(result, key=str.casefold)


class CommaSeparatedListInput:
	"""
	Bearbeitet Listenwerte als kommagetrennte Eingabezeile.
	"""
	def __init__(self, label: str) -> None:
		"""
		Initialisiert eine Eingabezeile für kommagetrennte Listenwerte.
		"""
		self._element = ui.input(label).props(
			'dense autocomplete="off"'
		).classes('w-full')

	@property
	def value(self) -> list[str]:
		"""
		Liefert die kommagetrennten Eingaben als Liste.
		"""
		return [
			item.strip()
			for item in str(self._element.value or '').split(',')
			if item.strip()
		]

	@value.setter
	def value(self, values: list[str] | str | None) -> None:
		"""
		Setzt die Eingabezeile aus einer Liste oder einem Rohtext.
		"""
		if values in (None, ''):
			self._element.value = ''
			return
		if isinstance(values, list):
			self._element.value = ', '.join(str(item) for item in values if str(item).strip())
			return
		self._element.value = str(values)

	def set_enabled(self, value: bool) -> None:
		"""
		Aktiviert oder deaktiviert das zugrunde liegende Eingabefeld.
		"""
		self._element.set_enabled(value)

	def on_value_change(self, handler: Callable[[Any], None]) -> None:
		"""
		Leitet Value-Change-Events an das Eingabefeld weiter.
		"""
		self._element.on_value_change(handler)


class IbanInput:
	"""
	Formatiert IBAN-Werte in Vierergruppen.
	"""
	def __init__(self, label: str) -> None:
		"""
		Initialisiert ein IBAN-Feld mit automatischer Formatierung.
		"""
		self._element = ui.input(label).props(
			'dense autocomplete="off" autocapitalize="characters" spellcheck="false"'
		).classes('w-full')
		self._element.on_value_change(self._format_current_value)

	@property
	def value(self) -> str:
		"""
		Liefert die formatierte IBAN aus dem Eingabefeld.
		"""
		return format_iban(self._element.value)

	@value.setter
	def value(self, value: Any) -> None:
		"""
		Setzt und formatiert den IBAN-Wert im Eingabefeld.
		"""
		self._element.value = format_iban(value)

	def set_enabled(self, value: bool) -> None:
		"""
		Aktiviert oder deaktiviert das zugrunde liegende Eingabefeld.
		"""
		self._element.set_enabled(value)

	def on_value_change(self, handler: Callable[[Any], None]) -> None:
		"""
		Leitet Value-Change-Events an das Eingabefeld weiter.
		"""
		self._element.on_value_change(handler)

	def classes(self, classes: str) -> None:
		"""
		Leitet CSS-Klassen an das Eingabefeld weiter.
		"""
		self._element.classes(classes)

	def _format_current_value(self, _event: Any) -> None:
		"""
		Normalisiert den sichtbaren IBAN-Wert nach einer Eingabeänderung.
		"""
		formatted = format_iban(self._element.value)
		if self._element.value != formatted:
			self._element.value = formatted


def format_iban(value: Any) -> str:
	"""
	Bereinigt eine IBAN und gruppiert sie in Viererblöcke.
	"""
	compact = ''.join(
		character
		for character in str(value or '').upper()
		if character.isalnum()
	)
	return ' '.join(compact[index:index + 4] for index in range(0, len(compact), 4))


class CourseBookingsInput:
	"""
	Bearbeitet gebuchte Kurse als Zeilen mit Kurs, Datum und Bezahlstatus.
	"""
	EMPTY_ROW = {'kurs': '', 'datumVon': '', 'bezahlt': None}

	def __init__(self, label: str, options: list[Any] | None = None) -> None:
		"""
		Initialisiert Kursbuchungszeilen mit optionalen Kursdefinitionen.
		"""
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
				"""
				Zeichnet alle Kursbuchungszeilen und ihre Aktionsbuttons.
				"""
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
							"""
							Aktualisiert das berechnete Enddatum einer Kurszeile.
							"""
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
		"""
		Liefert nur ausgefüllte Kursbesuchszeilen.
		"""
		self._sync_rows()
		return [
			row
			for row in self._rows
			if row['kurs'] or row['datumVon'] or row['bezahlt'] is not None
		]

	@value.setter
	def value(self, rows: list[dict[str, Any]] | None) -> None:
		"""
		Setzt die Kursbuchungszeilen aus gespeicherten Rohdaten.
		"""
		normalized_rows = self._normalize_rows(rows)
		if not normalized_rows:
			self.clear()
			return
		self._rows = normalized_rows
		self._controls.clear()
		self._render_rows.refresh()

	def clear(self) -> None:
		"""
		Leert Kursbesuche und vorhandene Steuerelementwerte sichtbar.
		"""
		self._rows = [self.EMPTY_ROW.copy()]
		for controls in self._controls:
			controls['kurs'].value = None
			controls['datumVon'].value = ''
			controls['datumBis'].value = ''
			controls['bezahlt'].value = None
		self._render_rows.refresh()

	def set_enabled(self, value: bool) -> None:
		"""
		Aktiviert oder deaktiviert die Kursbesuchszeilen.
		"""
		self._enabled = value
		self._render_rows.refresh()

	def _sync_rows(self) -> None:
		"""
		Schreibt die sichtbaren Steuerelementwerte in die interne Zeilenliste.
		"""
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
		"""
		Fügt nach der angegebenen Position eine leere Kurszeile ein.
		"""
		self._sync_rows()
		self._rows.insert(after_index + 1, self.EMPTY_ROW.copy())
		self._render_rows.refresh()

	def _delete_row(self, index: int) -> None:
		"""
		Entfernt eine Kurszeile und hält mindestens eine Leerzeile vor.
		"""
		self._sync_rows()
		if 0 <= index < len(self._rows):
			self._rows.pop(index)
		if not self._rows:
			self._rows.append(self.EMPTY_ROW.copy())
		self._render_rows.refresh()

	def _course_options(self, current_value: Any) -> list[str]:
		"""
		Liefert Kursoptionen inklusive eines noch unbekannten aktuellen Werts.
		"""
		options = list(self._options)
		current_text = str(current_value or '').strip()
		if current_text and current_text not in options:
			options.append(current_text)
		return options

	def _calculate_date_to(self, course_name: Any, date_from: Any) -> str:
		"""
		Berechnet das Kursende aus Kursdefinition und Startdatum.
		"""
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
		"""
		Normalisiert Kursoptionen zu einem Namensindex mit Kursdefinitionen.
		"""
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
		"""
		Bereinigt gespeicherte Kursbuchungszeilen für die interne Darstellung.
		"""
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
	"""
	Bereitet den gespeicherten Bezahlstatus für das Ja/Nein-Select vor.
	"""
	if value is None or value == '':
		return None
	return 'Ja' if paid_bool_value(value) else 'Nein'


def paid_bool_value(value: Any) -> bool | None:
	"""
	Normalisiert Bezahlstatus aus Select oder gespeicherten Altdaten.
	"""
	if value is None or value == '':
		return None
	if isinstance(value, str):
		return value.strip().casefold() == 'ja'
	return bool(value)


def parse_positive_int(value: Any) -> int | None:
	"""
	Liest eine positive Ganzzahl aus Preisstamm-Dauerwerten.
	"""
	text = str(value or '').strip()
	if not text:
		return None
	try:
		number = int(text)
	except ValueError:
		return None
	return number if number > 0 else None


def add_months(value: date, months: int) -> date:
	"""
	Addiert Monate und klemmt den Tag an das Monatsende.
	"""
	month_index = value.month - 1 + months
	year = value.year + month_index // 12
	month = month_index % 12 + 1
	month_lengths = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	day = min(value.day, month_lengths[month - 1])
	return date(year, month, day)


def is_leap_year(year: int) -> bool:
	"""
	Prüft, ob ein Jahr ein Schaltjahr ist.
	"""
	return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

