"""Beitragsbereich der VereinCani-Anwendung."""

from nicegui import ui


BEITRAEGE_DESCRIPTION = 'Finanz- und Beitragsbereich fuer den operativen Betrieb.'
BEITRAEGE_ITEMS = [
	'Beitragssaetze definieren',
	'Offene Zahlungen anzeigen',
	'Abrechnungen vorbereiten',
]


def render_beitraege_page() -> None:
	"""Erzeugt die vollständige Vorschau des Beitragsbereichs."""

	with ui.column().classes('w-full gap-4'):
		with ui.row().classes('w-full gap-4 items-stretch max-md:flex-col'):
			with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
				ui.label('Programmdaten').classes('text-sm uppercase tracking-wide text-slate-500')
				ui.label('VereinCani').classes('text-2xl font-bold')
				ui.label('Beitragsverwaltung in Vorbereitung').classes('text-sm text-slate-600')
			with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
				ui.label('Aktive Seite').classes('text-sm uppercase tracking-wide text-slate-500')
				ui.label('Beitraege').classes('text-2xl font-bold')
				ui.label(BEITRAEGE_DESCRIPTION).classes('text-sm text-slate-600')

		with ui.card().classes('w-full p-6 rounded-2xl shadow-sm gap-4'):
			ui.label('Beitraege').classes('text-2xl font-bold')
			ui.label(BEITRAEGE_DESCRIPTION).classes('text-base text-slate-600')
			ui.separator()
			for item in BEITRAEGE_ITEMS:
				with ui.row().classes('items-center gap-3'):
					ui.icon('chevron_right').classes('text-primary')
					ui.label(item).classes('text-base')
