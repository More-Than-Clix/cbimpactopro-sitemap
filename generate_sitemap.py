"""
Sitemap generator para cbimpactopro.com
Usa Playwright para navegar el sitio con scroll real,
descubrir todas las fichas /p/... y generar un sitemap XML.
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

# ─── Configuración ────────────────────────────────────────────────────────────

BASE_URL = "https://www.cbimpactopro.com"

# Páginas de listado donde están las fichas con scroll infinito
LISTING_PAGES = [
    "https://www.cbimpactopro.com/propiedades",   # Ajustá esta URL si es diferente
    # Agregá más páginas de listado si las hay (por tipo, zona, etc.)
]

# Prefijo que identifica las fichas de propiedades
PROPERTY_PREFIX = "/p/"

# Cuántas veces hacer scroll en cada página de listado
# Aumentá este número si tenés muchas propiedades
MAX_SCROLLS = 50

# Segundos de espera entre cada scroll (para que cargue el contenido)
SCROLL_WAIT = 2.0

OUTPUT_FILE = "sitemap_properties.xml"

# ─── Funciones ────────────────────────────────────────────────────────────────

async def scroll_and_collect(page, url: str) -> set[str]:
    """
    Navega a una página, hace scroll infinito hacia abajo
    y recolecta todos los links de fichas de propiedades.
    """
    print(f"\n🔍 Explorando: {url}")
    await page.goto(url, wait_until="networkidle", timeout=60000)

    found_urls = set()
    previous_count = 0

    for i in range(MAX_SCROLLS):
        # Extraer todos los links actuales de la página
        links = await page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(el => el.getAttribute('href'))"
        )

        for href in links:
            if href and PROPERTY_PREFIX in href:
                full_url = urljoin(BASE_URL, href)
                # Limpiar parámetros de tracking si los hay
                parsed = urlparse(full_url)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                found_urls.add(clean_url)

        current_count = len(found_urls)
        print(f"  Scroll {i+1}/{MAX_SCROLLS} — fichas encontradas: {current_count}")

        # Si ya no aparecen nuevas URLs después del scroll, terminamos
        if i > 2 and current_count == previous_count:
            print(f"  ✅ No hay más contenido nuevo. Terminando scroll.")
            break

        previous_count = current_count

        # Hacer scroll hasta el final de la página
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_WAIT)

    print(f"  📦 Total fichas en esta página: {len(found_urls)}")
    return found_urls


def generate_xml(all_urls: set[str]) -> str:
    """
    Genera el contenido XML del sitemap a partir de un conjunto de URLs.
    """
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for url in sorted(all_urls):
        url_elem = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_elem, "loc")
        loc.text = url
        lastmod = ET.SubElement(url_elem, "lastmod")
        lastmod.text = today
        changefreq = ET.SubElement(url_elem, "changefreq")
        changefreq.text = "weekly"
        priority = ET.SubElement(url_elem, "priority")
        priority.text = "0.8"

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)


async def main():
    all_property_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        for listing_url in LISTING_PAGES:
            urls = await scroll_and_collect(page, listing_url)
            all_property_urls.update(urls)

        await browser.close()

    print(f"\n✅ Total de fichas únicas encontradas: {len(all_property_urls)}")

    if not all_property_urls:
        print("⚠️  No se encontraron fichas. Verificá la URL de listado en LISTING_PAGES.")
        return

    xml_content = generate_xml(all_property_urls)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"📄 Sitemap guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
