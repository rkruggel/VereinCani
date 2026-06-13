"""
NiceGUI-Anmeldebereich für Registrierung, Anmeldung und Abmeldung.
"""
import re
from typing import Any, Callable

from nicegui import app, ui

from src.auth.repository import BENUTZER_REPOSITORY
from src.auth.session import AUTH_STORAGE_KEY


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def render_login_panel(on_auth_change: Callable[[bool], None] | None = None) -> None:
	"""
	Rendert den Anmeldebereich mit Login und Registrierung.
	"""
	login_controls: dict[str, Any] = {}

	def login() -> None:
		"""
		Meldet einen Benutzer mit E-Mail und Kennung an.
		"""
		email = str(login_controls['email'].value or '').strip()
		kennung = str(login_controls['kennung'].value or '')
		if not is_valid_email(email) or not kennung:
			ui.notify('Bitte E-Mail-Adresse und Kennung eingeben.', type='warning')
			return
		try:
			benutzer = BENUTZER_REPOSITORY.authenticate(email, kennung)
		except Exception as error:
			ui.notify(f'Anmeldung nicht moeglich: {error}', type='negative')
			return
		if benutzer is None:
			ui.notify('E-Mail-Adresse oder Kennung ist nicht korrekt.', type='negative')
			return
		app.storage.user[AUTH_STORAGE_KEY] = {
			'id': benutzer.id,
			'email': benutzer.email,
			'name': benutzer.name,
		}
		login_controls['kennung'].value = ''
		render_authentication.refresh()
		if on_auth_change is not None:
			on_auth_change(True)
		ui.notify(f'Willkommen, {benutzer.name}.')

	def register(name_control: Any, email_control: Any, kennung_control: Any) -> None:
		"""
		Registriert einen neuen Benutzer und meldet ihn an.
		"""
		name = str(name_control.value or '').strip()
		email = str(email_control.value or '').strip()
		kennung = str(kennung_control.value or '')
		if not name:
			ui.notify('Bitte einen Namen eingeben.', type='warning')
			return
		if not is_valid_email(email):
			ui.notify('Bitte eine gueltige E-Mail-Adresse eingeben.', type='warning')
			return
		if len(kennung) < 2:
			ui.notify('Die Kennung muss mindestens 2 Zeichen lang sein.', type='warning')
			return
		try:
			benutzer = BENUTZER_REPOSITORY.register(email, name, kennung)
		except ValueError as error:
			ui.notify(str(error), type='warning')
			return
		except Exception as error:
			ui.notify(f'Registrierung nicht moeglich: {error}', type='negative')
			return
		app.storage.user[AUTH_STORAGE_KEY] = {
			'id': benutzer.id,
			'email': benutzer.email,
			'name': benutzer.name,
		}
		kennung_control.value = ''
		render_authentication.refresh()
		if on_auth_change is not None:
			on_auth_change(True)
		ui.notify('Zugang wurde erstellt.')

	def logout() -> None:
		"""
		Meldet den aktuellen Benutzer ab.
		"""
		app.storage.user.pop(AUTH_STORAGE_KEY, None)
		render_authentication.refresh()
		if on_auth_change is not None:
			on_auth_change(False)
		ui.notify('Du bist abgemeldet.')

	@ui.refreshable
	def render_authentication() -> None:
		"""
		Rendert den passenden Authentifizierungszustand.
		"""
		benutzer = app.storage.user.get(AUTH_STORAGE_KEY)
		if benutzer:
			with ui.card().classes('w-full p-4 gap-2 rounded-xl shadow-sm border border-slate-200'):
				ui.label('Angemeldet').classes('text-xs uppercase tracking-wide text-slate-500')
				ui.label(benutzer['name']).classes('text-base font-semibold text-slate-900')
				ui.label(benutzer['email']).classes('text-xs text-slate-600 break-all')
				ui.button('Abmelden', icon='logout', on_click=logout).props('flat no-caps dense').classes('self-end')
			return

		with ui.card().classes('w-full p-4 gap-3 rounded-xl shadow-sm border border-slate-200'):
			ui.label('Anmeldung').classes('text-base font-semibold text-slate-900')
			ui.label('Die Anmeldung erfolgt ueber deine E-Mail-Adresse.').classes('text-xs text-slate-600')
			login_controls['email'] = ui.input('E-Mail-Adresse').props(
				'type=email dense autocomplete="off"'
			).classes('w-full')
			login_controls['kennung'] = ui.input(
				'Kennung',
				password=True,
				password_toggle_button=True,
			).props('dense autocomplete="off"').classes('w-full')
			ui.button('Anmelden', icon='login', on_click=login).props('no-caps dense').classes('w-full')

			with ui.expansion('Zugang erstellen', icon='person_add').classes('w-full'):
				with ui.column().classes('w-full gap-2 pt-2'):
					register_name = ui.input('Name').props('dense autocomplete="off"').classes('w-full')
					register_email = ui.input('E-Mail-Adresse').props(
						'type=email dense autocomplete="off"'
					).classes('w-full')
					register_kennung = ui.input(
						'Kennung',
						password=True,
						password_toggle_button=True,
					).props('dense autocomplete="off"').classes('w-full')
					ui.button(
						'Registrieren',
						on_click=lambda: register(register_name, register_email, register_kennung),
					).props('flat no-caps dense').classes('w-full')

	render_authentication()


def is_valid_email(email: str) -> bool:
	"""
	Prüft die syntaktische Form einer E-Mail-Adresse.
	"""
	return EMAIL_PATTERN.fullmatch(email.strip()) is not None
