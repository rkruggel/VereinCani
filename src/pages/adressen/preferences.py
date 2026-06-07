"""Laden und Speichern benutzerspezifischer Einstellungen der Adressliste."""

from nicegui import app

from src.pages.adressen.constants import FIELD_LABELS, FORM_FIELDS
from src.pages.adressen.list_logic import normalize_sort_criteria
from src.pages.adressen.settings import ADRESSLISTEN_EINSTELLUNGEN


LEGACY_VISIBLE_FIELDS_STORAGE_KEY = 'adressen_visible_fields'


def load_visible_fields(benutzer_name: str) -> set[str]:
	"""Lädt die sichtbaren Felder und übernimmt bei Bedarf alte NiceGUI-Einstellungen."""

	saved_fields = ADRESSLISTEN_EINSTELLUNGEN.get(benutzer_name)
	if saved_fields is None:
		legacy_fields = app.storage.general.get(LEGACY_VISIBLE_FIELDS_STORAGE_KEY)
		if isinstance(legacy_fields, list):
			save_visible_fields(benutzer_name, set(legacy_fields))
			app.storage.general.pop(LEGACY_VISIBLE_FIELDS_STORAGE_KEY, None)
			saved_fields = legacy_fields
	if saved_fields is None:
		return {'id', *FORM_FIELDS}
	return {field for field in saved_fields if field in FIELD_LABELS}


def save_visible_fields(benutzer_name: str, visible_fields: set[str]) -> None:
	"""Speichert die ausgewählten Listenfelder in ihrer definierten Reihenfolge."""

	ADRESSLISTEN_EINSTELLUNGEN.save(
		benutzer_name,
		[field for field in FIELD_LABELS if field in visible_fields],
	)


def load_sort_criteria(benutzer_name: str) -> list[str]:
	"""Lädt und normalisiert die persönliche Sortierreihenfolge."""

	document = ADRESSLISTEN_EINSTELLUNGEN.get_document(benutzer_name)
	if document is None:
		return []
	if document.sortierungen:
		return normalize_sort_criteria(document.sortierungen)
	return []
