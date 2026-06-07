"""Startkonfiguration und Einstiegspunkt der Mitgliederverwaltung."""

from src.pages.stammdaten import StammdatenConfig
from src.pages.stammdaten.models import create_stammdaten_model
from src.pages.stammdaten.page import render_stammdaten_page
from src.pages.stammdaten.repository import RavenStammdatenDatabase
from src.pages.stammdaten.settings import ListeneinstellungenRepository


"""
	'status': {								-> die id
		'type': 'string',						-> der Datentyp, z.B. string, datum, liste, bilder
		'text': 'Mitgliedsstatus',				-> die Bezeichnung im UI
		'steuerelement': 'select',				-> das Steuerelement im Formular
		'formular': True,						-> ob das Feld im Formular angezeigt wird
		'optionen': ['Aktiv', 'Passiv', ...],	-> Optionen für select/multiselect
		'suchbar': True,						-> ob das Feld in der Schnellsuche berücksichtigt wird
		'sortierbar': True,						-> ob das Feld in der Sortierung berücksichtigt wird
		'listSection': 'primary',				-> Sektion in der Mitgliederliste
		'listPos': 5,							-> Position in der Mitgliederliste
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
	'mitgliedsnummer': {
		'type': 'string',
		'text': 'Mitgliedsnummer',
		'steuerelement': 'input',
		'formular': True,
		'pflichtfeld': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'headerDetail',
		'listPos': 10,
		'listValueClasses': 'text-xs tracking-wide text-slate-500',
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
	'status': {
		'type': 'string',
		'text': 'Mitgliedsstatus',
		'steuerelement': 'select',
		'formular': True,
		'optionen': ['Aktiv', 'Passiv', 'Ehemalig'],
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'primary',
		'listPos': 5,
	},
	'eintritt': {
		'type': 'datum',
		'text': 'Eintritt',
		'steuerelement': 'date',
		'formular': True,
		'suchbar': True,
		'sortierbar': True,
		'listSection': 'secondary',
		'listPos': 5,
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

}

CONFIG = StammdatenConfig(
	key='mitglieder',
	singular='Mitglied',
	plural='Mitglieder',
	collection_name='Mitglieder',
	settings_collection_name='MitgliederlistenEinstellungen',
	field_labels=FIELD_LABELS,
	model_name='Mitglied',
	legacy_name_fields=('vorname', 'nachname'),
)
Mitglied = create_stammdaten_model(CONFIG)
MITGLIEDER_DB = RavenStammdatenDatabase(CONFIG, Mitglied)
MITGLIEDERLISTEN_EINSTELLUNGEN = ListeneinstellungenRepository(CONFIG)


def render_mitglieder_page() -> None:
	"""Übergibt die Mitgliederkonfiguration an die gemeinsame Stammdaten-Seite."""

	render_stammdaten_page(CONFIG, MITGLIEDER_DB, MITGLIEDERLISTEN_EINSTELLUNGEN)
