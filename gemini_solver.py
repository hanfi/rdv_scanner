"""
Résolveur de captcha utilisant Google Gemini Vision API
Solution gratuite et performante pour les captchas alphanumériques
"""
import os
import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)


class GeminiCaptchaSolver:
    """Résolveur de captcha utilisant Gemini Vision"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.use_gemini = os.getenv('USE_GEMINI', 'false').lower() == 'true'
        self.model = None
        
        if self.use_gemini and self.api_key and self.api_key != 'your_gemini_api_key_here':
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✅ Gemini Vision initialisé avec succès")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'initialisation de Gemini: {e}")
                self.model = None
        elif self.use_gemini:
            logger.warning("⚠️ USE_GEMINI=true mais GEMINI_API_KEY non configuré")
    
    def solve_captcha_from_file(self, image_path: str) -> Optional[str]:
        """
        Résout un captcha à partir d'un fichier image
        
        Args:
            image_path: Chemin vers l'image du captcha
            
        Returns:
            Le texte du captcha ou None si échec
        """
        if not self.model:
            logger.debug("Gemini non disponible")
            return None
        
        try:
            logger.info(f"🤖 Analyse du captcha avec Gemini: {image_path}")
            
            # Charger l'image
            from PIL import Image
            image = Image.open(image_path)
            
            # Prompt optimisé pour les captchas de préfecture
            prompt = """Analyze this CAPTCHA image carefully.

This is a prefecture (government) CAPTCHA that contains ONLY:
- Letters (uppercase A-Z and lowercase a-z)
- Numbers (0-9)
- NO special characters, NO symbols, NO accents

Your task:
1. Read the text in the image character by character
2. Return ONLY the exact text you see, with NO spaces, NO explanations, NO formatting
3. If you see "D7H4Y5", return exactly: D7H4Y5
4. If you see "abc123", return exactly: abc123

Important rules:
- Be very careful with similar-looking characters (0 vs O, 1 vs l vs I, 5 vs S, 8 vs B)
- Pay attention to uppercase vs lowercase
- ONLY use letters A-Z, a-z and numbers 0-9
- NO special characters like š, ç, é, ñ, etc.
- Return ONLY the captcha text, nothing else

CAPTCHA text:"""
            
            # Envoyer à Gemini
            response = self.model.generate_content([prompt, image])
            
            if response and response.text:
                # Nettoyer la réponse
                result = response.text.strip()
                # Enlever les marqueurs de code si présents
                result = result.replace('`', '').replace('\n', '').replace(' ', '')
                
                # Validation: garder seulement lettres et chiffres (préfecture)
                import re
                cleaned_result = re.sub(r'[^a-zA-Z0-9]', '', result)
                
                if cleaned_result != result:
                    logger.warning(f"⚠️ Caractères invalides supprimés: '{result}' -> '{cleaned_result}'")
                    result = cleaned_result
                
                logger.info(f"✅ Gemini a lu le captcha: '{result}'")
                return result
            else:
                logger.warning("❌ Gemini n'a pas pu lire le captcha")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la résolution avec Gemini: {e}", exc_info=True)
            return None
    
    def solve_captcha_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        Résout un captcha à partir de bytes
        
        Args:
            image_bytes: Bytes de l'image du captcha
            
        Returns:
            Le texte du captcha ou None si échec
        """
        if not self.model:
            return None
        
        try:
            import tempfile
            
            # Sauvegarder temporairement
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            
            # Résoudre
            result = self.solve_captcha_from_file(tmp_path)
            
            # Nettoyer
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution avec Gemini (bytes): {e}")
            return None
    
    def is_available(self) -> bool:
        """Vérifie si Gemini est disponible et configuré"""
        return self.model is not None
