"""
Sube el sitemap generado a Google Search Console.
Requiere credenciales de Google (service account).
"""

import os
import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ─── Configuración ────────────────────────────────────────────────────────────

SITE_URL = "https://www.cbimpactopro.com/"   # Con barra al final, tal como está en Search Console
SITEMAP_URL = "https://raw.githubusercontent.com/opapi/cbimpactopro-sitemap/main/sitemap_properties.xml"
# IMPORTANTE: reemplazá {TU_USUARIO} y {TU_REPO} con tus datos reales de GitHub

SCOPES = ["https://www.googleapis.com/auth/webmasters"]

# ─── Funciones ────────────────────────────────────────────────────────────────

def get_service():
    """
    Crea el cliente de Google Search Console usando las credenciales
    del Service Account (guardadas como secreto en GitHub Actions).
    """
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not credentials_json:
        print("❌ Error: no se encontró la variable de entorno GOOGLE_CREDENTIALS")
        sys.exit(1)

    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES,
    )
    return build("searchconsole", "v1", credentials=credentials)


def submit_sitemap(service):
    """Envía el sitemap a Google Search Console."""
    print(f"📤 Enviando sitemap a Google Search Console...")
    print(f"   Sitio:   {SITE_URL}")
    print(f"   Sitemap: {SITEMAP_URL}")

    service.sitemaps().submit(
        siteUrl=SITE_URL,
        feedpath=SITEMAP_URL,
    ).execute()

    print("✅ Sitemap enviado correctamente.")


def main():
    service = get_service()
    submit_sitemap(service)


if __name__ == "__main__":
    main()
