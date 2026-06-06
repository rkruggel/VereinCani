from nicegui import ui

from src.auth import is_authenticated, render_login_panel
from src.pages.adressen import render_adressen_page


PROTECTED_PAGES = {'adressen', 'mitglieder', 'termine'}


def can_access_page(page_key: str, authenticated: bool) -> bool:
	return page_key not in PROTECTED_PAGES or authenticated


def render_start_page() -> None:
	pages = {
		'dashboard': {
			'title': 'Dashboard',
			'description': 'Zentrale Uebersicht fuer den Einstieg in die Vereinssoftware.',
			'items': [
				'Mitgliederverwaltung vorbereiten',
				'Terminplanung als naechsten Fachbereich anbinden',
				'RavenDB-Verbindung in die Datenkarten integrieren',
			],
		},
		'adressen': {
			'title': 'Adressen',
			'description': 'Bereich fuer Stammdaten, Status und Rollen im Verein.',
			'items': [
				'Neue Adresse aufnehmen',
				'Adress- und Kontaktdaten pflegen',
				'Mitgliedsstatus und Funktionen verwalten',
			],
		},
		'mitglieder': {
			'title': 'Mitglieder',
			'description': 'Bereich fuer Stammdaten, Status und Rollen im Verein.',
			'items': [
				'Neues Mitglied aufnehmen',
				'Adress- und Kontaktdaten pflegen',
				'Mitgliedsstatus und Funktionen verwalten',
			],
		},
		'termine': {
			'title': 'Termine',
			'description': 'Verwaltung von Veranstaltungen, Trainings und internen Sitzungen.',
			'items': [
				'Jahreskalender aufbauen',
				'Teilnahmen dokumentieren',
				'Erinnerungen und Hinweise ausgeben',
			],
		},
		'beitraege': {
			'title': 'Beitraege',
			'description': 'Finanz- und Beitragsbereich fuer den operativen Betrieb.',
			'items': [
				'Beitragssaetze definieren',
				'Offene Zahlungen anzeigen',
				'Abrechnungen vorbereiten',
			],
		},
	}
	navigation_entries = [
		('dashboard', 'Dashboard', 'Start und Uebersicht'),
		('adressen', 'Adressen', 'Kontakte und Anschriften'),
		('mitglieder', 'Mitglieder', 'Stammdaten und Status'),
		('termine', 'Termine', 'Planung und Kalender'),
		('beitraege', 'Beitraege', 'Finanzen und Zahlungslauf'),
	]
	selected_page = {'key': 'dashboard'}

	def switch_page(page_key: str) -> None:
		if not can_access_page(page_key, is_authenticated()):
			ui.notify('Bitte zuerst anmelden.', type='warning')
			return
		selected_page['key'] = page_key
		render_header.refresh()
		render_navigation.refresh()
		render_content.refresh()

	def handle_auth_change(authenticated: bool) -> None:
		if not can_access_page(selected_page['key'], authenticated):
			selected_page['key'] = 'dashboard'
		render_header.refresh()
		render_navigation.refresh()
		render_content.refresh()

	@ui.refreshable
	def render_navigation() -> None:
		authenticated = is_authenticated()
		with ui.row().classes('items-center gap-2 flex-wrap justify-end'):
			for page_key, title, _subtitle in navigation_entries:
				is_active = selected_page['key'] == page_key
				is_enabled = can_access_page(page_key, authenticated)
				button_classes = 'rounded-full px-3 py-2 text-sm font-medium '
				if is_active:
					button_classes += 'bg-primary text-white'
				elif is_enabled:
					button_classes += 'bg-slate-100 text-slate-700'
				else:
					button_classes += 'bg-slate-100 text-slate-400'
				button = ui.button(
					title,
					on_click=lambda key=page_key: switch_page(key),
				).props('flat no-caps').classes(button_classes)
				button.set_enabled(is_enabled)
				if not is_enabled:
					button.tooltip('Anmeldung erforderlich')

	@ui.refreshable
	def render_content() -> None:
		if not can_access_page(selected_page['key'], is_authenticated()):
			selected_page['key'] = 'dashboard'
		page = pages[selected_page['key']]
		if selected_page['key'] == 'adressen':
			render_adressen_page()
			return

		with ui.column().classes('w-full gap-4'):
			with ui.row().classes('w-full gap-4 items-stretch max-md:flex-col'):
				with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
					ui.label('Programmdaten').classes('text-sm uppercase tracking-wide text-slate-500')
					ui.label('VereinCani').classes('text-2xl font-bold')
					ui.label('NiceGUI-Masterlayout aktiv').classes('text-sm text-slate-600')
				with ui.card().classes('flex-1 min-w-[220px] p-5 rounded-2xl shadow-sm'):
					ui.label('Aktive Seite').classes('text-sm uppercase tracking-wide text-slate-500')
					ui.label(page['title']).classes('text-2xl font-bold')
					ui.label(page['description']).classes('text-sm text-slate-600')

			with ui.card().classes('w-full p-6 rounded-2xl shadow-sm gap-4'):
				ui.label(page['title']).classes('text-2xl font-bold')
				ui.label(page['description']).classes('text-base text-slate-600')
				ui.separator()
				for item in page['items']:
					with ui.row().classes('items-center gap-3'):
						ui.icon('chevron_right').classes('text-primary')
						ui.label(item).classes('text-base')

	@ui.refreshable
	def render_header() -> None:
		with ui.row().classes('w-full items-center justify-between gap-5 px-6 py-3 bg-white border-b border-slate-200 shadow-sm max-md:flex-col max-md:items-start max-md:px-4'):
			with ui.column().classes('gap-0'):
				ui.label('VereinCani').classes('text-2xl font-bold text-slate-900')
				ui.label('Masteraufbau fuer Navigation und Arbeitsbereich.').classes('text-xs text-slate-600')
			render_navigation()

	with ui.column().classes('w-full h-screen bg-slate-50 gap-0'):
		render_header()

		with ui.row().classes('w-full flex-1 gap-0 max-md:flex-col'):
			with ui.column().classes('w-72 max-md:w-full bg-white border-r border-slate-200 px-4 py-6 gap-4'):
				with ui.column().classes('gap-1 px-2'):
					ui.label('Programmbereiche').classes('text-xs uppercase tracking-[0.25em] text-slate-500')
					ui.label('VereinCani').classes('text-xl font-semibold text-slate-900')
					ui.label('Der linke Bereich bleibt als fester Kontextbereich erhalten.').classes('text-sm text-slate-600')
				render_login_panel(on_auth_change=handle_auth_change)

			with ui.column().classes('flex-1 p-6 overflow-auto max-md:p-4'):
				render_content()
