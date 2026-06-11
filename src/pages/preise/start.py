"""Startpunkt der Preisverwaltung."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('preise.yaml')
Preis = create_popels_model(CONFIG)
PREISE_DB = CouchPopelsDatabase(CONFIG, Preis)
PREISLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_preise_page() -> None:
	"""Übergibt die Preiskonfiguration an die gemeinsame Popels-Seite."""

	render_popels_page(CONFIG, PREISE_DB, PREISLISTEN_EINSTELLUNGEN)
