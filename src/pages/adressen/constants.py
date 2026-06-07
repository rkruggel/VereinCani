"""Felddefinitionen und feste Auswahlwerte der Adressenverwaltung."""

FIELD_LABELS = {
	'id': {
		'type': 'string', 
		'text': 'ID', 
		'steuerelement': 'label', 
		'formular': False,
	},
	'anrede': {
		'type': 'string',
		'text': 'Anrede',
		'steuerelement': 'select',
		'formular': True,
		'optionen': ['Herr', 'Frau', 'Diverse'],
	},
	'titel': {
		'type': 'string',
		'text': 'Titel',
		'steuerelement': 'select',
		'formular': True,
		'optionen': ['Dr.', 'Prof.', 'Prof. Dr.'],
	},
	'vorname': {
		'type': 'string',
		'text': 'Vorname',
		'steuerelement': 'input',
		'formular': True,
		'formHeaderPos': 10,
	},
	'nachname': {
		'type': 'string',
		'text': 'Nachname',
		'steuerelement': 'input',
		'formular': True,
		'formHeaderPos': 20,
	},
	'zusatz': {
		'type': 'string', 
		'text': 'Zusatz', 
		'steuerelement': 'textarea', 
		'formular': True,
	},
	'adresse': {
		'type': 'string', 
		'text': 'Adresse', 
		'steuerelement': 'textarea', 
		'formular': True,
	},
	'ort': {
		'type': 'string', 
		'text': 'Ort', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'geboren': {
		'type': 'datum', 
		'text': 'Geboren', 
		'steuerelement': 'date', 
		'formular': True,
	},
	'festnetz': {
		'type': 'telefon', 
		'text': 'Festnetz', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'handy': {
		'type': 'telefon', 
		'text': 'Handy', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'email': {
		'type': 'email', 
		'text': 'E-Mail', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'www': {
		'type': 'url', 
		'text': 'WWW', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'nichtWochentag': {
		'type': 'liste',
		'text': 'Nicht an Wochentagen',
		'steuerelement': 'multiselect',
		'formular': True,
		'optionen': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
	},
	'beruf': {
		'type': 'string', 
		'text': 'Beruf', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'hobby': {
		'type': 'string', 
		'text': 'Hobby', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'hossa': {
		'type': 'string', 
		'text': 'Hossa', 
		'steuerelement': 'input', 
		'formular': True,
	},
	'faehigkeiten': {
		'type': 'string',
		'text': 'Fähigkeiten',
		'steuerelement': 'textarea',
		'formular': True,
	},
	'text': {
		'type': 'string', 
		'text': 'Text vorhanden', 
		'steuerelement': 'dialog', 
		'formular': False,
	},
	'bilder': {
		'type': 'bilder', 
		'text': 'Bilder vorhanden', 
		'steuerelement': 'upload', 
		'formular': False,
	},
}

LIST_DISPLAY_FIELDS = list(FIELD_LABELS)
FORM_FIELDS = [
	field
	for field, definition in FIELD_LABELS.items()
	if definition['formular']
]
DEFAULT_SORT_CRITERIA = ['nachname:asc', 'vorname:asc']
