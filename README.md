# ☕ Anketa — Kdy si dáváš kafe?

Webová anketa s jednou otázkou, výsledky, stránkou O anketě a ochranou proti vícenásobnému hlasování.

## Architektura

```
poll-app/
├── app.py              # Flask routes (HTTP vrstva)
├── poll.py             # Doménový model — otázka a možnosti
├── storage.py          # Strategy Pattern: FileStorage / MemoryStorage
├── auth.py             # Strategy Pattern: TokenAuthStrategy
├── wsgi.py             # WSGI entry point pro PythonAnywhere
├── Procfile            # Start příkaz pro Render.com
├── requirements.txt    # flask, gunicorn
├── .gitignore
└── templates/
    ├── base.html       # Základní layout (nav, styly, flash zprávy)
    ├── index.html      # Hlasování + výsledky po hlasování
    ├── results.html    # Výsledky bez hlasování
    └── about.html      # O anketě + hlášení chyb
```

### Design patterns
| Pattern | Kde | Proč |
|---------|-----|------|
| **Strategy** | `storage.py` → `StorageStrategy` | Vyměnitelné úložiště bez změny app logiky |
| **Strategy** | `auth.py` → `ResetAuthStrategy` | Vyměnitelná autentizace tokenu |
| **Template Method** | `base.html` + child šablony | Sdílený layout, různý obsah |

### Principy
- **KISS** — každý soubor/třída dělá jednu věc, routes jsou ~5 řádků
- **DRY** — `get_votes()`, `total_votes()`, `has_voted()` jako sdílené helpery; `base.html` pro layout
- **YAGNI** — žádné databáze, žádné OAuth, žádné cache — jen to, co zadání vyžaduje

### Ochrana proti vícenásobnému hlasování
Po odeslání hlasu server nastaví HTTP cookie `poll_voted=1` (platnost 1 rok).
Při každém dalším požadavku server cookie zkontroluje a druhý hlas zablokuje.
Cookie je nastavena a čtena **výhradně serverem** — žádný JavaScript k ní nepřistupuje.

---

## Lokální spuštění

```bash
pip install flask
python app.py
# → http://localhost:5000
```

---

## Nasazení na Render.com — krok za krokem

### První nasazení

**Krok 1 — Připrav Git repozitář**
```bash
cd poll-app
git init
git add .
git commit -m "initial commit"
```

**Krok 2 — Vytvoř repozitář na GitHubu**
1. Jdi na github.com → New repository → název např. `poll-app`
2. **Neklikej** na "Initialize repository" (máš ho lokálně)
3. Zkopíruj URL repozitáře (např. `https://github.com/tvuj-nick/poll-app.git`)

**Krok 3 — Propoj lokální repo s GitHubem a pushni**
```bash
git remote add origin https://github.com/tvuj-nick/poll-app.git
git branch -M main
git push -u origin main
```

**Krok 4 — Vytvoř Web Service na Render.com**
1. Přihlaš se na [render.com](https://render.com)
2. Klikni **New → Web Service**
3. Zvol **Connect a GitHub repository** → vyber `poll-app`
4. Vyplň nastavení:
   - **Name**: `poll-app` (nebo cokoliv)
   - **Region**: Frankfurt (nejblíže ČR)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Klikni **Create Web Service**

**Krok 5 — Nastav environment variables**
V dashboardu webu → záložka **Environment** → Add environment variable:
```
RESET_TOKEN = tvuj-tajny-token
SECRET_KEY  = nejaky-nahodny-retezec
```

**Krok 6 — Počkej na deploy**
Render automaticky spustí build. Ve výpisu logů musíš vidět:
```
==> Build successful 🎉
==> Running 'gunicorn app:app'
```
Aplikace je dostupná na URL ve formátu `https://poll-app-xxxx.onrender.com`

---

### Nasazení změn v kódu (každá další úprava)

Pokaždé, když změníš kód a chceš ho dostat na web, postup je vždy stejný:

**Krok 1 — Uprav soubory lokálně** (v editoru, jak potřebuješ)

**Krok 2 — Zkontroluj co ses změnil(a)**
```bash
git status          # které soubory jsou změněné
git diff            # co přesně se změnilo (řádek po řádce)
```

**Krok 3 — Přidej změny do stage**
```bash
git add .                    # přidá vše
# NEBO selektivně:
git add templates/about.html # přidá jen konkrétní soubor
```

**Krok 4 — Vytvoř commit s popisem změny**
```bash
git commit -m "feat: přidána stránka O anketě"
# Doporučené prefixy:
#   feat:  nová funkce
#   fix:   oprava chyby
#   style: změna vzhledu
#   docs:  změna dokumentace
```

**Krok 5 — Pushni na GitHub**
```bash
git push
```

**Krok 6 — Render automaticky nasadí**
Render sleduje větev `main` a po každém push spustí nový build automaticky.
Ve svém dashboardu na render.com uvidíš průběh deploye v reálném čase.
Celý proces trvá obvykle 1–2 minuty.

**Krok 7 — Ověř nasazení**
1. Počkej než Render zobrazí `Deploy live ✅`
2. Otevři URL aplikace v prohlížeči
3. Zkontroluj, že změna je vidět

---

### Řešení problémů při nasazení

| Problém | Příčina | Řešení |
|---------|---------|--------|
| `command not found: gunicorn` | chybí v requirements.txt | zkontroluj že soubor obsahuje `gunicorn` |
| `TemplateNotFound: index.html` | špatná cesta k templates | zkontroluj `BASE_DIR` v `app.py` |
| Build selže | chyba v kódu | zkontroluj logy v Render dashboardu |
| Stará verze na webu | zapomněl(a) jsi pushnut | spusť `git push` |
| Hlasy se resetují | Render restartoval instanci | normální chování na free plánu |

---

## Hlášení chyb

Našel(a) jsi chybu? Napiš na **chyby@anketa-kafe.cz** nebo vytvoř issue na GitHubu.
Popiš: co se stalo · na jaké stránce · co jsi očekával(a) · přilož screenshot.
