from dataclasses import dataclass


@dataclass
class Benutzer:
	id: str = ''
	email: str = ''
	name: str = ''
	kennung_hash: str = ''
	kennung_salt: str = ''
