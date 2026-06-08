"""
Projekt:
  VereinCani - Eine dynamische Vereinsverwaltung.

Modul:
  main.py

Beschreibung:
  Startpunkt und Konfiguration der VereinCani-Anwendung.

Autor: Roland Kruggel
Version: 0.0.1
Stand: 06.06.2026
Lizens: MIT
"""

import configparser
from pathlib import Path

from nicegui import ui

from src.run import render_start_page


CONFIG_PATH = Path(__file__).resolve().parent / 'config.ini'


def main() -> None:
	config = configparser.ConfigParser()
	config.read(CONFIG_PATH)
	title = config.get('allgemein', 'title', fallback='VereinCani')
	host = config.get('allgemein', 'host', fallback='0.0.0.0')
	port = config.getint('allgemein', 'port', fallback=9000)
	storage_secret = config.get('allgemein', 'storage_secret', fallback='aMqMoA7')

	ui.page('/')(render_start_page)
	ui.run(
		title=title,
		host=host,
		port=port,
		storage_secret=storage_secret,
		uvicorn_reload_includes='*.py,popels/*.yaml',
	)


if __name__ in {"__main__", "__mp_main__"}:
	main()
