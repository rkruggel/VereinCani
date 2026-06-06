import base64
import unicodedata
from typing import Any

from nicegui import app, events, ui

from src.auth.session import get_authenticated_user
from src.pages.adressen.constants import (
	ADDRESS_FIELDS,
	CONTENT_STATUS_FIELDS,
	DEFAULT_SORT_CRITERIA,
	FIELD_LABELS,
	FORM_FIELDS,
	LIST_DISPLAY_FIELDS,
	PHONE_FIELDS,
	WOCHENTAGE,
)
from src.pages.adressen.repository import ADRESSEN_DB
from src.pages.adressen.settings import ADRESSLISTEN_EINSTELLUNGEN


LEGACY_VISIBLE_FIELDS_STORAGE_KEY = 'adressen_visible_fields'
PAGE_TOP_ANCHOR_ID = 'adressen-page-top'


def image_data_url(content_type: str, data: bytes) -> str:
	encoded_data = base64.b64encode(data).decode('ascii')
	return f'data:{content_type};base64,{encoded_data}'


def load_visible_fields(benutzer_name: str) -> set[str]:
	saved_fields = ADRESSLISTEN_EINSTELLUNGEN.get(benutzer_name)
	if saved_fields is None:
		legacy_fields = app.storage.general.get(LEGACY_VISIBLE_FIELDS_STORAGE_KEY)
		if isinstance(legacy_fields, list):
			save_visible_fields(benutzer_name, set(legacy_fields))
			app.storage.general.pop(LEGACY_VISIBLE_FIELDS_STORAGE_KEY, None)
			saved_fields = legacy_fields
	if saved_fields is None:
		return set(ADDRESS_FIELDS)
	return {field for field in saved_fields if field in LIST_DISPLAY_FIELDS}


def save_visible_fields(benutzer_name: str, visible_fields: set[str]) -> None:
	ADRESSLISTEN_EINSTELLUNGEN.save(
		benutzer_name,
		[field for field in LIST_DISPLAY_FIELDS if field in visible_fields],
	)


def load_sort_criteria(benutzer_name: str) -> list[str]:
	document = ADRESSLISTEN_EINSTELLUNGEN.get_document(benutzer_name)
	if document is None:
		return list(DEFAULT_SORT_CRITERIA)
	if document.sortierungen:
		return normalize_sort_criteria(document.sortierungen)
	return []


def normalize_sort_criteria(sortierungen: list[str]) -> list[str]:
	result: list[str] = []
	used_fields: set[str] = set()
	for criterion in sortierungen:
		field, separator, direction = criterion.partition(':')
		if separator and field in ADDRESS_FIELDS and direction in {'asc', 'desc'} and field not in used_fields:
			result.append(criterion)
			used_fields.add(field)
	return result


def cycle_sort_criterion(sortierungen: list[str], field: str) -> list[str]:
	result = list(sortierungen)
	for index, criterion in enumerate(result):
		selected_field, _separator, direction = criterion.partition(':')
		if selected_field != field:
			continue
		if direction == 'asc':
			result[index] = f'{field}:desc'
		else:
			result.pop(index)
		return result
	result.append(f'{field}:asc')
	return result


def normalize_search_text(value: Any) -> str:
	if isinstance(value, list):
		value = ' '.join(str(item) for item in value)
	text = unicodedata.normalize('NFKD', str(value or ''))
	return ''.join(character for character in text if not unicodedata.combining(character)).casefold()


def filter_records(records: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
	search_terms = normalize_search_text(query).split()
	if not search_terms:
		return records
	result = []
	for record in records:
		searchable_text = ' '.join(
			normalize_search_text(record.get(field))
			for field in ADDRESS_FIELDS
		)
		if all(term in searchable_text for term in search_terms):
			result.append(record)
	return result


def render_adressen_page() -> None:
	benutzer = get_authenticated_user()
	if benutzer is None:
		ui.notify('Bitte zuerst anmelden.', type='warning')
		return
	benutzer_name = benutzer['name']
	selected_id = {'value': None}
	form_controls: dict[str, Any] = {}
	mode_label = {'element': None}
	search_query = {'value': ''}
	search_input = {'element': None}
	text_value = {'value': ''}
	text_input = {'element': None}
	image_upload = {'element': None}
	uploaded_images: list[dict[str, str]] = []
	selected_image = {'attachment_name': None}
	pending_delete = {'record_id': None, 'name': ''}
	try:
		visible_fields = load_visible_fields(benutzer_name)
		sort_criteria = {'value': load_sort_criteria(benutzer_name)}
	except Exception as error:
		visible_fields = set(ADDRESS_FIELDS)
		sort_criteria = {'value': list(DEFAULT_SORT_CRITERIA)}
		ui.notify(f'Listeneinstellungen konnten nicht geladen werden: {error}', type='warning')

	def validate_phone(value: Any) -> str | None:
		text = str(value or '')
		if all(character.isdigit() or character == '+' or character == ' ' for character in text):
			return None
		return 'Nur Zahlen, + und Leerzeichen erlaubt'

	def collect_form_data() -> dict[str, Any]:
		return {field: form_controls[field].value for field in FORM_FIELDS}

	def clear_form() -> None:
		selected_id['value'] = None
		text_value['value'] = ''
		uploaded_images.clear()
		selected_image['attachment_name'] = None
		for field in FORM_FIELDS:
			form_controls[field].value = [] if field == 'nichtWochentag' else ''
		if mode_label['element'] is not None:
			mode_label['element'].set_text('Neue Adresse')
		if text_input['element'] is not None:
			text_input['element'].value = ''
		render_uploaded_images.refresh()
		render_active_actions.refresh()

	def scroll_to_page_top() -> None:
		ui.run_javascript(
			f'document.getElementById("{PAGE_TOP_ANCHOR_ID}")'
			'?.scrollIntoView({behavior: "smooth", block: "start"});'
		)

	def load_record(record_id: str) -> None:
		scroll_to_page_top()
		try:
			record = ADRESSEN_DB.get(record_id)
		except Exception as error:
			ui.notify(f'RavenDB nicht erreichbar: {error}', type='negative')
			return
		if record is None:
			ui.notify('Adresse nicht gefunden', type='warning')
			return
		selected_id['value'] = record_id
		text_value['value'] = str(record.get('text') or '')
		if text_input['element'] is not None:
			text_input['element'].value = text_value['value']
		try:
			images = ADRESSEN_DB.get_images(record_id)
		except Exception as error:
			ui.notify(f'Bilder konnten nicht geladen werden: {error}', type='warning')
			images = []
		uploaded_images.clear()
		uploaded_images.extend({
			'attachment_name': image['attachment_name'],
			'name': image['name'],
			'content_type': image['content_type'],
			'source': image_data_url(image['content_type'], image['data']),
		} for image in images)
		selected_image['attachment_name'] = None
		render_uploaded_images.refresh()
		render_active_actions.refresh()
		for field in FORM_FIELDS:
			form_controls[field].value = record[field]
		if mode_label['element'] is not None:
			mode_label['element'].set_text(f'Adresse bearbeiten: #{record_id}')

	def save_record() -> None:
		data = collect_form_data()
		if not str(data['vorname']).strip() or not str(data['nachname']).strip():
			ui.notify('Vorname und Nachname sind Pflichtfelder', type='warning')
			return
		for field in PHONE_FIELDS:
			if validate_phone(data[field]) is not None:
				ui.notify('Festnetz und Handy duerfen nur Zahlen, + und Leerzeichen enthalten', type='warning')
				return

		if selected_id['value'] is None:
			try:
				record = ADRESSEN_DB.create(data)
			except Exception as error:
				ui.notify(f'Adresse konnte nicht gespeichert werden: {error}', type='negative')
				return
			ui.notify(f'Adresse #{record["id"]} angelegt')
		else:
			try:
				record = ADRESSEN_DB.update(selected_id['value'], data)
			except Exception as error:
				ui.notify(f'Adresse konnte nicht gespeichert werden: {error}', type='negative')
				return
			if record is None:
				ui.notify('Adresse nicht gefunden', type='warning')
				return
			ui.notify(f'Adresse #{selected_id["value"]} gespeichert')
		clear_form()
		render_records.refresh()

	def request_delete_record(record_id: str, name: str) -> None:
		scroll_to_page_top()
		pending_delete['record_id'] = record_id
		pending_delete['name'] = name
		delete_dialog_text.set_text(f'Soll die Adresse "{name}" wirklich geloescht werden?')
		delete_dialog.open()

	def delete_record() -> None:
		record_id = pending_delete['record_id']
		if record_id is None:
			delete_dialog.close()
			return
		try:
			deleted = ADRESSEN_DB.delete(record_id)
		except Exception as error:
			ui.notify(f'Adresse konnte nicht geloescht werden: {error}', type='negative')
			return
		delete_dialog.close()
		pending_delete['record_id'] = None
		pending_delete['name'] = ''
		if deleted:
			if selected_id['value'] == record_id:
				clear_form()
			ui.notify(f'Adresse #{record_id} geloescht')
			render_records.refresh()
		else:
			ui.notify('Adresse nicht gefunden', type='warning')

	def set_field_visibility(field: str, visible: bool | None) -> None:
		if visible:
			visible_fields.add(field)
		else:
			visible_fields.discard(field)
		try:
			save_visible_fields(benutzer_name, visible_fields)
		except Exception as error:
			ui.notify(f'Listeneinstellungen konnten nicht gespeichert werden: {error}', type='negative')
			return
		render_records.refresh()

	def cycle_sort_field(field: str) -> None:
		new_sortierungen = cycle_sort_criterion(sort_criteria['value'], field)
		try:
			ADRESSLISTEN_EINSTELLUNGEN.save_sortierungen(benutzer_name, new_sortierungen)
		except Exception as error:
			ui.notify(f'Sortierung konnte nicht gespeichert werden: {error}', type='negative')
			return
		sort_criteria['value'] = new_sortierungen
		render_sort_controls.refresh()
		render_records.refresh()

	def clear_sorting() -> None:
		default_sortierungen = list(DEFAULT_SORT_CRITERIA)
		try:
			ADRESSLISTEN_EINSTELLUNGEN.save_sortierungen(benutzer_name, default_sortierungen)
		except Exception as error:
			ui.notify(f'Sortierung konnte nicht gespeichert werden: {error}', type='negative')
			return
		sort_criteria['value'] = default_sortierungen
		render_sort_controls.refresh()
		render_records.refresh()

	def apply_search() -> None:
		search_query['value'] = str(search_input['element'].value or '').strip()
		search_dialog.close()
		render_records.refresh()

	def clear_search() -> None:
		search_query['value'] = ''
		if search_input['element'] is not None:
			search_input['element'].value = ''
		search_dialog.close()
		render_records.refresh()

	def save_text() -> None:
		record_id = selected_id['value']
		if record_id is None:
			ui.notify('Bitte zuerst eine Adresse auswaehlen.', type='warning')
			return
		value = str(text_input['element'].value or '')
		try:
			saved = ADRESSEN_DB.update_text(record_id, value)
		except Exception as error:
			ui.notify(f'Text konnte nicht gespeichert werden: {error}', type='negative')
			return
		if not saved:
			ui.notify('Adresse nicht gefunden', type='warning')
			return
		text_value['value'] = value
		text_dialog.close()
		ui.notify('Text wurde gespeichert.')

	async def handle_image_upload(event: events.UploadEventArguments) -> None:
		record_id = selected_id['value']
		if record_id is None:
			ui.notify('Bitte zuerst eine Adresse auswaehlen.', type='warning')
			return
		content_type = event.file.content_type or ''
		if not content_type.startswith('image/'):
			ui.notify(f'{event.file.name} ist keine Bilddatei.', type='warning')
			return
		data = await event.file.read()
		try:
			image = ADRESSEN_DB.add_image(record_id, event.file.name, content_type, data)
		except Exception as error:
			ui.notify(f'Bild konnte nicht gespeichert werden: {error}', type='negative')
			return
		if image is None:
			ui.notify('Adresse nicht gefunden', type='warning')
			return
		uploaded_images.append({
			**image,
			'source': image_data_url(content_type, data),
		})
		render_uploaded_images.refresh()
		ui.notify(f'{event.file.name} wurde gespeichert.')

	def handle_rejected_images() -> None:
		ui.notify(
			'Bild abgelehnt. Pro Auswahl sind maximal 50 Bilder mit jeweils bis zu 50 MB erlaubt.',
			type='warning',
		)

	def upload_selected_images() -> None:
		image_upload['element'].run_method('upload')

	def reset_image_upload() -> None:
		image_upload['element'].reset()

	def select_image(attachment_name: str, selected: bool | None) -> None:
		selected_image['attachment_name'] = attachment_name if selected else None
		render_uploaded_images.refresh()

	def delete_selected_image() -> None:
		record_id = selected_id['value']
		attachment_name = selected_image['attachment_name']
		if record_id is None or attachment_name is None:
			ui.notify('Bitte zuerst ein Bild auswaehlen.', type='warning')
			return
		try:
			deleted = ADRESSEN_DB.delete_image(record_id, attachment_name)
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
		ui.notify('Bild wurde geloescht.')

	def clear_images() -> None:
		record_id = selected_id['value']
		if record_id is None:
			return
		try:
			cleared = ADRESSEN_DB.clear_images(record_id)
		except Exception as error:
			ui.notify(f'Bilder konnten nicht entfernt werden: {error}', type='negative')
			return
		if not cleared:
			ui.notify('Adresse nicht gefunden', type='warning')
			return
		uploaded_images.clear()
		selected_image['attachment_name'] = None
		render_uploaded_images.refresh()
		ui.notify('Bilder wurden entfernt.')

	def display_value(record: dict[str, Any], field: str) -> str:
		value = record[field]
		if field == 'nichtWochentag':
			return ', '.join(value) if value else '-'
		return str(value or '-')

	def render_field_value(record: dict[str, Any], field: str, value_classes: str = 'text-slate-700') -> None:
		with ui.row().classes('items-baseline gap-1'):
			ui.label(f'{FIELD_LABELS[field]}:').classes('font-medium text-green-600')
			ui.label(display_value(record, field)).classes(value_classes)

	def render_content_status(record: dict[str, Any], field: str) -> None:
		available = bool(record.get(field))
		status = 'Ja' if available else 'Nein'
		status_classes = 'text-green-700 font-medium' if available else 'text-slate-400'
		with ui.row().classes('items-center gap-1'):
			ui.label(f'{FIELD_LABELS[field]}:').classes('font-medium text-green-600')
			ui.label(status).classes(status_classes)

	with ui.dialog() as field_dialog, ui.card().classes('w-[440px] max-w-full gap-3'):
		ui.label('Felder der Adressliste').classes('text-lg font-semibold text-slate-900')
		ui.label('Waehle aus, welche Felder in den Adresskarten angezeigt werden.').classes('text-sm text-slate-600')
		with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-1 max-sm:grid-cols-1'):
			for field in LIST_DISPLAY_FIELDS:
				ui.checkbox(
					FIELD_LABELS[field],
					value=field in visible_fields,
					on_change=lambda event, selected_field=field: set_field_visibility(selected_field, event.value),
				).props('dense')
		with ui.row().classes('w-full justify-end'):
			ui.button('Schliessen', on_click=field_dialog.close).props('flat no-caps')

	with ui.dialog() as sort_dialog, ui.card().classes('w-[520px] max-w-full gap-3'):
		@ui.refreshable
		def render_sort_controls() -> None:
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
						ui.label(f'{priority}. {FIELD_LABELS[field]} {direction_label}').classes(
							'text-sm font-medium text-green-700'
						)
			else:
				ui.label('Keine Sortierung ausgewaehlt.').classes('text-sm text-slate-500')
			ui.separator()
			with ui.grid(columns=2).classes('w-full gap-2 max-sm:grid-cols-1'):
				for field in ADDRESS_FIELDS:
					criterion = next(
						(item for item in sort_criteria['value'] if item.startswith(f'{field}:')),
						None,
					)
					suffix = ''
					if criterion is not None:
						suffix = ' A-Z' if criterion.endswith(':asc') else ' Z-A'
					ui.button(
						f'{FIELD_LABELS[field]}{suffix}',
						on_click=lambda selected_field=field: cycle_sort_field(selected_field),
					).props('flat no-caps dense').classes('justify-start bg-slate-100 text-slate-700')
			with ui.row().classes('w-full justify-between gap-2'):
				ui.button('Zuruecksetzen', on_click=clear_sorting).props('flat no-caps')
				ui.button('Schliessen', on_click=sort_dialog.close).props('flat no-caps')

		render_sort_controls()

	with ui.dialog() as search_dialog, ui.card().classes('w-[520px] max-w-full gap-3'):
		ui.label('Adressen durchsuchen').classes('text-lg font-semibold text-slate-900')
		ui.label(
			'Gesucht wird in allen Feldern. Mehrere Begriffe koennen aus unterschiedlichen Feldern stammen.'
		).classes('text-sm text-slate-600')
		search_input['element'] = ui.input(
			'Suchbegriffe',
			value=search_query['value'],
		).props('clearable autofocus').classes('w-full')
		search_input['element'].on('keydown.enter', apply_search)
		with ui.row().classes('w-full justify-between gap-2'):
			ui.button('Suche loeschen', on_click=clear_search).props('flat no-caps')
			with ui.row().classes('gap-2'):
				ui.button('Schliessen', on_click=search_dialog.close).props('flat no-caps')
				ui.button('Suchen', icon='search', on_click=apply_search).props('no-caps')

	with ui.dialog() as delete_dialog, ui.card().classes('w-[440px] max-w-full gap-3'):
		ui.label('Adresse loeschen').classes('text-lg font-semibold text-red-700')
		delete_dialog_text = ui.label().classes('text-sm text-slate-700')
		ui.label('Auch zugeordnete Bilder werden dauerhaft geloescht.').classes('text-xs text-slate-500')
		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Abbrechen', on_click=delete_dialog.close).props('flat no-caps')
			ui.button('Loeschen', icon='delete', on_click=delete_record).props('no-caps color=negative')

	with ui.dialog() as text_dialog, ui.card().classes('w-[620px] max-w-full gap-3'):
		ui.label('Text eingeben').classes('text-lg font-semibold text-slate-900')
		text_input['element'] = ui.textarea(
			'Text',
			value=text_value['value'],
		).props('autogrow autofocus').classes('w-full min-h-[180px]')
		with ui.row().classes('w-full justify-end gap-2'):
			ui.button('Abbrechen', on_click=text_dialog.close).props('flat no-caps')
			ui.button('Uebernehmen', icon='save', on_click=save_text).props('no-caps')

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
		ui.button(
			'Ausgewaehlte Bilder hochladen',
			icon='cloud_upload',
			on_click=upload_selected_images,
		).props('no-caps').classes('self-end')

		@ui.refreshable
		def render_uploaded_images() -> None:
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
		if selected_id['value'] is None:
			return
		with ui.row().classes('w-full gap-2'):
			ui.button('Text', icon='description', on_click=text_dialog.open).props('flat no-caps dense').classes(
				'flex-1 bg-slate-100 text-slate-700'
			)
			ui.button('Pic', icon='image', on_click=picture_dialog.open).props('flat no-caps dense').classes(
				'flex-1 bg-slate-100 text-slate-700'
			)

	@ui.refreshable
	def render_records() -> None:
		try:
			all_records = ADRESSEN_DB.list(sort_criteria['value'])
			records = filter_records(all_records, search_query['value'])
			database_error = None
		except Exception as error:
			all_records = []
			records = []
			database_error = str(error)
		with ui.column().classes('w-full gap-2'):
			with ui.row().classes('w-full items-center justify-between gap-2'):
				with ui.row().classes('items-center gap-1'):
					ui.label('Adressen').classes('text-lg font-semibold text-slate-900')
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
					ui.label('RavenDB konnte nicht geladen werden.').classes('text-sm font-semibold text-red-700')
					ui.label(database_error).classes('text-xs text-red-600')
				return

			if not records:
				with ui.card().classes('w-full p-3 rounded-lg shadow-sm border border-slate-200'):
					ui.label('Noch keine Adressen vorhanden.').classes('text-sm text-slate-600')
				return

			for record in records:
				with ui.card().classes('w-full p-3 rounded-lg shadow-sm border border-slate-200 gap-2'):
					with ui.row().classes('w-full items-start justify-between gap-2 max-md:flex-col'):
						with ui.column().classes('gap-0 min-w-[180px]'):
							name_parts = [
								record[field]
								for field in ('anrede', 'titel', 'vorname', 'nachname')
								if field in visible_fields and record[field]
							]
							if name_parts:
								ui.label(' '.join(name_parts)).classes('text-base font-semibold text-slate-900')
							if 'id' in visible_fields:
								render_field_value(record, 'id', 'text-xs tracking-wide text-slate-500')
							if 'zusatz' in visible_fields:
								render_field_value(record, 'zusatz', 'text-sm text-slate-500')
						with ui.row().classes('items-center gap-2'):
							ui.button(icon='edit', on_click=lambda record_id=record['id']: load_record(record_id)).props('flat round').classes('text-primary')
							record_name = ' '.join(
								str(record.get(field) or '').strip()
								for field in ('vorname', 'nachname')
							).strip() or record['id']
							ui.button(
								icon='delete',
								on_click=lambda record_id=record['id'], name=record_name: request_delete_record(
									record_id,
									name,
								),
							).props('flat round').classes('text-red-600')

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm text-slate-700'):
						for field in ('adresse', 'ort', 'email', 'handy', 'festnetz', 'www'):
							if field in visible_fields:
								render_field_value(record, field)

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm text-slate-500'):
						for field in ('geboren', 'beruf', 'hobby', 'nichtWochentag', 'faehigkeiten'):
							if field in visible_fields:
								render_field_value(record, field, 'text-slate-500')

					with ui.row().classes('w-full gap-x-3 gap-y-1 flex-wrap text-sm'):
						for field in CONTENT_STATUS_FIELDS:
							if field in visible_fields:
								render_content_status(record, field)

	with ui.column().classes('w-full gap-3'):
		ui.element('div').props(f'id={PAGE_TOP_ANCHOR_ID}').classes('h-0')
		with ui.row().classes('w-full gap-3 items-start max-lg:flex-col'):
			with ui.card().classes('w-[420px] max-lg:w-full p-3 rounded-lg shadow-sm border border-slate-200 gap-2'):
				mode_label['element'] = ui.label('Neue Adresse').classes('text-lg font-semibold text-slate-900')
				ui.label('Daten werden in RavenDB gespeichert.').classes('text-xs text-slate-600')
				render_active_actions()

				with ui.grid(columns=2).classes('w-full gap-2'):
					form_controls['anrede'] = ui.select(['Herr', 'Frau', 'Diverse'], label='Anrede').props('dense options-dense').classes('w-full')
					form_controls['titel'] = ui.select(['Dr.', 'Prof.', 'Prof. Dr.'], label='Titel').props('dense options-dense').classes('w-full')

				with ui.grid(columns=2).classes('w-full gap-2'):
					form_controls['vorname'] = ui.input('Vorname').classes('w-full').props('dense')
					form_controls['nachname'] = ui.input('Nachname').classes('w-full').props('dense')
				form_controls['zusatz'] = ui.textarea('Zusatz').classes('w-full').props('autogrow dense')
				form_controls['adresse'] = ui.textarea('Adresse').classes('w-full').props('autogrow dense')

				with ui.grid(columns=2).classes('w-full gap-2'):
					form_controls['ort'] = ui.input('Ort').props('dense').classes('w-full')
					form_controls['geboren'] = ui.input('Geboren').props('type=date dense').classes('w-full')
					form_controls['festnetz'] = ui.input('Festnetz', validation=validate_phone).props('dense').classes('w-full')
					form_controls['handy'] = ui.input('Handy', validation=validate_phone).props('dense').classes('w-full')
					form_controls['email'] = ui.input('E-Mail').props('type=email dense').classes('w-full')
					form_controls['www'] = ui.input('WWW').props('dense').classes('w-full')

				form_controls['nichtWochentag'] = ui.select(
					WOCHENTAGE,
					label='nichtWochentag',
					multiple=True,
					clearable=True,
				).props('dense options-dense use-chips').classes('w-full')

				with ui.grid(columns=2).classes('w-full gap-2'):
					form_controls['beruf'] = ui.input('Beruf').props('dense').classes('w-full')
					form_controls['hobby'] = ui.input('Hobby').props('dense').classes('w-full')

				form_controls['faehigkeiten'] = ui.textarea('Faehigkeiten').classes('w-full').props('autogrow dense')

				with ui.row().classes('w-full justify-end gap-2'):
					ui.button('Neu', icon='add', on_click=clear_form).props('flat no-caps dense').classes('text-slate-700 bg-slate-100 px-3')
					ui.button('Speichern', icon='save', on_click=save_record).props('no-caps dense').classes('bg-primary text-white px-3')

			with ui.column().classes('flex-1 w-full gap-3'):
				render_records()
