"""Startpunkt der Preisverwaltung."""

from typing import Any

from nicegui import ui

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('preise.yaml')
Preis = create_popels_model(CONFIG)
PREISE_DB = CouchPopelsDatabase(CONFIG, Preis)
PREISLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)
MITGLIEDER_CONFIG = load_popels_config('mitglieder.yaml')
Mitglied = create_popels_model(MITGLIEDER_CONFIG)
MITGLIEDER_DB = CouchPopelsDatabase(MITGLIEDER_CONFIG, Mitglied)


def render_preise_page() -> None:
	"""Übergibt die Preiskonfiguration an die gemeinsame Popels-Seite."""

	render_popels_page(
		CONFIG,
		PREISE_DB,
		PREISLISTEN_EINSTELLUNGEN,
		{
			'mitglied': {
				'options': load_member_options(),
			},
		},
		show_records_list=False,
	)


def load_member_options() -> dict[str, str]:
	"""Lädt Mitglieder als Optionen für die Preis-Zuordnung."""

	try:
		member_records = {
			record['id']: record
			for record in MITGLIEDER_DB.list()
		}
	except Exception as error:
		ui.notify(f'Mitglieder konnten nicht geladen werden: {error}', type='warning')
		return {}
	return create_member_options(member_records)


def create_member_options(member_records: dict[str, dict[str, Any]]) -> dict[str, str]:
	"""Erzeugt eindeutige Select-Beschriftungen aus den Mitgliedernamen."""

	options = {}
	used_labels: set[str] = set()
	for record_id, record in member_records.items():
		label = str(record.get('name') or '').strip() or record_id
		if label in used_labels:
			label = f'{label} ({record_id})'
		used_labels.add(label)
		options[record_id] = label
	return options
