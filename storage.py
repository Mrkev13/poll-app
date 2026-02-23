"""
storage.py — Storage Strategy Pattern

Defines abstract StorageStrategy interface and concrete implementations.
Swap strategies without touching app logic (Open/Closed Principle).

Principy:
  KISS  – každá třída dělá jednu věc
  DRY   – sdílená logika v abstraktní třídě
  YAGNI – jen co je potřeba (load/save)
"""

import json
import os
from abc import ABC, abstractmethod


# ── Strategy Interface ────────────────────────────────────────────────────────

class StorageStrategy(ABC):
    """Abstraktní strategie pro ukládání hlasů."""

    @abstractmethod
    def load(self) -> dict[str, int]:
        """Načte hlasy. Vrátí dict {option_id: count}."""

    @abstractmethod
    def save(self, votes: dict[str, int]) -> None:
        """Uloží hlasy."""

    @abstractmethod
    def reset(self, initial: dict[str, int]) -> None:
        """Vynuluje hlasy na výchozí stav."""


# ── Concrete Strategy: JSON soubor ───────────────────────────────────────────

class FileStorage(StorageStrategy):
    """
    Ukládá hlasy do JSON souboru na disku.
    Vhodné pro PythonAnywhere – soubor přetrvá restart.
    """

    def __init__(self, filepath: str = "votes.json"):
        self.filepath = filepath

    def load(self) -> dict[str, int]:
        if not os.path.exists(self.filepath):
            return {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, votes: dict[str, int]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(votes, f, ensure_ascii=False, indent=2)

    def reset(self, initial: dict[str, int]) -> None:
        self.save(initial)


# ── Concrete Strategy: In-memory (pro testy / dev) ───────────────────────────

class MemoryStorage(StorageStrategy):
    """
    Uchovává hlasy v paměti procesu.
    Sdílené napříč požadavky, ale nepřetrvá restart.
    Vhodné pro lokální vývoj / testy.
    """

    def __init__(self):
        self._store: dict[str, int] = {}

    def load(self) -> dict[str, int]:
        return dict(self._store)

    def save(self, votes: dict[str, int]) -> None:
        self._store = dict(votes)

    def reset(self, initial: dict[str, int]) -> None:
        self._store = dict(initial)
