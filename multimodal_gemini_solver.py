#!/usr/bin/env python3
"""
Résolveur Captcha Multimodal avec Gemini Flash (Image + Audio)
"""
import glob
import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class MultimodalGeminiSolver:
    """Résolveur captcha multimodal avec Gemini Flash"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY doit être configuré dans .env")

        genai.configure(api_key=self.api_key)

        # Utiliser Gemini 2.5 Flash qui supporte multimodal
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        print("✅ Gemini 2.5 Flash multimodal initialisé")

    def is_available(self) -> bool:
        """Vérifie si Gemini est disponible"""
        return bool(self.api_key)

    def solve_captcha_multimodal(self, image_path: str, audio_path: str) -> Optional[str]:
        """
        Résout un captcha en utilisant image ET audio simultanément

        Args:
            image_path: Chemin vers l'image captcha
            audio_path: Chemin vers l'audio captcha

        Returns:
            Code captcha résolu ou None
        """
        try:
            print(f"🤖 Analyse multimodale: {image_path} + {audio_path}")

            # Préparer l'image
            image_data = self._prepare_image(image_path)
            if not image_data:
                return None

            # Préparer l'audio
            audio_data = self._prepare_audio(audio_path)
            if not audio_data:
                return None

            # Prompt multimodal optimisé
            prompt = self._create_multimodal_prompt()

            # Génération avec les deux modalités
            response = self.model.generate_content([
                prompt,
                image_data,
                audio_data
            ])

            if not response.text:
                print("❌ Pas de réponse de Gemini")
                return None

            # Nettoyer la réponse
            captcha_code = self._clean_response(response.text)

            print(f"✅ Gemini multimodal: '{captcha_code}'")
            return captcha_code

        except Exception as e:
            print(f"❌ Erreur Gemini multimodal: {e}")
            return None

    def solve_captcha_image_only(self, image_path: str) -> Optional[str]:
        """Résolution image seule (fallback)"""
        try:
            image_data = self._prepare_image(image_path)
            if not image_data:
                return None

            prompt = self._create_image_prompt()

            response = self.model.generate_content([prompt, image_data])

            if not response.text:
                return None

            captcha_code = self._clean_response(response.text)
            print(f"✅ Gemini image: '{captcha_code}'")
            return captcha_code

        except Exception as e:
            print(f"❌ Erreur Gemini image: {e}")
            return None

    def solve_captcha_audio_only(self, audio_path: str) -> Optional[str]:
        """Résolution audio seule (fallback)"""
        try:
            audio_data = self._prepare_audio(audio_path)
            if not audio_data:
                return None

            prompt = self._create_audio_prompt()

            response = self.model.generate_content([prompt, audio_data])

            if not response.text:
                return None

            captcha_code = self._clean_response(response.text)
            print(f"✅ Gemini audio: '{captcha_code}'")
            return captcha_code

        except Exception as e:
            print(f"❌ Erreur Gemini audio: {e}")
            return None

    def _prepare_image(self, image_path: str):
        """Prépare les données image pour Gemini"""
        try:
            from PIL import Image

            # Charger l'image avec PIL
            image = Image.open(image_path)

            return image

        except Exception as e:
            print(f"❌ Erreur préparation image: {e}")
            return None

    def _prepare_audio(self, audio_path: str):
        """Prépare les données audio pour Gemini"""
        try:
            # Pour Gemini 2.5 Flash, on peut passer le chemin directement
            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            # Créer un objet compatible avec l'API
            return {
                "mime_type": "audio/wav",
                "data": audio_data
            }

        except Exception as e:
            print(f"❌ Erreur préparation audio: {e}")
            return None

    def _create_multimodal_prompt(self) -> str:
        """Prompt optimisé pour analyse multimodale"""
        return """Tu reçois un captcha de sécurité d'un site gouvernemental français sous DEUX FORMATS:
1. Une IMAGE avec du texte déformé
2. Un AUDIO qui énonce le même code

INSTRUCTIONS CRITIQUES:
- Analyse SIMULTANEMENT l'image ET l'audio
- Le code contient UNIQUEMENT des lettres (a-z, A-Z) et des chiffres (0-9)
- Aucun symbole, espace ou caractère spécial
- Longueur typique: 5-8 caractères
- Utilise les deux sources pour CONFIRMER le code exact

PROCESSUS:
1. Lis le texte dans l'image (malgré la déformation)
2. Écoute l'audio et transcris ce qui est énoncé
3. Compare les deux résultats
4. Si concordance → réponds avec ce code
5. Si différence → utilise la source la plus claire

RÉPONSE:
Réponds UNIQUEMENT avec le code captcha, rien d'autre.
Exemple: K93TDRK

Code captcha:"""

    def _create_image_prompt(self) -> str:
        """Prompt optimisé pour image seule"""
        return """Tu reçois un captcha de sécurité d'un site gouvernemental français.

CONTRAINTES STRICTES:
- Le code contient UNIQUEMENT des lettres (a-z, A-Z) et des chiffres (0-9)
- Aucun symbole, espace ou caractère spécial
- Longueur typique: 5-8 caractères
- Ignore toute déformation visuelle

Lis attentivement le texte dans cette image déformée.

RÉPONSE:
Réponds UNIQUEMENT avec le code captcha, rien d'autre.
Exemple: V54LpY

Code captcha:"""

    def _create_audio_prompt(self) -> str:
        """Prompt optimisé pour audio seule"""
        return """Tu reçois un captcha audio d'un site gouvernemental français.

CONTRAINTES STRICTES:
- L'audio énonce des lettres et des chiffres
- Le code contient UNIQUEMENT des lettres (a-z, A-Z) et des chiffres (0-9)
- Aucun symbole, espace ou caractère spécial
- Longueur typique: 5-8 caractères

Transcris exactement ce qui est énoncé dans cet audio.

RÉPONSE:
Réponds UNIQUEMENT avec le code captcha, rien d'autre.
Exemple: U42B84U

Code captcha:"""

    def _clean_response(self, response_text: str) -> str:
        """Nettoie la réponse de Gemini"""
        import re

        # Supprimer tout sauf lettres et chiffres
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', response_text.strip())

        return cleaned


def test_multimodal_solver():
    """Test du résolveur multimodal"""
    solver = MultimodalGeminiSolver()

    # Chercher les derniers fichiers capturés
    image_files = glob.glob("screenshots/captcha_image_*.png")
    audio_files = glob.glob("screenshots/captcha_audio_*.wav")

    if not image_files:
        print("❌ Aucune image captcha trouvée")
        print("   Lancez test_hybrid_captcha.py d'abord")
        return

    if not audio_files:
        print("❌ Aucun audio captcha trouvé")
        print("   Lancez test_hybrid_captcha.py d'abord")
        return

    # Prendre les fichiers les plus récents
    latest_image = max(image_files, key=os.path.getctime)
    latest_audio = max(audio_files, key=os.path.getctime)

    print("🎯 TEST MULTIMODAL GEMINI FLASH")
    print("=" * 50)
    print(f"Image: {latest_image}")
    print(f"Audio: {latest_audio}")
    print()

    # Test multimodal
    print("🔥 Test 1: MULTIMODAL (Image + Audio)")
    result_multimodal = solver.solve_captcha_multimodal(
        latest_image, latest_audio)

    print("\n� Test 2: IMAGE seule")
    result_image = solver.solve_captcha_image_only(latest_image)

    print("\n🎧 Test 3: AUDIO seul")
    result_audio = solver.solve_captcha_audio_only(latest_audio)

    # Comparaison
    print("\n📊 COMPARAISON DES RÉSULTATS:")
    print("=" * 50)
    print("🔥 Multimodal: '%s'" % result_multimodal)
    print("🖼️ Image seule: '%s'" % result_image)
    print("🎧 Audio seul: '%s'" % result_audio)

    # Recommandation
    if result_multimodal:
        print("\n💡 RECOMMANDATION: Utiliser résultat multimodal '%s'" %
              result_multimodal)
        return result_multimodal
    elif result_image:
        print("\n💡 FALLBACK: Utiliser résultat image '%s'" % result_image)
        return result_image
    elif result_audio:
        print("\n💡 FALLBACK: Utiliser résultat audio '%s'" % result_audio)
        return result_audio
    else:
        print("\n❌ ÉCHEC: Aucune méthode n'a fonctionné")
        return None


if __name__ == "__main__":
    test_multimodal_solver()
