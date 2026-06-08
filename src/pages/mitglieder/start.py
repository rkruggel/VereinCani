"""Startpunkt der Mitgliederverwaltung."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import RavenPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('mitglieder.json')
Mitglied = create_popels_model(CONFIG)
MITGLIEDER_DB = RavenPopelsDatabase(CONFIG, Mitglied)
MITGLIEDERLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_mitglieder_page() -> None:
	"""Übergibt die Mitgliederkonfiguration an die gemeinsame Popels-Seite."""

	render_popels_page(CONFIG, MITGLIEDER_DB, MITGLIEDERLISTEN_EINSTELLUNGEN)
