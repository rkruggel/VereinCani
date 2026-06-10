"""Konfiguration eines aus Felddefinitionen aufgebauten Popels-Moduls."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PopelsConfig:
	"""Beschreibt Felder, Texte und Persistenz eines Popels-Bereichs."""

	key: str
	singular: str
	plural: str
	collection_name: str
	settings_collection_name: str
	field_labels: dict[str, dict[str, Any]]
	model_name: str
	legacy_name_fields: tuple[str, str] | None = None

	@property
	def id_prefix(self) -> str:
		"""Liefert das CouchDB-ID-Präfix der Fachdokumente."""

		return self.key

	@property
	def settings_id_prefix(self) -> str:
		"""Liefert das CouchDB-ID-Präfix der Benutzereinstellungen."""

		return f'{self.key}-listen-einstellungen'

	@property
	def form_fields(self) -> list[str]:
		"""Liefert alle im Eingabeformular verwendeten Felder."""

		return self.page_fields_with('formular')

	@property
	def required_fields(self) -> list[str]:
		"""Liefert alle als Pflichtfeld markierten Felder."""

		return self.page_fields_with('pflichtfeld')

	@property
	def search_fields(self) -> list[str]:
		"""Liefert alle Felder der Volltextsuche."""

		return self.list_fields_with('suchbar')

	@property
	def sort_fields(self) -> list[str]:
		"""Liefert alle für die Sortierung freigegebenen Felder."""

		return self.list_fields_with('sortierbar')

	@property
	def content_action_fields(self) -> list[str]:
		"""Liefert separat bearbeitete Inhaltsfelder wie Text und Bilder."""

		return [
			field
			for field in self.field_labels
			if self.page(field).get('actionLabel')
		]

	@property
	def editor_field(self) -> str | None:
		"""Liefert das optionale Rich-Text-Feld."""

		return self.field_for_control('editor')

	@property
	def image_field(self) -> str | None:
		"""Liefert das optionale Bilderfeld."""

		return self.field_for_control('upload')

	def page(self, field: str) -> dict[str, Any]:
		"""Liefert die Seitenkonfiguration eines Feldes."""

		return self.field_labels[field].get('page', {})

	def liste(self, field: str) -> dict[str, Any]:
		"""Liefert die Listenkonfiguration eines Feldes."""

		return self.field_labels[field].get('liste', {})

	def page_fields_with(self, marker: str) -> list[str]:
		"""Liefert Felder mit einem gesetzten Marker im ``page``-Block."""

		return [
			field
			for field in self.field_labels
			if self.page(field).get(marker)
		]

	def list_fields_with(self, marker: str) -> list[str]:
		"""Liefert Felder mit einem gesetzten Marker im ``liste``-Block."""

		return [
			field
			for field in self.field_labels
			if self.liste(field).get(marker)
		]

	def field_for_control(self, control: str) -> str | None:
		"""Sucht das erste Feld mit einem bestimmten Steuerelement."""

		return next(
			(
				field
				for field in self.field_labels
				if self.page(field).get('steuerelement') == control
			),
			None,
		)

	def field_position(self, field: str, key: str, default: Any = None) -> Any:
		"""Liefert eine Positionsangabe aus dem ``liste``-Block eines Feldes."""

		value = self.liste(field).get(key, default)
		if key == 'listSection' and value is False:
			return 'off'
		return value

	def is_list_field(self, field: str) -> bool:
		"""Prüft, ob ein Feld grundsätzlich in der Kartenliste erscheinen darf."""

		return self.field_position(field, 'listSection') != 'off'

	@property
	def list_display_fields(self) -> list[str]:
		"""Liefert alle Felder, die für die Kartenliste freigegeben sind."""

		return [field for field in self.field_labels if self.is_list_field(field)]

	def list_fields(self, section: str) -> list[str]:
		"""Liefert die Felder eines Listenbereichs in konfigurierter Reihenfolge."""

		return [
			field
			for field in sorted(
				self.field_labels,
				key=lambda item: self.liste(item).get('listPos', 0),
			)
			if self.is_list_field(field)
			and self.field_position(field, 'listSection') == section
		]


def load_popels_config(file_name: str) -> PopelsConfig:
	"""Lädt eine Popels-Konfiguration aus dem Projektordner ``popels``."""

	project_root = Path(__file__).resolve().parents[2]
	config_path = project_root / 'popels' / file_name
	with config_path.open(encoding='utf-8') as config_file:
		raw_config = yaml.safe_load(config_file)
	config_values = raw_config['config']
	legacy_name_fields = config_values.get('legacy_name_fields')
	if legacy_name_fields is not None:
		config_values['legacy_name_fields'] = tuple(legacy_name_fields)
	return PopelsConfig(
		**config_values,
		field_labels=raw_config['field_labels'],
	)
