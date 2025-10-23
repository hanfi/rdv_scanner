#!/usr/bin/env python3
"""
Résolveur Captcha Multimodal avec Gemini Flash (Image + Audio)
"""
import glob
import os
from typing import List, Optional, Tuple
import logging
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class MultimodalGeminiSolver:
    """Résolveur captcha multimodal avec Gemini Flash"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY doit être configuré dans .env")

        genai.configure(api_key=self.api_key)

        # Liste prioritaire de modèles (séparés par des virgules) configurable via .env
        # Ajouter ici les modèles recommandés en fallback pour éviter le rate limiting
        # Priorité demandée : meilleure qualité puis fallback moins puissants
        default_priority = (
            "gemini-2.5-flash,gemini-2.0-flash-exp,gemini-2.0-flash,gemini-2.5-flash-lite,gemini-2.0-flash-lite,gemini-2.5-pro"
        )

        priority_env = os.getenv('GEMINI_MODEL_PRIORITY', default_priority)
        models = [m.strip() for m in priority_env.split(',') if m.strip()]

        self.model_candidates: List[Tuple[str, genai.GenerativeModel]] = []
        for model_name in models:
            try:
                candidate_model = genai.GenerativeModel(model_name)
                self.model_candidates.append((model_name, candidate_model))
                logger.info(f"✅ Modèle Gemini disponible: {model_name}")
            except Exception as err:
                logger.warning(f"⚠️ Impossible d'initialiser le modèle {model_name}: {err}")

        if not self.model_candidates:
            raise RuntimeError(
                "Aucun modèle Gemini disponible parmi la liste de priorité. Vérifiez GEMINI_API_KEY et GEMINI_MODEL_PRIORITY"
            )

        self._preferred_index = 0
        self.model_name, self.model = self.model_candidates[self._preferred_index]

        multimodal_env = os.getenv('GEMINI_MULTIMODAL_MODELS')
        if multimodal_env:
            self._multimodal_whitelist = {m.strip() for m in multimodal_env.split(',') if m.strip()}
        else:
            self._multimodal_whitelist = None

        self.supports_multimodal = self._model_supports_multimodal(self.model_name)

        logger.info(f"🔍 Support multimodal: {self.supports_multimodal} (modèle: {self.model_name})")
        if len(self.model_candidates) > 1:
            fallback_names = ', '.join(name for name, _ in self.model_candidates[1:])
            if fallback_names:
                logger.info(f"➡️ Fallbacks disponibles: {fallback_names}")

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
        image_data = self._prepare_image(image_path)
        if not image_data:
            return None

        audio_data = self._prepare_audio(audio_path)
        if not audio_data:
            return None

        prompt = self._create_multimodal_prompt()
        last_error: Optional[Exception] = None

        for index, (model_name, model_instance) in self._iterate_candidates():
            supports_multimodal = self._model_supports_multimodal(model_name)
            if not supports_multimodal:
                logger.info(f"⏭️ Modèle {model_name} ignoré (pas de support multimodal déclaré)")
                continue

            logger.info(f"🤖 Analyse multimodale avec modèle '{model_name}': {image_path} + {audio_path}")

            try:
                response = model_instance.generate_content([prompt, image_data, audio_data])
                text = getattr(response, 'text', None)
                if not text:
                    logger.warning(f"❌ Pas de réponse de Gemini pour le modèle {model_name}")
                    continue

                captcha_code = self._clean_response(text)
                logger.info(f"✅ Gemini multimodal (modèle {model_name}): '{captcha_code}'")
                self._set_active_model(index, supports_multimodal)
                return captcha_code

            except Exception as error:
                last_error = error
                if self._is_rate_limit_error(error):
                    logger.warning(f"⏳ Rate limit sur le modèle {model_name}, essai du suivant")
                    continue

                logger.error(f"❌ Erreur Gemini multimodal ({model_name}): {error}")
                continue

        if last_error:
            logger.error(f"❌ Tous les modèles multimodaux ont échoué. Dernière erreur: {last_error}")
        else:
            logger.error("❌ Aucun modèle multimodal n'a pu répondre.")
        return None

    def solve_captcha_image_only(self, image_path: str, image_data=None) -> Optional[str]:
        """Résolution image seule (fallback)"""
        try:
            if image_data is None:
                image_data = self._prepare_image(image_path)
            if not image_data:
                return None

            prompt = self._create_image_prompt()
            last_error: Optional[Exception] = None

            for index, (model_name, model_instance) in self._iterate_candidates():
                logger.info(f"🖼️ Résolution image-only avec modèle '{model_name}'")
                try:
                    response = model_instance.generate_content([prompt, image_data])
                    text = getattr(response, 'text', None)
                    if not text:
                        logger.warning(f"❌ Pas de réponse de Gemini pour le modèle {model_name}")
                        continue

                    captcha_code = self._clean_response(text)
                    logger.info(f"✅ Gemini image (modèle {model_name}): '{captcha_code}'")
                    supports_multimodal = self._model_supports_multimodal(model_name)
                    self._set_active_model(index, supports_multimodal)
                    return captcha_code

                except Exception as error:
                    last_error = error
                    if self._is_rate_limit_error(error):
                        logger.warning(f"⏳ Rate limit sur le modèle {model_name}, essai du suivant")
                        continue

                    logger.error(f"❌ Erreur Gemini image ({model_name}): {error}")
                    continue

            if last_error:
                logger.error(f"❌ Tous les modèles image-only ont échoué. Dernière erreur: {last_error}")
            else:
                logger.error("❌ Aucun modèle n'a pu traiter l'image.")
            return None

        except Exception as error:
            logger.error(f"❌ Erreur Gemini image: {error}")
            return None

    def solve_captcha_audio_only(self, audio_path: str, audio_data=None) -> Optional[str]:
        """Résolution audio seule (fallback)"""
        try:
            if audio_data is None:
                audio_data = self._prepare_audio(audio_path)
            if not audio_data:
                return None

            prompt = self._create_audio_prompt()
            last_error: Optional[Exception] = None

            for index, (model_name, model_instance) in self._iterate_candidates():
                supports_multimodal = self._model_supports_multimodal(model_name)
                if not supports_multimodal:
                    logger.info(f"⏭️ Modèle {model_name} ignoré (pas de support multimodal déclaré)")
                    continue

                logger.info(f"🎧 Résolution audio-only avec modèle '{model_name}'")
                try:
                    response = model_instance.generate_content([prompt, audio_data])
                    text = getattr(response, 'text', None)
                    if not text:
                        logger.warning(f"❌ Pas de réponse de Gemini pour le modèle {model_name}")
                        continue

                    captcha_code = self._clean_response(text)
                    logger.info(f"✅ Gemini audio (modèle {model_name}): '{captcha_code}'")
                    self._set_active_model(index, supports_multimodal)
                    return captcha_code

                except Exception as error:
                    last_error = error
                    if self._is_rate_limit_error(error):
                        logger.warning(f"⏳ Rate limit sur le modèle {model_name}, essai du suivant")
                        continue

                    logger.error(f"❌ Erreur Gemini audio ({model_name}): {error}")
                    continue

            if last_error:
                logger.error(f"❌ Tous les modèles audio-only ont échoué. Dernière erreur: {last_error}")
            else:
                logger.error("❌ Aucun modèle n'a pu traiter l'audio.")
            return None

        except Exception as error:
            logger.error(f"❌ Erreur Gemini audio: {error}")
            return None

    def _iterate_candidates(self):
        """Itère sur les candidats en commençant par le modèle préféré."""
        total = len(self.model_candidates)
        for offset in range(total):
            index = (self._preferred_index + offset) % total
            yield index, self.model_candidates[index]

    def _set_active_model(self, index: int, supports_multimodal: bool) -> None:
        """Mémorise le modèle actif après un succès."""
        self._preferred_index = index
        self.model_name, self.model = self.model_candidates[index]
        self.supports_multimodal = supports_multimodal

    def _model_supports_multimodal(self, model_name: str) -> bool:
        """Indique si un modèle supporte image+audio selon la configuration."""
        if self._multimodal_whitelist is None:
            return True
        return model_name in self._multimodal_whitelist

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Détecte les erreurs liées au rate limit pour déclencher un fallback."""
        keywords = (
            "rate limit",
            "quota",
            "429",
            "resource exhausted",
            "too many requests",
        )
        message = str(error).lower()
        if any(keyword in message for keyword in keywords):
            return True

        code = getattr(error, 'code', None)
        if code in (429, '429'):
            return True

        status = getattr(error, 'status', None)
        if status in (429, 'RESOURCE_EXHAUSTED', 'TOO_MANY_REQUESTS'):
            return True

        status_code = getattr(error, 'status_code', None)
        if status_code in (429, '429'):
            return True

        try:
            from google.api_core import exceptions as google_exceptions
            if isinstance(error, (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests)):
                return True
        except Exception:
            # google.api_core peut ne pas être présent ou ne pas exposer ces exceptions
            pass

        return False

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
