"""CouchDB-Modell und Repository für persönliche Listeneinstellungen."""

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote

from src.db.client import create_couch_database
from src.popelsapp import PopelsConfig


@dataclass
class Listeneinstellung:
	"""Speichert sichtbare Felder und Sortierung eines Benutzers."""

	id: str = ''
	benutzer_name: str = ''
	sichtbare_felder: list[str] | None = None
	sortierungen: list[str] | None = None

	def __post_init__(self) -> None:
		self.sichtbare_felder = list(self.sichtbare_felder or [])
		self.sortierungen = list(self.sortierungen or [])


class ListeneinstellungenRepository:
	"""Verwaltet benutzerspezifische Listeneinstellungen in CouchDB."""

	def __init__(self, config: PopelsConfig) -> None:
		self.config = config
		self._database = None

	def get(self, benutzer_name: str) -> list[str] | None:
		einstellung = self.get_document(benutzer_name)
		return list(einstellung.sichtbare_felder) if einstellung is not None else None

	def get_document(self, benutzer_name: str) -> Listeneinstellung | None:
		document = self._get_database().get_document(self.einstellung_id(benutzer_name))
		if document is None:
			return None
		return Listeneinstellung(**{
			field: document.get(field)
			for field in Listeneinstellung.__dataclass_fields__
		})

	def get_sortierungen(self, benutzer_name: str) -> list[str] | None:
		einstellung = self.get_document(benutzer_name)
		return list(einstellung.sortierungen) if einstellung is not None else None

	def save(self, benutzer_name: str, sichtbare_felder: list[str]) -> None:
		einstellung = self.get_document(benutzer_name) or Listeneinstellung(
			id=self.einstellung_id(benutzer_name),
			benutzer_name=benutzer_name,
		)
		einstellung.sichtbare_felder = list(sichtbare_felder)
		self._save(einstellung)

	def save_sortierungen(self, benutzer_name: str, sortierungen: list[str]) -> None:
		einstellung = self.get_document(benutzer_name) or Listeneinstellung(
			id=self.einstellung_id(benutzer_name),
			benutzer_name=benutzer_name,
		)
		einstellung.sortierungen = list(sortierungen)
		self._save(einstellung)

	def load_editable_options(self, field: str) -> list[str]:
		"""Lädt die gespeicherten Optionen eines editierbaren Select-Feldes."""

		document = self._get_database().get_document(self.editable_options_id(field)) or {}
		return normalize_editable_options(document.get('optionen') or [])

	def save_editable_options(self, field: str, options: list[Any]) -> None:
		"""Speichert die Optionen eines editierbaren Select-Feldes dauerhaft."""

		self._get_database().put_document(
			self.editable_options_id(field),
			{'optionen': normalize_editable_options(options)},
			self.config.settings_collection_name,
		)

	def delete(self, benutzer_name: str) -> bool:
		return self._get_database().delete_document(self.einstellung_id(benutzer_name))

	def einstellung_id(self, benutzer_name: str) -> str:
		return f'{self.config.settings_id_prefix}/{quote(benutzer_name.strip(), safe="")}'

	def editable_options_id(self, field: str) -> str:
		return f'{self.config.key}/{quote(field.strip(), safe="")}/optionen'

	def _save(self, einstellung: Listeneinstellung) -> None:
		self._get_database().put_document(
			einstellung.id,
			asdict(einstellung),
			self.config.settings_collection_name,
		)

	def _get_database(self):
		if self._database is None:
			self._database = create_couch_database()
		return self._database


def normalize_editable_options(options: list[Any]) -> list[str]:
	"""Normalisiert editierbare Select-Werte eindeutig und sortiert."""

	seen = set()
	result = []
	for option in options:
		text = str(option or '').strip()
		if not text or text.casefold() in seen:
			continue
		seen.add(text.casefold())
		result.append(text)
	return sorted(result, key=str.casefold)
