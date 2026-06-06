from dataclasses import dataclass
from urllib.parse import quote

from src.db.client import create_document_store


@dataclass
class AdresslistenEinstellung:
	id: str = ''
	benutzer_name: str = ''
	sichtbare_felder: list[str] | None = None
	sortierungen: list[str] | None = None

	def __post_init__(self) -> None:
		self.sichtbare_felder = list(self.sichtbare_felder or [])
		self.sortierungen = list(self.sortierungen or [])


class AdresslistenEinstellungenRepository:
	def __init__(self) -> None:
		self._store = None

	def get(self, benutzer_name: str) -> list[str] | None:
		with self._get_store().open_session() as session:
			einstellung = session.load(einstellung_id(benutzer_name), AdresslistenEinstellung)
			return list(einstellung.sichtbare_felder) if einstellung is not None else None

	def get_document(self, benutzer_name: str) -> AdresslistenEinstellung | None:
		with self._get_store().open_session() as session:
			return session.load(einstellung_id(benutzer_name), AdresslistenEinstellung)

	def get_sortierungen(self, benutzer_name: str) -> list[str] | None:
		with self._get_store().open_session() as session:
			einstellung = session.load(einstellung_id(benutzer_name), AdresslistenEinstellung)
			if einstellung is None:
				return None
			return list(einstellung.sortierungen)

	def save(self, benutzer_name: str, sichtbare_felder: list[str]) -> None:
		document_id = einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			einstellung = session.load(document_id, AdresslistenEinstellung)
			if einstellung is None:
				einstellung = AdresslistenEinstellung(
					id=document_id,
					benutzer_name=benutzer_name,
				)
				session.store(einstellung, einstellung.id)
			einstellung.sichtbare_felder = list(sichtbare_felder)
			session.save_changes()

	def save_sortierungen(self, benutzer_name: str, sortierungen: list[str]) -> None:
		document_id = einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			einstellung = session.load(document_id, AdresslistenEinstellung)
			if einstellung is None:
				einstellung = AdresslistenEinstellung(
					id=document_id,
					benutzer_name=benutzer_name,
				)
				session.store(einstellung, einstellung.id)
			einstellung.sortierungen = list(sortierungen)
			session.save_changes()

	def delete(self, benutzer_name: str) -> bool:
		document_id = einstellung_id(benutzer_name)
		with self._get_store().open_session() as session:
			if session.load(document_id, AdresslistenEinstellung) is None:
				return False
			session.delete(document_id)
			session.save_changes()
			return True

	def _get_store(self):
		if self._store is None:
			self._store = create_document_store(
				collection_names={AdresslistenEinstellung: 'AdresslistenEinstellungen'},
			)
		return self._store


def einstellung_id(benutzer_name: str) -> str:
	return f'adresslisten-einstellungen/{quote(benutzer_name.strip(), safe="")}'


ADRESSLISTEN_EINSTELLUNGEN = AdresslistenEinstellungenRepository()
