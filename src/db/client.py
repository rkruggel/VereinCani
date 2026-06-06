import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from ravendb import DocumentStore


CONFIG_PATH = Path(__file__).resolve().parents[2] / 'config.ini'


@dataclass
class RavenConfig:
    urls: list[str]
    database: str
    certificate_path: Optional[str] = None


def load_raven_config(config_path: Path = CONFIG_PATH) -> RavenConfig:
    parser = configparser.ConfigParser()
    parser.read(config_path)

    server_urls = os.getenv(
        'RAVENDB_URLS',
        parser.get('ravendb', 'server_url', fallback='http://127.0.0.1:8080'),
    )
    urls = [url.strip() for url in server_urls.split(',') if url.strip()]
    database = os.getenv(
        'RAVENDB_DATABASE',
        parser.get('ravendb', 'database', fallback='VereinCani'),
    )
    certificate_path = os.getenv('RAVENDB_CERT_PATH')
    return RavenConfig(urls=urls, database=database, certificate_path=certificate_path)


def create_document_store(
    config: Optional[RavenConfig] = None,
    collection_names: Optional[Mapping[type, str]] = None,
) -> DocumentStore:
    cfg = config or load_raven_config()
    store = DocumentStore(cfg.urls, cfg.database)
    store.conventions.find_identity_property_name = lambda _object_type: 'id'
    if collection_names:
        default_collection_name = store.conventions.find_collection_name

        def find_collection_name(object_type: type) -> str:
            if object_type in collection_names:
                return collection_names[object_type]
            return default_collection_name(object_type)

        store.conventions.find_collection_name = find_collection_name
    if cfg.certificate_path:
        store.certificate_pem_path = cfg.certificate_path
    store.initialize()
    return store
