"""
Tâches Celery pour le scraping automatique des annonces immobilières
"""
import logging
import time
import random
from celery import shared_task
from django.utils import timezone

from .models import SearchZone
from .scrapers import scrape_search_zone, mark_inactive_listings

logger = logging.getLogger(__name__)


@shared_task
def scrape_all_search_zones():
    """
    Scrape toutes les zones de recherche actives
    Optimisé pour éviter les doublons : si plusieurs zones ont les mêmes critères
    (city, radius_km, property_type), ne scrape qu'une seule fois
    """
    try:
        active_zones = SearchZone.objects.filter(is_active=True).select_related('created_by')
        total_listings = 0

        # Grouper les zones par critères identiques (city, radius, property_type)
        from collections import defaultdict
        zones_by_criteria = defaultdict(list)

        for zone in active_zones:
            # Créer une clé unique pour les critères
            criteria_key = (zone.city.lower(), zone.radius_km, zone.property_type)
            zones_by_criteria[criteria_key].append(zone)

        logger.info(f"Scraping de {len(zones_by_criteria)} groupes de zones uniques (total: {active_zones.count()} zones)")

        # Scraper une seule fois par groupe de critères identiques
        for idx, (criteria_key, zones) in enumerate(zones_by_criteria.items()):
            city, radius, prop_type = criteria_key
            # Utiliser la première zone du groupe pour le scraping
            primary_zone = zones[0]

            # Delay aléatoire entre chaque zone (sauf pour la première)
            if idx > 0:
                delay = random.uniform(10, 30)  # 10-30 secondes
                logger.info(f"Attente de {delay:.1f}s avant le prochain scraping...")
                time.sleep(delay)

            logger.info(f"Scraping du groupe : {primary_zone} ({len(zones)} zone(s) avec ces critères)")
            results = scrape_search_zone(primary_zone)

            # Associer les résultats à toutes les zones du groupe
            if len(zones) > 1:
                logger.info(f"Association des résultats aux {len(zones)} zones du groupe")
                # Les listings sont déjà associés à primary_zone dans scrape_search_zone
                # Il faut maintenant les associer aux autres zones du groupe
                for listing in primary_zone.listings.all():
                    for zone in zones[1:]:
                        listing.search_zones.add(zone)

            zone_listings_count = len(results['leboncoin'])
            total_listings += zone_listings_count

            logger.info(f"Groupe {primary_zone}: {zone_listings_count} annonces traitées")

        logger.info(f"Scraping terminé : {total_listings} annonces au total pour {len(zones_by_criteria)} groupes")
        return {
            'status': 'success',
            'zones_scraped': active_zones.count(),
            'unique_criteria_groups': len(zones_by_criteria),
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
        total_listings = len(results['leboncoin'])

        logger.info(f"Zone {zone}: {total_listings} annonces traitées")
        return {
            'status': 'success',
            'zone_id': zone_id,
            'total_listings': total_listings,
            'leboncoin': len(results['leboncoin']),
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
