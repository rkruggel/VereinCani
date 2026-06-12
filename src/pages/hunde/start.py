"""Startpunkt der Hundeverwaltung."""

from typing import Any

from nicegui import ui

from src.pages.persoenlich.start import PERSOENLICH_DB
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

	try:
		personal_records = {
			record['id']: record
			for record in PERSOENLICH_DB.list()
		}
	except Exception as error:
		personal_records = {}
		ui.notify(f'Persönlich konnte nicht geladen werden: {error}', type='warning')
	render_popels_page(
		CONFIG,
		HUNDE_DB,
		HUNDELISTEN_EINSTELLUNGEN,
		{
			'besitzer': {
				'options': create_personal_options(personal_records),
			},
		},
	)


def create_personal_options(personal_records: dict[str, dict[str, Any]]) -> dict[str, str]:
	"""Erzeugt eindeutige Select-Beschriftungen aus den Namen."""

	options = {}
	used_labels: set[str] = set()
	for record_id, record in personal_records.items():
		label = str(record.get('name') or '').strip() or record_id
		if label in used_labels:
			label = f'{label} ({record_id})'
		used_labels.add(label)
		options[record_id] = label
	return options
