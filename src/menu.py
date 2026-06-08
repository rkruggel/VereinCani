"""Menükonfiguration, Zugriffsschutz und Navigation der Anwendung."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.auth import is_authenticated
from src.pages.adressen.start import render_adressen_page
from src.pages.beitraege.start import render_beitraege_page
from src.pages.dashboard.start import render_dashboard_page
from src.pages.mitglieder.start import render_mitglieder_page
from src.pages.termine.start import render_termine_page


PAGES: dict[str, dict[str, Any]] = {
	'dashboard': {
		'title': 'Dashboard',
		'protected': False,
		'renderer': render_dashboard_page,
	},
	'mitglieder': {
		'title': 'Mitglieder',
		'protected': True,
		'renderer': render_mitglieder_page,
	},
	'adressen': {
		'title': 'Adressen',
		'protected': True,
		'renderer': render_adressen_page,
	},
	'termine': {
		'title': 'Termine',
		'protected': True,
		'renderer': render_termine_page,
	},
	'beitraege': {
		'title': 'Beitraege',
		'protected': False,
		'renderer': render_beitraege_page,
	},
}


def can_access_page(page_key: str, authenticated: bool) -> bool:
	"""Prüft anhand der Menükonfiguration, ob eine Seite erreichbar ist."""

	page = PAGES.get(page_key)
	return page is not None and (not page['protected'] or authenticated)


@ui.refreshable
def render_menu(selected_page: dict[str, str], on_select: Callable[[str], None]) -> None:
	"""Erzeugt die Menübuttons für den aktuellen Anmelde- und Auswahlzustand."""

	authenticated = is_authenticated()
	with ui.row().classes('items-center gap-2 flex-wrap justify-end'):
		for page_key, page in PAGES.items():
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
				page['title'],
				on_click=lambda key=page_key: on_select(key),
			).props('flat no-caps').classes(button_classes)
			button.set_enabled(is_enabled)
			if not is_enabled:
				button.tooltip('Anmeldung erforderlich')
