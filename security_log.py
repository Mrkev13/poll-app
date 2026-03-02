"""
security_log.py — Sledování podezřelé aktivity

Zaznamenává každý HTTP request a detekuje anomálie:
  - podezřelé User-Agenty (boti, curl, wget, skripty)
  - příliš mnoho requestů z jedné IP (rate anomaly)
  - skenování neexistujících cest

Principy:
  KISS  – jednoduchý append-only JSON log
  DRY   – detekční logika na jednom místě
  YAGNI – žádné blokování, jen pozorování
"""

import json
import os
import re
from datetime import datetime, timezone
from collections import defaultdict, deque

# ── Konfigurace ───────────────────────────────────────────────────────────────

LOG_FILE        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "security.log")
RATE_WINDOW_SEC = 60        # časové okno pro počítání requestů
RATE_THRESHOLD  = 20        # více než X requestů z jedné IP za okno = anomálie

# User-Agenty které jsou podezřelé (boti, nástroje, skripty)
SUSPICIOUS_UA_PATTERNS = [
    r"curl/",
    r"wget/",
    r"python-requests",
    r"python-urllib",
    r"httpie",
    r"go-http-client",
    r"java/",
    r"libwww-perl",
    r"scrapy",
    r"bot",
    r"crawler",
    r"spider",
    r"^-$",           # prázdný nebo pomlčka (PuTTY, vlastní skripty)
    r"^$",
]

# Cesty které nikdo normální nenavštěvuje — typické skenování
SUSPICIOUS_PATHS = [
    "/admin", "/.env", "/wp-login", "/phpmyadmin", "/config",
    "/etc/passwd", "/.git", "/backup", "/shell", "/cmd",
    "/.htaccess", "/robots.txt", "/sitemap.xml",
]

# In-memory store pro rate tracking {ip: deque of timestamps}
_request_times: dict[str, deque] = defaultdict(deque)


# ── Detekční logika ───────────────────────────────────────────────────────────

def _is_suspicious_ua(user_agent: str) -> tuple[bool, str]:
    """Zkontroluje User-Agent proti seznamu podezřelých vzorů."""
    ua = user_agent or ""
    for pattern in SUSPICIOUS_UA_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            return True, f"suspicious_user_agent:{pattern}"
    return False, ""


def _check_rate(ip: str, now: datetime) -> tuple[bool, str]:
    """Sleduje počet requestů z IP v časovém okně."""
    times = _request_times[ip]
    cutoff = now.timestamp() - RATE_WINDOW_SEC
    # odstraň staré záznamy
    while times and times[0] < cutoff:
        times.popleft()
    times.append(now.timestamp())
    count = len(times)
    if count > RATE_THRESHOLD:
        return True, f"rate_anomaly:{count}_requests_in_{RATE_WINDOW_SEC}s"
    return False, ""


def _is_suspicious_path(path: str) -> tuple[bool, str]:
    """Detekuje skenování typických admin/config cest."""
    for suspicious in SUSPICIOUS_PATHS:
        if path.lower().startswith(suspicious):
            return True, f"suspicious_path:{path}"
    return False, ""


# ── Hlavní funkce ─────────────────────────────────────────────────────────────

def log_request(ip: str, method: str, path: str, user_agent: str,
                status_code: int, referrer: str = "") -> dict:
    """
    Zaloguje request a vrátí záznam včetně detekovaných anomálií.
    Voláno z Flask after_request hooku.
    """
    now = datetime.now(timezone.utc)
    anomalies = []

    ua_suspicious, ua_reason   = _is_suspicious_ua(user_agent)
    rate_suspicious, rate_reason = _check_rate(ip, now)
    path_suspicious, path_reason = _is_suspicious_path(path)

    if ua_suspicious:   anomalies.append(ua_reason)
    if rate_suspicious: anomalies.append(rate_reason)
    if path_suspicious: anomalies.append(path_reason)

    record = {
        "ts":         now.isoformat(),
        "ip":         ip,
        "method":     method,
        "path":       path,
        "status":     status_code,
        "ua":         user_agent,
        "referrer":   referrer,
        "anomalies":  anomalies,
        "suspicious": len(anomalies) > 0,
    }

    # Append do logu (každý řádek = jeden JSON záznam — snadno parsovatelné)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def load_logs(limit: int = 200) -> list[dict]:
    """Načte posledních N záznamů z logu."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    records = []
    for line in lines[-limit:]:
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return list(reversed(records))  # nejnovější první


def get_stats() -> dict:
    """Agregované statistiky pro admin pohled."""
    logs = load_logs(500)
    if not logs:
        return {}

    ip_counts: dict[str, int]     = defaultdict(int)
    ua_counts: dict[str, int]     = defaultdict(int)
    anomaly_counts: dict[str, int] = defaultdict(int)
    suspicious_total = 0

    for r in logs:
        ip_counts[r["ip"]] += 1
        ua_short = r["ua"][:60] if r["ua"] else "(prázdný)"
        ua_counts[ua_short] += 1
        if r["suspicious"]:
            suspicious_total += 1
        for a in r["anomalies"]:
            anomaly_counts[a] += 1

    return {
        "total":           len(logs),
        "suspicious":      suspicious_total,
        "top_ips":         sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_uas":         sorted(ua_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_anomalies":   sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True),
    }
