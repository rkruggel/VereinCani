"""RavenDB-Modell und Repository für persönliche Listeneinstellungen."""

from dataclasses import dataclass
from urllib.parse import quote

from src.db.client import create_document_store
from src.pages.stammdaten import StammdatenConfig


@dataclass
class Listeneinstellung:
	"""Speichert sichtbare Felder und Sortierung eines Benutzers."""

	id: str = ''
	benutzer_name: str = ''
	sichtbare_felder: list[str] | None = None
	sortierungen: list[str] | None = None

	def __post_init__(self) -> None:
		"""Normalisiert optionale Einstellungslisten."""

		self.sichtbare_felder = list(self.sichtbare_felder or [])
		self.sortierungen = list(self.sortierungen or [])


class ListeneinstellungenRepository:
	"""Verwaltet benutzerspezifische Listeneinstellungen in RavenDB."""

	def __init__(self, config: StammdatenConfig) -> None:
		"""Initialisiert das Repository mit verzögertem Verbindungsaufbau."""

		self.config = config
		self._store = None

	def get(self, benutzer_name: str) -> list[str] | None:
		"""Lädt die sichtbaren Felder eines Benutzers."""

		with self._get_store().open_session() as session:
			einstellung = session.load(self.einstellung_id(benutzer_name), Listeneinstellung)
			return list(einstellung.sichtbare_felder) if einstellung is not None else None

	def get_document(self, benutzer_name: str) -> Listeneinstellung | None:
		"""Lädt das vollständige Einstellungsdokument eines Benutzers."""

		with self._get_store().open_session() as session:
			return session.load(self.einstellung_id(benutzer_name), Listeneinstellung)

	def get_sortierungen(self, benutzer_name: str) -> list[str] | None:
		"""Lädt nur die gespeicherten Sortierkriterien."""

		with self._get_store().open_session() as session:
			einstellung = session.load(self.einstellung_id(benutzer_name), Listeneinstellung)
			if einstellung is None:
				return None
			return list(einstellung.sortierungen)

	def save(self, benutzer_name: str, sichtbare_felder: list[str]) -> None:
		"""Erstellt oder aktualisiert die Auswahl sichtbarer Felder."""

		document_id = self.einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			einstellung = session.load(document_id, Listeneinstellung)
			if einstellung is None:
				einstellung = Listeneinstellung(
					id=document_id,
					benutzer_name=benutzer_name,
				)
				session.store(einstellung, einstellung.id)
			einstellung.sichtbare_felder = list(sichtbare_felder)
			session.save_changes()

	def save_sortierungen(self, benutzer_name: str, sortierungen: list[str]) -> None:
		"""Erstellt oder aktualisiert die persönliche Sortierreihenfolge."""

		document_id = self.einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			einstellung = session.load(document_id, Listeneinstellung)
			if einstellung is None:
				einstellung = Listeneinstellung(
					id=document_id,
					benutzer_name=benutzer_name,
				)
				session.store(einstellung, einstellung.id)
			einstellung.sortierungen = list(sortierungen)
			session.save_changes()

	def delete(self, benutzer_name: str) -> bool:
		"""Löscht alle Listeneinstellungen eines Benutzers."""

		document_id = self.einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			einstellung = session.load(document_id, Listeneinstellung)
			if einstellung is None:
				return False
			session.delete(einstellung)
			session.save_changes()
			return True

	def _get_store(self):
		"""Erzeugt den RavenDB-DocumentStore bei der ersten Verwendung."""

		if self._store is None:
			self._store = create_document_store(
				collection_names={Listeneinstellung: self.config.settings_collection_name},
			)
		return self._store

	def einstellung_id(self, benutzer_name: str) -> str:
		"""Erzeugt eine URL-sichere und benutzerspezifische RavenDB-ID."""

		return f'{self.config.settings_id_prefix}/{quote(benutzer_name.strip(), safe="")}'
