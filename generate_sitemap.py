"""
Sitemap generator para cbimpactopro.com
- Rastrea el sitio completo para páginas estáticas
- Usa scroll infinito en /Propiedades para capturar todas las fichas
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

# ─── Configuración ────────────────────────────────────────────────────────────

BASE_URL = "https://www.cbimpactopro.com"

# Página de listado con scroll infinito
LISTING_URL = "https://www.cbimpactopro.com/Propiedades"

# Prefijo de fichas de propiedades
PROPERTY_PREFIX = "/p/"

# Cuántas veces hacer scroll (aumentar si no aparecen todas las fichas)
MAX_SCROLLS = 80

# Segundos de espera entre cada scroll
SCROLL_WAIT = 2.5

OUTPUT_FILE = "sitemap_properties.xml"

# URLs a excluir del sitemap general (ajustar si es necesario)
EXCLUDE_PATTERNS = [
    "/api/",
    "?",
    "#",
    "javascript:",
    "mailto:",
    ".pdf",
    ".jpg",
    ".png",
    ".gif",
]

# ─── Funciones ────────────────────────────────────────────────────────────────

def is_internal(url: str) -> bool:
    """Verifica que la URL pertenece al dominio cbimpactopro.com"""
    parsed = urlparse(url)
    return parsed.netloc in ("www.cbimpactopro.com", "cbimpactopro.com", "")

def should_exclude(url: str) -> bool:
    """Verifica si la URL debe ser excluida"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in url:
            return True
    return False

def clean_url(url: str) -> str:
    """Elimina fragmentos y parámetros de tracking"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


async def crawl_site(page) -> set[str]:
    """
    Rastreo estático del sitio completo siguiendo links.
    Descubre páginas estáticas (home, contacto, zonas, etc.)
    """
    print("\n🌐 Rastreando sitio completo...")
    visited = set()
    to_visit = {BASE_URL}

    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => el.href)"
            )
            for link in links:
                c = clean_url(link)
                if (
                    c
                    and c not in visited
                    and is_internal(c)
                    and not should_exclude(c)
                    and PROPERTY_PREFIX not in c  # las fichas las manejamos aparte
                ):
                    to_visit.add(c)

            print(f"  ✓ {url} ({len(visited)} visitadas, {len(to_visit)} pendientes)")

        except Exception as e:
            print(f"  ⚠️  Error en {url}: {e}")

    print(f"  📦 Páginas estáticas encontradas: {len(visited)}")
    return visited


async def scroll_and_collect(page) -> set[str]:
    """
    Navega a /Propiedades y hace scroll infinito para
    descubrir todas las fichas /p/...
    """
    print(f"\n🔍 Explorando fichas con scroll: {LISTING_URL}")
    await page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(3)  # esperar que cargue el contenido inicial

    found_urls = set()
    previous_count = 0
    no_new_count = 0

    for i in range(MAX_SCROLLS):
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(el => el.href)"
        )
        for link in links:
            if PROPERTY_PREFIX in link:
                found_urls.add(clean_url(link))

        current_count = len(found_urls)
        print(f"  Scroll {i+1}/{MAX_SCROLLS} — fichas encontradas: {current_count}")

        if current_count == previous_count:
            no_new_count += 1
            if no_new_count >= 3:
                print("  ✅ No hay más contenido nuevo. Terminando scroll.")
                break
        else:
            no_new_count = 0

        previous_count = current_count

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_WAIT)

    print(f"  📦 Total fichas encontradas: {len(found_urls)}")
    return found_urls


def generate_xml(static_urls: set[str], property_urls: set[str]) -> str:
    """
    Genera el sitemap XML combinando páginas estáticas y fichas.
    """
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Páginas estáticas — alta prioridad
    for url in sorted(static_urls):
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = url
        ET.SubElement(url_elem, "lastmod").text = today
        ET.SubElement(url_elem, "changefreq").text = "weekly"
        ET.SubElement(url_elem, "priority").text = "0.9"

    # Fichas de propiedades
    for url in sorted(property_urls):
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = url
        ET.SubElement(url_elem, "lastmod").text = today
        ET.SubElement(url_elem, "changefreq").text = "weekly"
        ET.SubElement(url_elem, "priority").text = "0.8"

    ET.indent(ET.ElementTree(urlset), space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)


async def main():
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

        static_urls = await crawl_site(page)
        property_urls = await scroll_and_collect(page)

        await browser.close()

    all_count = len(static_urls) + len(property_urls)
    print(f"\n✅ Total URLs en sitemap: {all_count}")
    print(f"   Páginas estáticas: {len(static_urls)}")
    print(f"   Fichas de propiedades: {len(property_urls)}")

    if all_count == 0:
        print("⚠️  No se encontraron URLs.")
        return

    xml_content = generate_xml(static_urls, property_urls)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"📄 Sitemap guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
