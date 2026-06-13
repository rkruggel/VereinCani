"""NiceGUI-Hauptseite mit Navigation und geschützten Programmbereichen."""

from typing import Any

from nicegui import events, ui

from src.auth import is_authenticated, render_login_panel
from src.menu import can_access_page, get_page, render_menu


def render_start_page(initial_page_key: str = 'dashboard') -> None:
	selected_page = {'key': initial_page_key if get_page(initial_page_key) is not None else 'dashboard'}

	def key_from_hash(value: Any) -> str:
		text = str(value or '').strip()
		if isinstance(value, list) and value:
			text = str(value[0] or '').strip()
		return text.removeprefix('#').strip('/') or 'dashboard'

	def switch_page(page_key: str, *, update_hash: bool = True) -> None:
		if not can_access_page(page_key, is_authenticated()):
			ui.notify('Bitte zuerst anmelden.', type='warning')
			return
		selected_page['key'] = page_key
		if update_hash:
			ui.run_javascript(f'window.history.pushState(null, "", "#{page_key}");')
		render_menu.refresh()
		render_content.refresh()

	def handle_hash_change(event: events.GenericEventArguments) -> None:
		page_key = key_from_hash(event.args)
		if page_key != selected_page['key']:
			switch_page(page_key, update_hash=False)

	def handle_auth_change(authenticated: bool) -> None:
		if not can_access_page(selected_page['key'], authenticated):
			selected_page['key'] = 'dashboard'
			ui.run_javascript('window.history.replaceState(null, "", "#dashboard");')
		render_menu.refresh()
		render_content.refresh()

	@ui.refreshable
	def render_content() -> None:
		if not can_access_page(selected_page['key'], is_authenticated()):
			selected_page['key'] = 'dashboard'
			ui.run_javascript('window.history.replaceState(null, "", "#dashboard");')
		page = get_page(selected_page['key'])
		if page is None:
			return
		page['renderer']()

	@ui.refreshable
	def render_header() -> None:
		with ui.row().classes('w-full items-center justify-between gap-5 px-6 py-3 bg-white border-b border-slate-200 shadow-sm max-md:flex-col max-md:items-start max-md:px-4'):
			with ui.column().classes('gap-0'):
				ui.label('VereinGUI').classes('text-2xl font-bold text-slate-900')
				ui.label('Programm zur dynamischen Vereinsverwaltung').classes('text-xs text-slate-500')
			render_menu(selected_page, switch_page)

	with ui.column().classes('w-full h-screen bg-slate-50 gap-0'):
		ui.element('div').props('id=app-page-top').classes('h-0')
		ui.on('spa_hashchange', handle_hash_change)
		ui.run_javascript(
			'''
				if (!window.vereinguiSpaHashListener) {
					window.vereinguiSpaHashListener = true;
					window.addEventListener('hashchange', () => {
						emitEvent('spa_hashchange', window.location.hash);
					});
				}
				if (window.location.hash) {
					emitEvent('spa_hashchange', window.location.hash);
				} else {
					window.history.replaceState(null, "", "#__INITIAL_PAGE__");
				}
			'''.replace('__INITIAL_PAGE__', selected_page['key'])
		)
		render_header()

		with ui.row().classes('w-full flex-1 gap-0 max-md:flex-col'):
			with ui.column().classes('w-72 max-md:w-full bg-white border-r border-slate-200 px-4 py-6 gap-4'):
				with ui.column().classes('gap-1 px-2'):
					ui.label('Programmbereiche').classes('text-xs uppercase tracking-[0.25em] text-slate-500')
					ui.label('per-cani').classes('text-xl font-semibold text-slate-900')
					ui.label('Für und mit dem Hund').classes('text-sm text-slate-500')
				render_login_panel(on_auth_change=handle_auth_change)

			with ui.column().classes('flex-1 p-6 overflow-auto max-md:p-4'):
				render_content()
