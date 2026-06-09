"""Dashboard der VereinCani-Anwendung."""

from nicegui import ui


DASHBOARD_DESCRIPTION = 'Zentrale Uebersicht über die, für die Programmierung, offen stehenden Teile der Vereinssoftware.'
DASHBOARD_ITEMS = [
	'Texte allgemein erfassen',
	'Bankverbindungen erfassen',
	'Einwilligungen erfassen',
]


def render_dashboard_page() -> None:
	"""Erzeugt die vollständige Dashboard-Ansicht."""

	with ui.column().classes('w-full gap-4'):
		with ui.row().classes('w-full gap-4 items-stretch max-md:flex-col'):
			with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
				ui.label('Programmdaten').classes('text-sm uppercase tracking-wide text-slate-500')
				ui.label('VereinCani').classes('text-2xl font-bold')
				ui.label('NiceGUI-Masterlayout aktiv').classes('text-sm text-slate-600')
			with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
				ui.label('Aktive Seite').classes('text-sm uppercase tracking-wide text-slate-500')
				ui.label('Dashboard').classes('text-2xl font-bold')
				ui.label(DASHBOARD_DESCRIPTION).classes('text-sm text-slate-600')

		with ui.card().classes('w-full p-6 rounded-2xl shadow-sm gap-4'):
			ui.label('Dashboard').classes('text-2xl font-bold')
			ui.label(DASHBOARD_DESCRIPTION).classes('text-base text-slate-600')
			ui.separator()
			for item in DASHBOARD_ITEMS:
				with ui.row().classes('items-center gap-3'):
					ui.icon('chevron_right').classes('text-primary')
					ui.label(item).classes('text-base')
