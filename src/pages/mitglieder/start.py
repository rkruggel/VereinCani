"""Startpunkt der Mitgliederverwaltung."""

from typing import Any

from nicegui import ui

from src.pages.adressen.start import (
	ADRESSEN_DB,
	ADRESSLISTEN_EINSTELLUNGEN,
	CONFIG as ADRESSEN_CONFIG,
)
from src.pages.hunde.start import (
	CONFIG as HUNDE_CONFIG,
	HUNDE_DB,
	HUNDELISTEN_EINSTELLUNGEN,
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
	"""Zeigt Mitglieder sowie ausgewählte zugeordnete Adressen und Hunde."""

	selected_address = {'id': None}
	selected_dog = {'id': None}
	try:
		address_records = {
			record['id']: record
			for record in ADRESSEN_DB.list()
		}
	except Exception as error:
		address_records = {}
		ui.notify(f'Adressen konnten nicht geladen werden: {error}', type='warning')
	try:
		dog_records = {
			record['id']: record
			for record in HUNDE_DB.list()
		}
	except Exception as error:
		dog_records = {}
		ui.notify(f'Hunde konnten nicht geladen werden: {error}', type='warning')

	address_options = create_address_options(address_records)
	dog_options = create_dog_options(dog_records)

	with ui.tabs().props('align=left dense').classes('w-full justify-start') as tabs:
		mitglieder_tab = ui.tab('Mitglieder').props('no-caps').classes('text-xs px-2')
		address_tab = ui.tab('Adresse').props('no-caps').classes('text-xs px-2')
		dog_tab = ui.tab('Hund').props('no-caps').classes('text-xs px-2')
		address_tab.set_enabled(False)
		dog_tab.set_enabled(False)

	def select_address(record_id: str) -> None:
		"""Wählt eine zugeordnete Adresse und öffnet deren Registerkarte."""

		selected_address['id'] = record_id
		address_tab.set_enabled(True)
		render_selected_address.refresh()
		tabs.set_value(address_tab)

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
					'adressen': {
						'options': address_options,
						'on_select': select_address,
					},
					'hunde': {
						'options': dog_options,
						'on_select': select_dog,
					},
				},
			)
		with ui.tab_panel(address_tab).classes('px-0'):
			@ui.refreshable
			def render_selected_address() -> None:
				"""Zeigt die gemeinsame Adressverwaltung mit ausgewähltem Datensatz."""

				record_id = selected_address['id']
				if record_id is None:
					ui.label('Keine Adresse ausgewählt.').classes('text-sm text-slate-500')
					return
				render_popels_page(
					ADRESSEN_CONFIG,
					ADRESSEN_DB,
					ADRESSLISTEN_EINSTELLUNGEN,
					initial_record_id=record_id,
				)

			render_selected_address()
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


def create_address_options(address_records: dict[str, dict[str, Any]]) -> dict[str, str]:
	"""Erzeugt eindeutige Chip-Beschriftungen im Format ``Vorname Nachname``."""

	options = {}
	used_labels: set[str] = set()
	for record_id, record in address_records.items():
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
