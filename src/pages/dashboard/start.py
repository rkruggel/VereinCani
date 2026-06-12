"""Dashboard der VereinGUI-Anwendung."""

from nicegui import ui


DASHBOARD_DESCRIPTION = (
	'Zentrale Arbeitsoberflaeche fuer Mitglieder, Hunde, Termine und Beitraege.'
)
DASHBOARD_AREAS = [
	{
		'icon': 'groups',
		'title': 'Mitglieder',
		'text': 'Mitglieder anlegen, mit persoenlichen Daten verbinden und zugeordnete Hunde verwalten.',
		'status': 'Angemeldet',
	},
	{
		'icon': 'badge',
		'title': 'Stammdaten',
		'text': 'Persoenliche Daten, Hunde und den Preisstamm strukturiert pflegen.',
		'status': 'Angemeldet',
	},
	{
		'icon': 'event',
		'title': 'Termine',
		'text': 'Vereinstermine und Veranstaltungen vorbereiten. Der Bereich ist fuer die naechste Ausbaustufe vorgesehen.',
		'status': 'In Vorbereitung',
	},
	{
		'icon': 'payments',
		'title': 'Beitraege',
		'text': 'Beitraege und Zahlungen sollen hier spaeter zusammenlaufen.',
		'status': 'In Vorbereitung',
	},
]
DASHBOARD_STEPS = [
	'Zuerst persoenliche Stammdaten erfassen.',
	'Dann Hunde mit den passenden Besitzern verknuepfen.',
	'Anschliessend Mitgliederdatensaetze zusammenstellen.',
	'Preisstamm fuer die Beitragsberechnung pflegen.',
]


def render_dashboard_page() -> None:
	"""Erzeugt die vollständige Dashboard-Ansicht."""

	with ui.column().classes('w-full gap-4'):
		with ui.card().classes('w-full p-6 rounded-lg shadow-sm border border-slate-200 gap-3'):
			ui.label('Willkommen in VereinGUI').classes('text-2xl font-bold text-slate-900')
			ui.label(DASHBOARD_DESCRIPTION).classes('text-base text-slate-600')
			ui.label(
				'Die Navigation oben fuehrt zu den einzelnen Programmbereichen. Geschuetzte Bereiche werden nach der Anmeldung freigeschaltet.'
			).classes('text-sm text-slate-500')

		with ui.grid(columns=4).classes('w-full gap-4 max-xl:grid-cols-2 max-md:grid-cols-1'):
			for area in DASHBOARD_AREAS:
				with ui.card().classes('w-full h-full p-4 rounded-lg shadow-sm border border-slate-200 gap-3'):
					with ui.row().classes('w-full items-start justify-between gap-3'):
						ui.icon(area['icon']).classes('text-primary text-3xl')
						ui.label(area['status']).classes(
							'rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600'
						)
					ui.label(area['title']).classes('text-lg font-semibold text-slate-900')
					ui.label(area['text']).classes('text-sm text-slate-600')

		with ui.row().classes('w-full gap-4 items-stretch max-lg:flex-col'):
			with ui.card().classes('flex-1 p-5 rounded-lg shadow-sm border border-slate-200 gap-4'):
				ui.label('Sinnvoller Arbeitsablauf').classes('text-lg font-semibold text-slate-900')
				for step_number, item in enumerate(DASHBOARD_STEPS, start=1):
					with ui.row().classes('w-full items-start gap-3'):
						ui.label(str(step_number)).classes(
							'flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm font-semibold text-white'
						)
						ui.label(item).classes('flex-1 text-sm text-slate-700')

			with ui.card().classes('w-[360px] max-lg:w-full p-5 rounded-lg shadow-sm border border-slate-200 gap-3'):
				with ui.row().classes('items-center gap-2'):
					ui.icon('lock_open').classes('text-primary')
					ui.label('Aktueller Einstieg').classes('text-lg font-semibold text-slate-900')
				ui.label('Das Dashboard ist frei sichtbar.').classes('text-sm text-slate-700')
				ui.label(
					'Fuer Mitglieder, Stammdaten und Termine bitte links anmelden. Beitraege und Dashboard bleiben direkt erreichbar.'
				).classes('text-sm text-slate-600')
