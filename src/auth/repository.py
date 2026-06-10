"""CouchDB-Zugriff für Benutzerkonten und Anmeldedaten."""

import hashlib
from dataclasses import asdict

from src.auth.models import Benutzer
from src.auth.security import hash_kennung, verify_kennung
from src.db.client import CouchConflictError, create_couch_database


class BenutzerRepository:
	def __init__(self) -> None:
		self._database = None

	def register(self, email: str, name: str, kennung: str) -> Benutzer:
		normalized_email = normalize_email(email)
		document_id = benutzer_id(normalized_email)
		if self._get_database().get_document(document_id) is not None:
			raise ValueError('Fuer diese E-Mail-Adresse besteht bereits ein Zugang.')
		kennung_hash, kennung_salt = hash_kennung(kennung)
		benutzer = Benutzer(
			id=document_id,
			email=normalized_email,
			name=name.strip(),
			kennung_hash=kennung_hash,
			kennung_salt=kennung_salt,
		)
		try:
			self._get_database().create_document(
				document_id,
				asdict(benutzer),
				'Benutzer',
			)
		except CouchConflictError as error:
			raise ValueError('Fuer diese E-Mail-Adresse besteht bereits ein Zugang.') from error
		return benutzer

	def authenticate(self, email: str, kennung: str) -> Benutzer | None:
		document = self._get_database().get_document(benutzer_id(normalize_email(email)))
		if document is None:
			return None
		benutzer = Benutzer(**{
			field: document.get(field, '')
			for field in Benutzer.__dataclass_fields__
		})
		if not verify_kennung(kennung, benutzer.kennung_hash, benutzer.kennung_salt):
			return None
		return benutzer

	def delete(self, email: str) -> bool:
		return self._get_database().delete_document(benutzer_id(normalize_email(email)))

	def _get_database(self):
		if self._database is None:
			self._database = create_couch_database()
		return self._database


def normalize_email(email: str) -> str:
	return email.strip().lower()


def benutzer_id(email: str) -> str:
	email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
	return f'benutzer/{email_hash}'


BENUTZER_REPOSITORY = BenutzerRepository()
