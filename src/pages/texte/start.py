"""Startpunkt des Bereichs Texte."""

from typing import Any

from nicegui import ui

from src.db.client import create_couch_database
from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.page import render_popels_page
from src.popelsapp.repository import CouchPopelsDatabase
from src.popelsapp.settings import ListeneinstellungenRepository


CONFIG = load_popels_config('texte.yaml')
TextDokument = create_popels_model(CONFIG)
TEXTE_DB = CouchPopelsDatabase(CONFIG, TextDokument)
TEXTELISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)
TEXT_GROUP_OPTIONS_ID = 'texte/gruppen'


def render_texte_page() -> None:
	"""Zeigt die Textverwaltung."""

	try:
		group_options = load_group_options()
	except Exception as error:
		group_options = []
		ui.notify(f'Gruppen konnten nicht geladen werden: {error}', type='warning')
	render_popels_page(
		CONFIG,
		TEXTE_DB,
		TEXTELISTEN_EINSTELLUNGEN,
			{
				'gruppe': {
					'options': group_options,
					'on_options_change': save_group_options,
					'on_options_load': load_group_options,
					'on_option_rename': rename_text_group,
				},
			},
		)


def load_group_options() -> list[str]:
	"""Lädt die verwaltbaren Gruppenwerte."""

	document = create_couch_database().get_document(TEXT_GROUP_OPTIONS_ID) or {}
	return normalize_group_options(document.get('optionen') or [])


def save_group_options(options: list[str]) -> None:
	"""Speichert die verwaltbaren Gruppenwerte."""

	create_couch_database().put_document(
		TEXT_GROUP_OPTIONS_ID,
		{'optionen': normalize_group_options(options)},
		CONFIG.settings_collection_name,
	)


def rename_text_group(old_value: str, new_value: str) -> None:
	"""Übernimmt einen geänderten Gruppennamen in vorhandene Text-Dokumente."""

	old_text = str(old_value or '').strip()
	new_text = str(new_value or '').strip()
	if not old_text or not new_text or old_text == new_text:
		return
	for record in TEXTE_DB.list():
		if str(record.get('gruppe') or '').strip() == old_text:
			TEXTE_DB.update_fields(record['id'], {'gruppe': new_text})


def normalize_group_options(options: list[Any]) -> list[str]:
	"""Normalisiert Gruppenwerte eindeutig und sortiert."""

	seen = set()
	result = []
	for option in options:
		text = str(option or '').strip()
		if not text or text.casefold() in seen:
			continue
		seen.add(text.casefold())
		result.append(text)
	return sorted(result, key=str.casefold)
