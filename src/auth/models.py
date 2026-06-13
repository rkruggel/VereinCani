"""
Datenmodelle der Benutzeranmeldung.
"""
from dataclasses import dataclass


@dataclass
class Benutzer:
	"""
	Beschreibt ein Benutzerkonto mit Name, E-Mail und Kennung.
	"""
	id: str = ''
	email: str = ''
	name: str = ''
	kennung_hash: str = ''
	kennung_salt: str = ''
