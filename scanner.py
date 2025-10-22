#!/usr/bin/env python3
"""
Scanner automatisé de disponibilité de rendez-vous avec résolution de captcha
"""
import os
import sys
import time
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser
from captcha_solver import CaptchaSolver
from notifier import Notifier
from prefecture_analyzer import PrefectureAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RDVScanner:
    """Scanner de disponibilité de rendez-vous"""
    
    def __init__(self):
        load_dotenv()
        self.page_1_url = os.getenv('PAGE_1_URL')
        self.page_2_url = os.getenv('PAGE_2_URL')
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        
        # Validation de la configuration
        if not self.page_1_url or not self.page_2_url:
            raise ValueError("Les URLs PAGE_1_URL et PAGE_2_URL doivent être configurées dans .env")
        
        self.captcha_solver = CaptchaSolver()
        self.notifier = Notifier()
        self.prefecture_analyzer = PrefectureAnalyzer()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def start_browser(self, playwright):
        """Démarre le navigateur"""
        if not self.headless:
            logger.info("🖥️ Mode avec interface (recommandé pour contourner Cloudflare)")
        else:
            logger.info("Démarrage du navigateur en mode headless...")
        
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fr-FR',
            timezone_id='Europe/Paris',
            extra_http_headers={
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        )
        
        # Inject scripts pour masquer l'automatisation
        context.add_init_script("""
            // Remplacer webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Remplacer les plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Remplacer les langues
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en'],
            });
            
            // Chrome runtime
            window.chrome = { runtime: {} };
            
            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        self.page = context.new_page()
        logger.info("Navigateur démarré avec succès")
    
    def check_page(self, url: str, page_name: str) -> Dict[str, Any]:
        """
        Vérifie la disponibilité sur une page
        
        Args:
            url: URL de la page à vérifier
            page_name: Nom de la page pour les logs
            
        Returns:
            Dict contenant le statut et les informations de disponibilité
        """
        logger.info(f"Vérification de {page_name}: {url}")
        result = {
            'page': page_name,
            'url': url,
            'available': False,
            'message': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Utiliser la page existante pour éviter les problèmes de contexte
            # Juste naviguer vers une page vide pour "nettoyer" l'état
            self.page.goto('about:blank')
            self.page.wait_for_timeout(1000)
            
            # Navigation vers la page
            self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            logger.info(f"Page {page_name} chargée")
            
            # Attendre Cloudflare (important!)
            logger.info("Attente de passage Cloudflare...")
            self.page.wait_for_timeout(15000)  # Augmenté à 15 secondes
            
            # Vérifier si on est bloqué par Cloudflare
            body_text = self.page.locator('body').inner_text().lower()
            if 'cloudflare' in body_text or 'you have been blocked' in body_text or 'sorry, you have been blocked' in body_text:
                logger.warning(f"{page_name}: Détection de protection Cloudflare")
                # Attendre plus longtemps pour Cloudflare
                logger.info("Attente étendue pour contournement Cloudflare (30s)...")
                self.page.wait_for_timeout(30000)  # Attendre 30 secondes
                
                # Vérifier à nouveau
                body_text = self.page.locator('body').inner_text().lower()
                if 'cloudflare' in body_text or 'you have been blocked' in body_text or 'sorry, you have been blocked' in body_text:
                    result['message'] = "Bloqué par Cloudflare - IP peut-être temporairement limitée"
                    logger.error(f"{page_name}: {result['message']}")
                    logger.info("Conseil: Attendez quelques minutes et relancez, ou changez d'IP (WiFi -> 4G)")
                    # Capturer pour debug
                    self.page.screenshot(path=f"screenshots/{page_name.lower().replace(' ', '_')}_cloudflare_blocked.png", full_page=True)
                    return result
                else:
                    logger.info(f"{page_name}: Cloudflare contourné avec succès")
            
            # Attendre un peu plus pour que la page se charge complètement
            self.page.wait_for_timeout(2000)
            
            # Prendre une capture d'écran initiale complète
            screenshot_path = f"screenshots/{page_name.lower().replace(' ', '_')}_initial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs('screenshots', exist_ok=True)
            self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Capture initiale: {screenshot_path}")
            
            # Scroll pour révéler tout le contenu (notamment le captcha)
            self.page.evaluate('window.scrollBy(0, 500)')
            self.page.wait_for_timeout(1000)
            
            # Vérifier s'il y a un captcha (APRÈS le scroll)
            captcha_solved = self.handle_captcha()
            if not captcha_solved:
                result['message'] = "Échec de résolution du captcha"
                logger.warning(f"{page_name}: {result['message']}")
                return result
            
            # Attendre et analyser la réponse après validation
            logger.info("⏳ Attente de la réponse après validation du captcha...")
            
            # Attendre un peu pour voir la réponse
            self.page.wait_for_timeout(5000)
            
            # Vérifier si on est bloqué par Cloudflare APRÈS le captcha
            current_text = self.page.locator('body').inner_text().lower()
            if 'sorry, you have been blocked' in current_text or 'cloudflare' in current_text:
                logger.warning(f"{page_name}: Cloudflare bloque après validation du captcha")
                result['message'] = "Bloqué par Cloudflare après captcha - nécessite attente ou changement d'IP"
                logger.info("💡 Solution: Attendez 10-15 minutes ou changez d'IP (WiFi -> 4G)")
                return result
            
            # Pour les préfectures, tenter d'attendre la redirection
            if 'rdv-prefecture.interieur.gouv.fr' in url:
                try:
                    # Attendre soit la page creneau, soit un message d'erreur
                    self.page.wait_for_url('**/creneau/**', timeout=10000)
                    logger.info(f"✅ Redirection réussie vers: {self.page.url}")
                except Exception as e:
                    logger.info(f"ℹ️ Pas de redirection immédiate vers /creneau/ : {e}")
                    # Vérifier si on a une erreur de captcha
                    if 'error=invalidCaptcha' in self.page.url:
                        logger.warning("❌ Captcha invalide détecté")
                        result['message'] = "Captcha invalide - Gemini a peut-être mal lu l'image"
                        return result
                    # Attendre quand même un peu plus
                    self.page.wait_for_timeout(3000)
            
            # Prendre une capture après validation du captcha
            screenshot_after = f"screenshots/{page_name.lower().replace(' ', '_')}_after_captcha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.page.screenshot(path=screenshot_after, full_page=True)
            logger.info(f"Capture après captcha: {screenshot_after}")
            
            # Gestion spécifique pour les pages préfecture
            if 'rdv-prefecture.interieur.gouv.fr' in self.page.url:
                # Analyser la page CGU
                cgu_info = self.prefecture_analyzer.analyze_cgu_page(self.page)
                
                if cgu_info['has_accept_button']:
                    logger.info("Page CGU détectée, clic sur accepter...")
                    if self.prefecture_analyzer.click_accept_and_continue(self.page):
                        # Attendre que la page de calendrier se charge
                        self.page.wait_for_timeout(3000)
                        
                        # Vérifier le captcha sur la nouvelle page
                        captcha_solved = self.handle_captcha()
                        if not captcha_solved:
                            result['message'] = "Échec de résolution du captcha après CGU"
                            logger.warning(f"{page_name}: {result['message']}")
                            return result
                        
                        self.page.wait_for_timeout(2000)
            
            # Analyser le contenu de la page pour debug
            page_content = self.page.locator('body').inner_text()
            content_excerpt = page_content[:200] if page_content else "Contenu vide"
            logger.info(f"📄 Analyse du contenu de la page (extrait): {content_excerpt.lower()}")
            
            # Rechercher des indicateurs de disponibilité
            if 'rdv-prefecture.interieur.gouv.fr' in self.page.url:
                availability_info = self.prefecture_analyzer.check_calendar_availability(self.page)
            else:
                availability_info = self.check_availability()
            
            result['available'] = availability_info['available']
            result['message'] = availability_info['message']
            result['details'] = availability_info.get('details', {})
            
            if result['available']:
                logger.info(f"✅ {page_name}: Rendez-vous disponible!")
            else:
                logger.info(f"❌ {page_name}: Pas de rendez-vous disponible")
            
        except Exception as e:
            result['message'] = f"Erreur: {str(e)}"
            logger.error(f"Erreur lors de la vérification de {page_name}: {e}", exc_info=True)
        
        return result
    
    def handle_captcha(self) -> bool:
        """
        Détecte et résout les captchas sur la page
        
        Returns:
            True si le captcha est résolu ou absent, False sinon
        """
        try:
            # Scroll pour voir tout le contenu
            self.page.evaluate('window.scrollBy(0, 500)')
            self.page.wait_for_timeout(500)
            
            # Rechercher les types de captcha courants
            # reCAPTCHA v2
            if self.page.locator('iframe[src*="recaptcha"]').count() > 0:
                logger.info("reCAPTCHA v2 détecté")
                return self.captcha_solver.solve_recaptcha_v2(self.page)
            
            # reCAPTCHA v3 (invisible)
            if self.page.locator('.grecaptcha-badge').count() > 0:
                logger.info("reCAPTCHA v3 détecté")
                # reCAPTCHA v3 est généralement automatique
                self.page.wait_for_timeout(3000)
                return True
            
            # hCaptcha
            if self.page.locator('iframe[src*="hcaptcha"]').count() > 0:
                logger.info("hCaptcha détecté")
                return self.captcha_solver.solve_hcaptcha(self.page)
            
            # Captcha préfecture (image avec calcul mathématique)
            if 'rdv-prefecture.interieur.gouv.fr' in self.page.url:
                # Chercher le champ captcha spécifique
                if self.page.locator('input[name="captchaUsercode"], input[id*="captcha" i]').count() > 0:
                    logger.info("Captcha préfecture détecté (champ captchaUsercode trouvé)")
                    return self.captcha_solver.solve_prefecture_captcha(self.page)
                # Ou chercher une image de captcha
                elif self.page.locator('img[alt*="captcha" i], img[src*="captcha" i], img[id*="captcha" i]').count() > 0:
                    logger.info("Captcha préfecture détecté (image captcha)")
                    return self.captcha_solver.solve_prefecture_captcha(self.page)
            
            # Image captcha personnalisé générique
            if self.page.locator('img[alt*="captcha" i]').count() > 0 or \
               self.page.locator('img[src*="captcha" i]').count() > 0:
                logger.info("Captcha image détecté")
                return self.captcha_solver.solve_image_captcha(self.page)
            
            # Pas de captcha détecté
            logger.info("Aucun captcha détecté")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion du captcha: {e}", exc_info=True)
            return False
    
    def check_availability(self) -> Dict[str, Any]:
        """
        Vérifie la disponibilité de rendez-vous sur la page actuelle
        
        Returns:
            Dict avec les informations de disponibilité
        """
        result = {
            'available': False,
            'message': 'Vérification en cours...',
            'details': {}
        }
        
        try:
            # Prendre une capture d'écran pour analyse
            screenshot_path = f"screenshots/page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs('screenshots', exist_ok=True)
            self.page.screenshot(path=screenshot_path)
            logger.info(f"Capture d'écran sauvegardée: {screenshot_path}")
            
            # Récupérer le texte de la page
            body_text = self.page.locator('body').inner_text().lower()
            
            # Mots-clés indiquant une disponibilité
            availability_keywords = [
                'disponible', 'available', 'réserver', 'book',
                'choisir un créneau', 'select a slot', 'prendre rendez-vous'
            ]
            
            # Mots-clés indiquant une indisponibilité
            unavailability_keywords = [
                'aucun créneau', 'no slots', 'complet', 'full',
                'indisponible', 'unavailable', 'aucune disponibilité'
            ]
            
            # Vérifier la présence de boutons/liens de réservation
            booking_buttons = self.page.locator('button, a').filter(
                has_text=['Réserver', 'Book', 'Choisir', 'Select', 'Prendre RDV']
            )
            
            if booking_buttons.count() > 0:
                result['available'] = True
                result['message'] = f"Boutons de réservation trouvés ({booking_buttons.count()})"
                result['details']['button_count'] = booking_buttons.count()
            
            # Vérifier les calendriers/sélecteurs de date
            date_selectors = self.page.locator('input[type="date"], .calendar, .datepicker').count()
            if date_selectors > 0:
                result['details']['date_selectors'] = date_selectors
            
            # Analyse des mots-clés
            has_availability_keyword = any(keyword in body_text for keyword in availability_keywords)
            has_unavailability_keyword = any(keyword in body_text for keyword in unavailability_keywords)
            
            if has_unavailability_keyword:
                result['available'] = False
                result['message'] = "Message d'indisponibilité détecté"
            elif has_availability_keyword and not result['available']:
                result['available'] = True
                result['message'] = "Indicateurs de disponibilité détectés"
            
            if not result['available'] and result['message'] == 'Vérification en cours...':
                result['message'] = "Aucune disponibilité claire détectée"
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de disponibilité: {e}", exc_info=True)
            result['message'] = f"Erreur: {str(e)}"
        
        return result
    
    def scan(self):
        """Lance un scan des deux pages"""
        logger.info("=" * 60)
        logger.info("Début du scan")
        logger.info("=" * 60)
        
        results = []
        
        # Vérifier page 1
        result_1 = self.check_page(self.page_1_url, "Page 1")
        results.append(result_1)
        
        # Attendre un délai aléatoire entre les deux pages (3-7 secondes)
        delay = random.randint(3, 7)
        logger.info(f"Attente de {delay}s avant la page suivante...")
        time.sleep(delay)
        
        # Vérifier page 2
        result_2 = self.check_page(self.page_2_url, "Page 2")
        results.append(result_2)
        
        # Vérifier si des rendez-vous sont disponibles
        available_results = [r for r in results if r['available']]
        
        if available_results:
            logger.info("🎉 Rendez-vous disponible(s) trouvé(s)!")
            self.notifier.send_notification(available_results)
        else:
            logger.info("Aucun rendez-vous disponible pour le moment")
        
        logger.info("=" * 60)
        return results
    
    def run_continuous(self):
        """Lance le scanner en mode continu"""
        logger.info(f"Démarrage du scanner en mode continu (intervalle: {self.check_interval}s)")
        
        with sync_playwright() as playwright:
            self.start_browser(playwright)
            
            try:
                while True:
                    self.scan()
                    logger.info(f"Prochaine vérification dans {self.check_interval} secondes...")
                    time.sleep(self.check_interval)
                    
            except KeyboardInterrupt:
                logger.info("Arrêt du scanner par l'utilisateur")
            finally:
                if self.browser:
                    self.browser.close()
                    logger.info("Navigateur fermé")
    
    def run_once(self):
        """Lance le scanner une seule fois"""
        logger.info("Démarrage du scanner (mode unique)")
        
        with sync_playwright() as playwright:
            self.start_browser(playwright)
            
            try:
                results = self.scan()
                return results
            finally:
                if self.browser:
                    self.browser.close()
                    logger.info("Navigateur fermé")


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scanner de disponibilité de rendez-vous')
    parser.add_argument('--once', action='store_true', help='Exécuter une seule fois')
    parser.add_argument('--continuous', action='store_true', help='Exécuter en continu')
    
    args = parser.parse_args()
    
    try:
        scanner = RDVScanner()
        
        if args.once:
            scanner.run_once()
        else:
            scanner.run_continuous()
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
