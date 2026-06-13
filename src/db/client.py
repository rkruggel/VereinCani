"""
Konfiguration und HTTP-Zugriff für die gemeinsame CouchDB-Datenbank.
"""
import configparser
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import requests


CONFIG_PATH = Path(__file__).resolve().parents[2] / 'config.ini'
COLLECTION_FIELD = 'vereingui_collection'
LEGACY_COLLECTION_FIELDS = {'vereincani_collection'}
COUCH_INTERNAL_FIELDS = {
	'_id',
	'_rev',
	'_attachments',
	COLLECTION_FIELD,
	*LEGACY_COLLECTION_FIELDS,
}


class CouchDatabaseError(RuntimeError):
	"""
	Meldet fehlgeschlagene CouchDB-Anfragen.
	"""
class CouchConflictError(CouchDatabaseError):
	"""
	Meldet einen nicht auflösbaren Revisionskonflikt.
	"""
@dataclass(frozen=True)
class CouchConfig:
	"""
	Verbindungsdaten der CouchDB-Instanz.
	"""
	server_url: str
	database: str
	username: str = ''
	password: str = ''


def load_couch_config(config_path: Path = CONFIG_PATH) -> CouchConfig:
	"""
	Lädt die CouchDB-Zugangsdaten aus Umgebung oder ``config.ini``.
	"""
	parser = configparser.ConfigParser()
	parser.read(config_path)
	return CouchConfig(
		server_url=os.getenv(
			'COUCHDB_URL',
			parser.get('couchdb', 'server_url', fallback='http://127.0.0.1:5984'),
		).rstrip('/'),
		database=os.getenv(
			'COUCHDB_DATABASE',
			parser.get('couchdb', 'database', fallback='vereingui'),
		),
		username=os.getenv(
			'COUCHDB_USERNAME',
			parser.get('couchdb', 'username', fallback=''),
		),
		password=os.getenv(
			'COUCHDB_PASSWORD',
			parser.get('couchdb', 'password', fallback=''),
		),
	)


class CouchDatabase:
	"""
	Kapselt dokumentorientierte CouchDB-Operationen für die Anwendung.
	"""
	MAX_RETRIES = 5

	def __init__(self, config: CouchConfig | None = None) -> None:
		"""
		Initialisiert die Instanz mit den übergebenen Werten.
		"""
		self.config = config or load_couch_config()
		self._session = requests.Session()
		if self.config.username:
			self._session.auth = (self.config.username, self.config.password)
		self._session.headers.update({'Accept': 'application/json'})
		self._database_url = (
			f'{self.config.server_url}/{quote(self.config.database, safe="")}'
		)
		self.ensure_database()

	def ensure_database(self) -> None:
		"""
		Legt die konfigurierte Datenbank an, falls sie noch nicht existiert.
		"""
		response = self._session.get(self._database_url, timeout=15)
		if response.status_code == 404:
			response = self._session.put(self._database_url, timeout=15)
		self._raise_for_status(response, 'CouchDB-Datenbank konnte nicht geöffnet werden')

	def list_documents(self, collection: str) -> list[dict[str, Any]]:
		"""
		Lädt alle Dokumente einer logischen Collection.
		"""
		response = self._session.get(
			f'{self._database_url}/_all_docs',
			params={'include_docs': 'true'},
			timeout=30,
		)
		self._raise_for_status(response, 'CouchDB-Dokumente konnten nicht geladen werden')
		return [
			deepcopy(row['doc'])
			for row in response.json().get('rows', [])
			if self._document_collection(row.get('doc', {})) == collection
		]

	def get_document(self, document_id: str) -> dict[str, Any] | None:
		"""
		Lädt ein Dokument anhand seiner stabilen ID.
		"""
		response = self._session.get(self._document_url(document_id), timeout=15)
		if response.status_code == 404:
			return None
		self._raise_for_status(response, f'CouchDB-Dokument {document_id} konnte nicht geladen werden')
		return response.json()

	def create_document(
		self,
		document_id: str,
		data: dict[str, Any],
		collection: str,
	) -> dict[str, Any]:
		"""
		Erstellt ein neues Dokument und lehnt vorhandene IDs ab.
		"""
		document = self._prepare_document(document_id, data, collection)
		response = self._session.put(
			self._document_url(document_id),
			json=document,
			timeout=30,
		)
		if response.status_code == 409:
			raise CouchConflictError(f'CouchDB-Dokument existiert bereits: {document_id}')
		self._raise_for_status(response, f'CouchDB-Dokument {document_id} konnte nicht erstellt werden')
		document['_rev'] = response.json()['rev']
		return document

	def put_document(
		self,
		document_id: str,
		data: dict[str, Any],
		collection: str,
	) -> dict[str, Any]:
		"""
		Erstellt oder ersetzt ein Dokument revisionssicher.
		"""
		for _attempt in range(self.MAX_RETRIES):
			existing = self.get_document(document_id)
			document = self._prepare_document(document_id, data, collection)
			if existing is not None:
				document['_rev'] = existing['_rev']
				if '_attachments' in existing and '_attachments' not in document:
					document['_attachments'] = existing['_attachments']
			response = self._session.put(
				self._document_url(document_id),
				json=document,
				timeout=60,
			)
			if response.status_code == 409:
				continue
			self._raise_for_status(response, f'CouchDB-Dokument {document_id} konnte nicht gespeichert werden')
			document['_rev'] = response.json()['rev']
			return document
		raise CouchConflictError(f'CouchDB-Dokument {document_id} wurde gleichzeitig geändert')

	def mutate_document(
		self,
		document_id: str,
		mutator: Callable[[dict[str, Any]], None],
	) -> dict[str, Any] | None:
		"""
		Ändert ein vorhandenes Dokument mit Konfliktwiederholung.
		"""
		for _attempt in range(self.MAX_RETRIES):
			document = self.get_document(document_id)
			if document is None:
				return None
			mutator(document)
			response = self._session.put(
				self._document_url(document_id),
				json=document,
				timeout=60,
			)
			if response.status_code == 409:
				continue
			self._raise_for_status(response, f'CouchDB-Dokument {document_id} konnte nicht geändert werden')
			document['_rev'] = response.json()['rev']
			return document
		raise CouchConflictError(f'CouchDB-Dokument {document_id} wurde gleichzeitig geändert')

	def delete_document(self, document_id: str) -> bool:
		"""
		Löscht ein Dokument einschließlich seiner Anhänge.
		"""
		for _attempt in range(self.MAX_RETRIES):
			document = self.get_document(document_id)
			if document is None:
				return False
			response = self._session.delete(
				self._document_url(document_id),
				params={'rev': document['_rev']},
				timeout=30,
			)
			if response.status_code == 409:
				continue
			self._raise_for_status(response, f'CouchDB-Dokument {document_id} konnte nicht gelöscht werden')
			return True
		raise CouchConflictError(f'CouchDB-Dokument {document_id} wurde gleichzeitig geändert')

	def get_attachment(self, document_id: str, attachment_name: str) -> bytes | None:
		"""
		Lädt die Binärdaten eines CouchDB-Anhangs.
		"""
		response = self._session.get(
			f'{self._document_url(document_id)}/{quote(attachment_name, safe="")}',
			timeout=60,
		)
		if response.status_code == 404:
			return None
		self._raise_for_status(
			response,
			f'CouchDB-Anhang {attachment_name} konnte nicht geladen werden',
		)
		return response.content

	def plain_document(self, document: dict[str, Any]) -> dict[str, Any]:
		"""
		Entfernt CouchDB-interne Felder aus einem Anwendungsdokument.
		"""
		return {
			key: deepcopy(value)
			for key, value in document.items()
			if key not in COUCH_INTERNAL_FIELDS
		}

	def close(self) -> None:
		"""
		Schließt die HTTP-Sitzung des CouchDB-Clients.
		"""
		self._session.close()

	def _prepare_document(
		self,
		document_id: str,
		data: dict[str, Any],
		collection: str,
	) -> dict[str, Any]:
		"""
		Bereitet ein Anwendungsdokument für CouchDB vor.
		"""
		document = deepcopy(data)
		document['_id'] = document_id
		document[COLLECTION_FIELD] = collection
		return document

	@staticmethod
	def _document_collection(document: dict[str, Any]) -> str | None:
		"""
		Liest die logische Collection eines CouchDB-Dokuments.
		"""
		if document.get(COLLECTION_FIELD) is not None:
			return document[COLLECTION_FIELD]
		for legacy_field in LEGACY_COLLECTION_FIELDS:
			if document.get(legacy_field) is not None:
				return document[legacy_field]
		return None

	def _document_url(self, document_id: str) -> str:
		"""
		Erzeugt die URL eines CouchDB-Dokuments.
		"""
		return f'{self._database_url}/{quote(document_id, safe="")}'

	@staticmethod
	def _raise_for_status(response: requests.Response, message: str) -> None:
		"""
		Wandelt fehlgeschlagene HTTP-Antworten in Ausnahmen um.
		"""
		if response.ok:
			return
		try:
			detail = response.json()
		except requests.JSONDecodeError:
			detail = response.text
		raise CouchDatabaseError(f'{message}: HTTP {response.status_code} {detail}')


def create_couch_database(config: CouchConfig | None = None) -> CouchDatabase:
	"""
	Erzeugt einen CouchDB-Client für die konfigurierte Datenbank.
	"""
	return CouchDatabase(config)
