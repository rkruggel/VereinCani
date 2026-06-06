"""Öffentliche Schnittstelle des Adressen-Pakets."""

from src.pages.adressen.adressen import render_adressen_page
from src.pages.adressen.models import Adresse


__all__ = ['Adresse', 'render_adressen_page']
