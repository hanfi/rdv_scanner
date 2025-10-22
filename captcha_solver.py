"""
Module de résolution de captcha
Supporte reCAPTCHA v2/v3, hCaptcha, captchas image et Gemini Vision
"""
import os
import logging
from typing import Optional
from playwright.sync_api import Page
from gemini_solver import GeminiCaptchaSolver

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """Résolveur de captcha utilisant des services externes ou Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('CAPTCHA_API_KEY')
        self.service = os.getenv('CAPTCHA_SERVICE', '2captcha')
        
        # Initialiser Gemini
        self.gemini_solver = GeminiCaptchaSolver()
        
        if not self.api_key or self.api_key == 'your_api_key_here':
            if self.gemini_solver.is_available():
                logger.info("💡 CAPTCHA_API_KEY non configuré - utilisation de Gemini Vision (gratuit)")
            else:
                logger.warning("⚠️ Ni CAPTCHA_API_KEY ni GEMINI_API_KEY configurés - résolution de captcha limitée")
        
        # Importer le service approprié si configuré
        if self.api_key and self.api_key != 'your_api_key_here':
            if self.service == '2captcha':
                try:
                    from twocaptcha import TwoCaptcha
                    self.solver = TwoCaptcha(self.api_key)
                except ImportError:
                    logger.warning("Module 2captcha non installé: pip install 2captcha-python")
                    self.solver = None
            else:
                self.solver = None
        else:
            self.solver = None
    
    def solve_recaptcha_v2(self, page: Page) -> bool:
        """
        Résout un reCAPTCHA v2
        
        Args:
            page: Page Playwright contenant le captcha
            
        Returns:
            True si résolu, False sinon
        """
        try:
            logger.info("Tentative de résolution de reCAPTCHA v2...")
            
            if not self.solver:
                logger.warning("Pas de solver configuré - tentative de résolution manuelle")
                # Attendre que l'utilisateur résolve manuellement si pas en headless
                if not os.getenv('HEADLESS', 'true').lower() == 'true':
                    logger.info("Mode manuel: résolvez le captcha dans le navigateur...")
                    page.wait_for_timeout(30000)
                    return True
                return False
            
            # Récupérer le sitekey
            iframe = page.frame_locator('iframe[src*="recaptcha"]').first
            sitekey = None
            
            # Extraire le sitekey de l'iframe
            recaptcha_frame = page.locator('iframe[src*="recaptcha/api2/anchor"]').first
            if recaptcha_frame:
                src = recaptcha_frame.get_attribute('src')
                if 'k=' in src:
                    sitekey = src.split('k=')[1].split('&')[0]
            
            if not sitekey:
                logger.error("Impossible de trouver le sitekey reCAPTCHA")
                return False
            
            logger.info(f"Sitekey trouvé: {sitekey}")
            
            # Résoudre avec le service
            result = self.solver.recaptcha(
                sitekey=sitekey,
                url=page.url
            )
            
            if result and 'code' in result:
                # Injecter la réponse
                page.evaluate(f'''
                    document.getElementById('g-recaptcha-response').innerHTML = '{result["code"]}';
                ''')
                logger.info("reCAPTCHA résolu avec succès")
                page.wait_for_timeout(1000)
                return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de reCAPTCHA v2: {e}", exc_info=True)
        
        return False
    
    def solve_hcaptcha(self, page: Page) -> bool:
        """
        Résout un hCaptcha
        
        Args:
            page: Page Playwright contenant le captcha
            
        Returns:
            True si résolu, False sinon
        """
        try:
            logger.info("Tentative de résolution de hCaptcha...")
            
            if not self.solver:
                logger.warning("Pas de solver configuré")
                if not os.getenv('HEADLESS', 'true').lower() == 'true':
                    logger.info("Mode manuel: résolvez le captcha dans le navigateur...")
                    page.wait_for_timeout(30000)
                    return True
                return False
            
            # Récupérer le sitekey hCaptcha
            hcaptcha_frame = page.locator('iframe[src*="hcaptcha"]').first
            if hcaptcha_frame:
                src = hcaptcha_frame.get_attribute('src')
                if 'sitekey=' in src:
                    sitekey = src.split('sitekey=')[1].split('&')[0]
                    
                    # Résoudre avec le service
                    result = self.solver.hcaptcha(
                        sitekey=sitekey,
                        url=page.url
                    )
                    
                    if result and 'code' in result:
                        # Injecter la réponse
                        page.evaluate(f'''
                            document.querySelector('[name="h-captcha-response"]').innerHTML = '{result["code"]}';
                        ''')
                        logger.info("hCaptcha résolu avec succès")
                        page.wait_for_timeout(1000)
                        return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de hCaptcha: {e}", exc_info=True)
        
        return False
    
    def solve_prefecture_captcha(self, page: Page) -> bool:
        """
        Résout le captcha spécifique des pages préfecture (calcul mathématique)
        
        Args:
            page: Page Playwright contenant le captcha
            
        Returns:
            True si résolu, False sinon
        """
        try:
            logger.info("Recherche du captcha préfecture...")
            
            # Scroll pour voir le captcha
            page.evaluate('window.scrollBy(0, 500)')
            page.wait_for_timeout(500)
            
            # Chercher l'image du captcha (calcul mathématique)
            captcha_selectors = [
                'img[alt*="captcha" i]',
                'img[src*="captcha" i]',
                'img[id*="captcha" i]',
                '.captcha img',
                '#captcha img'
            ]
            
            captcha_img = None
            for selector in captcha_selectors:
                try:
                    img = page.locator(selector).first
                    if img.is_visible(timeout=1000):
                        captcha_img = img
                        logger.info(f"Captcha trouvé avec sélecteur: {selector}")
                        break
                except:
                    continue
            
            if not captcha_img:
                logger.info("Aucun captcha image trouvé")
                return True  # Pas de captcha = OK
            
            # Définir le chemin de sauvegarde
            screenshot_path = f"screenshots/captcha_{page.url.split('/')[-2]}.png"
            logger.info(f"Captcha détecté, préparation capture: {screenshot_path}")
            
            # Chercher le champ de saisie du captcha
            input_selectors = [
                'input[name*="captcha" i]',
                'input[id*="captcha" i]',
                'input[placeholder*="captcha" i]',
                'input[placeholder*="calcul" i]',
                'input[type="text"][name*="code" i]'
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=1000):
                        input_field = field
                        logger.info(f"Champ captcha trouvé: {selector}")
                        break
                except Exception:
                    continue
            
            if not input_field:
                logger.warning("Champ de saisie du captcha non trouvé")
                return False
            
            # Si on a un solver configuré
            if self.solver:
                try:
                    # Capturer le screenshot et sauvegarder
                    captcha_img.screenshot(path=screenshot_path)
                    logger.info(f"📸 Captcha sauvegardé: {screenshot_path}")
                    
                    # Passer le chemin du fichier au solver (pas les bytes)
                    result = self.solver.normal(screenshot_path)
                    
                    if result and 'code' in result:
                        input_field.fill(result['code'])
                        logger.info(f"✅ Captcha résolu automatiquement: {result['code']}")
                        page.wait_for_timeout(1000)
                        return True
                except Exception as e:
                    logger.error(f"Erreur avec le solver: {e}")
                    logger.info("Tentative de sauvegarde de la capture pour analyse manuelle...")
            
            # Essayer avec Gemini si disponible
            if self.gemini_solver.is_available():
                try:
                    # Sauvegarder l'image si pas déjà fait
                    if not os.path.exists(screenshot_path):
                        captcha_img.screenshot(path=screenshot_path)
                        logger.info(f"📸 Captcha sauvegardé: {screenshot_path}")
                    
                    # Résoudre avec Gemini
                    captcha_text = self.gemini_solver.solve_captcha_from_file(screenshot_path)
                    
                    if captcha_text:
                        logger.info(f"🤖 Gemini a résolu: '{captcha_text}'")
                        
                        # Attendre un peu avant de commencer (comportement humain)
                        page.wait_for_timeout(800)
                        
                        # Remplir le champ caractère par caractère (plus humain, plus lent)
                        for char in captcha_text:
                            input_field.type(char, delay=250)  # 250ms par caractère (très humain)
                        
                        logger.info(f"✅ Captcha rempli avec: {captcha_text}")
                        
                        # Attendre un peu plus (comportement humain - relecture)
                        page.wait_for_timeout(2000)
                        
                        # Chercher et cliquer sur le bouton de validation du formulaire
                        submit_buttons = [
                            'button[formaction*="_validerCaptcha"]',
                            'button[type="submit"]:has-text("Suivant")',
                            'button[type="submit"]',
                            'input[type="submit"]',
                            'button:has-text("Valider")',
                            'button:has-text("Continuer")',
                            'button:has-text("Suivant")',
                            'input[value*="Valider" i]',
                            'input[value*="Continuer" i]'
                        ]
                        
                        for selector in submit_buttons:
                            try:
                                button = page.locator(selector).first
                                if button.is_visible(timeout=1000):
                                    logger.info(f"🔘 Clic sur le bouton de validation: {selector}")
                                    
                                    # Déplacer la souris vers le bouton (comportement humain)
                                    box = button.bounding_box()
                                    if box:
                                        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                        page.wait_for_timeout(300)
                                    
                                    button.click()
                                    
                                    # Attendre la navigation avec un délai plus long
                                    logger.info("⏳ Attente de la navigation (Cloudflare protection)...")
                                    page.wait_for_timeout(8000)  # 8 secondes pour Cloudflare
                                    
                                    # Attendre explicitement que Cloudflare termine
                                    try:
                                        page.wait_for_load_state('networkidle', timeout=15000)
                                    except Exception:
                                        page.wait_for_timeout(7000)
                                    
                                    logger.info(f"✅ Formulaire validé, page actuelle: {page.url}")
                                    return True
                            except Exception as e:
                                logger.debug(f"Bouton {selector} non trouvé: {e}")
                                continue
                        
                        # Si aucun bouton trouvé, essayer de soumettre le formulaire directement
                        try:
                            form = page.locator('form').first
                            if form:
                                logger.info("🔘 Soumission du formulaire directement")
                                input_field.press('Enter')
                                page.wait_for_timeout(2000)
                                logger.info(f"✅ Formulaire soumis, page actuelle: {page.url}")
                                return True
                        except Exception as e:
                            logger.warning(f"Impossible de soumettre le formulaire: {e}")
                        
                        logger.warning("⚠️ Captcha rempli mais bouton de validation non trouvé")
                        return True
                    else:
                        logger.warning("❌ Gemini n'a pas pu résoudre le captcha")
                except Exception as e:
                    logger.error(f"Erreur avec Gemini: {e}")
            
            # Mode manuel si pas de solver ou échec
            if not self.solver and not self.gemini_solver.is_available():
                logger.warning("⚠️ Pas de CAPTCHA_API_KEY ni GEMINI_API_KEY configurés")
                logger.info("💡 Pour résolution automatique:")
                logger.info("   - Gratuit: Ajoutez GEMINI_API_KEY dans .env")
                logger.info("   - Payant: Ajoutez CAPTCHA_API_KEY dans .env")
            else:
                logger.warning("Captcha détecté mais échec de résolution automatique")
            
            # Sauvegarder le captcha pour analyse manuelle
            try:
                if not os.path.exists(screenshot_path):
                    captcha_img.screenshot(path=screenshot_path)
                logger.info(f"📸 Captcha sauvegardé pour analyse manuelle: {screenshot_path}")
            except Exception:
                pass
            
            if not os.getenv('HEADLESS', 'true').lower() == 'true':
                logger.info("Mode manuel: résolvez le captcha dans le navigateur (30s)...")
                page.wait_for_timeout(30000)
                return True
            
            # En mode headless sans solver, on retourne False pour signaler l'échec
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution du captcha préfecture: {e}", exc_info=True)
            return False
    
    def solve_image_captcha(self, page: Page) -> bool:
        """
        Résout un captcha image personnalisé
        
        Args:
            page: Page Playwright contenant le captcha
            
        Returns:
            True si résolu, False sinon
        """
        try:
            logger.info("Tentative de résolution de captcha image...")
            
            if not self.solver:
                logger.warning("Pas de solver configuré")
                return False
            
            # Localiser l'image du captcha
            captcha_img = page.locator('img[alt*="captcha" i], img[src*="captcha" i]').first
            
            if captcha_img:
                # Prendre une capture de l'image
                screenshot = captcha_img.screenshot()
                
                # Résoudre avec le service
                result = self.solver.normal(screenshot)
                
                if result and 'code' in result:
                    # Trouver le champ de saisie et entrer la réponse
                    input_field = page.locator('input[name*="captcha" i], input[id*="captcha" i]').first
                    if input_field:
                        input_field.fill(result['code'])
                        logger.info("Captcha image résolu avec succès")
                        page.wait_for_timeout(1000)
                        return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de captcha image: {e}", exc_info=True)
        
        return False
