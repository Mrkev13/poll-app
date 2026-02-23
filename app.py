"""
app.py — Flask webová aplikace ankety

Propojuje Storage Strategy, Auth Strategy a Poll model.
Routes jsou tenké — logika je v strategiích.

Principy:
  KISS  – routes dělají jen HTTP orchestraci
  DRY   – get_votes() je sdílená helper funkce
  YAGNI – žádné sessions, žádné cookies, žádné API tokeny navíc
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash

from poll import POLL
from storage import FileStorage
from auth import TokenAuthStrategy

# Absolutní cesta zajistí, že Flask najde templates/ a static/
# bez ohledu na to, ze které složky je app.py spuštěn.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.secret_key = "poll-secret-key-2024"  # pro flash zprávy

# ── Dependency Injection strategií ───────────────────────────────────────────
# Vyměn za MemoryStorage() pro lokální dev bez souboru
storage = FileStorage("votes.json")
auth    = TokenAuthStrategy()          # token z env RESET_TOKEN nebo fallback

# Inicializace: pokud soubor neexistuje, vytvoř nulové hlasy
_initial = POLL.initial_votes()
existing = storage.load()
if not existing:
    storage.save(_initial)


# ── Helper ────────────────────────────────────────────────────────────────────

def get_votes() -> dict[str, int]:
    """Načte aktuální hlasy a doplní chybějící klíče nulami (DRY)."""
    votes = storage.load()
    for opt in POLL.options:
        votes.setdefault(opt.id, 0)
    return votes


def total_votes(votes: dict[str, int]) -> int:
    return sum(votes.values())


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Zobraz anketu (F1.1)."""
    return render_template("index.html", poll=POLL, votes=None, total=0)


@app.route("/vote", methods=["POST"])
def vote():
    """Ulož hlas a zobraz výsledky (F1.2, F1.3)."""
    option_id = request.form.get("option")
    if not POLL.get_option(option_id):
        flash("Vyber platnou možnost.", "error")
        return redirect(url_for("index"))

    votes = get_votes()
    votes[option_id] += 1
    storage.save(votes)

    return render_template(
        "index.html",
        poll=POLL,
        votes=votes,
        total=total_votes(votes),
        voted=option_id,
    )


@app.route("/results")
def results():
    """Zobraz výsledky bez hlasování (F2.1, F2.2)."""
    votes = get_votes()
    return render_template(
        "index.html",
        poll=POLL,
        votes=votes,
        total=total_votes(votes),
        voted=None,
    )


@app.route("/reset", methods=["POST"])
def reset():
    """Resetuj hlasy po ověření tokenu (F3)."""
    token = request.form.get("token", "")
    if auth.verify(token):
        storage.reset(POLL.initial_votes())
        flash("✅ Hlasy byly úspěšně vynulovány.", "success")
    else:
        flash("❌ Nesprávný token. Reset nebyl proveden.", "error")
    return redirect(url_for("index"))


# ── Entry point (lokální dev) ─────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
