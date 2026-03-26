import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.async_api import async_playwright

BASE_URL = "https://www.cbimpactopro.com"
LISTING_URL = "https://www.cbimpactopro.com/Buscar?operation=1,2&o=2,2&1=1"
PROPERTY_PREFIX = "/p/"
MAX_SCROLLS = 100
SCROLL_WAIT = 3.0
OUTPUT_FILE = "sitemap_properties.xml"
EXCLUDE_PATTERNS = ["/api/", "?", "#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif", "/Buscar", "/Favoritos"]

def is_internal(url):
    parsed = urlparse(url)
    return parsed.netloc in ("www.cbimpactopro.com", "cbimpactopro.com", "")

def should_exclude(url):
    return any(p in url for p in EXCLUDE_PATTERNS)

def clean_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

async def crawl_site(page):
    print("\n Rastreando sitio completo...")
    visited = set()
    to_visit = {BASE_URL}
    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            links = await page.eval_on_selector_all("a[href]", "els => els.map(el => el.href)")
            for link in links:
                c = clean_url(link)
                if c and c not in visited and is_internal(c) and not should_exclude(c) and PROPERTY_PREFIX not in c:
                    to_visit.add(c)
            print(f"  OK {url} ({len(visited)} visitadas, {len(to_visit)} pendientes)")
        except Exception as e:
            print(f"  ERROR {url}: {e}")
    print(f"  Paginas estaticas: {len(visited)}")
    return visited

async def collect_properties(page):
    print(f"\n Recolectando fichas desde: {LISTING_URL}")
    await page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        await page.wait_for_selector("#propiedades", timeout=20000)
        print("  Contenedor de fichas detectado.")
    except Exception:
        print("  Advertencia: contenedor #propiedades no detectado, continuando igual.")
    await asyncio.sleep(5)
    
    # DIAGNOSTICO - mostrar HTML que ve el crawler
    html = await page.content()
    tiene_propiedades = "#propiedades" in html or "prop-id" in html
    tiene_buscar = "/Buscar" in html
    print(f"  HTML recibido: {len(html)} caracteres")
    print(f"  Contiene prop-id: {tiene_propiedades}")
    print(f"  Contiene /Buscar: {tiene_buscar}")
    url_actual = page.url
    print(f"  URL actual despues de cargar: {url_actual}")
    
    found_urls = set()
    previous_count = 0
    no_new_count = 0
    for i in range(MAX_SCROLLS):
        links = await page.eval_on_selector_all(
            "#propiedades a[href], .results-area a[href]",
            "els => els.map(el => el.href)"
        )
        for link in links:
            if PROPERTY_PREFIX in link:
                found_urls.add(clean_url(link))
        current_count = len(found_urls)
        print(f"  Scroll {i+1}/{MAX_SCROLLS} - fichas: {current_count}")
        if current_count == previous_count:
            no_new_count += 1
            if no_new_count >= 4:
                print("  No hay mas fichas nuevas. Terminando.")
                break
        else:
            no_new_count = 0
        previous_count = current_count
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_WAIT)
    print(f"  Total fichas: {len(found_urls)}")
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
        ET.SubElement(u, "priority").text = "0.8"
    ET.indent(ET.ElementTree(urlset), space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        static_urls = await crawl_site(page)
        property_urls = await collect_properties(page)
        await browser.close()
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
    asyncio.run(main())
