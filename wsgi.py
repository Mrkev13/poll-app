# wsgi.py — WSGI entry point pro PythonAnywhere
#
# V PythonAnywhere nastav cestu k tomuto souboru v konfiguraci WSGI.
# PythonAnywhere hledá objekt pojmenovaný `application`.

import sys
import os

# Přidej složku projektu do Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application  # noqa: F401
