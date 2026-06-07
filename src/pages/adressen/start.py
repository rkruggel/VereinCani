"""Startkonfiguration und Einstiegspunkt der Adressenverwaltung."""

from src.pages.stammdaten import StammdatenConfig
from src.pages.stammdaten.models import create_stammdaten_model
from src.pages.stammdaten.page import render_stammdaten_page
from src.pages.stammdaten.repository import RavenStammdatenDatabase
from src.pages.stammdaten.settings import ListeneinstellungenRepository


"""
	'nichtWochentag': {							-> die id
		'type': 'liste',						-> der Datentyp, z.B. string, datum, liste, bilder
		'text': 'Nicht an Wochentagen',			-> die Bezeichnung im UI
		'steuerelement': 'multiselect',			-> das Steuerelement im Formular
		'formular': True,						-> ob das Feld im Formular angezeigt wird
		'optionen': ['Montag', 'Dienstag', ...],	-> Optionen für select/multiselect
		'suchbar': True,						-> ob das Feld in der Schnellsuche berücksichtigt wird
		'sortierbar': True,						-> ob das Feld in der Sortierung berücksichtigt wird
		'listSection': 'secondary',				-> Sektion in der Adressliste
		'listPos': 40,							-> Position in der Adressliste
		'listValueClasses': 'text-slate-500',	-> CSS-Klassen für die Anzeige in der Adressliste
	},
"""

FIELD_LABELS = {
	'id': {
		'type': 'string',
		'text': 'ID',
		'steuerelement': 'label',
		'formular': False,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'headerDetail',
		'listPos': 10,
		'listValueClasses': 'text-xs tracking-wide text-slate-500',
	},
	'anrede': {
		'type': 'string',
		'text': 'Anrede',
		'steuerelement': 'select',
		'formular': True,
		'optionen': ['Herr', 'Frau', 'Diverse'],
		'suchbar': True,
		'sortierbar': True,
		'formHeaderPos': 10,
	},
	'titel': {
		'type': 'string',
		'text': 'Titel',
		'steuerelement': 'select',
		'formular': True,
		'optionen': ['Dr.', 'Prof.', 'Prof. Dr.'],
		'suchbar': True,
		'sortierbar': True,
		'formHeaderPos': 20,
	},
	'vorname': {
		'type': 'string',
		'text': 'Vorname',
		'steuerelement': 'input',
		'formular': True,
		'pflichtfeld': True,
		'suchbar': True,
		'sortierbar': True,
		'formHeaderPos': 30,
	},
	'nachname': {
		'type': 'string',
		'text': 'Nachname',
		'steuerelement': 'input',
		'formular': True,
		'pflichtfeld': True,
		'suchbar': True,
		'sortierbar': True,
		'formHeaderPos': 40,
	},
	'zusatz': {
		'type': 'string',
		'text': 'Zusatz',
		'steuerelement': 'textarea',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'headerDetail',
		'listPos': 20,
		'listValueClasses': 'text-sm text-slate-500',
	},
	'adresse': {
		'type': 'string',
		'text': 'Adresse',
		'steuerelement': 'textarea',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 10,
		'listValueClasses': 'text-sm tracking-wide text-slate-500',
	},
	'ort': {
		'type': 'string',
		'text': 'Ort',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 20,
		'listValueClasses': 'text-sm tracking-wide text-slate-500',
	},
	'email': {
		'type': 'email',
		'text': 'E-Mail',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 30,
	},
	'handy': {
		'type': 'telefon',
		'text': 'Handy',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 40,
	},
	'festnetz': {
		'type': 'telefon',
		'text': 'Festnetz',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 50,
	},
	'www': {
		'type': 'url',
		'text': 'WWW',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 60,
	},
	'geboren': {
		'type': 'datum',
		'text': 'Geboren',
		'steuerelement': 'date',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 10,
		'listValueClasses': 'text-slate-500',
	},
	'beruf': {
		'type': 'string',
		'text': 'Beruf',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 20,
		'listValueClasses': 'text-slate-500',
	},
	'hobby': {
		'type': 'string',
		'text': 'Hobby',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 30,
		'listValueClasses': 'text-slate-500',
	},
	'nichtWochentag': {
		'type': 'liste',
		'text': 'Nicht an Wochentagen',
		'steuerelement': 'multiselect',
		'formular': True,
		'optionen': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 40,
		'listValueClasses': 'text-slate-500',
	},
	'faehigkeiten': {
		'type': 'string',
		'text': 'Fähigkeiten',
		'steuerelement': 'textarea',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 50,
		'listValueClasses': 'text-slate-500',
	},
	'hossa': {
		'type': 'string',
		'text': 'Hossa',
		'steuerelement': 'input',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 60,
		'listValueClasses': 'text-slate-500',
	},
	'text': {
		'type': 'string',
		'text': 'Text vorhanden',
		'steuerelement': 'editor',
		'formular': False,
		'suchbar': True,
		'sortierbar': False,
		'listSection': 'status',
		'listPos': 10,
		'actionLabel': 'Text',
		'actionIcon': 'description',
	},
	'bilder': {
		'type': 'bilder',
		'text': 'Bilder vorhanden',
		'steuerelement': 'upload',
		'formular': False,
		'suchbar': False,
		'sortierbar': False,
		'listSection': 'status',
		'listPos': 20,
		'actionLabel': 'Pic',
		'actionIcon': 'image',
	},
}

CONFIG = StammdatenConfig(
	key='adressen',
	singular='Adresse',
	plural='Adressen',
	collection_name='Adressen',
	settings_collection_name='AdresslistenEinstellungen',
	field_labels=FIELD_LABELS,
	model_name='Adresse',
	legacy_name_fields=('vorname', 'nachname'),
)
Adresse = create_stammdaten_model(CONFIG)
ADRESSEN_DB = RavenStammdatenDatabase(CONFIG, Adresse)
ADRESSLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_adressen_page() -> None:
	"""Übergibt die Adresskonfiguration an die gemeinsame Stammdaten-Seite."""

	render_stammdaten_page(CONFIG, ADRESSEN_DB, ADRESSLISTEN_EINSTELLUNGEN)
