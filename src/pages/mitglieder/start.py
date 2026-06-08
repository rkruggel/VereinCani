"""Startpunkt der Mitgliederverwaltung."""

from nicegui import ui

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
	"""Zeigt die Mitgliederverwaltung in einer Registerkarte."""

	with ui.tabs().props('align=left dense').classes('w-full justify-start') as tabs:
		mitglieder_tab = ui.tab('Mitglieder').props('no-caps').classes('text-xs px-2')

	with ui.tab_panels(tabs, value=mitglieder_tab).classes('w-full bg-transparent'):
		with ui.tab_panel(mitglieder_tab).classes('px-0'):
			render_popels_page(CONFIG, MITGLIEDER_DB, MITGLIEDERLISTEN_EINSTELLUNGEN)
