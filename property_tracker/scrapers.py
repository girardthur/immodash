"""
Scrapers pour récupérer les annonces immobilières depuis Leboncoin et SeLoger
"""
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from lbc import LeboncoinAPI
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from .models import SearchZone, Listing, PriceHistory, Source, PropertyType

logger = logging.getLogger(__name__)


class BaseScraper:
    """Classe de base pour les scrapers"""

    def __init__(self, search_zone: SearchZone):
        self.search_zone = search_zone

    def scrape(self) -> List[Dict]:
        """Méthode à implémenter par les scrapers"""
        raise NotImplementedError

    def save_or_update_listing(self, listing_data: Dict) -> Optional[Listing]:
        """
        Sauvegarde ou met à jour une annonce et son historique de prix
        """
        try:
            external_id = listing_data['external_id']
            source = listing_data['source']

            # Vérifier si l'annonce existe déjà
            listing, created = Listing.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'search_zone': self.search_zone,
                    'source': source,
                    'url': listing_data['url'],
                    'title': listing_data['title'],
                    'description': listing_data.get('description', ''),
                    'property_type': listing_data['property_type'],
                    'current_price': listing_data['price'],
                    'surface': listing_data.get('surface'),
                    'rooms': listing_data.get('rooms'),
                    'bedrooms': listing_data.get('bedrooms'),
                    'city': listing_data['city'],
                    'postal_code': listing_data.get('postal_code', ''),
                    'latitude': listing_data.get('latitude'),
                    'longitude': listing_data.get('longitude'),
                }
            )

            if created:
                # Nouvelle annonce : créer l'entrée initiale dans l'historique
                PriceHistory.objects.create(
                    listing=listing,
                    price=listing.current_price,
                    price_per_sqm=listing.price_per_sqm,
                )
                logger.info(f"Nouvelle annonce créée : {listing.title} - {listing.current_price}€")
            else:
                # Annonce existante : vérifier si le prix a changé
                if listing.current_price != Decimal(str(listing_data['price'])):
                    old_price = listing.current_price
                    new_price = Decimal(str(listing_data['price']))

                    # Calculer le pourcentage de changement
                    change_percent = ((new_price - old_price) / old_price) * 100

                    # Mettre à jour l'annonce
                    listing.current_price = new_price
                    listing.has_price_changed = True
                    listing.last_price_change_date = timezone.now()
                    listing.last_price_change_percent = change_percent

                    # Recalculer le prix au m²
                    if listing.surface and listing.surface > 0:
                        listing.price_per_sqm = new_price / listing.surface

                    listing.save()

                    # Ajouter l'entrée dans l'historique
                    PriceHistory.objects.create(
                        listing=listing,
                        price=new_price,
                        price_per_sqm=listing.price_per_sqm,
                        change_percent=change_percent,
                    )

                    logger.info(f"Changement de prix détecté : {listing.title} - {old_price}€ → {new_price}€ ({change_percent:.2f}%)")
                else:
                    # Pas de changement de prix, juste mettre à jour last_seen_at
                    listing.save()

            return listing

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'annonce : {e}")
            return None


class LeboncoinScraper(BaseScraper):
    """Scraper pour Leboncoin utilisant la bibliothèque lbc"""

    def scrape(self) -> List[Listing]:
        """
        Scrape les annonces depuis Leboncoin
        """
        try:
            api = LeboncoinAPI()

            # Déterminer le type de catégorie
            if self.search_zone.property_type == PropertyType.APARTMENT:
                category = 'ventes_immobilieres'  # À ajuster selon l'API lbc
            elif self.search_zone.property_type == PropertyType.HOUSE:
                category = 'ventes_immobilieres'
            else:
                category = 'ventes_immobilieres'

            # Rechercher les annonces
            # Note: Cette partie doit être adaptée selon la documentation de lbc
            # Voici une implémentation de base
            search_params = {
                'location': self.search_zone.city,
                'radius': self.search_zone.radius_km * 1000,  # Convertir en mètres
                'category': category,
            }

            results = api.search(**search_params)

            listings = []
            for item in results:
                # Extraire les données de l'annonce
                listing_data = self._parse_leboncoin_item(item)
                if listing_data:
                    listing = self.save_or_update_listing(listing_data)
                    if listing:
                        listings.append(listing)

            return listings

        except Exception as e:
            logger.error(f"Erreur lors du scraping Leboncoin : {e}")
            return []

    def _parse_leboncoin_item(self, item) -> Optional[Dict]:
        """
        Parse un item Leboncoin et retourne un dictionnaire avec les données
        """
        try:
            # Déterminer le type de propriété
            property_type = PropertyType.APARTMENT  # Par défaut
            if 'attributes' in item:
                real_estate_type = item.get('attributes', {}).get('real_estate_type', '')
                if 'maison' in real_estate_type.lower():
                    property_type = PropertyType.HOUSE

            return {
                'external_id': f"lbc_{item.get('list_id', '')}",
                'source': Source.LEBONCOIN,
                'url': item.get('url', ''),
                'title': item.get('subject', ''),
                'description': item.get('body', ''),
                'property_type': property_type,
                'price': item.get('price', [0])[0] if isinstance(item.get('price'), list) else item.get('price', 0),
                'surface': item.get('attributes', {}).get('square', None),
                'rooms': item.get('attributes', {}).get('rooms', None),
                'bedrooms': item.get('attributes', {}).get('bedrooms', None),
                'city': item.get('location', {}).get('city', self.search_zone.city),
                'postal_code': item.get('location', {}).get('zipcode', ''),
                'latitude': item.get('location', {}).get('lat', None),
                'longitude': item.get('location', {}).get('lng', None),
            }
        except Exception as e:
            logger.error(f"Erreur lors du parsing de l'item Leboncoin : {e}")
            return None


class SeLogerScraper(BaseScraper):
    """Scraper pour SeLoger (implémentation basique avec BeautifulSoup)"""

    def scrape(self) -> List[Listing]:
        """
        Scrape les annonces depuis SeLoger
        Note: Cette implémentation est basique et devra être adaptée
        selon la structure HTML de SeLoger et ses protections anti-scraping
        """
        try:
            # Construire l'URL de recherche
            # Cette URL est un exemple et devra être adaptée
            property_types = []
            if self.search_zone.property_type in [PropertyType.APARTMENT, PropertyType.BOTH]:
                property_types.append('1')  # Appartement
            if self.search_zone.property_type in [PropertyType.HOUSE, PropertyType.BOTH]:
                property_types.append('2')  # Maison

            base_url = "https://www.seloger.com/list.htm"
            params = {
                'types': ','.join(property_types),
                'projects': '2',  # Achat
                'places': self.search_zone.city,
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Note: SeLoger a des protections anti-scraping
            # Cette implémentation est basique et peut nécessiter:
            # - L'utilisation de proxies
            # - La gestion de CAPTCHAs
            # - L'utilisation de Playwright/Selenium pour JavaScript

            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            listings = []
            # Cette partie doit être adaptée selon la structure HTML actuelle de SeLoger
            # Voici un exemple de structure
            listing_cards = soup.find_all('article', class_='listing')  # À adapter

            for card in listing_cards:
                listing_data = self._parse_seloger_card(card)
                if listing_data:
                    listing = self.save_or_update_listing(listing_data)
                    if listing:
                        listings.append(listing)

            return listings

        except requests.RequestException as e:
            logger.error(f"Erreur lors de la requête SeLoger : {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors du scraping SeLoger : {e}")
            return []

    def _parse_seloger_card(self, card) -> Optional[Dict]:
        """
        Parse une carte d'annonce SeLoger
        Note: Cette méthode doit être adaptée selon la structure HTML actuelle
        """
        try:
            # Exemple de parsing - à adapter selon la structure réelle
            external_id = card.get('data-listing-id', '')
            if not external_id:
                return None

            title = card.find('h2', class_='title')  # À adapter
            price_elem = card.find('span', class_='price')  # À adapter
            surface_elem = card.find('span', class_='surface')  # À adapter

            if not all([title, price_elem]):
                return None

            # Extraction et nettoyage des données
            price_text = price_elem.text.strip().replace('€', '').replace(' ', '').replace('\xa0', '')
            price = Decimal(price_text)

            surface = None
            if surface_elem:
                surface_text = surface_elem.text.strip().replace('m²', '').replace(' ', '')
                try:
                    surface = Decimal(surface_text)
                except:
                    pass

            return {
                'external_id': f"seloger_{external_id}",
                'source': Source.SELOGER,
                'url': f"https://www.seloger.com/annonces/achat/{external_id}",
                'title': title.text.strip(),
                'description': '',  # À extraire si disponible
                'property_type': PropertyType.APARTMENT,  # À déterminer depuis les données
                'price': price,
                'surface': surface,
                'rooms': None,  # À extraire si disponible
                'bedrooms': None,
                'city': self.search_zone.city,
                'postal_code': '',
                'latitude': None,
                'longitude': None,
            }
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la carte SeLoger : {e}")
            return None


def scrape_search_zone(search_zone: SearchZone) -> Dict[str, List[Listing]]:
    """
    Scrape toutes les sources pour une zone de recherche donnée
    """
    results = {
        'leboncoin': [],
        'seloger': [],
    }

    # Scraper Leboncoin
    try:
        leboncoin_scraper = LeboncoinScraper(search_zone)
        results['leboncoin'] = leboncoin_scraper.scrape()
        logger.info(f"Leboncoin: {len(results['leboncoin'])} annonces trouvées pour {search_zone}")
    except Exception as e:
        logger.error(f"Erreur Leboncoin pour {search_zone}: {e}")

    # Scraper SeLoger
    try:
        seloger_scraper = SeLogerScraper(search_zone)
        results['seloger'] = seloger_scraper.scrape()
        logger.info(f"SeLoger: {len(results['seloger'])} annonces trouvées pour {search_zone}")
    except Exception as e:
        logger.error(f"Erreur SeLoger pour {search_zone}: {e}")

    return results


def mark_inactive_listings():
    """
    Marque comme vendues les annonces qui n'ont pas été vues depuis plus de 24h
    """
    from datetime import timedelta

    cutoff_time = timezone.now() - timedelta(hours=24)

    inactive_listings = Listing.objects.filter(
        is_active=True,
        last_seen_at__lt=cutoff_time
    )

    count = inactive_listings.count()
    inactive_listings.update(
        is_active=False,
        sold_at=timezone.now()
    )

    logger.info(f"{count} annonces marquées comme vendues")
    return count
