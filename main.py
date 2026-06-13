"""
Projekt:
	VereinGUI - Eine dynamische Vereinsverwaltung.

Modul:
  main.py

Beschreibung:
	Startpunkt und Konfiguration der VereinGUI-Anwendung.

Autor: Roland Kruggel
Version: 0.0.1
Stand: 06.06.2026
Lizens: MIT
"""

import configparser
from pathlib import Path
from time import perf_counter

from nicegui import app, ui

from src.run import render_start_page


CONFIG_PATH = Path(__file__).resolve().parent / 'config.ini'
REQUEST_TIME_LOGGING_REGISTERED = False


def register_request_time_logging() -> None:
	"""Gibt nach jeder HTTP-Anfrage die verstrichene Zeit aus."""

	global REQUEST_TIME_LOGGING_REGISTERED
	if REQUEST_TIME_LOGGING_REGISTERED:
		return
	REQUEST_TIME_LOGGING_REGISTERED = True

	@app.middleware('http')
	async def log_request_time(request, call_next):
		start = perf_counter()
		status = 'Fehler'
		try:
			response = await call_next(request)
			status = str(response.status_code)
			return response
		finally:
			elapsed_ms = (perf_counter() - start) * 1000
			print(
				f'Anfrage {request.method} {request.url.path} beendet mit {status} '
				f'nach {elapsed_ms:.1f} ms',
				flush=True,
			)


def main() -> None:
	config = configparser.ConfigParser()
	config.read(CONFIG_PATH)
	title = config.get('allgemein', 'title', fallback='VereinGUI')
	host = config.get('allgemein', 'host', fallback='0.0.0.0')
	port = config.getint('allgemein', 'port', fallback=9000)
	storage_secret = config.get('allgemein', 'storage_secret', fallback='aMqMoA7')

	register_request_time_logging()

	ui.page('/')(render_start_page)
	ui.run(
		title=title,
		host=host,
		port=port,
		storage_secret=storage_secret,
		uvicorn_reload_includes='*.py,popels/*.yaml',
		native=True,
		window_size=(1400, 900),
	)


if __name__ in {"__main__", "__mp_main__"}:
	main()
