#!/usr/bin/env python3
"""
Scanner simplifié - Une seule page
"""
import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from captcha_solver import CaptchaSolver

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SimpleRDVScanner:
    """Scanner simplifié pour une seule page"""
    
    def __init__(self):
        load_dotenv()
        # Utiliser seulement PAGE_1_URL
        self.url = os.getenv('PAGE_1_URL')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        
        if not self.url:
            raise ValueError("PAGE_1_URL doit être configuré dans .env")
        
        self.captcha_solver = CaptchaSolver()
        logger.info(f"Scanner configuré pour: {self.url}")
    
    def check_page(self):
        """Vérification simplifiée d'une seule page"""
        logger.info("🚀 Démarrage du scan simplifié")
        logger.info(f"📍 URL: {self.url}")
        
        with sync_playwright() as p:
            # Lancer le navigateur
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            try:
                # 1. Navigation
                logger.info("📂 Navigation vers la page...")
                page.goto(self.url, wait_until='domcontentloaded', timeout=30000)
                logger.info("✅ Page chargée")
                
                # 3. Capture initiale
                os.makedirs('screenshots', exist_ok=True)
                screenshot_path = f"screenshots/simple_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Capture: {screenshot_path}")
                
                # 4. Vérifier si bloqué par Cloudflare
                body_text = page.locator('body').inner_text().lower()
                if 'sorry, you have been blocked' in body_text or 'cloudflare' in body_text:
                    logger.error("❌ Bloqué par Cloudflare")
                    logger.info("💡 Solution: Attendez 10-15 min ou changez d'IP (WiFi -> 4G)")
                    return False
                
                # 5. Scroll pour révéler le contenu
                page.evaluate('window.scrollBy(0, 500)')
                page.wait_for_timeout(500)  # Juste pour que le scroll se termine
                
                # 6. Gérer le captcha
                if self.handle_captcha(page):
                    logger.info("✅ Captcha géré avec succès")
                    
                    # 7. Attendre la réponse
                    page.wait_for_timeout(5000)
                    
                    # 8. Vérifier à nouveau si bloqué
                    current_text = page.locator('body').inner_text().lower()
                    if 'sorry, you have been blocked' in current_text:
                        logger.error("❌ Bloqué par Cloudflare après captcha")
                        return False
                    
                    # 9. Analyser la disponibilité
                    is_available = self.analyze_availability(page)
                    
                    # 10. Capture finale
                    final_screenshot = f"screenshots/simple_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=final_screenshot, full_page=True)
                    logger.info(f"📸 Capture finale: {final_screenshot}")
                    
                    return is_available
                else:
                    logger.error("❌ Échec de résolution du captcha")
                    return False
                    
            except Exception as e:
                logger.error(f"Erreur: {e}", exc_info=True)
                return False
                
            finally:
                browser.close()
    
    def handle_captcha(self, page):
        """Gestion simplifiée du captcha"""
        try:
            # Chercher le champ captcha
            captcha_field = page.locator('input[name*="captcha" i], input[id*="captcha" i]').first
            
            if not captcha_field.is_visible():
                logger.info("ℹ️ Pas de captcha détecté")
                return True
            
            logger.info("🔍 Captcha détecté")
            
            # Chercher l'image du captcha
            captcha_img = page.locator('.captcha img, img[src*="captcha"]').first
            
            if captcha_img.is_visible():
                # Sauvegarder l'image
                screenshot_path = "screenshots/captcha_simple.png"
                captcha_img.screenshot(path=screenshot_path)
                logger.info(f"📸 Captcha sauvegardé: {screenshot_path}")
                
                # Résoudre avec le solver
                result = self.captcha_solver.solve_prefecture_captcha(page)
                
                if result:
                    logger.info("✅ Captcha résolu")
                    
                    # Chercher et cliquer le bouton de validation
                    submit_btn = page.locator('button[type="submit"], button[formaction*="valider"]').first
                    if submit_btn.is_visible():
                        submit_btn.click()
                        logger.info("🔘 Bouton de validation cliqué")
                        page.wait_for_timeout(3000)
                        return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur captcha: {e}")
            return False
    
    def analyze_availability(self, page):
        """Analyse simplifiée de la disponibilité"""
        try:
            body_text = page.locator('body').inner_text().lower()
            
            # Messages d'indisponibilité
            unavailable_keywords = [
                'aucun créneau disponible',
                'aucune disponibilité',
                'pas de rendez-vous disponible',
                'complet',
                'indisponible'
            ]
            
            # Messages de disponibilité
            available_keywords = [
                'choisissez votre créneau',
                'sélectionnez un créneau',
                'créneau disponible',
                'places disponibles',
                'choisir un lieu'
            ]
            
            logger.info(f"📄 Extrait du contenu: {body_text[:200]}...")
            
            # Vérifier indisponibilité
            for keyword in unavailable_keywords:
                if keyword in body_text:
                    logger.info(f"❌ Indisponible: '{keyword}'")
                    return False
            
            # Vérifier disponibilité
            for keyword in available_keywords:
                if keyword in body_text:
                    logger.info(f"✅ Disponible: '{keyword}'")
                    return True
            
            # Chercher des boutons de réservation
            booking_buttons = page.locator('button, a').filter(has_text=['Réserver', 'Choisir', 'Sélectionner'])
            if booking_buttons.count() > 0:
                logger.info(f"✅ Boutons de réservation trouvés: {booking_buttons.count()}")
                return True
            
            logger.info("⚠️ Aucun indicateur clair")
            return False
            
        except Exception as e:
            logger.error(f"Erreur analyse: {e}")
            return False


def main():
    """Point d'entrée"""
    try:
        scanner = SimpleRDVScanner()
        result = scanner.check_page()
        
        if result:
            logger.info("🎉 RENDEZ-VOUS DISPONIBLE!")
        else:
            logger.info("😔 Pas de rendez-vous disponible")
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()