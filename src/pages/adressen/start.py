"""Startpunkt der Adressenverwaltung."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import RavenPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('adressen.yaml')
Adresse = create_popels_model(CONFIG)
ADRESSEN_DB = RavenPopelsDatabase(CONFIG, Adresse)
ADRESSLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_adressen_page() -> None:
	"""Übergibt die Adresskonfiguration an die gemeinsame Popels-Seite."""

	render_popels_page(CONFIG, ADRESSEN_DB, ADRESSLISTEN_EINSTELLUNGEN)
