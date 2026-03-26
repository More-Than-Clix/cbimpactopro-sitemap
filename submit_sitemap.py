"""
Notifica a Google y Bing que el sitemap fue actualizado.
Usa ping directo, sin necesidad de credenciales.
"""

import urllib.request
import urllib.parse
import sys

SITEMAP_URL = "https://raw.githubusercontent.com/opapi/cbimpactopro-sitemap/main/sitemap_properties.xml"

def ping(name, url):
    try:
        urllib.request.urlopen(url, timeout=15)
        print(f"✅ {name} notificado correctamente.")
    except Exception as e:
        print(f"⚠️  {name}: {e}")

def main():
    encoded = urllib.parse.quote(SITEMAP_URL, safe="")
    print(f"📤 Notificando buscadores sobre el sitemap actualizado...")
    print(f"   Sitemap: {SITEMAP_URL}\n")

    ping("Google", f"https://www.google.com/ping?sitemap={encoded}")
    ping("Bing",   f"https://www.bing.com/ping?sitemap={encoded}")

    print("\n✅ Listo.")

if __name__ == "__main__":
    main()
