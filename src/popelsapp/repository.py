"""CouchDB-Zugriff für konfigurierbare Popels und Bild-Anhänge."""

from __future__ import annotations

import base64
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from src.db.client import COUCH_INTERNAL_FIELDS, create_couch_database
from src.popelsapp import PopelsConfig


class CouchPopelsDatabase:
	"""Kapselt Datenbankoperationen für ein konfiguriertes Popels-Modul."""

	def __init__(self, config: PopelsConfig, model: type) -> None:
		self.config = config
		self.model = model
		self._database = None

	def list(self, sortierungen: list[str] | None = None) -> list[dict[str, Any]]:
		"""Lädt alle Datensätze und sortiert sie nach den übergebenen Kriterien."""

		documents = self._get_database().list_documents(self.config.collection_name)
		criteria = [] if sortierungen is None else sortierungen
		records = [self._normalize_document(document) for document in documents]
		return sort_records(records, criteria, self.config.sort_fields)

	def get(self, record_id: str) -> dict[str, Any] | None:
		"""Lädt einen Datensatz anhand seiner CouchDB-ID."""

		document = self._get_database().get_document(record_id)
		return self._normalize_document(document) if document is not None else None

	def cleanup_unknown_fields(self) -> tuple[int, int]:
		"""Entfernt alle Dokumentfelder, die nicht in der Feldkonfiguration stehen."""

		allowed_fields = set(self.config.field_labels) | set(COUCH_INTERNAL_FIELDS)
		checked = 0
		updated = 0
		for document in self._get_database().list_documents(self.config.collection_name):
			record_id = document.get('_id')
			if record_id is None:
				continue
			checked += 1
			extra_fields = [
				field_name
				for field_name in document
				if field_name not in allowed_fields
			]
			if not extra_fields:
				continue
			updated += 1

			def mutate(stored_document: dict[str, Any]) -> None:
				for field_name in extra_fields:
					stored_document.pop(field_name, None)

			self._get_database().mutate_document(record_id, mutate)
		return checked, updated

	def create(self, data: dict[str, Any]) -> dict[str, Any]:
		"""Erstellt und speichert einen neuen Datensatz mit eindeutiger ID."""

		record = self._create_record(data, f'{self.config.id_prefix}/{uuid4()}')
		self._get_database().create_document(
			record.id,
			asdict(record),
			self.config.collection_name,
		)
		return asdict(record)

	def update(self, record_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
		"""Aktualisiert die Formularfelder eines vorhandenen Datensatzes."""

		def mutate(document: dict[str, Any]) -> None:
			for field in self.config.form_fields:
				if self.config.page(field).get('berechnen'):
					document.pop(field, None)
					continue
				value = data.get(field, '')
				if self.config.field_labels[field]['type'] == 'liste':
					value = normalize_list_value(value)
				elif self.config.field_labels[field]['type'] in {'kursbuchungen', 'kursbesuche'}:
					value = normalize_course_bookings_value(value)
				document[field] = value
				if field == 'kursbesuche':
					document.pop('kursbuchungen', None)

		document = self._get_database().mutate_document(record_id, mutate)
		return self._normalize_document(document) if document is not None else None

	def update_text(self, record_id: str, text: str) -> bool:
		"""Speichert den freien Text eines Datensatzes."""

		if self.config.editor_field is None:
			return False

		def mutate(document: dict[str, Any]) -> None:
			document[self.config.editor_field] = text

		return self._get_database().mutate_document(record_id, mutate) is not None

	def add_image(
		self,
		record_id: str,
		file_name: str,
		content_type: str,
		data: bytes,
		caption: str | None = None,
	) -> dict[str, str] | None:
		"""Speichert ein Bild als CouchDB-Anhang und ergänzt dessen Metadaten."""

		if self.config.image_field is None:
			return None
		attachment_name = f'{uuid4()}-{file_name}'
		image = {
			'attachment_name': attachment_name,
			'name': file_name,
			'content_type': content_type,
			'caption': (caption or '').strip(),
		}

		def mutate(document: dict[str, Any]) -> None:
			images = list(document.get(self.config.image_field) or [])
			images.append(image)
			document[self.config.image_field] = images
			attachments = dict(document.get('_attachments') or {})
			attachments[attachment_name] = {
				'content_type': content_type,
				'data': base64.b64encode(data).decode('ascii'),
			}
			document['_attachments'] = attachments

		document = self._get_database().mutate_document(record_id, mutate)
		return image if document is not None else None

	def update_image_caption(self, record_id: str, attachment_name: str, caption: str) -> bool:
		"""Aktualisiert den Kurztext (caption) eines vorhandenen Bildes."""

		if self.config.image_field is None:
			return False

		updated = {'value': False}

		def mutate(document: dict[str, Any]) -> None:
			images = list(document.get(self.config.image_field) or [])
			for image in images:
				if image.get('attachment_name') == attachment_name:
					image['caption'] = caption.strip()
					updated['value'] = True
					break
			document[self.config.image_field] = images

		document = self._get_database().mutate_document(record_id, mutate)
		return document is not None and updated['value']

	def get_images(self, record_id: str) -> list[dict[str, Any]]:
		"""Lädt Bildmetadaten und Binärdaten aller konfigurierten Anhänge."""

		document = self._get_database().get_document(record_id)
		if document is None or self.config.image_field is None:
			return []
		images = []
		for image in document.get(self.config.image_field) or []:
			data = self._get_database().get_attachment(
				record_id,
				image['attachment_name'],
			)
			if data is not None:
				images.append({**image, 'data': data})
		return images

	def clear_images(self, record_id: str) -> bool:
		"""Löscht sämtliche konfigurierten Bild-Anhänge eines Datensatzes."""

		if self.config.image_field is None:
			return False

		def mutate(document: dict[str, Any]) -> None:
			attachments = dict(document.get('_attachments') or {})
			for image in document.get(self.config.image_field) or []:
				attachments.pop(image.get('attachment_name'), None)
			document[self.config.image_field] = []
			if attachments:
				document['_attachments'] = attachments
			else:
				document.pop('_attachments', None)

		return self._get_database().mutate_document(record_id, mutate) is not None

	def delete_image(self, record_id: str, attachment_name: str) -> bool:
		"""Löscht ein einzelnes Bild anhand seines internen Attachment-Namens."""

		if self.config.image_field is None:
			return False
		deleted = {'value': False}

		def mutate(document: dict[str, Any]) -> None:
			images = list(document.get(self.config.image_field) or [])
			if not any(image.get('attachment_name') == attachment_name for image in images):
				return
			document[self.config.image_field] = [
				image
				for image in images
				if image.get('attachment_name') != attachment_name
			]
			attachments = dict(document.get('_attachments') or {})
			attachments.pop(attachment_name, None)
			if attachments:
				document['_attachments'] = attachments
			else:
				document.pop('_attachments', None)
			deleted['value'] = True

		document = self._get_database().mutate_document(record_id, mutate)
		return document is not None and deleted['value']

	def delete(self, record_id: str) -> bool:
		"""Löscht einen Datensatz samt seiner Anhänge."""

		return self._get_database().delete_document(record_id)

	def _get_database(self):
		if self._database is None:
			self._database = create_couch_database()
		return self._database

	def _create_record(self, data: dict[str, Any], record_id: str):
		"""Erstellt ein normalisiertes Modell aus Formularwerten."""

		values = {}
		for field in self.config.form_fields:
			if self.config.page(field).get('berechnen'):
				continue
			value = data.get(field, '')
			if self.config.field_labels[field]['type'] == 'liste':
				value = normalize_list_value(value)
			elif self.config.field_labels[field]['type'] in {'kursbuchungen', 'kursbesuche'}:
				value = normalize_course_bookings_value(value)
			values[field] = value
		return self.model(id=record_id, **values)

	def _normalize_document(self, document: dict[str, Any]) -> dict[str, Any]:
		"""Übernimmt ein CouchDB-Dokument mit den konfigurierten Feldnamen."""

		values = {}
		for field, definition in self.config.field_labels.items():
			default = [] if definition['type'] in {'liste', 'bilder', 'kursbuchungen', 'kursbesuche'} else ''
			value = document.get(field, default)
			if definition['type'] == 'liste':
				value = normalize_list_value(value)
			elif definition['type'] in {'kursbuchungen', 'kursbesuche'}:
				value = normalize_course_bookings_value(value)
				if field == 'kursbesuche' and not value:
					value = normalize_course_bookings_value(document.get('kursbuchungen', default))
			values[field] = value
		values['id'] = document.get('_id') or document.get('id') or values.get('id', '')
		return values


def normalize_list_value(value: Any) -> list[Any]:
	"""Normalisiert alte Einzelwerte und neue Listenwerte auf eine Liste."""

	if value in (None, ''):
		return []
	if isinstance(value, list):
		return value
	return [value]


def normalize_course_bookings_value(value: Any) -> list[dict[str, Any]]:
	"""Normalisiert Kursbesuchszeilen auf saubere Wörterbücher."""

	if value in (None, ''):
		return []
	if not isinstance(value, list):
		return []
	rows = []
	for row in value:
		if not isinstance(row, dict):
			continue
		booking = {
			'kurs': str(row.get('kurs') or '').strip(),
			'datumVon': str(row.get('datumVon') or row.get('datum') or '').strip(),
			'bezahlt': normalize_paid_value(row.get('bezahlt')),
		}
		if booking['kurs'] or booking['datumVon'] or booking['bezahlt'] is not None:
			rows.append(booking)
	return rows


def normalize_paid_value(value: Any) -> bool | None:
	"""Normalisiert den Bezahlstatus und erhält leere Werte."""

	if value is None or value == '':
		return None
	if isinstance(value, str):
		return value.strip().casefold() == 'ja'
	return bool(value)


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
			key=lambda record, selected_field=field: sortable_field_value(
				selected_field,
				record.get(selected_field),
			),
			reverse=direction == 'desc',
		)
	return result


def sortable_field_value(field: str, value: Any) -> str | tuple[str, str]:
	"""Bereitet ein Feld entsprechend seiner fachlichen Sortierung auf."""

	if field == 'name':
		return sortable_name(value)
	return sortable_value(value)


def sortable_name(value: Any) -> tuple[str, str]:
	"""Sortiert vollständige Namen nach dem letzten und danach den übrigen Teilen."""

	parts = str(value or '').split()
	if not parts:
		return '', ''
	return parts[-1].casefold(), ' '.join(parts[:-1]).casefold()


def sortable_value(value: Any) -> str:
	"""Wandelt unterschiedliche Feldwerte in einen vergleichbaren Suchtext um."""

	if isinstance(value, list):
		value = ', '.join(str(item) for item in value)
	return str(value or '').casefold()
