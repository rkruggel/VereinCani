"""RavenDB-Zugriff für Adressen und zugeordnete Bild-Attachments."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.db.client import create_document_store
from src.pages.adressen.constants import EDITOR_FIELD, FIELD_LABELS, FORM_FIELDS, IMAGE_FIELD, SORT_FIELDS
from src.pages.adressen.models import Adresse


class RavenAdressenDatabase:
	"""Kapselt alle Datenbankoperationen für Adressdokumente."""

	def __init__(self) -> None:
		"""Initialisiert das Repository mit einem verzögert erzeugten DocumentStore."""

		self._store = None

	def list(self, sortierungen: list[str] | None = None) -> list[dict[str, Any]]:
		"""Lädt alle Adressen und sortiert sie nach den übergebenen Kriterien."""

		with self._get_store().open_session() as session:
			records = list(session.query_collection('Adressen', Adresse))
			criteria = [] if sortierungen is None else sortierungen
			return sort_records([asdict(record) for record in records], criteria)

	def get(self, record_id: str) -> dict[str, Any] | None:
		"""Lädt eine Adresse anhand ihrer RavenDB-ID."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			return asdict(record) if record is not None else None

	def create(self, data: dict[str, Any]) -> dict[str, Any]:
		"""Erstellt und speichert eine neue Adresse mit einer eindeutigen ID."""

		record = self._create_record(data, f'adressen/{uuid4()}')
		with self._get_store().open_session() as session:
			session.store(record, record.id)
			session.save_changes()
		return asdict(record)

	def update(self, record_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
		"""Aktualisiert die Formularfelder einer vorhandenen Adresse."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return None
			for field in FORM_FIELDS:
				value = data.get(field, '')
				if FIELD_LABELS[field]['type'] == 'liste':
					value = list(value or [])
				setattr(record, field, value)
			session.save_changes()
			return asdict(record)

	def update_text(self, record_id: str, text: str) -> bool:
		"""Speichert den freien Text einer Adresse."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			setattr(record, EDITOR_FIELD, text)
			session.save_changes()
			return True

	def add_image(
		self,
		record_id: str,
		file_name: str,
		content_type: str,
		data: bytes,
	) -> dict[str, str] | None:
		"""Speichert ein Bild als RavenDB-Attachment und ergänzt dessen Metadaten."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return None
			attachment_name = f'{uuid4()}-{file_name}'
			image = {
				'attachment_name': attachment_name,
				'name': file_name,
				'content_type': content_type,
			}
			images = list(getattr(record, IMAGE_FIELD) or [])
			images.append(image)
			setattr(record, IMAGE_FIELD, images)
			session.advanced.attachments.store(record_id, attachment_name, data, content_type)
			session.save_changes()
			return image

	def get_images(self, record_id: str) -> list[dict[str, Any]]:
		"""Lädt Bildmetadaten und Binärdaten aller Attachments einer Adresse."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return []
			images = []
			for image in getattr(record, IMAGE_FIELD) or []:
				with session.advanced.attachments.get(record_id, image['attachment_name']) as attachment:
					images.append({
						**image,
						'data': attachment.data,
					})
			return images

	def clear_images(self, record_id: str) -> bool:
		"""Löscht sämtliche Bild-Attachments einer Adresse."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			for image in getattr(record, IMAGE_FIELD) or []:
				session.advanced.attachments.delete(record_id, image['attachment_name'])
			setattr(record, IMAGE_FIELD, [])
			session.save_changes()
			return True

	def delete_image(self, record_id: str, attachment_name: str) -> bool:
		"""Löscht ein einzelnes Bild anhand seines internen Attachment-Namens."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			images = list(getattr(record, IMAGE_FIELD) or [])
			if not any(image.get('attachment_name') == attachment_name for image in images):
				return False
			session.advanced.attachments.delete(record_id, attachment_name)
			setattr(record, IMAGE_FIELD, [
				image for image in images
				if image.get('attachment_name') != attachment_name
			])
			session.save_changes()
			return True

	def delete(self, record_id: str) -> bool:
		"""Löscht eine Adresse; RavenDB entfernt dabei auch ihre Attachments."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			session.delete(record)
			session.save_changes()
			return True

	def _get_store(self):
		"""Erzeugt den RavenDB-DocumentStore bei der ersten Verwendung."""

		if self._store is None:
			self._store = create_document_store(collection_names={Adresse: 'Adressen'})
		return self._store

	@staticmethod
	def _create_record(data: dict[str, Any], record_id: str) -> Adresse:
		"""Erstellt ein normalisiertes Adressmodell aus Formularwerten."""

		values = {}
		for field in FORM_FIELDS:
			value = data.get(field, '')
			if FIELD_LABELS[field]['type'] == 'liste':
				value = list(value or [])
			values[field] = value
		return Adresse(id=record_id, **values)


ADRESSEN_DB = RavenAdressenDatabase()


def sort_records(records: list[dict[str, Any]], sortierungen: list[str]) -> list[dict[str, Any]]:
	"""Sortiert Datensätze stabil nach mehreren priorisierten Kriterien."""

	result = list(records)
	for criterion in reversed(sortierungen):
		field, separator, direction = criterion.partition(':')
		if (
			not separator
			or field not in SORT_FIELDS
			or direction not in {'asc', 'desc'}
		):
			continue
		result.sort(
			key=lambda record, selected_field=field: sortable_value(record.get(selected_field)),
			reverse=direction == 'desc',
		)
	return result


def sortable_value(value: Any) -> str:
	"""Wandelt unterschiedliche Feldwerte in einen vergleichbaren Suchtext um."""

	if isinstance(value, list):
		value = ', '.join(str(item) for item in value)
	return str(value or '').casefold()
