#!/usr/bin/env python3
"""
Analyse détaillée du contenu d'une page avec extraction complète
"""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def analyze_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fr-FR',
            extra_http_headers={
                'Accept-Language': 'fr-FR,fr;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )
        
        # Anti-détection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = { runtime: {} };
        """)
        
        page = context.new_page()
        
        try:
            logger.info(f"Navigation vers: {url}\n")
            page.goto(url, wait_until='domcontentloaded')
            
            # Attendre Cloudflare
            logger.info("Attente de Cloudflare (10s)...")
            page.wait_for_timeout(10000)
            
            # Hauteur de la page
            page_height = page.evaluate('document.body.scrollHeight')
            logger.info(f"Hauteur totale de la page: {page_height}px\n")
            
            # Capture full page
            page.screenshot(path='screenshots/analysis_full.png', full_page=True)
            logger.info("✅ Capture full page sauvegardée\n")
            
            # Extraire le HTML complet
            html = page.content()
            with open('screenshots/page_html.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info("✅ HTML complet sauvegardé dans screenshots/page_html.html\n")
            
            # Extraire le texte visible
            body_text = page.locator('body').inner_text()
            with open('screenshots/page_text.txt', 'w', encoding='utf-8') as f:
                f.write(body_text)
            logger.info("✅ Texte visible sauvegardé dans screenshots/page_text.txt\n")
            
            logger.info("=== TEXTE DE LA PAGE ===")
            logger.info(body_text)
            logger.info("\n" + "="*60 + "\n")
            
            # Rechercher des éléments spécifiques
            logger.info("=== RECHERCHE D'ÉLÉMENTS ===\n")
            
            # Images
            images = page.locator('img')
            logger.info(f"Images trouvées: {images.count()}")
            for i in range(min(images.count(), 20)):
                img = images.nth(i)
                src = img.get_attribute('src') or ''
                alt = img.get_attribute('alt') or ''
                if src or alt:
                    logger.info(f"  {i+1}. src={src[:80]}, alt={alt}")
            
            logger.info("")
            
            # Inputs
            inputs = page.locator('input')
            logger.info(f"Champs input trouvés: {inputs.count()}")
            for i in range(min(inputs.count(), 20)):
                inp = inputs.nth(i)
                type_ = inp.get_attribute('type') or ''
                name = inp.get_attribute('name') or ''
                id_ = inp.get_attribute('id') or ''
                placeholder = inp.get_attribute('placeholder') or ''
                logger.info(f"  {i+1}. type={type_}, name={name}, id={id_}, placeholder={placeholder}")
            
            logger.info("")
            
            # Boutons
            buttons = page.locator('button, input[type="submit"]')
            logger.info(f"Boutons trouvés: {buttons.count()}")
            for i in range(min(buttons.count(), 20)):
                btn = buttons.nth(i)
                try:
                    text = btn.inner_text().strip()
                    value = btn.get_attribute('value') or ''
                    if text or value:
                        logger.info(f"  {i+1}. text='{text}', value='{value}'")
                except:
                    pass
            
            logger.info("")
            
            # Liens
            links = page.locator('a')
            logger.info(f"Liens trouvés: {links.count()}")
            for i in range(min(links.count(), 10)):
                link = links.nth(i)
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href') or ''
                    if text:
                        logger.info(f"  {i+1}. '{text}' -> {href[:60]}")
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
        finally:
            browser.close()


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else os.getenv('PAGE_1_URL')
    if not url:
        print("Usage: python analyze_page.py <URL>")
        sys.exit(1)
    analyze_page(url)
