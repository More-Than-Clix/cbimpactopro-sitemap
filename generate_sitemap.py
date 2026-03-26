import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse
import urllib.request
import urllib.parse
import json
import re

BASE_URL = "https://www.cbimpactopro.com"
PROPERTY_PREFIX = "/p/"
OUTPUT_FILE = "sitemap_properties.xml"

STATIC_PAGES = [
    "https://www.cbimpactopro.com",
    "https://www.cbimpactopro.com/Propiedades",
    "https://www.cbimpactopro.com/Venta",
    "https://www.cbimpactopro.com/Alquiler",
    "https://www.cbimpactopro.com/Emprendimientos",
    "https://www.cbimpactopro.com/Tasacion",
    "https://www.cbimpactopro.com/Contacto",
    "https://www.cbimpactopro.com/s/Nuestro-equipo",
    "https://www.cbimpactopro.com/s/Nuestros-Tours-Virtuales-Inmobiliarios",
    "https://www.cbimpactopro.com/s/Terminos-y-Privacidad",
]

SEARCH_URL = (
    "https://www.cbimpactopro.com/Buscar"
    "?q=&currency=ANY&min-price=&max-price="
    "&min-roofed=&max-roofed=&min-surface=&max-surface="
    "&min-total_surface=&max-total_surface="
    "&min-front_measure=&max-front_measure="
    "&min-depth_measure=&max-depth_measure="
    "&age=&min-age=&max-age=&suites=&rooms="
    "&credit_eligible=&is_exclusive=&tags="
    "&operation=1,2&locations=&location_type=&ptypes="
    "&o=2,2&watermark=&p={page}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.cbimpactopro.com/Buscar?operation=1,2&o=2,2&1=1",
}

def fetch_page(page_num):
    url = SEARCH_URL.format(page=page_num)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def extract_property_urls(html):
    pattern = r'href="(/p/[^"]+)"'
    matches = re.findall(pattern, html)
    urls = set()
    for m in matches:
        full = f"https://www.cbimpactopro.com{m}"
        parsed = urlparse(full)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        urls.add(clean)
    return urls

def collect_properties():
    print("\n Recolectando fichas via API paginada...")
    all_urls = set()
    page = 1

    while True:
        print(f"  Pagina {page}...", end=" ")
        try:
            html = fetch_page(page)
            urls = extract_property_urls(html)
            print(f"{len(urls)} fichas encontradas")

            if not urls:
                print(f"  Pagina {page} vacia. Terminando.")
                break

            # Si todas las URLs ya las tenemos, terminamos
            new_urls = urls - all_urls
            if not new_urls and page > 1:
                print(f"  Sin fichas nuevas. Terminando.")
                break

            all_urls.update(urls)
            page += 1

        except Exception as e:
            print(f"  Error en pagina {page}: {e}")
            break

    print(f"  Total fichas unicas: {len(all_urls)}")
    return all_urls

def generate_xml(static_urls, property_urls):
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for url in sorted(static_urls):
        u = ET.SubElement(urlset, "url")
        ET.SubElement(u, "loc").text = url
        ET.SubElement(u, "lastmod").text = today
        ET.SubElement(u, "changefreq").text = "weekly"
        ET.SubElement(u, "priority").text = "0.9"
    for url in sorted(property_urls):
        u = ET.SubElement(urlset, "url")
        ET.SubElement(u, "loc").text = url
        ET.SubElement(u, "lastmod").text = today
        ET.SubElement(u, "changefreq").text = "weekly"
        ET.SubElement(u, "priority").text = "0.8"
    ET.indent(ET.ElementTree(urlset), space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)

def main():
    static_urls = set(STATIC_PAGES)
    print(f" Paginas estaticas: {len(static_urls)}")

    property_urls = collect_properties()

    total = len(static_urls) + len(property_urls)
    print(f"\nTotal URLs: {total}")
    print(f"  Estaticas: {len(static_urls)}")
    print(f"  Fichas: {len(property_urls)}")

    if total == 0:
        print("No se encontraron URLs.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(generate_xml(static_urls, property_urls))
    print(f"Sitemap guardado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
