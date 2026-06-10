"""Startpunkt der Mitgliederverwaltung."""

from typing import Any

from nicegui import ui

from src.pages.hunde.start import (
	CONFIG as HUNDE_CONFIG,
	HUNDE_DB,
	HUNDELISTEN_EINSTELLUNGEN,
)
from src.pages.persoenlich.start import (
	CONFIG as PERSOENLICH_CONFIG,
	PERSOENLICH_DB,
	PERSOENLICHLISTEN_EINSTELLUNGEN,
)
from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import RavenPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('mitglieder.yaml')
Mitglied = create_popels_model(CONFIG)
MITGLIEDER_DB = RavenPopelsDatabase(CONFIG, Mitglied)
MITGLIEDERLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_mitglieder_page() -> None:
	"""Zeigt Mitglieder sowie ausgewählte zugeordnete persönliche Daten und Hunde."""

	selected_personal = {'id': None}
	selected_dog = {'id': None}
	try:
		personal_records = {
			record['id']: record
			for record in PERSOENLICH_DB.list()
		}
	except Exception as error:
		personal_records = {}
		ui.notify(f'Persönlich konnte nicht geladen werden: {error}', type='warning')
	try:
		dog_records = {
			record['id']: record
			for record in HUNDE_DB.list()
		}
	except Exception as error:
		dog_records = {}
		ui.notify(f'Hunde konnten nicht geladen werden: {error}', type='warning')

	personal_options = create_personal_options(personal_records)
	dog_options = create_dog_options(dog_records)

	with ui.tabs().props('align=left dense').classes('w-full justify-start') as tabs:
		mitglieder_tab = ui.tab('Mitglieder').props('no-caps').classes('text-xs px-2')
		personal_tab = ui.tab('Persönlich').props('no-caps').classes('text-xs px-2')
		dog_tab = ui.tab('Hund').props('no-caps').classes('text-xs px-2')
		personal_tab.set_enabled(False)
		dog_tab.set_enabled(False)

	def select_personal(record_id: str) -> None:
		"""Wählt zugeordnete persönliche Daten und öffnet deren Registerkarte."""

		selected_personal['id'] = record_id
		personal_tab.set_enabled(True)
		render_selected_personal.refresh()
		tabs.set_value(personal_tab)

	def select_dog(record_id: str) -> None:
		"""Wählt einen zugeordneten Hund und öffnet dessen Registerkarte."""

		selected_dog['id'] = record_id
		dog_tab.set_enabled(True)
		render_selected_dog.refresh()
		tabs.set_value(dog_tab)

	with ui.tab_panels(tabs, value=mitglieder_tab).classes('w-full bg-transparent'):
		with ui.tab_panel(mitglieder_tab).classes('px-0'):
			render_popels_page(
				CONFIG,
				MITGLIEDER_DB,
				MITGLIEDERLISTEN_EINSTELLUNGEN,
				{
					'persoenlich': {
						'options': personal_options,
						'on_select': select_personal,
					},
					'hunde': {
						'options': dog_options,
						'on_select': select_dog,
					},
				},
			)
		with ui.tab_panel(personal_tab).classes('px-0'):
			@ui.refreshable
			def render_selected_personal() -> None:
				"""Zeigt den Bereich Persönlich mit ausgewähltem Datensatz."""

				record_id = selected_personal['id']
				if record_id is None:
					ui.label('Nichts unter Persönlich ausgewählt.').classes('text-sm text-slate-500')
					return
				render_popels_page(
					PERSOENLICH_CONFIG,
					PERSOENLICH_DB,
					PERSOENLICHLISTEN_EINSTELLUNGEN,
					initial_record_id=record_id,
				)

			render_selected_personal()
		with ui.tab_panel(dog_tab).classes('px-0'):
			@ui.refreshable
			def render_selected_dog() -> None:
				"""Zeigt die gemeinsame Hundeverwaltung mit ausgewähltem Datensatz."""

				record_id = selected_dog['id']
				if record_id is None:
					ui.label('Kein Hund ausgewählt.').classes('text-sm text-slate-500')
					return
				render_popels_page(
					HUNDE_CONFIG,
					HUNDE_DB,
					HUNDELISTEN_EINSTELLUNGEN,
					initial_record_id=record_id,
				)

			render_selected_dog()


def create_personal_options(personal_records: dict[str, dict[str, Any]]) -> dict[str, str]:
	"""Erzeugt eindeutige Chip-Beschriftungen im Format ``Vorname Nachname``."""

	options = {}
	used_labels: set[str] = set()
	for record_id, record in personal_records.items():
		name = str(record.get('nachname') or '').strip()
		first_name = str(record.get('vorname') or '').strip()
		label = ' '.join(part for part in (first_name, name) if part) or record_id
		if label in used_labels:
			label = f'{label} ({record_id})'
		used_labels.add(label)
		options[record_id] = label
	return options


def create_dog_options(dog_records: dict[str, dict[str, Any]]) -> dict[str, str]:
	"""Erzeugt eindeutige Chip-Beschriftungen aus den Hundenamen."""

	options = {}
	used_labels: set[str] = set()
	for record_id, record in dog_records.items():
		label = str(record.get('name') or '').strip() or record_id
		if label in used_labels:
			label = f'{label} ({record_id})'
		used_labels.add(label)
		options[record_id] = label
	return options
