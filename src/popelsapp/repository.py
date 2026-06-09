"""RavenDB-Zugriff für konfigurierbare Popels und Bild-Attachments."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.db.client import create_document_store
from src.popelsapp import PopelsConfig


class RavenPopelsDatabase:
	"""Kapselt Datenbankoperationen für ein konfiguriertes Popels-Modul."""

	def __init__(self, config: PopelsConfig, model: type) -> None:
		"""Initialisiert das Repository mit einem verzögert erzeugten DocumentStore."""

		self.config = config
		self.model = model
		self._store = None

	def list(self, sortierungen: list[str] | None = None) -> list[dict[str, Any]]:
		"""Lädt alle Datensätze und sortiert sie nach den übergebenen Kriterien."""

		with self._get_store().open_session() as session:
			documents = list(session.query_collection(self.config.collection_name, dict))
			criteria = [] if sortierungen is None else sortierungen
			records = [self._normalize_document(document) for document in documents]
			return sort_records(records, criteria, self.config.sort_fields)

	def get(self, record_id: str) -> dict[str, Any] | None:
		"""Lädt einen Datensatz anhand seiner RavenDB-ID."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			return self._normalize_document(document) if document is not None else None

	def create(self, data: dict[str, Any]) -> dict[str, Any]:
		"""Erstellt und speichert einen neuen Datensatz mit eindeutiger ID."""

		record = self._create_record(data, f'{self.config.id_prefix}/{uuid4()}')
		with self._get_store().open_session() as session:
			session.store(record, record.id)
			session.save_changes()
		return asdict(record)

	def update(self, record_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
		"""Aktualisiert die Formularfelder eines vorhandenen Datensatzes."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None:
				return None
			for field in self.config.form_fields:
				if self.config.field_labels[field].get('berechnen'):
					document.pop(field, None)
					continue
				value = data.get(field, '')
				if self.config.field_labels[field]['type'] == 'liste':
					value = list(value or [])
				document[field] = value
			session.save_changes()
			return self._normalize_document(document)

	def update_text(self, record_id: str, text: str) -> bool:
		"""Speichert den freien Text eines Datensatzes."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None:
				return False
			if self.config.editor_field is None:
				return False
			document[self.config.editor_field] = text
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
			document = session.load(record_id, dict)
			if document is None:
				return None
			if self.config.image_field is None:
				return None
			attachment_name = f'{uuid4()}-{file_name}'
			image = {
				'attachment_name': attachment_name,
				'name': file_name,
				'content_type': content_type,
			}
			images = list(document.get(self.config.image_field) or [])
			images.append(image)
			document[self.config.image_field] = images
			session.advanced.attachments.store(record_id, attachment_name, data, content_type)
			session.save_changes()
			return image

	def get_images(self, record_id: str) -> list[dict[str, Any]]:
		"""Lädt Bildmetadaten und Binärdaten aller Attachments."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None or self.config.image_field is None:
				return []
			images = []
			for image in document.get(self.config.image_field) or []:
				with session.advanced.attachments.get(record_id, image['attachment_name']) as attachment:
					images.append({
						**image,
						'data': attachment.data,
					})
			return images

	def clear_images(self, record_id: str) -> bool:
		"""Löscht sämtliche Bild-Attachments eines Datensatzes."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None or self.config.image_field is None:
				return False
			for image in document.get(self.config.image_field) or []:
				session.advanced.attachments.delete(record_id, image['attachment_name'])
			document[self.config.image_field] = []
			session.save_changes()
			return True

	def delete_image(self, record_id: str, attachment_name: str) -> bool:
		"""Löscht ein einzelnes Bild anhand seines internen Attachment-Namens."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None or self.config.image_field is None:
				return False
			images = list(document.get(self.config.image_field) or [])
			if not any(image.get('attachment_name') == attachment_name for image in images):
				return False
			session.advanced.attachments.delete(record_id, attachment_name)
			document[self.config.image_field] = [
				image for image in images
				if image.get('attachment_name') != attachment_name
			]
			session.save_changes()
			return True

	def delete(self, record_id: str) -> bool:
		"""Löscht einen Datensatz samt seiner Attachments."""

		with self._get_store().open_session() as session:
			document = session.load(record_id, dict)
			if document is None:
				return False
			session.delete(document)
			session.save_changes()
			return True

	def _get_store(self):
		"""Erzeugt den RavenDB-DocumentStore bei der ersten Verwendung."""

		if self._store is None:
			self._store = create_document_store(
				collection_names={self.model: self.config.collection_name},
			)
		return self._store

	def _create_record(self, data: dict[str, Any], record_id: str):
		"""Erstellt ein normalisiertes Modell aus Formularwerten."""

		values = {}
		for field in self.config.form_fields:
			if self.config.field_labels[field].get('berechnen'):
				continue
			value = data.get(field, '')
			if self.config.field_labels[field]['type'] == 'liste':
				value = list(value or [])
			values[field] = value
		return self.model(id=record_id, **values)

	def _normalize_document(self, document: dict[str, Any]) -> dict[str, Any]:
		"""Übernimmt RavenDB-Dokumente mit exakt den konfigurierten Feldnamen."""

		values = {
			field: document.get(
				field,
				[] if definition['type'] in {'liste', 'bilder'} else '',
			)
			for field, definition in self.config.field_labels.items()
		}
		metadata = document.get('@metadata') or {}
		values['id'] = document.get('id') or metadata.get('@id') or values.get('id', '')
		return values


def sort_records(
	records: list[dict[str, Any]],
	sortierungen: list[str],
	sort_fields: list[str],
) -> list[dict[str, Any]]:
	"""Sortiert Datensätze stabil nach mehreren priorisierten Kriterien."""

	result = list(records)
	for criterion in reversed(sortierungen):
		field, separator, direction = criterion.partition(':')
		if (
			not separator
			or field not in sort_fields
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
