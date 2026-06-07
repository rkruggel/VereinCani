"""Dynamische Modelle für konfigurierbare Stammdaten."""

from dataclasses import asdict, field, make_dataclass
from typing import Any, Self

from src.pages.stammdaten import StammdatenConfig


def model_field_definition(definition: dict[str, Any]) -> tuple[type, Any]:
	"""Ermittelt Python-Typ und Dataclass-Standardwert einer Felddefinition."""

	field_type = definition['type']
	if field_type == 'liste':
		return list[str], field(default_factory=list)
	if field_type == 'bilder':
		return list[dict[str, str]], field(default_factory=list)
	return str, field(default='')


class StammdatenModel:
	"""Stellt gemeinsames Verhalten für dynamisch erzeugte Modelle bereit."""

	_config: StammdatenConfig

	def __post_init__(self) -> None:
		"""Normalisiert Listenfelder aus älteren Dokumenten auf leere Listen."""

		for field_name, definition in self._config.field_labels.items():
			if definition['type'] in {'liste', 'bilder'}:
				setattr(self, field_name, list(getattr(self, field_name, None) or []))

	@classmethod
	def from_json(cls, data: dict[str, Any]) -> Self:
		"""Erstellt ein Modell aus RavenDB-Daten und übernimmt optionale Altdaten."""

		values = {
			key: value
			for key, value in data.items()
			if key in cls._config.field_labels
		}
		legacy_name = str(data.get('name', '') or '').strip()
		name_fields = cls._config.legacy_name_fields
		if name_fields and legacy_name and not any(values.get(field) for field in name_fields):
			values[name_fields[0]], values[name_fields[1]] = split_legacy_name(legacy_name)
		return cls(**values)

	def to_json(self) -> dict[str, Any]:
		"""Gibt alle konfigurierten Modellfelder als Wörterbuch zurück."""

		return asdict(self)


def create_stammdaten_model(config: StammdatenConfig) -> type[StammdatenModel]:
	"""Erzeugt eine Dataclass passend zu den Felddefinitionen eines Moduls."""

	model = make_dataclass(
		config.model_name,
		[
			(field_name, *model_field_definition(definition))
			for field_name, definition in config.field_labels.items()
		],
		bases=(StammdatenModel,),
	)
	model.__module__ = __name__
	model.__doc__ = f'Repräsentiert ein dynamisch erzeugtes {config.singular}-Dokument.'
	model._config = config
	return model


def split_legacy_name(name: str) -> tuple[str, str]:
	"""Teilt einen alten vollständigen Namen in Vorname und Nachname auf."""

	parts = name.split()
	if len(parts) < 2:
		return '', name
	return ' '.join(parts[:-1]), parts[-1]
