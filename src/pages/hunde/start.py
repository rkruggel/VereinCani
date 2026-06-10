"""Startpunkt der Hundeverwaltung."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('hunde.yaml')
Hund = create_popels_model(CONFIG)
HUNDE_DB = CouchPopelsDatabase(CONFIG, Hund)
HUNDELISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_hunde_page() -> None:
	"""Übergibt die Hundekonfiguration an die gemeinsame Popels-Seite."""

	render_popels_page(CONFIG, HUNDE_DB, HUNDELISTEN_EINSTELLUNGEN)
