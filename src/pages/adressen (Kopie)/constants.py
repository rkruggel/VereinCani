ADDRESS_FIELDS = [
	'id',
	'anrede',
	'titel',
	'vorname',
	'nachname',
	'zusatz',
	'adresse',
	'ort',
	'geboren',
	'festnetz',
	'handy',
	'email',
	'www',
	'nichtWochentag',
	'beruf',
	'hobby',
	'faehigkeiten',
]

CONTENT_STATUS_FIELDS = ['text', 'bilder']
LIST_DISPLAY_FIELDS = ADDRESS_FIELDS + CONTENT_STATUS_FIELDS
FORM_FIELDS = [field for field in ADDRESS_FIELDS if field != 'id']
WOCHENTAGE = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
PHONE_FIELDS = {'festnetz', 'handy'}
FIELD_LABELS = {
	'id': 'ID',
	'anrede': 'Anrede',
	'titel': 'Titel',
	'vorname': 'Vorname',
	'nachname': 'Nachname',
	'zusatz': 'Zusatz',
	'adresse': 'Adresse',
	'ort': 'Ort',
	'geboren': 'Geboren',
	'festnetz': 'Festnetz',
	'handy': 'Handy',
	'email': 'E-Mail',
	'www': 'WWW',
	'nichtWochentag': 'Nicht an Wochentagen',
	'beruf': 'Beruf',
	'hobby': 'Hobby',
	'faehigkeiten': 'Faehigkeiten',
	'text': 'Text vorhanden',
	'bilder': 'Bilder vorhanden',
}

DEFAULT_SORT_CRITERIA = ['nachname:asc', 'vorname:asc']
