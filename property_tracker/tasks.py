"""
Tâches Celery pour le scraping automatique des annonces immobilières
"""
import logging
from celery import shared_task
from django.utils import timezone

from .models import SearchZone
from .scrapers import scrape_search_zone, mark_inactive_listings

logger = logging.getLogger(__name__)


@shared_task
def scrape_all_search_zones():
    """
    Scrape toutes les zones de recherche actives
    """
    try:
        active_zones = SearchZone.objects.filter(is_active=True).select_related('user')
        total_listings = 0

        for zone in active_zones:
            logger.info(f"Scraping de la zone : {zone}")
            results = scrape_search_zone(zone)

            zone_listings_count = len(results['leboncoin']) + len(results['seloger'])
            total_listings += zone_listings_count

            logger.info(f"Zone {zone}: {zone_listings_count} annonces traitées")

        logger.info(f"Scraping terminé : {total_listings} annonces au total")
        return {
            'status': 'success',
            'zones_scraped': active_zones.count(),
            'total_listings': total_listings,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erreur lors du scraping de toutes les zones : {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def scrape_single_zone(zone_id: int):
    """
    Scrape une seule zone de recherche
    """
    try:
        zone = SearchZone.objects.get(id=zone_id, is_active=True)
        logger.info(f"Scraping de la zone : {zone}")

        results = scrape_search_zone(zone)
        total_listings = len(results['leboncoin']) + len(results['seloger'])

        logger.info(f"Zone {zone}: {total_listings} annonces traitées")
        return {
            'status': 'success',
            'zone_id': zone_id,
            'total_listings': total_listings,
            'leboncoin': len(results['leboncoin']),
            'seloger': len(results['seloger']),
            'timestamp': timezone.now().isoformat()
        }

    except SearchZone.DoesNotExist:
        logger.error(f"Zone de recherche {zone_id} introuvable ou inactive")
        return {
            'status': 'error',
            'error': f'Zone {zone_id} not found',
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors du scraping de la zone {zone_id} : {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def check_inactive_listings():
    """
    Vérifie et marque comme vendues les annonces inactives
    """
    try:
        logger.info("Vérification des annonces inactives")
        count = mark_inactive_listings()

        return {
            'status': 'success',
            'inactive_count': count,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des annonces inactives : {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def periodic_scraping_task():
    """
    Tâche périodique qui scrape toutes les zones et vérifie les annonces inactives
    Cette tâche doit être exécutée toutes les 30 minutes
    """
    logger.info("Démarrage de la tâche périodique de scraping")

    # Scraper toutes les zones
    scraping_result = scrape_all_search_zones()

    # Vérifier les annonces inactives
    inactive_result = check_inactive_listings()

    return {
        'scraping': scraping_result,
        'inactive_check': inactive_result,
        'timestamp': timezone.now().isoformat()
    }
