"""
Hilfsfunktionen für eingebettete Bankdaten.
"""
def embedded_bankdata_document(record: dict) -> dict:
	"""
	Bereitet Bankdaten für die Einbettung im Mitglied vor.
	"""
	result = {
		'kreditinstitut': str(record.get('kreditinstitut') or '').strip(),
		'iban': str(record.get('iban') or '').strip(),
		'mandat': str(record.get('mandat') or '').strip(),
	}
	return {
		key: value
		for key, value in result.items()
		if value
	}


def format_bankdaten_summary(record: dict) -> str:
	"""
	Formatiert Bankdaten für die Mitgliederliste.
	"""
	parts = [
		str(record.get('kreditinstitut') or '').strip(),
		str(record.get('iban') or '').strip(),
		str(record.get('mandat') or '').strip(),
	]
	return ' / '.join(part for part in parts if part)
