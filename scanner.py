#!/usr/bin/env python3
"""
Scanner RDV Préfecture - Version Finale avec Multimodal Gemini
Intègre résolution multimodale (image + audio) avec fallback intelligent
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from hybrid_optimized_solver_clean import HybridOptimizedSolver
from notifier import Notifier

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rdv_scanner_multimodal.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MultimodalRDVScanner:
    """Scanner RDV avec résolution multimodale avancée"""
    
    def __init__(self):
        load_dotenv()
        self.url_page1 = os.getenv('PAGE_1_URL')
        self.url_page2 = os.getenv('PAGE_2_URL')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        self.mute_browser = os.getenv('MUTE_BROWSER', 'true').lower() == 'true'
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        self.max_retries = 3
        
        if not self.url_page1:
            raise ValueError("PAGE_1_URL doit être configuré dans .env")
        if not self.url_page2:
            raise ValueError("PAGE_2_URL doit être configuré dans .env")
        
        # Initialiser le résolveur hybride optimisé
        self.captcha_solver = HybridOptimizedSolver()
        self.notifier = Notifier()
        
        logger.info("=" * 60)
        logger.info("🎯 SCANNER RDV MULTIMODAL INITIALISÉ")
        logger.info("=" * 60)
        logger.info(f"Page 1: {self.url_page1}")
        logger.info(f"Page 2: {self.url_page2}")
        logger.info(f"Mode headless: {self.headless}")
        logger.info(f"Mode muet: {self.mute_browser}")
        logger.info(f"Intervalle: {self.check_interval}s")
        logger.info(f"Max retries: {self.max_retries}")
    
    def capture_captcha_resources(self, page, attempt: int) -> Dict[str, str]:
        """
        Capture les ressources captcha (image + audio)
        
        Returns:
            Dict avec chemins vers image et audio
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        resources = {'image': None, 'audio': None}
        
        try:
            # Capture de l'image captcha
            captcha_images = page.locator('img')
            if captcha_images.count() > 0:
                os.makedirs('screenshots', exist_ok=True)
                image_path = f"screenshots/captcha_image_{timestamp}_attempt_{attempt}.png"
                captcha_images.first.screenshot(path=image_path)
                resources['image'] = image_path
                logger.info(f"   📸 Image captcha: {image_path}")
            
            # Capture de l'audio captcha
            audio_path = f"screenshots/captcha_audio_{timestamp}_attempt_{attempt}.wav"
            audio_captured = self.capture_audio_captcha(page, audio_path)
            if audio_captured:
                resources['audio'] = audio_path
                logger.info(f"   🎵 Audio captcha: {audio_path}")
            
            return resources
            
        except Exception as e:
            logger.error(f"   ❌ Erreur capture: {e}")
            return resources
    
    def capture_audio_captcha(self, page, audio_path: str) -> bool:
        """Capture l'audio captcha en cliquant sur le bouton"""
        try:
            # Trouver le bouton audio
            audio_button = page.locator('button[title="Énoncer le code du captcha"]')
            if audio_button.count() == 0:
                return False
            
            # Écouter les requêtes audio
            audio_data = None
            
            def handle_response(response):
                nonlocal audio_data
                content_type = response.headers.get('content-type', '').lower()
                if 'audio' in content_type and not audio_data:
                    try:
                        audio_data = response.body()
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # Cliquer et attendre l'audio
            audio_button.click()
            page.wait_for_timeout(3000)
            
            # Sauvegarder si capturé
            if audio_data:
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"   ⚠️ Erreur capture audio: {e}")
            return False
    
    def try_captcha_submission_multimodal(self, page, url: str, page_name: str, attempt: int) -> Dict[str, Any]:
        """
        Tentative de soumission avec approche multimodale
        
        Returns:
            Dict avec statut et informations détaillées
        """
        result = {
            'status': 'ERROR',
            'message': '',
            'page': page_name,
            'attempt': attempt,
            'captcha_text': '',
            'captcha_method': '',
            'captcha_confidence': '',
            'url': '',
            'available': False
        }
        
        try:
            # Navigation seulement si première tentative
            if attempt == 1:
                logger.info(f"🚀 Navigation vers {page_name}...")
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                logger.info(f"✅ {page_name} chargée")
            else:
                logger.info(f"🔄 Continuation sur {page_name}...")
            
            # Scroll et attente
            page.evaluate('window.scrollBy(0, 500)')
            page.wait_for_timeout(500)
            
            # Vérifier la présence du captcha
            captcha_field = page.locator('input[name="captchaUsercode"]')
            if captcha_field.count() == 0:
                result['message'] = "Champ captcha non trouvé"
                return result
            
            # Capture des ressources captcha
            logger.info("📋 Capture des ressources captcha...")
            resources = self.capture_captcha_resources(page, attempt)
            
            if not resources['image']:
                result['message'] = "Image captcha non capturée"
                return result
            
            # Résolution avec approche multimodale
            logger.info("🧠 Résolution multimodale du captcha...")
            solver_result = self.captcha_solver.solve_captcha_with_fallback(
                resources['image'], 
                resources['audio']
            )
            
            if solver_result['status'] != 'SUCCESS':
                result['message'] = f"Échec résolution: {solver_result.get('attempts', [])}"
                return result
            
            captcha_text = solver_result['text']
            result.update({
                'captcha_text': captcha_text,
                'captcha_method': solver_result['method'],
                'captcha_confidence': solver_result['confidence']
            })
            
            logger.info(f"✅ Captcha résolu: '{captcha_text}' ({solver_result['method']}, {solver_result['confidence']})")
            
            # Remplissage et soumission
            captcha_field.clear()
            captcha_field.fill(captcha_text)
            
            submit_btn = page.locator('button[type="submit"]')
            if submit_btn.count() == 0:
                result['message'] = "Bouton submit non trouvé"
                return result
            
            # Screenshots avant/après
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            before_path = f"screenshots/before_submit_{timestamp}_attempt_{attempt}.png"
            page.screenshot(path=before_path, full_page=True)
            
            # Soumission
            page.wait_for_timeout(1000)
            submit_btn.click()
            logger.info("✅ Formulaire soumis")
            
            # Attendre la réponse
            page.wait_for_timeout(5000)
            
            # Analyser la réponse
            current_url = page.url
            body_text = page.locator('body').inner_text()
            
            after_path = f"screenshots/after_submit_{timestamp}_attempt_{attempt}.png"
            page.screenshot(path=after_path, full_page=True)
            
            result['url'] = current_url
            body_lower = body_text.lower()
            
            # Classification du résultat
            if 'sorry, you have been blocked' in body_lower:
                result['status'] = 'BLOCKED'
                result['message'] = "Bloqué par Cloudflare"
                
            elif 'error=invalidcaptcha' in current_url.lower():
                result['status'] = 'INVALID_CAPTCHA'
                result['message'] = f"Captcha '{captcha_text}' invalide ({solver_result['method']})"
                
            elif '/creneau/' in current_url:
                result['status'] = 'SUCCESS'
                result['message'] = "Accès aux créneaux réussi"
                
                # Analyser la disponibilité
                if 'aucun créneau disponible' in body_lower:
                    result['available'] = False
                    result['message'] += " - Aucun créneau disponible"
                elif 'choisissez votre créneau' in body_lower or 'sélectionnez' in body_lower:
                    result['available'] = True
                    result['message'] += " - 🎉 CRÉNEAUX DISPONIBLES!"
                else:
                    result['available'] = False
                    result['message'] += " - Statut indéterminé"
                    
            else:
                result['status'] = 'OTHER'
                result['message'] = "Réponse inconnue"
            
            return result
            
        except Exception as e:
            result['message'] = f"Erreur: {str(e)}"
            logger.error(f"Erreur tentative {attempt}: {e}")
            return result
    
    def scan_single_page_with_retry(self, page, url: str, page_name: str) -> Dict[str, Any]:
        """Scanne une page unique avec retry"""
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"🔄 {page_name} - TENTATIVE {attempt}/{self.max_retries}")
            
            result = self.try_captcha_submission_multimodal(page, url, page_name, attempt)
            
            # Log détaillé du résultat
            logger.info(f"   Status: {result['status']}")
            if result.get('captcha_text'):
                logger.info(f"   Captcha: '{result['captcha_text']}' ({result['captcha_method']}, {result['captcha_confidence']})")
            logger.info(f"   Message: {result['message']}")
            
            if result['status'] == 'SUCCESS':
                logger.info(f"🎉 {page_name} SUCCÈS! {result['message']}")
                return result
                
            elif result['status'] == 'BLOCKED':
                logger.warning(f"❌ {page_name} BLOQUÉ: {result['message']}")
                return result
                
            elif result['status'] == 'INVALID_CAPTCHA':
                logger.warning(f"❌ {page_name} CAPTCHA INVALIDE: {result['message']}")
                if attempt < self.max_retries:
                    logger.info(f"🔄 Retry dans 2s... ({attempt + 1}/{self.max_retries})")
                    time.sleep(2)
                else:
                    logger.warning(f"❌ {page_name} - Maximum de tentatives atteint")
                    return result
            else:
                logger.warning(f"⚠️ {page_name} AUTRE: {result['message']}")
                if attempt < self.max_retries:
                    logger.info(f"🔄 {page_name} - Nouvelle tentative par précaution...")
                    time.sleep(2)
                else:
                    return result
        
        return result
    
    def scan_with_multimodal_retry(self) -> List[Dict[str, Any]]:
        logger.info("=" * 60)
        logger.info("🎯 DÉBUT DU SCAN MULTIMODAL AVEC RETRY")
        logger.info("=" * 60)
        
        results = []
        
        with sync_playwright() as p:
            # Arguments de lancement avec muting si configuré
            launch_args = ['--disable-blink-features=AutomationControlled']
            if self.mute_browser:
                launch_args.extend([
                    '--mute-audio',
                    '--disable-audio-output',
                    '--disable-background-audio'
                ])
                logger.info("🔇 Arguments de muting ajoutés au navigateur")
            
            browser = p.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            
            # Muter l'onglet pour éviter le son du captcha (si configuré)
            if self.mute_browser:
                try:
                    page.evaluate('() => { if (navigator.mediaDevices) { navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error("Muted")); } }')
                    page.evaluate('() => { Object.defineProperty(HTMLMediaElement.prototype, "muted", { value: true, writable: false }); }')
                    page.evaluate('() => { Object.defineProperty(HTMLAudioElement.prototype, "volume", { value: 0, writable: false }); }')
                    logger.info("🔇 Onglet muté automatiquement")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de muter l'onglet: {e}")
            else:
                logger.info("🔊 Son du captcha activé")
            
            try:
                # Scanner la page 1
                logger.info("� SCAN PAGE 1")
                result_page1 = self.scan_single_page_with_retry(page, self.url_page1, "Page 1")
                results.append(result_page1)
                
                # Scanner la page 2
                logger.info("📝 SCAN PAGE 2")
                result_page2 = self.scan_single_page_with_retry(page, self.url_page2, "Page 2")
                results.append(result_page2)
                
            except Exception as e:
                logger.error(f"Erreur globale: {e}", exc_info=True)
                results.append({
                    'status': 'ERROR',
                    'message': f"Erreur globale: {str(e)}",
                    'page': 'Global',
                    'available': False
                })
                
            finally:
                browser.close()
                
        return results
    
    def run_once(self) -> List[Dict[str, Any]]:
        """Lance un scan unique"""
        logger.info("🚀 Démarrage du scanner multimodal (mode unique)")
        
        results = self.scan_with_multimodal_retry()
        
        # Affichage des résultats finaux
        logger.info("=" * 60)
        logger.info("📊 RÉSULTATS FINAUX:")
        
        available_pages = []
        
        for result in results:
            page_name = result.get('page', 'Unknown')
            logger.info(f"\n{page_name}:")
            logger.info(f"  Status: {result['status']}")
            logger.info(f"  Message: {result['message']}")
            if result.get('captcha_text'):
                logger.info(f"  Captcha: '{result['captcha_text']}' ({result.get('captcha_method', 'unknown')})")
            
            if result.get('available'):
                logger.info(f"  🎉 CRÉNEAUX DISPONIBLES DÉTECTÉS!")
                available_pages.append({
                    'page': page_name,
                    'url': result.get('url', ''),
                    'available': True,
                    'message': result['message'],
                    'captcha_method': result.get('captcha_method', ''),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.info(f"  😔 Pas de créneaux disponibles")
        
        # Notifications si des créneaux sont disponibles
        if available_pages:
            logger.info(f"\n🎉 {len(available_pages)} PAGE(S) AVEC CRÉNEAUX TROUVÉES!")
            try:
                self.notifier.send_notification(available_pages)
            except Exception as e:
                logger.warning(f"Erreur notification: {e}")
        else:
            logger.info(f"\n😔 Aucun créneau disponible sur les {len(results)} pages")
        
        logger.info("=" * 60)
        
        return results
    
    def run_continuous(self):
        """Lance le scanner en mode continu"""
        logger.info(f"🔄 Démarrage du scanner multimodal continu (intervalle: {self.check_interval}s)")
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info(f"🎯 SCAN #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                results = self.scan_with_multimodal_retry()
                
                # Vérifier les créneaux disponibles
                available_pages = []
                for result in results:
                    if result.get('available'):
                        available_pages.append({
                            'page': result.get('page', 'Unknown'),
                            'url': result.get('url', ''),
                            'available': True,
                            'message': result['message'],
                            'captcha_method': result.get('captcha_method', ''),
                            'timestamp': datetime.now().isoformat()
                        })
                
                # Notification si disponible
                if available_pages:
                    logger.info(f"🎉 {len(available_pages)} PAGE(S) AVEC CRÉNEAUX TROUVÉES! Notification envoyée.")
                    try:
                        self.notifier.send_notification(available_pages)
                    except Exception as e:
                        logger.warning(f"Erreur notification: {e}")
                else:
                    logger.info(f"😔 Aucun créneau disponible sur les {len(results)} pages")
                
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
    
    parser = argparse.ArgumentParser(description='Scanner RDV Préfecture Multimodal')
    parser.add_argument('--once', action='store_true', help='Exécuter une seule fois')
    parser.add_argument('--continuous', action='store_true', help='Exécuter en continu')
    
    args = parser.parse_args()
    
    try:
        scanner = MultimodalRDVScanner()
        
        if args.once:
            scanner.run_once()
        else:
            scanner.run_continuous()
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()