"""
Hilfsfunktionen zur sicheren Verarbeitung von Kennungen.
"""
import hashlib
import hmac
import secrets


PBKDF2_ITERATIONS = 310_000


def hash_kennung(kennung: str, salt: str | None = None) -> tuple[str, str]:
	"""
	Hasht eine Kennung für die sichere Speicherung.
	"""
	salt = salt or secrets.token_hex(16)
	digest = hashlib.pbkdf2_hmac(
		'sha256',
		kennung.encode('utf-8'),
		bytes.fromhex(salt),
		PBKDF2_ITERATIONS,
	)
	return digest.hex(), salt


def verify_kennung(kennung: str, expected_hash: str, salt: str) -> bool:
	"""
	Vergleicht eine Kennung mit einem gespeicherten Hash.
	"""
	actual_hash, _ = hash_kennung(kennung, salt)
	return hmac.compare_digest(actual_hash, expected_hash)
