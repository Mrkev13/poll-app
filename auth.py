"""
auth.py — Auth Strategy Pattern

Definuje abstraktní ResetAuthStrategy a konkrétní TokenAuthStrategy.
Umožňuje vyměnit autentizaci bez úpravy app logiky.

Principy:
  KISS  – jednoduchá metoda verify()
  DRY   – jeden místo pro ověření tokenu
  YAGNI – žádné role, žádné JWT, jen token
"""

import os
from abc import ABC, abstractmethod


# ── Strategy Interface ────────────────────────────────────────────────────────

class ResetAuthStrategy(ABC):
    """Abstraktní strategie pro ověření oprávnění k resetu."""

    @abstractmethod
    def verify(self, token: str) -> bool:
        """Vrátí True, pokud je token platný."""


# ── Concrete Strategy: pevný token ───────────────────────────────────────────

class TokenAuthStrategy(ResetAuthStrategy):
    """
    Ověřuje token oproti hodnotě z prostředí (env var) nebo fallback hodnotě.
    Token je uložen na serveru – nikdy se neposílá klientovi.
    """

    def __init__(self, env_var: str = "RESET_TOKEN", fallback: str = "tajny-token-2024"):
        self._token = os.environ.get(env_var, fallback)

    def verify(self, token: str) -> bool:
        return token == self._token
