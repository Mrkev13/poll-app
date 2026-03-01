"""
app.py — Flask webová aplikace ankety

Propojuje Storage Strategy, Auth Strategy a Poll model.
Routes jsou tenké — logika je v strategiích.

Principy:
  KISS  – routes dělají jen HTTP orchestraci
  DRY   – get_votes() a render_results() jsou sdílené helpery
  YAGNI – žádné sessions, žádné OAuth, jen to co zadání vyžaduje
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, make_response

from poll import POLL
from storage import FileStorage
from auth import TokenAuthStrategy

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "poll-secret-key-2024")

# ── Dependency Injection strategií ───────────────────────────────────────────
storage = FileStorage(os.path.join(BASE_DIR, "votes.json"))
auth    = TokenAuthStrategy()

if not storage.load():
    storage.save(POLL.initial_votes())

VOTED_COOKIE = "poll_voted"   # název cookie pro ochranu proti vícenásobnému hlasování


# ── Helpery (DRY) ─────────────────────────────────────────────────────────────

def get_votes() -> dict[str, int]:
    votes = storage.load()
    for opt in POLL.options:
        votes.setdefault(opt.id, 0)
    return votes

def total_votes(votes: dict[str, int]) -> int:
    return sum(votes.values())

def has_voted() -> bool:
    """Zkontroluje cookie — vrátí True pokud uživatel už hlasoval."""
    return request.cookies.get(VOTED_COOKIE) == "1"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if has_voted():
        # Uživatel už hlasoval — ukaž mu výsledky přímo na hlavní stránce
        votes = get_votes()
        return render_template(
            "index.html", poll=POLL,
            votes=votes, total=total_votes(votes),
            voted=None, already_voted=True, active="index"
        )
    return render_template("index.html", poll=POLL, votes=None, total=0,
                           voted=None, already_voted=False, active="index")


@app.route("/vote", methods=["POST"])
def vote():
    if has_voted():
        flash("Už jsi hlasoval(a). Každý může hlasovat jen jednou.", "info")
        return redirect(url_for("index"))

    option_id = request.form.get("option")
    if not POLL.get_option(option_id):
        flash("Vyber platnou možnost.", "error")
        return redirect(url_for("index"))

    votes = get_votes()
    votes[option_id] += 1
    storage.save(votes)

    # Nastav cookie na 1 rok — uložena v prohlížeči, ověřována serverem
    response = make_response(render_template(
        "index.html", poll=POLL,
        votes=votes, total=total_votes(votes),
        voted=option_id, already_voted=False, active="index"
    ))
    response.set_cookie(VOTED_COOKIE, "1", max_age=60*60*24*365, samesite="Lax")
    return response


@app.route("/results")
def results():
    votes = get_votes()
    return render_template(
        "results.html", poll=POLL,
        votes=votes, total=total_votes(votes), active="results"
    )


@app.route("/about")
def about():
    return render_template("about.html", active="about")


@app.route("/restart")
def restart():
    # Získáme token přímo z instance auth strategie
    # V reálné produkci bychom toto nedělali (security risk), ale pro účely dema/testování:
    current_token = auth._token if hasattr(auth, "_token") else ""
    return render_template("restart.html", token=current_token, active="restart")


@app.route("/reset", methods=["POST"])
def reset():
    token = request.form.get("token", "")
    if auth.verify(token):
        storage.reset(POLL.initial_votes())
        flash("✅ Hlasy byly úspěšně vynulovány.", "success")
    else:
        flash("❌ Nesprávný token. Reset nebyl proveden.", "error")
    return redirect(url_for("index"))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)