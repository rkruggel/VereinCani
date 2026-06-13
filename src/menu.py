"""Menükonfiguration, Zugriffsschutz und Navigation der Anwendung."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from src.auth import is_authenticated
from src.pages.beitraege.start import render_beitraege_page
from src.pages.dashboard.start import render_dashboard_page
from src.pages.hunde.start import render_hunde_page
from src.pages.kasse.start import render_kasse_page
from src.pages.mitglieder.start import render_mitglieder_page
from src.pages.persoenlich.start import render_persoenlich_page
from src.pages.preise.preisstamm import render_preisstamm_page
from src.pages.termine.start import render_termine_page


PAGES: dict[str, dict[str, Any]] = {
	'dashboard': {
		'title': 'Dashboard',
		'tooltip': 'Zur zentralen Übersicht wechseln',
		'protected': False,
		'renderer': render_dashboard_page,
	},
	'mitglieder': {
		'title': 'Mitglieder',
		'tooltip': 'Mitglieder verwalten',
		'protected': True,
		'renderer': render_mitglieder_page,
	},
	'stammdaten': {
		'title': 'Stammdaten',
		'tooltip': 'Persönlich, Hunde und Preisstamm verwalten',
		'submenu': {
			'persoenlich': {
				'title': 'Persönlich',
				'tooltip': 'Persönlich verwalten',
				'protected': True,
				'renderer': render_persoenlich_page,
			},
			'hunde': {
				'title': 'Hunde',
				'tooltip': 'Hunde verwalten',
				'protected': True,
				'renderer': render_hunde_page,
			},
			'preisstamm': {
				'title': 'Preisstamm',
				'tooltip': 'Preisstamm für ein bis fünf Hunde verwalten',
				'protected': True,
				'renderer': render_preisstamm_page,
			},
		},
	},
	'termine': {
		'title': 'Termine',
		'tooltip': 'Termine und Veranstaltungen verwalten',
		'protected': True,
		'renderer': render_termine_page,
	},
	'beitraege': {
		'title': 'Beitraege',
		'tooltip': 'Beiträge und Zahlungen verwalten',
		'protected': False,
		'renderer': render_beitraege_page,
	},
	'kasse': {
		'title': 'Kasse',
		'tooltip': 'Kassenprogramm verwalten',
		'protected': True,
		'renderer': render_kasse_page,
	},
}


def get_page(page_key: str) -> dict[str, Any] | None:
	"""
	Liefert eine Seite unabhängig von ihrer Menüebene.
	"""
	for key, page in PAGES.items():
		if key == page_key and 'renderer' in page:
			return page
		submenu = page.get('submenu', {})
		if page_key in submenu:
			return submenu[page_key]
	return None


def can_access_page(page_key: str, authenticated: bool) -> bool:
	"""
	Prüft anhand der Menükonfiguration, ob eine Seite erreichbar ist.
	"""
	page = get_page(page_key)
	return page is not None and (not page['protected'] or authenticated)


@ui.refreshable
def render_menu(selected_page: dict[str, str], on_select: Callable[[str], None]) -> None:
	"""
	Erzeugt die Menübuttons für den aktuellen Anmelde- und Auswahlzustand.
	"""
	authenticated = is_authenticated()

	def button_classes(is_active: bool, is_enabled: bool) -> str:
		"""
		Bestimmt die CSS-Klassen für einen Menübutton basierend auf Aktivität und Zugriffsberechtigung.
		"""
		classes = 'rounded-full px-3 py-2 text-sm font-medium '
		if is_active:
			return classes + 'bg-primary text-white'
		if is_enabled:
			return classes + 'bg-slate-100 text-slate-700'
		return classes + 'bg-slate-100 text-slate-400'

	def tooltip_text(page: dict[str, Any], is_enabled: bool) -> str:
		"""
		Berechnet den Tooltip-Text für einen Menübutton basierend auf Zugriffsberechtigung.
		"""
		tooltip = page['tooltip']
		if not is_enabled:
			return f'{tooltip} – Anmeldung erforderlich'
		return tooltip

	def render_page_button(page_key: str, page: dict[str, Any]) -> None:
		"""
		Erzeugt einen Menübutton für eine Seite ohne Untermenü.
		"""
		is_active = selected_page['key'] == page_key
		is_enabled = can_access_page(page_key, authenticated)
		button = ui.button(
			page['title'],
			on_click=lambda key=page_key: on_select(key),
		).props('flat no-caps').classes(button_classes(is_active, is_enabled))
		button.set_enabled(is_enabled)
		button.tooltip(tooltip_text(page, is_enabled))

	with ui.row().classes('items-center gap-2 flex-wrap justify-end'):
		for page_key, page in PAGES.items():
			submenu = page.get('submenu')
			if not submenu:
				render_page_button(page_key, page)
				continue

			is_active = selected_page['key'] in submenu
			is_enabled = any(
				can_access_page(submenu_key, authenticated)
				for submenu_key in submenu
			)
			with ui.button(page['title']).props('flat no-caps icon-right=expand_more').classes(
				button_classes(is_active, is_enabled)
			) as menu_button:
				with ui.menu().props('auto-close'):
					for submenu_key, submenu_page in submenu.items():
						submenu_enabled = can_access_page(submenu_key, authenticated)
						menu_item = ui.menu_item(
							submenu_page['title'],
							on_click=lambda key=submenu_key: on_select(key),
						).classes('min-w-40')
						menu_item.set_enabled(submenu_enabled)
						menu_item.tooltip(tooltip_text(submenu_page, submenu_enabled))
			menu_button.set_enabled(is_enabled)
			menu_button.tooltip(tooltip_text(page, is_enabled))
