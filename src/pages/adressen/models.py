

from dataclasses import asdict, field, make_dataclass
from typing import Any

from src.pages.adressen.constants import FIELD_LABELS


def model_field_definition(definition: dict[str, Any]) -> tuple[type, Any]:
	"""Ermittelt Python-Typ und Dataclass-Standardwert einer Felddefinition."""

	field_type = definition['type']
	if field_type == 'liste':
		return list[str], field(default_factory=list)
	if field_type == 'bilder':
		return list[dict[str, str]], field(default_factory=list)
	return str, field(default='')


class AdresseModel:
	"""Stellt gemeinsames Verhalten für das dynamische Adressmodell bereit."""

	def __post_init__(self) -> None:
		"""Normalisiert Listenfelder aus älteren Dokumenten auf leere Listen."""

		for field_name, definition in FIELD_LABELS.items():
			if definition['type'] in {'liste', 'bilder'}:
				setattr(self, field_name, list(getattr(self, field_name, None) or []))

	@classmethod
	def from_json(cls, data: dict[str, Any]) -> 'Adresse':
		"""Erstellt eine Adresse aus RavenDB-Daten und migriert alte Namensfelder."""

		values = {
			key: value
			for key, value in data.items()
			if key in FIELD_LABELS
		}
		legacy_name = str(data.get('name', '') or '').strip()
		if legacy_name and not values.get('vorname') and not values.get('nachname'):
			values['vorname'], values['nachname'] = split_legacy_name(legacy_name)
		return cls(**values)

	def to_json(self) -> dict[str, Any]:
		"""Gibt alle aus ``FIELD_LABELS`` erzeugten Modellfelder als Wörterbuch zurück."""

		return asdict(self)


Adresse = make_dataclass(
	'Adresse',
	[
		(field_name, *model_field_definition(definition))
		for field_name, definition in FIELD_LABELS.items()
	],
	bases=(AdresseModel,),
)
Adresse.__module__ = __name__
Adresse.__doc__ = 'Repräsentiert ein aus FIELD_LABELS erzeugtes Adressdokument.'


def split_legacy_name(name: str) -> tuple[str, str]:
	"""Teilt einen alten vollständigen Namen in Vorname und Nachname auf."""

	parts = name.split()
	if len(parts) < 2:
		return '', name
	return ' '.join(parts[:-1]), parts[-1]
