"""
Analyseur spécifique pour les pages de la préfecture
"""
import logging
from typing import Dict, Any
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class PrefectureAnalyzer:
    """Analyseur optimisé pour les pages rdv-prefecture.interieur.gouv.fr"""
    
    @staticmethod
    def analyze_cgu_page(page: Page) -> Dict[str, Any]:
        """
        Analyse une page CGU de la préfecture
        
        Returns:
            Dict avec les informations de la page
        """
        result = {
            'on_cgu_page': False,
            'has_accept_button': False,
            'has_error_message': False,
            'message': ''
        }
        
        try:
            # Vérifier si on est sur la page CGU
            if 'cgu' in page.url:
                result['on_cgu_page'] = True
                logger.info("Sur la page CGU")
            
            # Chercher le bouton "J'accepte"
            accept_buttons = page.locator('button, input[type="submit"], a').filter(
                has_text=['accepte', 'Accepter', 'Continuer', 'Suivant', 'Valider']
            )
            
            if accept_buttons.count() > 0:
                result['has_accept_button'] = True
                result['message'] = f"Bouton d'acceptation trouvé ({accept_buttons.count()})"
                logger.info(f"Bouton d'acceptation trouvé: {accept_buttons.count()}")
            
            # Vérifier les messages d'erreur
            error_patterns = [
                'aucun créneau',
                'aucune disponibilité',
                'complet',
                'indisponible',
                'fermé',
                'pas de rendez-vous'
            ]
            
            body_text = page.locator('body').inner_text().lower()
            
            for pattern in error_patterns:
                if pattern in body_text:
                    result['has_error_message'] = True
                    result['message'] = f"Message détecté: {pattern}"
                    logger.info(f"Message d'erreur détecté: {pattern}")
                    break
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
            result['message'] = f"Erreur: {str(e)}"
        
        return result
    
    @staticmethod
    def scroll_page_down(page: Page):
        """Scrolle progressivement la page vers le bas"""
        try:
            # Scroll en plusieurs étapes pour charger le contenu
            for i in range(3):
                page.evaluate(f'window.scrollBy(0, {500 + i * 200})')
                page.wait_for_timeout(500)
            logger.info("Scroll effectué vers le bas de la page")
        except Exception as e:
            logger.warning(f"Erreur lors du scroll: {e}")
    
    @staticmethod
    def click_accept_and_continue(page: Page) -> bool:
        """
        Clique sur le bouton d'acceptation CGU et continue
        
        Returns:
            True si réussi, False sinon
        """
        try:
            logger.info("Recherche du bouton d'acceptation...")
            
            # Scroll pour voir tout le contenu
            PrefectureAnalyzer.scroll_page_down(page)
            
            # Variantes de boutons possibles
            button_selectors = [
                'button:has-text("accepte")',
                'button:has-text("Accepter")',
                'input[type="submit"][value*="accepte" i]',
                'input[type="submit"][value*="continuer" i]',
                'button:has-text("Continuer")',
                'button:has-text("Suivant")',
                'a:has-text("Continuer")'
            ]
            
            for selector in button_selectors:
                try:
                    button = page.locator(selector).first
                    if button.is_visible(timeout=1000):
                        logger.info(f"Clic sur le bouton: {selector}")
                        button.click()
                        
                        # Attendre la navigation
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=5000)
                        except:
                            pass
                        
                        page.wait_for_timeout(2000)
                        logger.info(f"Navigation réussie vers: {page.url}")
                        return True
                except Exception as e:
                    logger.debug(f"Sélecteur {selector} non trouvé: {e}")
                    continue
            
            logger.warning("Aucun bouton d'acceptation trouvé")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors du clic: {e}", exc_info=True)
            return False
    
    @staticmethod
    def check_calendar_availability(page: Page) -> Dict[str, Any]:
        """
        Vérifie la disponibilité sur la page du calendrier
        
        Returns:
            Dict avec les informations de disponibilité
        """
        result = {
            'available': False,
            'message': 'Analyse en cours...',
            'details': {}
        }
        
        try:
            body_text = page.locator('body').inner_text().lower()
            page_url = page.url.lower()
            
            # Vérifier d'abord si on est bloqué par Cloudflare
            cloudflare_indicators = [
                'sorry, you have been blocked',
                'you are unable to access',
                'this website is using a security service',
                'cloudflare ray id',
                'error 1020'
            ]
            
            for indicator in cloudflare_indicators:
                if indicator in body_text:
                    result['available'] = False
                    result['message'] = f"⚠️ Bloqué par Cloudflare: {indicator}"
                    logger.warning(f"Page bloquée par Cloudflare: {indicator}")
                    return result
            
            # Vérifier si on est sur une page d'erreur
            if 'error=' in page_url or 'erreur' in body_text:
                result['available'] = False
                result['message'] = "Page d'erreur détectée"
                logger.warning("Page d'erreur détectée")
                return result
            
            # Messages d'indisponibilité de la préfecture
            unavailable_messages = [
                'aucun créneau disponible',
                'aucune disponibilité',
                'pas de rendez-vous disponible',
                'tous les créneaux sont complets',
                'aucun rendez-vous disponible',
                'il n\'y a pas de place disponible',
                'aucun créneau',
                'pas de créneau',
                'veuillez réessayer ultérieurement'
            ]
            
            # Messages de disponibilité
            available_messages = [
                'choisissez votre créneau',
                'sélectionnez un créneau',
                'créneau disponible',
                'places disponibles',
                'choisissez le lieu',
                'sélectionnez un lieu',
                'choix du rendez-vous',
                'prendre rendez-vous'
            ]
            
            logger.info(f"📄 Analyse du contenu de la page (extrait): {body_text[:500]}")
            
            # Vérifier les messages d'indisponibilité
            for msg in unavailable_messages:
                if msg in body_text:
                    result['available'] = False
                    result['message'] = f"Indisponible: '{msg}'"
                    logger.info(f"❌ Indisponible: {msg}")
                    return result
            
            # Vérifier les messages de disponibilité
            for msg in available_messages:
                if msg in body_text:
                    result['available'] = True
                    result['message'] = f"Disponible: '{msg}'"
                    logger.info(f"✅ Disponible: {msg}")
                    return result
            
            # Chercher des boutons/liens de choix de lieu ou date
            location_selectors = page.locator(
                'button:has-text("lieu"), '
                'a:has-text("lieu"), '
                'select[name*="lieu"], '
                'button[class*="location"], '
                'a[href*="lieu"]'
            )
            
            if location_selectors.count() > 0:
                result['available'] = True
                result['message'] = f"Sélecteurs de lieu trouvés ({location_selectors.count()})"
                logger.info(f"✅ {location_selectors.count()} sélecteurs de lieu disponibles")
                return result
            
            # Chercher des créneaux horaires (format HH:MM)
            time_slots = page.locator('button, a, div').filter(
                has_text=[':00', ':15', ':30', ':45']
            )
            
            if time_slots.count() > 0:
                result['available'] = True
                result['message'] = f"Créneaux horaires trouvés ({time_slots.count()})"
                result['details']['time_slots'] = time_slots.count()
                logger.info(f"✅ {time_slots.count()} créneaux horaires trouvés")
                return result
            
            # Chercher des éléments de calendrier
            calendar_elements = page.locator(
                '.calendar, .datepicker, input[type="date"], '
                '[class*="calendar"], [class*="date"], [id*="calendar"]'
            ).count()
            
            if calendar_elements > 0:
                result['details']['calendar_elements'] = calendar_elements
                
                # Chercher des jours sélectionnables
                clickable_days = page.locator(
                    'button[class*="day"]:not([disabled]), '
                    'a[class*="day"], '
                    '[class*="available"]'
                ).count()
                
                if clickable_days > 0:
                    result['available'] = True
                    result['message'] = f"Calendrier avec {clickable_days} jours disponibles"
                    result['details']['clickable_days'] = clickable_days
                    logger.info(f"✅ {clickable_days} jours disponibles dans le calendrier")
                    return result
            
            # Si on n'a rien trouvé de concluant
            # Vérifier si on a au moins du contenu utile
            if len(body_text.strip()) < 50:
                result['message'] = "Page quasiment vide - possiblement bloquée"
                logger.warning("⚠️ Page quasiment vide")
            elif 'javascript' in body_text or 'veuillez activer' in body_text:
                result['message'] = "Page nécessite JavaScript - contenu non chargé"
                logger.warning("⚠️ Page nécessite JavaScript")
            else:
                result['message'] = "Aucun indicateur clair de disponibilité"
                logger.info("⚠️ Aucun indicateur clair")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}", exc_info=True)
            result['message'] = f"Erreur: {str(e)}"
        
        return result
