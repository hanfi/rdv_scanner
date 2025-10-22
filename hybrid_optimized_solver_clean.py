#!/usr/bin/env python3
"""
Résolveur Captcha Hybride Optimisé - Utilise multimodal en priorité
"""
import glob
import os
import re
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv
from gemini_solver import GeminiCaptchaSolver
from multimodal_gemini_solver import MultimodalGeminiSolver

load_dotenv()


class HybridOptimizedSolver:
    """Résolveur hybride avec multimodal en priorité"""

    def __init__(self):
        self.multimodal_solver = MultimodalGeminiSolver()
        self.image_solver = GeminiCaptchaSolver()  # Fallback

        print("✅ Résolveur hybride optimisé initialisé")

    def solve_captcha_with_fallback(
        self, image_path: str, audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Résout un captcha avec stratégie de fallback intelligente

        Priorité:
        1. Multimodal (image + audio) si audio disponible
        2. Image seule en fallback

        Args:
            image_path: Chemin vers l'image captcha
            audio_path: Chemin vers l'audio captcha (optionnel)

        Returns:
            Dict avec résultat et informations de debug
        """
        attempts_list: List[Tuple[str, str, str]] = []
        result: Dict[str, Any] = {
            'status': 'ERROR',
            'text': '',
            'method': '',
            'confidence': 'low',
            'attempts': attempts_list
        }

        # Stratégie 1: Multimodal si audio disponible
        if audio_path and os.path.exists(audio_path):
            print("🔥 Tentative multimodale (image + audio)...")

            multimodal_text = self.multimodal_solver.solve_captcha_multimodal(
                image_path, audio_path)
            if multimodal_text and self._validate_captcha_format(multimodal_text):
                result.update({
                    'status': 'SUCCESS',
                    'text': multimodal_text,
                    'method': 'multimodal',
                    'confidence': 'high'
                })
                result['attempts'].append(
                    ('multimodal', multimodal_text, 'success'))
                return result
            else:
                result['attempts'].append(
                    ('multimodal', multimodal_text or 'null', 'failed'))

        # Stratégie 2: Image seule (fallback)
        print("🖼️ Fallback: Image seule...")

        if self.image_solver.is_available():
            image_text = self.image_solver.solve_captcha_from_file(image_path)
            if image_text and self._validate_captcha_format(image_text):
                result.update({
                    'status': 'SUCCESS',
                    'text': image_text,
                    'method': 'image_only',
                    'confidence': 'medium'
                })
                result['attempts'].append(
                    ('image_only', image_text, 'success'))
                return result
            else:
                result['attempts'].append(
                    ('image_only', image_text or 'null', 'failed'))

        # Stratégie 3: Audio seul si disponible (dernier recours)
        if audio_path and os.path.exists(audio_path):
            print("🎧 Dernier recours: Audio seul...")

            audio_text = self.multimodal_solver.solve_captcha_audio_only(
                audio_path)
            if audio_text and self._validate_captcha_format(audio_text):
                result.update({
                    'status': 'SUCCESS',
                    'text': audio_text,
                    'method': 'audio_only',
                    'confidence': 'low'
                })
                result['attempts'].append(
                    ('audio_only', audio_text, 'success'))
                return result
            else:
                result['attempts'].append(
                    ('audio_only', audio_text or 'null', 'failed'))

        # Échec total
        result.update({
            'status': 'FAILED',
            'text': '',
            'method': 'none',
            'confidence': 'none'
        })

        return result

    def _validate_captcha_format(self, text: str) -> bool:
        """Valide le format du captcha"""
        if not text:
            return False

        # Nettoyer
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text)

        # Vérifier longueur et format
        return 4 <= len(cleaned) <= 10  # Longueur raisonnable


def test_hybrid_solver():
    """Test du résolveur hybride optimisé"""
    solver = HybridOptimizedSolver()

    image_files = glob.glob("screenshots/captcha_image_*.png")
    audio_files = glob.glob("screenshots/captcha_audio_*.wav")

    if not image_files:
        print("❌ Aucune image trouvée. Lancez test_hybrid_captcha.py d'abord")
        return

    latest_image = max(image_files, key=os.path.getctime)
    latest_audio = max(
        audio_files, key=os.path.getctime) if audio_files else None

    print("🎯 TEST RÉSOLVEUR HYBRIDE OPTIMISÉ")
    print("=" * 50)
    print(f"Image: {latest_image}")
    print(f"Audio: {latest_audio or 'Non disponible'}")
    print()

    # Test avec stratégie de fallback
    result = solver.solve_captcha_with_fallback(latest_image, latest_audio)

    print("📊 RÉSULTAT:")
    print(f"   Status: {result['status']}")
    print(f"   Texte: '{result['text']}'")
    print(f"   Méthode: {result['method']}")
    print(f"   Confiance: {result['confidence']}")

    print("\n🔍 TENTATIVES:")
    for i, (method, text, status) in enumerate(result['attempts'], 1):
        print("   %s. %s: '%s' → %s" % (i, method, text, status))

    return result


if __name__ == "__main__":
    test_hybrid_solver()
