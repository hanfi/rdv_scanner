#!/usr/bin/env python3
"""
Scanner RDV Préfecture - Version Finale avec Multimodal Gemini
Intègre résolution multimodale (image + audio) avec fallback intelligent
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from hybrid_optimized_solver_clean import HybridOptimizedSolver
from notifier import Notifier

# Import optionnel du health check pour déploiement cloud
try:
    from health_check import start_health_server
    HEALTH_CHECK_AVAILABLE = True
except ImportError:
    HEALTH_CHECK_AVAILABLE = False

# Import optionnel du viewer de screenshots
try:
    from screenshot_viewer import start_screenshot_viewer
    SCREENSHOT_VIEWER_AVAILABLE = True
except ImportError:
    SCREENSHOT_VIEWER_AVAILABLE = False

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
        self.background_mode = os.getenv('BACKGROUND_MODE', 'false').lower() == 'true'
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
        logger.info("Page 1: %s", self.url_page1)
        logger.info("Page 2: %s", self.url_page2)
        logger.info("Mode headless: %s", self.headless)
        logger.info("Mode muet: %s", self.mute_browser)
        logger.info("Mode arrière-plan: %s", self.background_mode)
        logger.info("Intervalle: %ss", self.check_interval)
        logger.info("Max retries: %s", self.max_retries)

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
                logger.info("   📸 Image captcha: %s", image_path)

            # Capture de l'audio captcha
            audio_path = f"screenshots/captcha_audio_{timestamp}_attempt_{attempt}.wav"
            audio_captured = self.capture_audio_captcha(page, audio_path)
            if audio_captured:
                resources['audio'] = audio_path
                logger.info("   🎵 Audio captcha: %s", audio_path)

            return resources

        except Exception as e:
            logger.error("   ❌ Erreur capture: %s", e)
            return resources

    def capture_audio_captcha(self, page, audio_path: str) -> bool:
        """Capture l'audio captcha en cliquant sur le bouton"""
        try:
            # Trouver le bouton audio
            audio_button = page.locator(
                'button[title="Énoncer le code du captcha"]')
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
                    except Exception:
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
            logger.error("   ⚠️ Erreur capture audio: %s", e)
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
                logger.info("🚀 Navigation vers %s...", page_name)
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                logger.info("✅ %s chargée", page_name)
            else:
                logger.info("🔄 Continuation sur %s...", page_name)

            # Scroll et attente
            page.evaluate('window.scrollBy(0, 500)')

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

            logger.info(
                "✅ Captcha résolu: '%s' (%s, %s)",
                captcha_text,
                solver_result['method'],
                solver_result['confidence']
            )

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
            submit_btn.click()
            logger.info("✅ Formulaire soumis")

            # Attendre la réponse (navigation ou changement d'URL)
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                # Si pas de changement de page, attendre un peu pour le contenu
                page.wait_for_timeout(2000)

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
            logger.error("Erreur tentative %s: %s", attempt, e)
            return result

    def scan_single_page_with_retry(self, page, url: str, page_name: str) -> Dict[str, Any]:
        """Scanne une page unique avec retry"""
        for attempt in range(1, self.max_retries + 1):
            logger.info(
                "🔄 %s - TENTATIVE %s/%s",
                page_name,
                attempt,
                self.max_retries
            )

            result = self.try_captcha_submission_multimodal(
                page, url, page_name, attempt)

            # Log détaillé du résultat
            logger.info("   Status: %s", result['status'])
            if result.get('captcha_text'):
                logger.info(
                    "   Captcha: '%s' (%s, %s)",
                    result['captcha_text'],
                    result['captcha_method'],
                    result['captcha_confidence']
                )
            logger.info("   Message: %s", result['message'])

            if result['status'] == 'SUCCESS':
                logger.info("🎉 %s SUCCÈS! %s", page_name, result['message'])
                return result

            elif result['status'] == 'BLOCKED':
                logger.warning("❌ %s BLOQUÉ: %s", page_name, result['message'])
                return result

            elif result['status'] == 'INVALID_CAPTCHA':
                logger.warning(
                    "❌ %s CAPTCHA INVALIDE: %s",
                    page_name,
                    result['message']
                )
                if attempt < self.max_retries:
                    logger.info(
                        "🔄 Retry dans 2s... (%s/%s)",
                        attempt + 1,
                        self.max_retries
                    )
                    time.sleep(2)
                else:
                    logger.warning(
                        "❌ %s - Maximum de tentatives atteint",
                        page_name
                    )
                    return result
            else:
                logger.warning("⚠️ %s AUTRE: %s", page_name, result['message'])
                if attempt < self.max_retries:
                    logger.info(
                        "🔄 %s - Nouvelle tentative par précaution...",
                        page_name
                    )
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
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',              # Pas de setup initial
                '--no-default-browser-check',  # Pas de vérification navigateur par défaut
                '--disable-background-timer-throttling',  # Meilleure performance
                '--disable-renderer-backgrounding',       # Empêche la mise en arrière-plan
                '--disable-backgrounding-occluded-windows', # Garde les fenêtres actives
                '--disable-ipc-flooding-protection',       # Améliore la réactivité
            ]
            
            # Mode arrière-plan : empêche la prise de focus
            if self.background_mode:
                launch_args.extend([
                    '--silent-launch',           # Lancement silencieux
                    '--disable-background-mode', # Désactive le mode arrière-plan agressif
                    '--disable-extensions',      # Désactive les extensions
                    '--disable-plugins',         # Désactive les plugins
                    '--disable-default-apps',    # Pas d'apps par défaut
                ])
                logger.info("🔕 Mode arrière-plan activé (pas de prise de focus)")
            
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
                    page.evaluate(
                        '() => { if (navigator.mediaDevices) { navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error("Muted")); } }')
                    page.evaluate(
                        '() => { Object.defineProperty(HTMLMediaElement.prototype, "muted", { value: true, writable: false }); }')
                    page.evaluate(
                        '() => { Object.defineProperty(HTMLAudioElement.prototype, "volume", { value: 0, writable: false }); }')
                    logger.info("🔇 Onglet muté automatiquement")
                except Exception as e:
                    logger.warning("⚠️ Impossible de muter l'onglet: %s", e)
            else:
                logger.info("🔊 Son du captcha activé")

            try:
                # Scanner la page 1
                logger.info("� SCAN PAGE 1")
                result_page1 = self.scan_single_page_with_retry(
                    page, self.url_page1, "Page 1")
                results.append(result_page1)

                # Scanner la page 2
                logger.info("📝 SCAN PAGE 2")
                result_page2 = self.scan_single_page_with_retry(
                    page, self.url_page2, "Page 2")
                results.append(result_page2)

            except Exception as e:
                logger.error("Erreur globale: %s", e, exc_info=True)
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
            logger.info("\n%s:", page_name)
            logger.info("  Status: %s", result['status'])
            logger.info("  Message: %s", result['message'])
            if result.get('captcha_text'):
                logger.info(
                    "  Captcha: '%s' (%s)",
                    result['captcha_text'],
                    result.get('captcha_method', 'unknown')
                )

            if result.get('available'):
                logger.info("  🎉 CRÉNEAUX DISPONIBLES DÉTECTÉS!")
                available_pages.append({
                    'page': page_name,
                    'url': result.get('url', ''),
                    'available': True,
                    'message': result['message'],
                    'captcha_method': result.get('captcha_method', ''),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.info("  😔 Pas de créneaux disponibles")

        # Notifications si des créneaux sont disponibles
        if available_pages:
            logger.info(
                "\n🎉 %s PAGE(S) AVEC CRÉNEAUX TROUVÉES!",
                len(available_pages)
            )
            try:
                self.notifier.send_notification(available_pages)
            except Exception as e:
                logger.warning("Erreur notification: %s", e)
        else:
            logger.info(
                "\n😔 Aucun créneau disponible sur les %s pages",
                len(results)
            )

        logger.info("=" * 60)

        return results

    def run_continuous(self):
        """Lance le scanner en mode continu"""
        logger.info(
            "🔄 Démarrage du scanner multimodal continu (intervalle: %ss)",
            self.check_interval
        )

        # Démarrer le health check server si disponible (pour déploiement cloud)
        if HEALTH_CHECK_AVAILABLE:
            try:
                start_health_server()
            except Exception as e:
                logger.warning("Health check server non démarré: %s", e)

        # Démarrer le screenshot viewer si disponible
        if SCREENSHOT_VIEWER_AVAILABLE:
            try:
                start_screenshot_viewer(8081)
                logger.info("🖼️ Screenshot viewer disponible sur :8081")
            except Exception as e:
                logger.warning("Screenshot viewer non démarré: %s", e)

        scan_count = 0

        try:
            while True:
                scan_count += 1
                logger.info(
                    "🎯 SCAN #%s - %s",
                    scan_count,
                    datetime.now().strftime('%H:%M:%S')
                )

                results = self.scan_with_multimodal_retry()

                # Vérifier les créneaux disponibles
                available_pages = []
                for result in results:
                    if result.get('available'):
                        available_pages.append({
                            'page': result.get('page'),
                            'url': result.get('url', ''),
                            'available': True,
                            'message': result['message'],
                            'captcha_method': result.get('captcha_method', ''),
                            'timestamp': datetime.now().isoformat()
                        })

                # Notification si disponible
                if available_pages:
                    logger.info(
                        "\n🎉 %s PAGE(S) AVEC CRÉNEAUX TROUVÉES!",
                        len(available_pages)
                    )
                    try:
                        self.notifier.send_notification(available_pages)
                    except Exception as e:
                        logger.warning("Erreur notification: %s", e)
                else:
                    logger.info(
                        "\n😔 Aucun créneau disponible sur les %s pages",
                        len(results)
                    )

                # Attendre avant le prochain scan
                logger.info("💤 Attente %ss avant le prochain scan...", self.check_interval)
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt du scanner par l'utilisateur")
        except Exception as e:
            logger.error("Erreur fatale: %s", e, exc_info=True)


def main():
    """Point d'entrée principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Scanner RDV Préfecture Multimodal')
    parser.add_argument('--once', action='store_true',
                        help='Exécuter une seule fois')
    parser.add_argument('--continuous', action='store_true',
                        help='Exécuter en continu')

    args = parser.parse_args()

    try:
        scanner = MultimodalRDVScanner()

        if args.once:
            scanner.run_once()
        else:
            scanner.run_continuous()

    except Exception as e:
        logger.error("Erreur fatale: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
