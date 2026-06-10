"""Einmalige Entfernung der Mitgliedsnummer aus RavenDB."""

from src.db.client import create_document_store


store = create_document_store()
try:
	changed_members = 0
	with store.open_session() as session:
		session.advanced.use_optimistic_concurrency = True
		for member in session.query_collection('Mitglieder', dict):
			if 'mitgliedsnummer' in member:
				member.pop('mitgliedsnummer')
				changed_members += 1
		if changed_members:
			session.save_changes()

	changed_settings = 0
	with store.open_session() as session:
		session.advanced.use_optimistic_concurrency = True
		for settings in session.query_collection('MitgliederlistenEinstellungen', dict):
			fields = list(settings.get('sichtbare_felder') or [])
			sortings = list(settings.get('sortierungen') or [])
			new_fields = [field for field in fields if field != 'mitgliedsnummer']
			new_sortings = [
				sorting
				for sorting in sortings
				if sorting.partition(':')[0] != 'mitgliedsnummer'
			]
			if new_fields != fields or new_sortings != sortings:
				settings['sichtbare_felder'] = new_fields
				settings['sortierungen'] = new_sortings
				changed_settings += 1
		if changed_settings:
			session.save_changes()

	deleted_counters = 0
	with store.open_session() as session:
		session.advanced.use_optimistic_concurrency = True
		for counter in session.query_collection('FestNummer', dict):
			session.delete(counter)
			deleted_counters += 1
		if deleted_counters:
			session.save_changes()

	print(
		f'Bereinigt: {changed_members} Mitglieder, '
		f'{changed_settings} Listeneinstellungen, '
		f'{deleted_counters} FestNummer-Dokumente.'
	)
finally:
	store.close()
