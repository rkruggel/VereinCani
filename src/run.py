"""NiceGUI-Hauptseite mit Navigation und geschützten Programmbereichen."""

from nicegui import ui

from src.auth import is_authenticated, render_login_panel
from src.menu import PAGES, can_access_page, render_menu


def render_start_page() -> None:
	selected_page = {'key': 'dashboard'}

	def switch_page(page_key: str) -> None:
		if not can_access_page(page_key, is_authenticated()):
			ui.notify('Bitte zuerst anmelden.', type='warning')
			return
		selected_page['key'] = page_key
		render_menu.refresh()
		render_content.refresh()

	def handle_auth_change(authenticated: bool) -> None:
		if not can_access_page(selected_page['key'], authenticated):
			selected_page['key'] = 'dashboard'
		render_menu.refresh()
		render_content.refresh()

	@ui.refreshable
	def render_content() -> None:
		if not can_access_page(selected_page['key'], is_authenticated()):
			selected_page['key'] = 'dashboard'
		page = PAGES[selected_page['key']]
		page['renderer']()

	@ui.refreshable
	def render_header() -> None:
		with ui.row().classes('w-full items-center justify-between gap-5 px-6 py-3 bg-white border-b border-slate-200 shadow-sm max-md:flex-col max-md:items-start max-md:px-4'):
			with ui.column().classes('gap-0'):
				ui.label('VereinCani').classes('text-2xl font-bold text-slate-900')
				ui.label('Für und mit dem Hund').classes('text-xs text-slate-500')
			render_menu(selected_page, switch_page)

	with ui.column().classes('w-full h-screen bg-slate-50 gap-0'):
		render_header()

		with ui.row().classes('w-full flex-1 gap-0 max-md:flex-col'):
			with ui.column().classes('w-72 max-md:w-full bg-white border-r border-slate-200 px-4 py-6 gap-4'):
				with ui.column().classes('gap-1 px-2'):
					ui.label('Programmbereiche').classes('text-xs uppercase tracking-[0.25em] text-slate-500')
					ui.label('VereinCani').classes('text-xl font-semibold text-slate-900')
					ui.label('Für und mit dem Hund').classes('text-sm text-slate-500')
				render_login_panel(on_auth_change=handle_auth_change)

			with ui.column().classes('flex-1 p-6 overflow-auto max-md:p-4'):
				render_content()
