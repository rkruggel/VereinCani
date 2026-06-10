"""Startpunkt des Bereichs Persönlich."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import RavenPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('persoenlich.yaml')
Persoenlich = create_popels_model(CONFIG)
PERSOENLICH_DB = RavenPopelsDatabase(CONFIG, Persoenlich)
PERSOENLICHLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_persoenlich_page() -> None:
	"""Übergibt die Konfiguration für Persönlich an die gemeinsame Popels-Seite."""

	render_popels_page(CONFIG, PERSOENLICH_DB, PERSOENLICHLISTEN_EINSTELLUNGEN)
