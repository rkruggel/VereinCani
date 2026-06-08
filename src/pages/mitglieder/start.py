"""Startpunkt der Mitgliederverwaltung."""

from nicegui import ui

from src.pages.adressen.start import (
	ADRESSEN_DB,
	ADRESSLISTEN_EINSTELLUNGEN,
	CONFIG as ADRESSEN_CONFIG,
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
	"""Zeigt Mitglieder und Adressen als zusammengehörige Registerkarten."""

	popels_tabs = [
		('Mitglieder', CONFIG, MITGLIEDER_DB, MITGLIEDERLISTEN_EINSTELLUNGEN),
		('Adressen', ADRESSEN_CONFIG, ADRESSEN_DB, ADRESSLISTEN_EINSTELLUNGEN),
	]
	tab_elements = {}
	with ui.tabs().classes('w-full') as tabs:
		for title, _config, _database, _settings in popels_tabs:
			tab_elements[title] = ui.tab(title)

	with ui.tab_panels(tabs, value=tab_elements['Mitglieder']).classes('w-full bg-transparent'):
		for title, config, database, settings in popels_tabs:
			with ui.tab_panel(tab_elements[title]).classes('px-0'):
				render_popels_page(config, database, settings)
