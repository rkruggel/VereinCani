from nicegui import app


AUTH_STORAGE_KEY = 'angemeldeter_benutzer'


def get_authenticated_user() -> dict[str, str] | None:
	benutzer = app.storage.user.get(AUTH_STORAGE_KEY)
	if not isinstance(benutzer, dict):
		return None
	if not benutzer.get('id') or not benutzer.get('email') or not benutzer.get('name'):
		return None
	return benutzer


def is_authenticated() -> bool:
	return get_authenticated_user() is not None
