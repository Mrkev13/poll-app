# ☕ Anketa — Kdy si dáváš kafe?

Webová anketa s jednou otázkou, výsledky a resetem. Nasazena na PythonAnywhere.

## Architektura

```
poll-app/
├── app.py          # Flask routes (HTTP vrstva)
├── poll.py         # Doménový model — otázka a možnosti
├── storage.py      # Strategy Pattern: FileStorage / MemoryStorage
├── auth.py         # Strategy Pattern: TokenAuthStrategy
├── wsgi.py         # WSGI entry point pro PythonAnywhere
├── requirements.txt
└── templates/
    └── index.html  # Jinja2 šablona (hlasování + výsledky)
```

### Design patterns
| Pattern   | Kde | Proč |
|-----------|-----|------|
| **Strategy** | `storage.py` — `StorageStrategy` | Vyměnitelné úložiště (soubor ↔ paměť) bez změny app logiky |
| **Strategy** | `auth.py` — `ResetAuthStrategy` | Vyměnitelná autentizace tokenu |

### Principy
- **KISS** — každý soubor/třída dělá jednu věc
- **DRY** — `get_votes()` helper, sdílená abstraktní rozhraní
- **YAGNI** — žádné zbytečné featury, jen to co zadání vyžaduje

---

## Nasazení na PythonAnywhere

### 1. Upload souborů
Nahraj celou složku `poll-app/` na PythonAnywhere přes:
- **Files** tab → upload, nebo
- `git clone` ve **Bash** konzoli

```bash
git clone https://github.com/tvuj-repo/poll-app.git ~/poll-app
```

### 2. Vytvoř virtualenv a nainstaluj závislosti

Ve **Bash** konzoli na PythonAnywhere:

```bash
mkvirtualenv poll-env --python=python3.11
cd ~/poll-app
pip install -r requirements.txt
```

### 3. Nastav Web App

1. Jdi na **Web** tab → **Add a new web app**
2. Zvol **Manual configuration** → **Python 3.11**
3. Nastavení:
   - **Source code**: `/home/tvuj-username/poll-app`
   - **Working directory**: `/home/tvuj-username/poll-app`
   - **Virtualenv**: `/home/tvuj-username/.virtualenvs/poll-env`

### 4. Nastav WSGI soubor

Klikni na odkaz WSGI souboru (např. `/var/www/tvuj-username_pythonanywhere_com_wsgi.py`)
a nahraď celý obsah tímto:

```python
import sys, os
project_home = '/home/tvuj-username/poll-app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
from app import app as application
```

### 5. (Volitelné) Nastav reset token přes environment variable

V **Web** tab → sekce **Environment variables**:
```
RESET_TOKEN = muj-super-tajny-token
```

Pokud proměnnou nenastavíš, použije se výchozí hodnota `tajny-token-2024`.

### 6. Reload

Klikni **Reload** — aplikace běží! 🎉

---

## Lokální spuštění (dev)

```bash
pip install flask
python app.py
# → http://localhost:5000
```

Pro použití paměťového úložiště místo souboru uprav `app.py`:
```python
from storage import MemoryStorage
storage = MemoryStorage()
```

---

## Funkce

| Feature | Route | Metoda |
|---------|-------|--------|
| Zobraz anketu | `/` | GET |
| Hlasuj | `/vote` | POST |
| Zobraz výsledky | `/results` | GET |
| Reset hlasů | `/reset` | POST (vyžaduje token) |
