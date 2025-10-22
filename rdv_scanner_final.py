#!/usr/bin/env python3
"""
Scanner RDV Préfecture - Version Finale Optimisée
Intègre toutes les optimisations validées avec retry automatique
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from gemini_solver import GeminiCaptchaSolver
from notifier import Notifier

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rdv_scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OptimizedRDVScanner:
    """Scanner RDV optimisé avec retry automatique"""
    
    def __init__(self):
        load_dotenv()
        self.url = os.getenv('PAGE_1_URL')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        self.max_retries = 3
        
        if not self.url:
            raise ValueError("PAGE_1_URL doit être configuré dans .env")
        
        self.captcha_solver = GeminiCaptchaSolver()
        self.notifier = Notifier()
        
        logger.info(f"Scanner initialisé pour: {self.url}")
        logger.info(f"Mode headless: {self.headless}")
        logger.info(f"Intervalle: {self.check_interval}s")
    
    def try_captcha_submission(self, page, attempt):
        """
        Tente une soumission de captcha
        
        Returns:
            Dict avec status et informations
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = {
            'status': 'ERROR',
            'message': '',
            'attempt': attempt,
            'captcha_text': '',
            'url': '',
            'available': False
        }
        
        try:
            # Navigation seulement si première tentative
            if attempt == 1:
                logger.info("🚀 Navigation vers la page...")
                page.goto(self.url, wait_until='domcontentloaded', timeout=30000)
                logger.info("✅ Page chargée")
            else:
                logger.info("🔄 Continuation sur la page existante...")
            
            # Scroll et détection
            page.evaluate('window.scrollBy(0, 500)')
            page.wait_for_timeout(500)
            
            captcha_field = page.locator('input[name="captchaUsercode"]')
            if captcha_field.count() == 0:
                result['message'] = "Champ captcha non trouvé"
                return result
            
            # Extraction du captcha
            captcha_images = page.locator('img')
            if captcha_images.count() == 0:
                result['message'] = "Image captcha non trouvée"
                return result
            
            os.makedirs('screenshots', exist_ok=True)
            captcha_path = f"screenshots/captcha_{timestamp}_attempt_{attempt}.png"
            
            captcha_images.first.screenshot(path=captcha_path)
            logger.info(f"📸 Captcha sauvegardé: {captcha_path}")
            
            # Résolution avec Gemini
            if not self.captcha_solver.is_available():
                result['message'] = "Gemini non disponible"
                return result
            
            captcha_text = self.captcha_solver.solve_captcha_from_file(captcha_path)
            if not captcha_text:
                result['message'] = "Gemini n'a pas pu résoudre le captcha"
                return result
                
            logger.info(f"✅ Gemini: '{captcha_text}' ({len(captcha_text)} caractères)")
            result['captcha_text'] = captcha_text
            
            # Remplissage et soumission
            captcha_field.clear()
            captcha_field.fill(captcha_text)
            
            submit_btn = page.locator('button[type="submit"]')
            if submit_btn.count() == 0:
                result['message'] = "Bouton submit non trouvé"
                return result
            
            # Capture avant clic
            before_path = f"screenshots/before_submit_{timestamp}_attempt_{attempt}.png"
            page.screenshot(path=before_path, full_page=True)
            
            # Clic et attente
            page.wait_for_timeout(1000)
            submit_btn.click()
            logger.info("✅ Formulaire soumis")
            
            # Attendre la réponse
            page.wait_for_timeout(5000)
            
            # Analyser la réponse
            current_url = page.url
            body_text = page.locator('body').inner_text()
            
            # Capture après clic
            after_path = f"screenshots/after_submit_{timestamp}_attempt_{attempt}.png"
            page.screenshot(path=after_path, full_page=True)
            
            result['url'] = current_url
            body_lower = body_text.lower()
            
            # Analyser le résultat
            if 'sorry, you have been blocked' in body_lower:
                result['status'] = 'BLOCKED'
                result['message'] = "Bloqué par Cloudflare"
                
            elif 'error=invalidcaptcha' in current_url.lower():
                result['status'] = 'INVALID_CAPTCHA'
                result['message'] = f"Captcha '{captcha_text}' invalide"
                
            elif '/creneau/' in current_url:
                result['status'] = 'SUCCESS'
                result['message'] = "Accès aux créneaux réussi"
                
                # Analyser la disponibilité
                if 'aucun créneau disponible' in body_lower:
                    result['available'] = False
                    result['message'] += " - Aucun créneau disponible"
                elif 'choisissez votre créneau' in body_lower or 'sélectionnez' in body_lower:
                    result['available'] = True
                    result['message'] += " - CRÉNEAUX DISPONIBLES!"
                else:
                    result['available'] = False
                    result['message'] += " - Statut indéterminé"
                    
            else:
                result['status'] = 'OTHER'
                result['message'] = "Réponse inconnue"
                result['url'] = current_url
            
            return result
            
        except Exception as e:
            result['message'] = f"Erreur: {str(e)}"
            logger.error(f"Erreur tentative {attempt}: {e}")
            return result
    
    def scan_with_retry(self):
        """
        Lance un scan avec retry automatique
        
        Returns:
            Dict avec le résultat final
        """
        logger.info("=" * 60)
        logger.info("🎯 DÉBUT DU SCAN AVEC RETRY")
        logger.info("=" * 60)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            final_result = None
            
            try:
                for attempt in range(1, self.max_retries + 1):
                    logger.info(f"🔄 TENTATIVE {attempt}/{self.max_retries}")
                    
                    result = self.try_captcha_submission(page, attempt)
                    
                    if result['status'] == 'SUCCESS':
                        logger.info(f"🎉 SUCCÈS! {result['message']}")
                        final_result = result
                        break
                        
                    elif result['status'] == 'BLOCKED':
                        logger.warning(f"❌ BLOQUÉ: {result['message']}")
                        final_result = result
                        break
                        
                    elif result['status'] == 'INVALID_CAPTCHA':
                        logger.warning(f"❌ CAPTCHA INVALIDE: {result['message']}")
                        if attempt < self.max_retries:
                            logger.info(f"🔄 Retry dans 2s... ({attempt + 1}/{self.max_retries})")
                            time.sleep(2)
                        else:
                            logger.warning("❌ Maximum de tentatives atteint")
                            final_result = result
                    else:
                        logger.warning(f"⚠️ AUTRE: {result['message']}")
                        if attempt < self.max_retries:
                            logger.info("🔄 Nouvelle tentative par précaution...")
                            time.sleep(2)
                        else:
                            final_result = result
                            
            except Exception as e:
                logger.error(f"Erreur globale: {e}", exc_info=True)
                final_result = {
                    'status': 'ERROR',
                    'message': f"Erreur globale: {str(e)}",
                    'available': False
                }
                
            finally:
                browser.close()
                
        return final_result
    
    def run_once(self):
        """Lance un scan unique"""
        logger.info("🚀 Démarrage du scanner (mode unique)")
        
        result = self.scan_with_retry()
        
        # Afficher le résultat final
        logger.info("=" * 60)
        logger.info("📊 RÉSULTAT FINAL:")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Message: {result['message']}")
        if result.get('available'):
            logger.info("🎉 CRÉNEAUX DISPONIBLES DÉTECTÉS!")
            # Envoyer notification
            try:
                self.notifier.send_notification([{
                    'page': 'Préfecture',
                    'url': self.url,
                    'available': True,
                    'message': result['message'],
                    'timestamp': datetime.now().isoformat()
                }])
            except Exception as e:
                logger.warning(f"Erreur notification: {e}")
        else:
            logger.info("😔 Pas de créneaux disponibles")
        logger.info("=" * 60)
        
        return result
    
    def run_continuous(self):
        """Lance le scanner en mode continu"""
        logger.info(f"🔄 Démarrage du scanner en mode continu (intervalle: {self.check_interval}s)")
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info(f"🎯 SCAN #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                result = self.scan_with_retry()
                
                # Notification si disponible
                if result.get('available'):
                    logger.info("🎉 CRÉNEAUX TROUVÉS! Notification envoyée.")
                    try:
                        self.notifier.send_notification([{
                            'page': 'Préfecture',
                            'url': self.url,
                            'available': True,
                            'message': result['message'],
                            'timestamp': datetime.now().isoformat()
                        }])
                    except Exception as e:
                        logger.warning(f"Erreur notification: {e}")
                
                # Attendre avant le prochain scan
                logger.info(f"⏳ Prochain scan dans {self.check_interval} secondes...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt du scanner par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur fatale: {e}", exc_info=True)


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scanner RDV Préfecture Optimisé')
    parser.add_argument('--once', action='store_true', help='Exécuter une seule fois')
    parser.add_argument('--continuous', action='store_true', help='Exécuter en continu')
    
    args = parser.parse_args()
    
    try:
        scanner = OptimizedRDVScanner()
        
        if args.once:
            scanner.run_once()
        else:
            scanner.run_continuous()
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()