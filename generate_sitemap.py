import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

BASE_URL = "https://www.cbimpactopro.com"

# URL de búsqueda con todos los resultados (sin filtros de tipo/zona)
# operation=1,2 = Venta + Alquiler, o=2,2 = orden por última actualización
LISTING_URL = "https://www.cbimpactopro.com/Buscar?operation=1,2&o=2,2&1=1"

PROPERTY_PREFIX = "/p/"
MAX_SCROLLS = 100
SCROLL_WAIT = 3.0
OUTPUT_FILE = "sitemap_properties.xml"

EXCLUDE_PATTERNS = ["/api/", "?", "#", "javascript:", "mailto:",
                    ".pdf", ".jpg", ".png", ".gif", "/Buscar", "/Favoritos"]

def is_internal(url):
    parsed = urlparse(url)
    return parsed.netloc in ("www.cbimpactopro.com", "cbimpactopro.com", "")

def should_exclude(url):
    return any(p in url for p in EXCLUDE_PATTERNS)

def clean_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

async def crawl_site(page):
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
                "a[href]", "els => els.map(el => el.href)"
            )
            for link in links:
                c = clean_url(link)
                if (c and c not in visited and is_internal(c)
                        and not should_exclude(c) and PROPERTY_PREFIX not in c):
                    to_visit.add(c)
            print(f"  ✓ {url} ({len(visited)} visitadas, {len(to_visit)} pendientes)")
        except Exception as e:
            print(f"  ⚠️  Error en {url}: {e}")

    print(f"  📦 Páginas estáticas encontradas: {len(visited)}")
    return visited

async def collect_properties(page):
    print(f"\n🔍 Recolectando fichas desde: {LISTING_URL}")
    await page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(4)

    found_urls = set()
    previous_count = 0
    no_new_count = 0

    for i in range(MAX_SCROLLS):
        # Buscar links de fichas en el contenedor de resultados
        links = await page.eval_on_selector_all(
            "#propiedades a[href], .results-area a[href]",
            "els => els.map(el => el.href)"
        )
        for link in links:
            if PROPERTY_PREFIX in link:
                found_urls.add(clean_url(link))

        current_count = len(found_urls)
        print(f"  Scroll {i+1}/{MAX_SCROLLS} — fichas: {current_count}")

        if current_count == previous_count:
            no_new_count += 1
            if no_new_count >= 4:
                print("  ✅ No hay más fichas nuevas. Terminando.")
                break
        else:
            no_new_count = 0

        previous_count = current_count

        # Scroll al final del contenedor de resultados
        await page.evaluate("""
            const el = document.querySelector('.results-area') || document.body;
            el.scrollTo(0, el.scrollHeight);
            window.scrollTo(0, document.body.scrollHeight);
        """)
        await asyncio.sleep(SCROLL_WAIT)

    print(f"  📦 Total fichas: {len(found_urls)}")
    return found_urls

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
        ET.SubElement(u, "priori
