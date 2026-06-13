"""
Öffentliche Schnittstelle des Authentifizierungspakets.
"""
from src.auth.panel import render_login_panel
from src.auth.session import is_authenticated


__all__ = ['is_authenticated', 'render_login_panel']
