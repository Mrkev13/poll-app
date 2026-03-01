# Technická dokumentace Anketního Systému

Tato dokumentace poskytuje kompletní přehled o architektuře, konfiguraci a správě webové aplikace pro hlasování.

---

## 1. URL Adresy a API Endpointy

Aplikace využívá jednoduché REST-like rozhraní. Níže je uveden seznam všech dostupných endpointů.

### Veřejné endpointy

#### Hlavní stránka
- **URL**: `/`
- **Metoda**: `GET`
- **Popis**: Zobrazí hlasovací formulář. Pokud uživatel již hlasoval (dle cookie), zobrazí rovnou výsledky.
- **Parametry**: Žádné.
- **Odpověď**: HTML stránka (`index.html`).

#### Odeslání hlasu
- **URL**: `/vote`
- **Metoda**: `POST`
- **Popis**: Zpracuje hlas uživatele.
- **Parametry (Form Data)**:
  - `option` (povinný): ID vybrané možnosti (např. `a`, `b`, `c`, `d`).
- **Autentizace**: Žádná, ale kontroluje se cookie `poll_voted`.
- **Chování**:
  - Pokud je hlas platný: Uloží hlas, nastaví cookie `poll_voted=1` (platnost 1 rok) a přesměruje na `/`.
  - Pokud uživatel již hlasoval: Zobrazí flash zprávu a přesměruje na `/`.
  - Pokud je možnost neplatná: Zobrazí chybovou hlášku.

#### Zobrazení výsledků
- **URL**: `/results`
- **Metoda**: `GET`
- **Popis**: Zobrazí aktuální stav hlasování v grafické podobě.
- **Parametry**: Žádné.
- **Odpověď**: HTML stránka (`results.html`).

#### O aplikaci
- **URL**: `/about`
- **Metoda**: `GET`
- **Popis**: Informační stránka o projektu.
- **Odpověď**: HTML stránka (`about.html`).

### Administrativní endpointy

#### Formulář pro reset (Restart)
- **URL**: `/restart`
- **Metoda**: `GET`
- **Popis**: Zobrazí stránku s formulářem pro resetování ankety. Token je zde předvyplněn pro usnadnění testování (POZOR: V produkci by měl být tento endpoint zabezpečen nebo token skryt).
- **Odpověď**: HTML stránka (`restart.html`).

#### Provedení resetu
- **URL**: `/reset`
- **Metoda**: `POST`
- **Popis**: Vynuluje všechny hlasy v anketě.
- **Parametry (Form Data)**:
  - `token` (povinný): Bezpečnostní token pro ověření oprávnění.
- **Autentizace**: Porovnává zaslaný token s proměnnou prostředí `RESET_TOKEN`.
- **Odpověď**: Přesměrování na `/` s flash zprávou o úspěchu či neúspěchu.

---

## 2. Postup pro reset ankety

Resetování ankety uvede počítadla všech možností zpět na nulu. Tento proces je nevratný.

### Přípravné kroky a zálohování
Před resetem doporučujeme provést zálohu aktuálních dat, pokud jsou důležitá.
- Data jsou uložena v souboru `votes.json` v kořenovém adresáři aplikace.
- **Záloha (SSH/Lokálně)**:
  ```bash
  cp votes.json votes_backup_$(date +%F).json
  ```
- Pokud běží aplikace na platformě jako Render/Heroku s efemérním souborovým systémem, data mohou být ztracena při restartu (pokud se nepoužívá perzistentní disk), proto je `votes.json` vhodný spíše pro jednodušší nasazení.

### Proces resetu přes webové rozhraní
1. Přejděte na stránku `/restart`.
2. V poli "Token" zkontrolujte předvyplněný token (nebo zadejte správný `RESET_TOKEN`).
3. Klikněte na tlačítko **"Resetovat anketu"**.
4. Pokud je token správný, budete přesměrováni na úvodní stránku a zobrazí se zpráva "✅ Hlasy byly úspěšně vynulovány.".

### Manuální reset (pokud webové rozhraní není dostupné)
Pokud máte přístup k serverové konzoli:
1. Smažte soubor `votes.json` nebo jej upravte:
   ```bash
   echo '{"a": 0, "b": 0, "c": 0, "d": 0}' > votes.json
   ```
2. Aplikace si při dalším požadavku načte prázdný stav (nebo vytvoří nový soubor).

---

## 3. Popis konfigurace

Konfigurace aplikace se provádí primárně pomocí proměnných prostředí (Environment Variables).

### Umístění
- **Lokální vývoj**: Proměnné jsou načítány z OS prostředí. Lze použít `.env` soubor (pokud je implementováno načítání, zde standardně přes `os.environ`).
- **Produkce (Render/Heroku)**: Nastavují se v administraci dané platformy.

### Konfigurační parametry

| Parametr | Popis | Výchozí hodnota | Doporučená hodnota (Produkce) |
|---|---|---|---|
| `SECRET_KEY` | Klíč pro podepisování session cookies a flash zpráv. | `poll-secret-key-2024` | Dlouhý náhodný řetězec (např. vygenerovaný přes `openssl rand -hex 32`). |
| `RESET_TOKEN` | Heslo/token vyžadovaný pro resetování hlasování. | `tajny-token-2024` | Silné heslo, které není snadno uhadnutelné. |
| `PORT` | Port, na kterém webový server naslouchá. | `5000` | Nastavuje automaticky hosting (např. Render). |

### Úprava konfigurace
- **V kódu**: Výchozí hodnoty jsou definovány v `app.py` a `auth.py` jako fallback.
- **Při spuštění**:
  ```bash
  export RESET_TOKEN="moje-super-tajne-heslo"
  python app.py
  ```

---

## 4. Postup deploymentu

Návod pro nasazení aplikace na cloudovou platformu **Render.com** (nebo kompatibilní).

### Požadavky na prostředí
- **Python verze**: 3.13 (nebo kompatibilní 3.x)
- **Závislosti**: Uvedeny v `requirements.txt` (`flask`, `gunicorn`).

### Krok 1: Příprava kódu
Ujistěte se, že máte soubor `Procfile` v kořenovém adresáři:
```text
web: gunicorn app:app --bind 0.0.0.0:$PORT
```
Tento soubor říká serveru, jak aplikaci spustit pomocí produkčního WSGI serveru Gunicorn.

### Krok 2: Vytvoření služby na Render.com
1. Přihlašte se do Render Dashboard.
2. Klikněte na **New +** -> **Web Service**.
3. Propojte svůj GitHub/GitLab repozitář.
4. Nastavte parametry:
   - **Name**: `poll-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Krok 3: Konfigurace proměnných
V sekci **Environment** přidejte:
- `PYTHON_VERSION`: `3.13.0` (volitelné, pro specifikaci verze)
- `SECRET_KEY`: *Váš vygenerovaný tajný klíč*
- `RESET_TOKEN`: *Váš zvolený token pro reset*

### Krok 4: Nasazení a ověření
1. Klikněte na **Create Web Service**.
2. Sledujte logy buildu. Po dokončení uvidíte "Your service is live".
3. Otevřete URL aplikace.
4. **Test po nasazení**:
   - Zkuste zahlasovat.
   - Ověřte, že se zobrazí výsledky.
   - Zkuste resetovat anketu přes `/restart` s vaším novým tokenem.

### Rollback procedura
V případě, že nasazení nové verze způsobí chybu:
1. V Render Dashboard přejděte na záložku **Events** nebo **Deploys**.
2. Najděte poslední funkční nasazení (označené "Live" nebo "Succeeded" před tím aktuálním).
3. Klikněte na menu u daného nasazení a zvolte **Rollback**.
4. Systém okamžitě přepne provoz na předchozí verzi Docker image.
