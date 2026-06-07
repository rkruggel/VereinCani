"""RavenDB-Zugriff für konfigurierbare Stammdaten und Bild-Attachments."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.db.client import create_document_store
from src.pages.stammdaten import StammdatenConfig


class RavenStammdatenDatabase:
	"""Kapselt Datenbankoperationen für ein konfiguriertes Stammdatenmodul."""

	def __init__(self, config: StammdatenConfig, model: type) -> None:
		"""Initialisiert das Repository mit einem verzögert erzeugten DocumentStore."""

		self.config = config
		self.model = model
		self._store = None

	def list(self, sortierungen: list[str] | None = None) -> list[dict[str, Any]]:
		"""Lädt alle Datensätze und sortiert sie nach den übergebenen Kriterien."""

		with self._get_store().open_session() as session:
			records = list(session.query_collection(self.config.collection_name, self.model))
			criteria = [] if sortierungen is None else sortierungen
			return sort_records([asdict(record) for record in records], criteria, self.config.sort_fields)

	def get(self, record_id: str) -> dict[str, Any] | None:
		"""Lädt einen Datensatz anhand seiner RavenDB-ID."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			return asdict(record) if record is not None else None

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
			record = session.load(record_id, self.model)
			if record is None:
				return None
			for field in self.config.form_fields:
				value = data.get(field, '')
				if self.config.field_labels[field]['type'] == 'liste':
					value = list(value or [])
				setattr(record, field, value)
			session.save_changes()
			return asdict(record)

	def update_text(self, record_id: str, text: str) -> bool:
		"""Speichert den freien Text eines Datensatzes."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			if record is None:
				return False
			if self.config.editor_field is None:
				return False
			setattr(record, self.config.editor_field, text)
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
			record = session.load(record_id, self.model)
			if record is None:
				return None
			if self.config.image_field is None:
				return None
			attachment_name = f'{uuid4()}-{file_name}'
			image = {
				'attachment_name': attachment_name,
				'name': file_name,
				'content_type': content_type,
			}
			images = list(getattr(record, self.config.image_field) or [])
			images.append(image)
			setattr(record, self.config.image_field, images)
			session.advanced.attachments.store(record_id, attachment_name, data, content_type)
			session.save_changes()
			return image

	def get_images(self, record_id: str) -> list[dict[str, Any]]:
		"""Lädt Bildmetadaten und Binärdaten aller Attachments."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			if record is None or self.config.image_field is None:
				return []
			images = []
			for image in getattr(record, self.config.image_field) or []:
				with session.advanced.attachments.get(record_id, image['attachment_name']) as attachment:
					images.append({
						**image,
						'data': attachment.data,
					})
			return images

	def clear_images(self, record_id: str) -> bool:
		"""Löscht sämtliche Bild-Attachments eines Datensatzes."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			if record is None or self.config.image_field is None:
				return False
			for image in getattr(record, self.config.image_field) or []:
				session.advanced.attachments.delete(record_id, image['attachment_name'])
			setattr(record, self.config.image_field, [])
			session.save_changes()
			return True

	def delete_image(self, record_id: str, attachment_name: str) -> bool:
		"""Löscht ein einzelnes Bild anhand seines internen Attachment-Namens."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			if record is None or self.config.image_field is None:
				return False
			images = list(getattr(record, self.config.image_field) or [])
			if not any(image.get('attachment_name') == attachment_name for image in images):
				return False
			session.advanced.attachments.delete(record_id, attachment_name)
			setattr(record, self.config.image_field, [
				image for image in images
				if image.get('attachment_name') != attachment_name
			])
			session.save_changes()
			return True

	def delete(self, record_id: str) -> bool:
		"""Löscht einen Datensatz samt seiner Attachments."""

		with self._get_store().open_session() as session:
			record = session.load(record_id, self.model)
			if record is None:
				return False
			session.delete(record)
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
			value = data.get(field, '')
			if self.config.field_labels[field]['type'] == 'liste':
				value = list(value or [])
			values[field] = value
		return self.model(id=record_id, **values)


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
