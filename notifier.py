"""
Module de notification
Envoie des notifications par email, webhook, etc.
"""
import os
import logging
import json
import requests
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """Gestionnaire de notifications"""
    
    def __init__(self):
        self.email = os.getenv('NOTIFICATION_EMAIL')
        self.webhook_url = os.getenv('NOTIFICATION_WEBHOOK')
    
    def send_notification(self, results: List[Dict[str, Any]]):
        """
        Envoie une notification avec les résultats
        
        Args:
            results: Liste des résultats de disponibilité
        """
        available_results = [r for r in results if r.get('available')]
        
        if not available_results:
            return
        
        message = self._format_message(available_results)
        
        # Envoyer par webhook si configuré
        if self.webhook_url:
            self._send_webhook(message, available_results)
        
        # Log de la notification
        logger.info("=" * 60)
        logger.info("NOTIFICATION: RENDEZ-VOUS DISPONIBLE(S)")
        logger.info("=" * 60)
        logger.info(message)
        logger.info("=" * 60)
    
    def _format_message(self, results: List[Dict[str, Any]]) -> str:
        """Formate le message de notification"""
        lines = ["🎉 RENDEZ-VOUS DISPONIBLE(S) DÉTECTÉ(S)!", ""]
        
        for result in results:
            lines.append(f"📍 {result['page']}")
            lines.append(f"   URL: {result['url']}")
            lines.append(f"   Message: {result['message']}")
            lines.append(f"   Heure: {result['timestamp']}")
            
            if 'details' in result:
                details = result['details']
                if details.get('button_count'):
                    lines.append(f"   Boutons trouvés: {details['button_count']}")
                if details.get('date_selectors'):
                    lines.append(f"   Sélecteurs de date: {details['date_selectors']}")
            
            lines.append("")
        
        lines.append("⏰ Agissez rapidement!")
        
        return "\n".join(lines)
    
    def _send_webhook(self, message: str, results: List[Dict[str, Any]]):
        """
        Envoie une notification via webhook
        
        Args:
            message: Message formaté
            results: Résultats bruts
        """
        try:
            # Format Slack optimisé avec liens cliquables
            payload = {
                "text": "🚨 *RENDEZ-VOUS DISPONIBLE DÉTECTÉ!*",
                "attachments": [
                    {
                        "color": "good",
                        "title": f"🎯 {result['page']}",
                        "title_link": result['url'],
                        "text": f"{result['message']}\n\n🔗 *Lien direct:* <{result['url']}|Réserver maintenant>",
                        "fields": [
                            {
                                "title": "📅 Détection",
                                "value": result['timestamp'][:19].replace('T', ' '),
                                "short": True
                            },
                            {
                                "title": "⚡ Action",
                                "value": f"<{result['url']}|Ouvrir la page>",
                                "short": True
                            }
                        ],
                        "footer": "RDV Scanner • Agissez vite!",
                        "footer_icon": "https://🚀",
                        "ts": int(datetime.fromisoformat(result['timestamp']).timestamp())
                    }
                    for result in results
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Notification webhook envoyée avec succès")
            else:
                logger.warning(f"Échec d'envoi du webhook: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du webhook: {e}", exc_info=True)
