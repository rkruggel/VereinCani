"""Startpunkt des Kassenprogramms."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('kasse.yaml')
Kassenbuchung = create_popels_model(CONFIG)
KASSE_DB = CouchPopelsDatabase(CONFIG, Kassenbuchung)
KASSENLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_kasse_page() -> None:
	"""Zeigt das Kassenprogramm."""

	render_popels_page(CONFIG, KASSE_DB, KASSENLISTEN_EINSTELLUNGEN)
