"""
app.py — Flask webová aplikace ankety

Principy:
  KISS  – routes dělají jen HTTP orchestraci
  DRY   – get_votes(), total_votes(), has_voted() jako sdílené helpery
  YAGNI – jen co zadání vyžaduje
"""

import os
from flask import (Flask, render_template, request,
                   redirect, url_for, flash, make_response, session)

from poll import POLL
from storage import FileStorage
from auth import TokenAuthStrategy
from security_log import log_request, load_logs, get_stats

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "poll-secret-key-2024")

storage = FileStorage(os.path.join(BASE_DIR, "votes.json"))
auth    = TokenAuthStrategy()

if not storage.load():
    storage.save(POLL.initial_votes())

VOTED_COOKIE  = "poll_voted"
ADMIN_SESSION = "admin_ok"


# ── Security logging ──────────────────────────────────────────────────────────


@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com; "
        "img-src 'self' https://www.google-analytics.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    return response

@app.after_request
def log_every_request(response):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    ip = ip.split(",")[0].strip()
    log_request(
        ip          = ip,
        method      = request.method,
        path        = request.path,
        user_agent  = request.headers.get("User-Agent", ""),
        status_code = response.status_code,
        referrer    = request.headers.get("Referer", ""),
    )
    return response


# ── Helpery ───────────────────────────────────────────────────────────────────

def get_votes() -> dict[str, int]:
    votes = storage.load()
    for opt in POLL.options:
        votes.setdefault(opt.id, 0)
    return votes

def total_votes(votes: dict[str, int]) -> int:
    return sum(votes.values())

def has_voted() -> bool:
    return request.cookies.get(VOTED_COOKIE) == "1"

def is_admin() -> bool:
    """Zkontroluje session — vrátí True pokud je uživatel přihlášen jako admin."""
    return session.get(ADMIN_SESSION) is True


# ── Veřejné routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if has_voted():
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


# ── Admin routes (chráněno tokenem + session) ─────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """
    Admin panel — přihlášení tokenem, reset hlasů, security log.
    Token se NIKDY neposílá klientovi ani nezobrazuje.
    """
    if request.method == "POST":
        action = request.form.get("action")

        # Přihlášení
        if action == "login":
            token = request.form.get("token", "")
            if auth.verify(token):
                session[ADMIN_SESSION] = True
                flash("✅ Přihlášení úspěšné.", "success")
            else:
                flash("❌ Nesprávný token.", "error")
            return redirect(url_for("admin"))

        # Odhlášení
        if action == "logout":
            session.pop(ADMIN_SESSION, None)
            flash("Byl(a) jsi odhlášen(a).", "info")
            return redirect(url_for("admin"))

        # Reset hlasů — jen pro přihlášeného admina
        if action == "reset":
            if not is_admin():
                flash("❌ Nejsi přihlášen(a).", "error")
                return redirect(url_for("admin"))
            storage.reset(POLL.initial_votes())
            flash("✅ Hlasy byly úspěšně vynulovány.", "success")
            return redirect(url_for("admin"))

    # GET — zobraz panel nebo login formulář
    logs  = load_logs(200) if is_admin() else []
    stats = get_stats()    if is_admin() else {}
    votes = get_votes()    if is_admin() else {}

    return render_template("admin.html",
                           authorized=is_admin(),
                           logs=logs, stats=stats,
                           votes=votes,
                           total=total_votes(votes) if votes else 0,
                           poll=POLL,
                           active="")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)