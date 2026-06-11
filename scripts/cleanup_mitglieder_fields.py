"""Einmalige Bereinigung der Mitglieder-Dokumente in CouchDB."""

from src.popelsapp import load_popels_config
from src.popelsapp.models import create_popels_model
from src.popelsapp.repository import CouchPopelsDatabase


def main() -> None:
	"""Bereinigt alle nicht zur Konfiguration gehörenden Felder aus Mitgliederdokumenten."""

	config = load_popels_config('mitglieder.yaml')
	model = create_popels_model(config)
	database = CouchPopelsDatabase(config, model)
	checked, updated = database.cleanup_unknown_fields()
	print(f'Mitglieder bereinigt: {updated} von {checked} Datensatz(en) aktualisiert.')


if __name__ == '__main__':
	main()
