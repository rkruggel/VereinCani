from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.db.client import create_document_store
from src.pages.adressen.constants import ADDRESS_FIELDS, DEFAULT_SORT_CRITERIA, FORM_FIELDS
from src.pages.adressen.models import Adresse


class RavenAdressenDatabase:
	def __init__(self) -> None:
		self._store = None

	def list(self, sortierungen: list[str] | None = None) -> list[dict[str, Any]]:
		with self._get_store().open_session() as session:
			records = list(session.query_collection('Adressen', Adresse))
			criteria = DEFAULT_SORT_CRITERIA if sortierungen is None else sortierungen
			return sort_records([asdict(record) for record in records], criteria)

	def get(self, record_id: str) -> dict[str, Any] | None:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			return asdict(record) if record is not None else None

	def create(self, data: dict[str, Any]) -> dict[str, Any]:
		record = self._create_record(data, f'adressen/{uuid4()}')
		with self._get_store().open_session() as session:
			session.store(record, record.id)
			session.save_changes()
		return asdict(record)

	def update(self, record_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return None
			for field in FORM_FIELDS:
				value = data.get(field, '')
				setattr(record, field, list(value or []) if field == 'nichtWochentag' else value)
			session.save_changes()
			return asdict(record)

	def update_text(self, record_id: str, text: str) -> bool:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			record.text = text
			session.save_changes()
			return True

	def add_image(
		self,
		record_id: str,
		file_name: str,
		content_type: str,
		data: bytes,
	) -> dict[str, str] | None:
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
			record.bilder = list(record.bilder or [])
			record.bilder.append(image)
			session.advanced.attachments.store(record_id, attachment_name, data, content_type)
			session.save_changes()
			return image

	def get_images(self, record_id: str) -> list[dict[str, Any]]:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return []
			images = []
			for image in record.bilder or []:
				with session.advanced.attachments.get(record_id, image['attachment_name']) as attachment:
					images.append({
						**image,
						'data': attachment.data,
					})
			return images

	def clear_images(self, record_id: str) -> bool:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			for image in record.bilder or []:
				session.advanced.attachments.delete(record_id, image['attachment_name'])
			record.bilder = []
			session.save_changes()
			return True

	def delete_image(self, record_id: str, attachment_name: str) -> bool:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			images = list(record.bilder or [])
			if not any(image.get('attachment_name') == attachment_name for image in images):
				return False
			session.advanced.attachments.delete(record_id, attachment_name)
			record.bilder = [
				image for image in images
				if image.get('attachment_name') != attachment_name
			]
			session.save_changes()
			return True

	def delete(self, record_id: str) -> bool:
		with self._get_store().open_session() as session:
			record = session.load(record_id, Adresse)
			if record is None:
				return False
			session.delete(record)
			session.save_changes()
			return True

	def _get_store(self):
		if self._store is None:
			self._store = create_document_store(collection_names={Adresse: 'Adressen'})
		return self._store

	@staticmethod
	def _create_record(data: dict[str, Any], record_id: str) -> Adresse:
		values = {field: data.get(field, '') for field in FORM_FIELDS}
		values['nichtWochentag'] = list(data.get('nichtWochentag') or [])
		return Adresse(id=record_id, **values)


ADRESSEN_DB = RavenAdressenDatabase()


def sort_records(records: list[dict[str, Any]], sortierungen: list[str]) -> list[dict[str, Any]]:
	result = list(records)
	for criterion in reversed(sortierungen):
		field, separator, direction = criterion.partition(':')
		if not separator or field not in ADDRESS_FIELDS or direction not in {'asc', 'desc'}:
			continue
		result.sort(
			key=lambda record, selected_field=field: sortable_value(record.get(selected_field)),
			reverse=direction == 'desc',
		)
	return result


def sortable_value(value: Any) -> str:
	if isinstance(value, list):
		value = ', '.join(str(item) for item in value)
	return str(value or '').casefold()
