"""
Dynamische Modelle für konfigurierbare Popels.
"""
from dataclasses import asdict, field, make_dataclass
from typing import Any, Self

from src.popelsapp import PopelsConfig


def model_field_definition(definition: dict[str, Any]) -> tuple[type, Any]:
	"""
	Ermittelt Python-Typ und Dataclass-Standardwert einer Felddefinition.
	"""
	field_type = definition['type']
	if field_type == 'liste':
		return list[str], field(default_factory=list)
	if field_type in {'kursbuchungen', 'kursbesuche'}:
		return list[dict[str, Any]], field(default_factory=list)
	if field_type == 'bankdaten':
		return dict[str, Any], field(default_factory=dict)
	if field_type == 'bilder':
		return list[dict[str, str]], field(default_factory=list)
	return str, field(default='')


class PopelsModel:
	"""
	Stellt gemeinsames Verhalten für dynamisch erzeugte Modelle bereit.
	"""
	_config: PopelsConfig

	def __post_init__(self) -> None:
		"""
		Normalisiert Listenfelder aus älteren Dokumenten auf leere Listen.
		"""
		for field_name, definition in self._config.field_labels.items():
			if definition['type'] in {'liste', 'bilder', 'kursbuchungen', 'kursbesuche'}:
				value = getattr(self, field_name, None)
				if value is None or value == '':
					normalized_value = []
				elif isinstance(value, list):
					normalized_value = value
				else:
					normalized_value = [value]
				setattr(self, field_name, normalized_value)
			elif definition['type'] == 'bankdaten':
				value = getattr(self, field_name, None)
				setattr(self, field_name, value if isinstance(value, dict) else {})

	@classmethod
	def from_json(cls, data: dict[str, Any]) -> Self:
		"""
		Erstellt ein Modell aus CouchDB-Daten und übernimmt optionale Altdaten.
		"""
		values = {
			key: value
			for key, value in data.items()
			if key in cls._config.field_labels
		}
		return cls(**values)

	def to_json(self) -> dict[str, Any]:
		"""
		Gibt alle konfigurierten Modellfelder als Wörterbuch zurück.
		"""
		data = asdict(self)
		for field_name in self._config.field_labels:
			if self._config.page(field_name).get('berechnen'):
				data.pop(field_name, None)
		return data


def create_popels_model(config: PopelsConfig) -> type[PopelsModel]:
	"""
	Erzeugt eine Dataclass passend zu den Felddefinitionen eines Moduls.
	"""
	model = make_dataclass(
		config.model_name,
		[
			(field_name, *model_field_definition(definition))
			for field_name, definition in config.field_labels.items()
		],
		bases=(PopelsModel,),
	)
	model.__module__ = __name__
	model.__doc__ = f'Repräsentiert ein dynamisch erzeugtes {config.singular}-Dokument.'
	model._config = config
	return model
