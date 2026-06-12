"""NiceGUI-Seite zur Pflege, Suche und Anzeige konfigurierbarer Popels."""

from functools import partial
from typing import Any

from nicegui import events, ui

from src.auth.session import get_authenticated_user
from src.popelsapp import PopelsConfig
from src.popelsapp.form import recalculate_form, render_popels_form
from src.popelsapp.list_logic import (
	cycle_sort_criterion,
	content_available as configured_content_available,
	display_value as configured_display_value,
	filter_records as configured_filter_records,
	image_data_url,
	record_heading as configured_record_heading,
	validate_phone,
)
from src.popelsapp.preferences import load_sort_criteria, load_visible_fields, save_visible_fields
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


def render_popels_page(
	config: PopelsConfig,
	database: CouchPopelsDatabase,
	settings: ListeneinstellungenRepository,
	form_control_contexts: dict[str, dict[str, Any]] | None = None,
	initial_record_id: str | None = None,
	clear_form_after_save: bool = True,
) -> None:
	"""Erzeugt eine vollständige Popels-Seite für den angemeldeten Benutzer."""

	benutzer = get_authenticated_user()
	if benutzer is None:
		ui.notify('Bitte zuerst anmelden.', type='warning')
		return
	POPELS_FIELDS = config.field_labels
	FORM_FIELDS = config.form_fields
	REQUIRED_FIELDS = config.required_fields
	SORT_FIELDS = config.sort_fields
	CONTENT_ACTION_FIELDS = config.content_action_fields
	EDITOR_FIELD = config.editor_field
	PAGE_TOP_ANCHOR_ID = f'{config.key}-page-top'
	POPELS_DB = database
	LISTEN_EINSTELLUNGEN = settings
	list_fields = config.list_fields
	filter_records = partial(configured_filter_records, config)
	display_value = partial(configured_display_value, config)
	content_available = partial(configured_content_available, config)
	record_heading = partial(configured_record_heading, config)
	benutzer_name = benutzer['name']
	selected_id = {'value': None}
	form_controls: dict[str, Any] = {}
	mode_label = {'element': None}
	search_query = {'value': ''}
	search_input = {'element': None}
	text_value = {'value': ''}
	text_editor = {'element': None}
	text_save_button = {'element': None}
	image_upload = {'element': None}
	image_caption_draft = {'value': ''}
	uploaded_images: list[dict[str, Any]] = []
	selected_image = {'attachment_name': None}
	pending_delete = {'record_id': None, 'name': ''}
	try:
		visible_fields = load_visible_fields(config, settings, benutzer_name)
		sort_criteria = {'value': load_sort_criteria(config, settings, benutzer_name)}
	except Exception as error:
		visible_fields = {'id', *FORM_FIELDS} & set(config.list_display_fields)
		sort_criteria = {'value': []}
		ui.notify(f'Listeneinstellungen konnten nicht geladen werden: {error}', type='warning')

	def collect_form_data() -> dict[str, Any]:
		"""Liest die aktuellen Werte aller Steuerelemente des Popels-Formulars."""

		return {
			field: form_controls[field].value
			for field in FORM_FIELDS
			if not config.page(field).get('berechnen')
		}

	def clear_form() -> None:
		"""Setzt Formular, Text, Bilder und aktive Datensatzauswahl zurück."""

		selected_id['value'] = None
		text_value['value'] = ''
		uploaded_images.clear()
		selected_image['attachment_name'] = None
		for field in FORM_FIELDS:
			form_controls[field].value = [] if POPELS_FIELDS[field]['type'] == 'liste' else ''
		recalculate_form(config, form_controls)
		if mode_label['element'] is not None:
			mode_label['element'].set_text(f'Neue {config.singular}')
		if text_editor['element'] is not None:
			text_editor['element'].value = ''
		if text_save_button['element'] is not None:
			text_save_button['element'].set_enabled(False)
		render_uploaded_images.refresh()
		render_active_actions.refresh()

	def scroll_to_page_top() -> None:
		"""Scrollt den Arbeitsbereich zum Anfang des Popels-Formulars."""

		ui.run_javascript(
			f'document.getElementById("{PAGE_TOP_ANCHOR_ID}")'
			'?.scrollIntoView({behavior: "smooth", block: "start"});'
		)

	def load_record(record_id: str, *, scroll: bool = True) -> None:
		"""Lädt einen Datensatz samt Text und Bildern in den Bearbeitungszustand."""

		if scroll:
			scroll_to_page_top()
		try:
			record = POPELS_DB.get(record_id)
		except Exception as error:
			ui.notify(f'CouchDB nicht erreichbar: {error}', type='negative')
			return
		if record is None:
			ui.notify(f'{config.singular} nicht gefunden', type='warning')
			return
		selected_id['value'] = record_id
		text_value['value'] = str(record.get(EDITOR_FIELD) or '')
		if text_editor['element'] is not None:
			text_editor['element'].value = text_value['value']
		if text_save_button['element'] is not None:
			text_save_button['element'].set_enabled(False)
		try:
			images = POPELS_DB.get_images(record_id)
		except Exception as error:
			ui.notify(f'Bilder konnten nicht geladen werden: {error}', type='warning')
			images = []
		uploaded_images.clear()
		uploaded_images.extend({
			'attachment_name': image['attachment_name'],
			'name': image['name'],
			'content_type': image['content_type'],
			'caption': image.get('caption', ''),
			'source': image_data_url(image['content_type'], image['data']),
		} for image in images)
		selected_image['attachment_name'] = None
		render_uploaded_images.refresh()
		render_active_actions.refresh()
		for field in FORM_FIELDS:
			form_controls[field].value = record.get(field, '')
		recalculate_form(config, form_controls)
		if mode_label['element'] is not None:
			mode_label['element'].set_text(f'{config.singular} bearbeiten: {record_heading(record)}')

	def save_record() -> None:
		"""Validiert und erstellt beziehungsweise aktualisiert einen Datensatz."""

		data = collect_form_data()
		missing_fields = [
			POPELS_FIELDS[field]['text']
			for field in REQUIRED_FIELDS
			if not str(data.get(field) or '').strip()
		]
		if missing_fields:
			ui.notify(f'Pflichtfelder ausfüllen: {", ".join(missing_fields)}', type='warning')
			return
		for field in FORM_FIELDS:
			if POPELS_FIELDS[field]['type'] != 'telefon':
				continue
			if validate_phone(data[field]) is not None:
				ui.notify(
					f'{POPELS_FIELDS[field]["text"]} darf nur Zahlen, + und Leerzeichen enthalten',
					type='warning',
				)
				return

		if selected_id['value'] is None:
			try:
				record = POPELS_DB.create(data)
			except Exception as error:
				ui.notify(f'{config.singular} konnte nicht gespeichert werden: {error}', type='negative')
				return
			ui.notify(f'{config.singular} #{record["id"]} angelegt')
		else:
			try:
				record = POPELS_DB.update(selected_id['value'], data)
			except Exception as error:
				ui.notify(f'{config.singular} konnte nicht gespeichert werden: {error}', type='negative')
				return
			if record is None:
				ui.notify(f'{config.singular} nicht gefunden', type='warning')
				return
			ui.notify(f'{config.singular} #{selected_id["value"]} gespeichert')
		if clear_form_after_save:
			clear_form()
		render_records.refresh()

	def request_delete_record(record_id: str, name: str) -> None:
		"""Bereitet den Bestätigungsdialog für das Löschen eines Datensatzes vor."""

		scroll_to_page_top()
		pending_delete['record_id'] = record_id
		pending_delete['name'] = name
		delete_dialog_text.set_text(f'Soll {config.singular} "{name}" wirklich geloescht werden?')
		delete_dialog.open()

	def delete_record() -> None:
		"""Löscht den im Bestätigungsdialog vorgemerkten Datensatz."""

		record_id = pending_delete['record_id']
		if record_id is None:
			delete_dialog.close()
			return
		try:
			deleted = POPELS_DB.delete(record_id)
		except Exception as error:
			ui.notify(f'{config.singular} konnte nicht geloescht werden: {error}', type='negative')
			return
		delete_dialog.close()
		pending_delete['record_id'] = None
		pending_delete['name'] = ''
		if deleted:
			if selected_id['value'] == record_id:
				clear_form()
			ui.notify(f'{config.singular} #{record_id} geloescht')
			render_records.refresh()
		else:
			ui.notify(f'{config.singular} nicht gefunden', type='warning')

	def set_field_visibility(field: str, visible: bool | None) -> None:
		"""Ändert und speichert die Sichtbarkeit eines Feldes in der Popels-Liste."""

		if visible:
			visible_fields.add(field)
		else:
			visible_fields.discard(field)
		try:
			save_visible_fields(config, settings, benutzer_name, visible_fields)
		except Exception as error:
			ui.notify(f'Listeneinstellungen konnten nicht gespeichert werden: {error}', type='negative')
			return
		render_records.refresh()

	def cycle_sort_field(field: str) -> None:
		"""Schaltet die Sortierrichtung eines Feldes weiter und speichert sie."""

		new_sortierungen = cycle_sort_criterion(sort_criteria['value'], field)
		try:
			LISTEN_EINSTELLUNGEN.save_sortierungen(benutzer_name, new_sortierungen)
		except Exception as error:
			ui.notify(f'Sortierung konnte nicht gespeichert werden: {error}', type='negative')
			return
		sort_criteria['value'] = new_sortierungen
		render_sort_controls.refresh()
		render_records.refresh()

	def clear_sorting() -> None:
		"""Entfernt die gespeicherte Sortierung."""

		default_sortierungen: list[str] = []
		try:
			LISTEN_EINSTELLUNGEN.save_sortierungen(benutzer_name, default_sortierungen)
		except Exception as error:
			ui.notify(f'Sortierung konnte nicht gespeichert werden: {error}', type='negative')
			return
		sort_criteria['value'] = default_sortierungen
		render_sort_controls.refresh()
		render_records.refresh()

	def apply_search() -> None:
		"""Übernimmt den Suchtext und aktualisiert die Popels-Liste."""

		search_query['value'] = str(search_input['element'].value or '').strip()
		search_dialog.close()
		render_records.refresh()

	def clear_search() -> None:
		"""Leert den Suchtext und zeigt wieder alle Popels-Datensätze an."""

		search_query['value'] = ''
		if search_input['element'] is not None:
			search_input['element'].value = ''
		search_dialog.close()
		render_records.refresh()

	def save_text() -> None:
		"""Speichert den freien Text des aktuell bearbeiteten Datensatzes."""

		record_id = selected_id['value']
		if record_id is None:
			ui.notify(f'Bitte zuerst {config.singular} auswaehlen.', type='warning')
			return
		value = str(text_editor['element'].value or '')
		try:
			saved = POPELS_DB.update_text(record_id, value)
		except Exception as error:
			ui.notify(f'Text konnte nicht gespeichert werden: {error}', type='negative')
			return
		if not saved:
			ui.notify(f'{config.singular} nicht gefunden', type='warning')
			return
		text_value['value'] = value
		text_save_button['element'].set_enabled(False)
		text_dialog.close()
		ui.notify('Text wurde gespeichert.')
		render_records.refresh()

	def handle_text_change(event: events.ValueChangeEventArguments) -> None:
		"""Aktiviert das Speichern nur bei einer Änderung des Editor-Inhalts."""

		changed = str(event.value or '') != text_value['value']
		text_save_button['element'].set_enabled(changed)

	def cancel_text_editing() -> None:
		"""Verwirft ungespeicherte Editor-Änderungen und schließt den Dialog."""

		text_editor['element'].value = text_value['value']
		text_save_button['element'].set_enabled(False)
		text_dialog.close()

	async def handle_image_upload(event: events.UploadEventArguments) -> None:
		"""Prüft und speichert ein hochgeladenes Bild für den aktiven Datensatz."""

		record_id = selected_id['value']
		if record_id is None:
			ui.notify(f'Bitte zuerst {config.singular} auswaehlen.', type='warning')
			return
		content_type = event.file.content_type or ''
		if not content_type.startswith('image/'):
			ui.notify(f'{event.file.name} ist keine Bilddatei.', type='warning')
			return
		data = await event.file.read()
		try:
			image = POPELS_DB.add_image(
				record_id,
				event.file.name,
				content_type,
				data,
				image_caption_draft['value'],
			)
		except Exception as error:
			ui.notify(f'Bild konnte nicht gespeichert werden: {error}', type='negative')
			return
		if image is None:
			ui.notify(f'{config.singular} nicht gefunden', type='warning')
			return
		uploaded_images.append({
			**image,
			'caption': image.get('caption', ''),
			'source': image_data_url(content_type, data),
		})
		render_uploaded_images.refresh()
		render_records.refresh()
		ui.notify(f'{event.file.name} wurde gespeichert.')
		image_caption_draft['value'] = ''
		render_records.refresh()

	def update_image_caption(attachment_name: str, caption: str | None) -> None:
		"""Speichert den Kurztext zu einem Bild dauerhaft."""

		record_id = selected_id['value']
		if record_id is None:
			ui.notify(f'Bitte zuerst {config.singular} auswaehlen.', type='warning')
			return
		try:
			saved = POPELS_DB.update_image_caption(record_id, attachment_name, caption or '')
		except Exception as error:
			ui.notify(f'Bildtext konnte nicht gespeichert werden: {error}', type='negative')
			return
		if not saved:
			ui.notify('Bild nicht gefunden.', type='warning')
			return
		for image in uploaded_images:
			if image['attachment_name'] == attachment_name:
				image['caption'] = caption or ''
				break

	def handle_rejected_images() -> None:
		"""Informiert über abgelehnte Bilddateien oder überschrittene Uploadgrenzen."""

		ui.notify(
			'Bild abgelehnt. Pro Auswahl sind maximal 50 Bilder mit jeweils bis zu 50 MB erlaubt.',
			type='warning',
		)

	def upload_selected_images() -> None:
		"""Startet den Upload der lokal ausgewählten Dateien."""

		image_upload['element'].run_method('upload')

	def reset_image_upload() -> None:
		"""Leert die Upload-Warteschlange nach abgeschlossenem Mehrfach-Upload."""

		image_upload['element'].reset()

	def select_image(attachment_name: str, selected: bool | None) -> None:
		"""Markiert genau ein vorhandenes Bild für eine mögliche Löschung."""

		selected_image['attachment_name'] = attachment_name if selected else None
		render_uploaded_images.refresh()

	def delete_selected_image() -> None:
		"""Löscht das ausgewählte Bild aus CouchDB und der lokalen Vorschau."""

		record_id = selected_id['value']
		attachment_name = selected_image['attachment_name']
		if record_id is None or attachment_name is None:
			ui.notify('Bitte zuerst ein Bild auswaehlen.', type='warning')
			return
		try:
			deleted = POPELS_DB.delete_image(record_id, attachment_name)
		except Exception as error:
			ui.notify(f'Bild konnte nicht geloescht werden: {error}', type='negative')
			return
		if not deleted:
			ui.notify('Bild nicht gefunden.', type='warning')
			return
		uploaded_images[:] = [
			image for image in uploaded_images
			if image['attachment_name'] != attachment_name
		]
		selected_image['attachment_name'] = None
		render_uploaded_images.refresh()
		render_records.refresh()
		ui.notify('Bild wurde geloescht.')

	def clear_images() -> None:
		"""Löscht alle Bilder des aktuell bearbeiteten Datensatzes."""

		record_id = selected_id['value']
		if record_id is None:
			return
		try:
			cleared = POPELS_DB.clear_images(record_id)
		except Exception as error:
			ui.notify(f'Bilder konnten nicht entfernt werden: {error}', type='negative')
			return
		if not cleared:
			ui.notify(f'{config.singular} nicht gefunden', type='warning')
			return
		uploaded_images.clear()
		selected_image['attachment_name'] = None
		render_uploaded_images.refresh()
		render_records.refresh()
		ui.notify('Bilder wurden entfernt.')

	def render_field_value(record: dict[str, Any], field: str, value_classes: str = 'text-slate-700') -> None:
		"""Zeigt Beschriftung und formatierten Wert eines Popels-Feldes an."""

		with ui.row().classes('items-baseline gap-1'):
			ui.label(f'{POPELS_FIELDS[field]["text"]}:').classes('font-medium text-green-600')
			ui.label(display_value(record, field)).classes(value_classes)

	def render_content_status(record: dict[str, Any], field: str) -> None:
		"""Zeigt nur an, ob Text beziehungsweise Bilder vorhanden sind."""

		available = content_available(field, record.get(field))
		status = 'Ja' if available else 'Nein'
		status_classes = 'text-green-700 font-medium' if available else 'text-slate-400'
		with ui.row().classes('items-center gap-1'):
			ui.label(f'{POPELS_FIELDS[field]["text"]}:').classes('font-medium text-green-600')
			ui.label(status).classes(status_classes)

	with ui.dialog() as field_dialog, ui.card().classes('w-[440px] max-w-full gap-3'):
		ui.label(f'Felder der {config.singular}-Liste').classes('text-lg font-semibold text-slate-900')
		ui.label(f'Waehle aus, welche Felder in den {config.singular}-Karten angezeigt werden.').classes('text-sm text-slate-600')
		with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-1 max-sm:grid-cols-1'):
			for field in config.list_display_fields:
				ui.checkbox(
					POPELS_FIELDS[field]['text'],
					value=field in visible_fields,
					on_change=lambda event, selected_field=field: set_field_visibility(selected_field, event.value),
				).props('dense')
		with ui.row().classes('w-full justify-end'):
			ui.button('Schliessen', on_click=field_dialog.close).props('flat no-caps')

	with ui.dialog() as sort_dialog, ui.card().classes('w-[520px] max-w-full gap-3'):
		@ui.refreshable
		def render_sort_controls() -> None:
			"""Rendert Prioritäten und Schaltflächen der aktuellen Sortierung."""

			ui.label('Sortierreihenfolge').classes('text-lg font-semibold text-slate-900')
			ui.label(
				'Klick: aufsteigend, nochmals: absteigend, nochmals: entfernen. '
				'Die Klickreihenfolge bestimmt die Prioritaet.'
			).classes('text-sm text-slate-600')
			if sort_criteria['value']:
				with ui.column().classes('w-full gap-1'):
					for priority, criterion in enumerate(sort_criteria['value'], start=1):
						field, _separator, direction = criterion.partition(':')
						direction_label = 'A-Z' if direction == 'asc' else 'Z-A'
						ui.label(f'{priority}. {POPELS_FIELDS[field]["text"]} {direction_label}').classes(
							'text-sm font-medium text-green-700'
						)
			else:
				ui.label('Keine Sortierung ausgewaehlt.').classes('text-sm text-slate-500')
			ui.separator()
			with ui.grid(columns=2).classes('w-full gap-2 max-sm:grid-cols-1'):
				for field in SORT_FIELDS:
					criterion = next(
						(item for item in sort_criteria['value'] if item.startswith(f'{field}:')),
						None,
					)
					suffix = ''
					if criterion is not None:
						suffix = ' A-Z' if criterion.endswith(':asc') else ' Z-A'
					ui.button(
						f'{POPELS_FIELDS[field]["text"]}{suffix}',
						on_click=lambda selected_field=field: cycle_sort_field(selected_field),
					).props('flat no-caps dense').classes('justify-start bg-slate-100 text-slate-700')
			with ui.row().classes('w-full justify-between gap-2'):
				ui.button('Zuruecksetzen', on_click=clear_sorting).props('flat no-caps')
				ui.button('Schliessen', on_click=sort_dialog.close).props('flat no-caps')

		render_sort_controls()

	with ui.dialog() as search_dialog, ui.card().classes('w-[520px] max-w-full gap-3'):
		ui.label(f'{config.plural} durchsuchen').classes('text-lg font-semibold text-slate-900')
		ui.label(
			'Gesucht wird in allen Feldern. Mehrere Begriffe koennen aus unterschiedlichen Feldern stammen.'
		).classes('text-sm text-slate-600')
		search_input['element'] = ui.input(
			'Suchbegriffe',
			value=search_query['value'],
		).props('clearable autofocus autocomplete="off"').classes('w-full')
		search_input['element'].on('keydown.enter', apply_search)
		with ui.row().classes('w-full justify-between gap-2'):
			ui.button('Suche loeschen', on_click=clear_search).props('flat no-caps')
			with ui.row().classes('gap-2'):
				ui.button('Schliessen', on_click=search_dialog.close).props('flat no-caps')
				ui.button('Suchen', icon='search', on_click=apply_search).props('no-caps')

	with ui.dialog() as delete_dialog, ui.card().classes('w-[440px] max-w-full gap-3'):
		ui.label(f'{config.singular} loeschen').classes('text-lg font-semibold text-red-700')
		delete_dialog_text = ui.label().classes('text-sm text-slate-700')
		ui.label('Auch zugeordnete Bilder werden dauerhaft geloescht.').classes('text-xs text-slate-500')
		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Abbrechen', on_click=delete_dialog.close).props('flat no-caps')
			ui.button('Loeschen', icon='delete', on_click=delete_record).props('no-caps color=negative')

	with ui.dialog() as text_dialog, ui.card().classes('w-[620px] max-w-full gap-3'):
		ui.label('Text bearbeiten').classes('text-lg font-semibold text-slate-900')
		text_editor['element'] = ui.editor(
			placeholder='Text eingeben',
			value=text_value['value'],
			on_change=handle_text_change,
		).classes('w-full min-h-[280px]')
		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Abbrechen', on_click=cancel_text_editing).props('flat no-caps')
			text_save_button['element'] = ui.button(
				'Uebernehmen',
				icon='save',
				on_click=save_text,
			).props('no-caps')
			text_save_button['element'].set_enabled(False)

	with ui.dialog() as picture_dialog, ui.card().classes('w-[720px] max-w-full gap-3'):
		ui.label('Bilder hochladen').classes('text-lg font-semibold text-slate-900')
		ui.label(
			'Waehle Bilder von deinem Rechner aus und klicke danach im Uploadfeld auf das Hochladen-Symbol.'
		).classes('text-sm text-slate-600')
		image_upload['element'] = ui.upload(
			label='Bilder vom Rechner auswaehlen',
			multiple=True,
			max_files=50,
			max_file_size=50_000_000,
			on_upload=handle_image_upload,
			on_multi_upload=reset_image_upload,
			on_rejected=handle_rejected_images,
			auto_upload=False,
		).props('accept="image/*" color="primary" bordered').classes('w-full')
		image_caption = ui.textarea(
			'Bildtext',
			placeholder='z. B. Gruppenfoto, Auktionsbild ...',
		).props('dense autogrow autocomplete="off"').classes('w-full')
		image_caption.bind_value(image_caption_draft, 'value')
		ui.button(
			'Ausgewaehlte Bilder hochladen',
			icon='cloud_upload',
			on_click=upload_selected_images,
		).props('no-caps').classes('self-end')

		@ui.refreshable
		def render_uploaded_images() -> None:
			"""Rendert die gespeicherten Bilder samt Einzelauswahl."""

			if not uploaded_images:
				ui.label('Noch keine Bilder hochgeladen.').classes('text-sm text-slate-500')
				return
			with ui.grid(columns=3).classes('w-full gap-3 max-md:grid-cols-2 max-sm:grid-cols-1'):
				for image in uploaded_images:
					with ui.card().classes('w-full p-2 gap-1'):
						ui.image(image['source']).classes('w-full h-32 object-cover rounded')
						with ui.row().classes('w-full items-center gap-1'):
							ui.checkbox(
								'Auswaehlen',
								value=selected_image['attachment_name'] == image['attachment_name'],
								on_change=lambda event, attachment_name=image['attachment_name']: select_image(
									attachment_name,
									event.value,
								),
							).props('dense')
							ui.label(image['name']).classes('text-xs text-slate-600 break-all flex-1')
						ui.textarea(
							'Text zum Bild',
							value=image.get('caption', ''),
							on_change=lambda event, attachment_name=image['attachment_name']: update_image_caption(
								attachment_name,
								event.value,
							),
						).props('dense autogrow autocomplete="off"').classes('w-full')

		render_uploaded_images()
		with ui.row().classes('w-full justify-between gap-2'):
			with ui.row().classes('gap-2'):
				ui.button(
					'Ausgewaehltes Bild loeschen',
					icon='delete',
					on_click=delete_selected_image,
				).props('flat no-caps').classes('text-red-600')
				ui.button('Alle Bilder entfernen', on_click=clear_images).props('flat no-caps')
			ui.button('Schliessen', on_click=picture_dialog.close).props('flat no-caps')

	@ui.refreshable
	def render_active_actions() -> None:
		"""Zeigt Text- und Bildaktionen nur bei einem aktiven Datensatz."""

		if selected_id['value'] is None:
			return
		action_handlers = {
			'editor': text_dialog.open,
			'upload': picture_dialog.open,
		}
		with ui.row().classes('w-full gap-2'):
			for field in CONTENT_ACTION_FIELDS:
				definition = config.page(field)
				ui.button(
					definition['actionLabel'],
					icon=definition['actionIcon'],
					on_click=action_handlers[definition['steuerelement']],
				).props('flat no-caps dense').classes('flex-1 bg-slate-100 text-slate-700')

	@ui.refreshable
	def render_records() -> None:
		"""Lädt, filtert und rendert die Popels-Datensätze als Kartenliste."""

		try:
			all_records = POPELS_DB.list(sort_criteria['value'])
			records = filter_records(all_records, search_query['value'])
			database_error = None
		except Exception as error:
			all_records = []
			records = []
			database_error = str(error)
		with ui.column().classes('w-full gap-2'):
			with ui.row().classes('w-full items-center justify-between gap-2'):
				with ui.row().classes('items-center gap-1'):
					ui.label(config.plural).classes('text-lg font-semibold text-slate-900')
					ui.button(icon='edit', on_click=field_dialog.open).props('flat round dense').classes('text-slate-500').tooltip(
						'Angezeigte Felder bearbeiten'
					)
					ui.button(icon='sort', on_click=sort_dialog.open).props('flat round dense').classes(
						'text-slate-500'
					).tooltip('Sortierreihenfolge bearbeiten')
					search_button_classes = 'text-green-600' if search_query['value'] else 'text-slate-500'
					ui.button(icon='search', on_click=search_dialog.open).props('flat round dense').classes(
						search_button_classes
					).tooltip('Alle Felder durchsuchen')
				count_text = f'{len(records)} von {len(all_records)} Eintraegen' if search_query['value'] else f'{len(records)} Eintraege'
				ui.label(count_text).classes('text-sm text-slate-500')

			if database_error is not None:
				with ui.card().classes('w-full p-3 rounded-lg shadow-sm border border-red-200 bg-red-50'):
					ui.label('CouchDB konnte nicht geladen werden.').classes('text-sm font-semibold text-red-700')
					ui.label(database_error).classes('text-xs text-red-600')
				return

			if not records:
				with ui.card().classes('w-full p-3 rounded-lg shadow-sm border border-slate-200'):
					ui.label(f'Noch keine {config.plural} vorhanden.').classes('text-sm text-slate-600')
				return

			for record in records:
				with ui.card().classes('w-full p-3 rounded-lg shadow-sm border border-slate-200 gap-2'):
					with ui.row().classes('w-full items-start justify-between gap-2 max-md:flex-col'):
						with ui.column().classes('gap-0 min-w-[180px]'):
							name_sort_active = any(
								criterion.partition(':')[0] == 'name'
								for criterion in sort_criteria['value']
							)
							heading = record_heading(
								record,
								visible_fields,
								fallback_to_id=False,
								name_last_first=name_sort_active,
							)
							if heading:
								ui.label(heading).classes(
									'text-base font-semibold text-slate-900 cursor-pointer hover:text-primary'
								).on(
									'click',
									lambda record_id=record['id']: load_record(record_id),
								).tooltip(f'{config.singular} bearbeiten')
							for field in list_fields('headerDetail'):
								if field in visible_fields:
									render_field_value(
										record,
										field,
										config.liste(field).get('listValueClasses', 'text-slate-700'),
									)
						with ui.row().classes('items-center gap-2'):
							ui.button(icon='edit', on_click=lambda record_id=record['id']: load_record(record_id)).props('flat round').classes('text-primary')
							record_name = record_heading(record)
							ui.button(
								icon='delete',
								on_click=lambda record_id=record['id'], name=record_name: request_delete_record(
									record_id,
									name,
								),
							).props('flat round').classes('text-red-600')

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm text-slate-700'):
						for field in list_fields('primary'):
							if field in visible_fields:
								render_field_value(
									record,
									field,
									config.liste(field).get('listValueClasses', 'text-slate-700'),
								)

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm text-slate-500'):
						for field in list_fields('secondary'):
							if field in visible_fields:
								render_field_value(
									record,
									field,
									config.liste(field).get('listValueClasses', 'text-slate-500'),
								)

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm'):
						for field in list_fields('status'):
							if field in visible_fields:
								render_content_status(record, field)

	with ui.column().classes('w-full gap-3'):
		ui.element('div').props(f'id={PAGE_TOP_ANCHOR_ID}').classes('h-0')
		with ui.splitter(value=50, limits=(25, 60)).classes('w-full') as page_splitter:
			with page_splitter.before:
				with ui.card().classes('w-full min-w-0 p-3 rounded-lg shadow-sm border border-slate-200 gap-2'):
					mode_label['element'] = ui.label(f'Neue {config.singular}').classes('text-lg font-semibold text-slate-900')
					ui.label('Daten werden in CouchDB gespeichert.').classes('text-xs text-slate-600')
					render_active_actions()

					form_controls.update(render_popels_form(
						config,
						validate_phone,
						clear_form,
						save_record,
						form_control_contexts,
					))

			with page_splitter.after:
				with ui.column().classes('w-full min-w-0 gap-3 pl-3'):
					render_records()

	if initial_record_id is not None:
		load_record(initial_record_id, scroll=False)
