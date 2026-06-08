"""Konfiguration eines aus Felddefinitionen aufgebauten Popels-Moduls."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
		"""Liefert das RavenDB-ID-Präfix der Fachdokumente."""

		return self.key

	@property
	def settings_id_prefix(self) -> str:
		"""Liefert das RavenDB-ID-Präfix der Benutzereinstellungen."""

		return f'{self.key}-listen-einstellungen'

	@property
	def form_fields(self) -> list[str]:
		"""Liefert alle im Eingabeformular verwendeten Felder."""

		return self.fields_with('formular')

	@property
	def required_fields(self) -> list[str]:
		"""Liefert alle als Pflichtfeld markierten Felder."""

		return self.fields_with('pflichtfeld')

	@property
	def search_fields(self) -> list[str]:
		"""Liefert alle Felder der Volltextsuche."""

		return self.fields_with('suchbar')

	@property
	def sort_fields(self) -> list[str]:
		"""Liefert alle für die Sortierung freigegebenen Felder."""

		return self.fields_with('sortierbar')

	@property
	def content_action_fields(self) -> list[str]:
		"""Liefert separat bearbeitete Inhaltsfelder wie Text und Bilder."""

		return [
			field
			for field, definition in self.field_labels.items()
			if definition.get('actionLabel')
		]

	@property
	def editor_field(self) -> str | None:
		"""Liefert das optionale Rich-Text-Feld."""

		return self.field_for_control('editor')

	@property
	def image_field(self) -> str | None:
		"""Liefert das optionale Bilderfeld."""

		return self.field_for_control('upload')

	def fields_with(self, marker: str) -> list[str]:
		"""Liefert Felder, deren Definition einen gesetzten Marker enthält."""

		return [
			field
			for field, definition in self.field_labels.items()
			if definition.get(marker)
		]

	def field_for_control(self, control: str) -> str | None:
		"""Sucht das erste Feld mit einem bestimmten Steuerelement."""

		return next(
			(
				field
				for field, definition in self.field_labels.items()
				if definition.get('steuerelement') == control
			),
			None,
		)

	def list_fields(self, section: str) -> list[str]:
		"""Liefert die Felder eines Listenbereichs in konfigurierter Reihenfolge."""

		return [
			field
			for field, definition in sorted(
				self.field_labels.items(),
				key=lambda item: item[1].get('listPos', 0),
			)
			if definition.get('listSection') == section
		]


def load_popels_config(file_name: str) -> PopelsConfig:
	"""Lädt eine Popels-Konfiguration aus dem Projektordner ``popels``."""

	project_root = Path(__file__).resolve().parents[2]
	config_path = project_root / 'popels' / file_name
	with config_path.open(encoding='utf-8') as config_file:
		raw_config = json.load(config_file)
	config_values = raw_config['config']
	legacy_name_fields = config_values.get('legacy_name_fields')
	if legacy_name_fields is not None:
		config_values['legacy_name_fields'] = tuple(legacy_name_fields)
	return PopelsConfig(
		**config_values,
		field_labels=raw_config['field_labels'],
	)
