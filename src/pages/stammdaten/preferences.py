"""Laden und Speichern benutzerspezifischer Stammdatenlisten-Einstellungen."""

from nicegui import app

from src.pages.stammdaten.list_logic import normalize_sort_criteria
from src.pages.stammdaten.settings import ListeneinstellungenRepository
from src.pages.stammdaten import StammdatenConfig


def load_visible_fields(
	config: StammdatenConfig,
	settings: ListeneinstellungenRepository,
	benutzer_name: str,
) -> set[str]:
	"""Lädt die sichtbaren Felder und übernimmt bei Bedarf alte NiceGUI-Einstellungen."""

	saved_fields = settings.get(benutzer_name)
	if saved_fields is None:
		legacy_fields = app.storage.general.get(f'{config.key}_visible_fields')
		if isinstance(legacy_fields, list):
			save_visible_fields(config, settings, benutzer_name, set(legacy_fields))
			app.storage.general.pop(f'{config.key}_visible_fields', None)
			saved_fields = legacy_fields
	if saved_fields is None:
		return {'id', *config.form_fields}
	return {field for field in saved_fields if field in config.field_labels}


def save_visible_fields(
	config: StammdatenConfig,
	settings: ListeneinstellungenRepository,
	benutzer_name: str,
	visible_fields: set[str],
) -> None:
	"""Speichert die ausgewählten Listenfelder in ihrer definierten Reihenfolge."""

	settings.save(
		benutzer_name,
		[field for field in config.field_labels if field in visible_fields],
	)


def load_sort_criteria(
	config: StammdatenConfig,
	settings: ListeneinstellungenRepository,
	benutzer_name: str,
) -> list[str]:
	"""Lädt und normalisiert die persönliche Sortierreihenfolge."""

	document = settings.get_document(benutzer_name)
	if document is None:
		return []
	if document.sortierungen:
		return normalize_sort_criteria(config, document.sortierungen)
	return []
