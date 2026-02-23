"""
poll.py — Doménový model ankety

Drží definici otázky a možností odpovědí.
Odděleno od storage a HTTP vrstvy (Single Responsibility).

Principy:
  KISS  – prostý dataclass
  DRY   – options jsou single source of truth
  YAGNI – žádné kategorie, žádné váhy
"""

from dataclasses import dataclass, field


@dataclass
class Option:
    id: str          # klíč pro storage (např. "a")
    label: str       # písmenný label (A, B, C…)
    text: str        # text zobrazený uživateli


@dataclass
class Poll:
    question: str
    options: list[Option] = field(default_factory=list)

    def initial_votes(self) -> dict[str, int]:
        """Vrátí dict s nulovými hlasy pro všechny možnosti."""
        return {opt.id: 0 for opt in self.options}

    def get_option(self, option_id: str) -> Option | None:
        return next((o for o in self.options if o.id == option_id), None)


# ── Definice ankety (single source of truth) ─────────────────────────────────

POLL = Poll(
    question="Kdy si dáváš první kafe dne?",
    options=[
        Option("a", "A", "Ještě před vstáváním z postele 🛏️"),
        Option("b", "B", "Hned po příchodu do práce ☕"),
        Option("c", "C", "Až mě první meeting přinutí 😩"),
        Option("d", "D", "Kafe? Já piju čaj 🍵"),
    ]
)
