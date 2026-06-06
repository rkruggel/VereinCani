import hashlib

from src.auth.models import Benutzer
from src.auth.security import hash_kennung, verify_kennung
from src.db.client import create_document_store


class BenutzerRepository:
	def __init__(self) -> None:
		self._store = None

	def register(self, email: str, name: str, kennung: str) -> Benutzer:
		normalized_email = normalize_email(email)
		document_id = benutzer_id(normalized_email)
		with self._get_store().open_session() as session:
			if session.load(document_id, Benutzer) is not None:
				raise ValueError('Fuer diese E-Mail-Adresse besteht bereits ein Zugang.')
			kennung_hash, kennung_salt = hash_kennung(kennung)
			benutzer = Benutzer(
				id=document_id,
				email=normalized_email,
				name=name.strip(),
				kennung_hash=kennung_hash,
				kennung_salt=kennung_salt,
			)
			session.store(benutzer, benutzer.id)
			session.save_changes()
			return benutzer

	def authenticate(self, email: str, kennung: str) -> Benutzer | None:
		normalized_email = normalize_email(email)
		with self._get_store().open_session() as session:
			benutzer = session.load(benutzer_id(normalized_email), Benutzer)
			if benutzer is None:
				return None
			if not verify_kennung(kennung, benutzer.kennung_hash, benutzer.kennung_salt):
				return None
			return benutzer

	def delete(self, email: str) -> bool:
		document_id = benutzer_id(normalize_email(email))
		with self._get_store().open_session() as session:
			if session.load(document_id, Benutzer) is None:
				return False
			session.delete(document_id)
			session.save_changes()
			return True

	def _get_store(self):
		if self._store is None:
			self._store = create_document_store(collection_names={Benutzer: 'Benutzer'})
		return self._store


def normalize_email(email: str) -> str:
	return email.strip().lower()


def benutzer_id(email: str) -> str:
	email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
	return f'benutzer/{email_hash}'


BENUTZER_REPOSITORY = BenutzerRepository()
