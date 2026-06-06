from dataclasses import dataclass
from typing import Any


@dataclass
class Adresse:
	id: str = ''
	anrede: str = ''
	titel: str = ''
	vorname: str = ''
	nachname: str = ''
	zusatz: str = ''
	adresse: str = ''
	ort: str = ''
	geboren: str = ''
	festnetz: str = ''
	handy: str = ''
	email: str = ''
	www: str = ''
	nichtWochentag: list[str] | None = None
	beruf: str = ''
	hobby: str = ''
	faehigkeiten: str = ''
	text: str = ''
	bilder: list[dict[str, str]] | None = None

	def __post_init__(self) -> None:
		self.nichtWochentag = list(self.nichtWochentag or [])
		self.bilder = list(self.bilder or [])

	@classmethod
	def from_json(cls, data: dict[str, Any]) -> 'Adresse':
		values = {key: value for key, value in data.items() if key != '@metadata'}
		legacy_name = str(values.pop('name', '') or '').strip()
		if legacy_name and not values.get('vorname') and not values.get('nachname'):
			values['vorname'], values['nachname'] = split_legacy_name(legacy_name)
		return cls(**values)

	def to_json(self) -> dict[str, Any]:
		return {
			'id': self.id,
			'anrede': self.anrede,
			'titel': self.titel,
			'vorname': self.vorname,
			'nachname': self.nachname,
			'zusatz': self.zusatz,
			'adresse': self.adresse,
			'ort': self.ort,
			'geboren': self.geboren,
			'festnetz': self.festnetz,
			'handy': self.handy,
			'email': self.email,
			'www': self.www,
			'nichtWochentag': self.nichtWochentag,
			'beruf': self.beruf,
			'hobby': self.hobby,
			'faehigkeiten': self.faehigkeiten,
			'text': self.text,
			'bilder': self.bilder,
		}


def split_legacy_name(name: str) -> tuple[str, str]:
	parts = name.split()
	if len(parts) < 2:
		return '', name
	return ' '.join(parts[:-1]), parts[-1]
