"""
Scrapers pour récupérer les annonces immobilières depuis Leboncoin
"""
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from lbc import Client, Category, City
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
            # Créer un client Leboncoin
            client = Client()

            # Utiliser la catégorie ventes immobilières
            category = Category.IMMOBILIER_VENTES_IMMOBILIERES

            # Construire les paramètres de recherche
            # On utilise le nom de la ville comme texte de recherche
            # Le rayon en mètres (lbc utilise des mètres par défaut)
            search_params = {
                'category': category,
                'text': self.search_zone.city,
                'limit': 100,  # Limite par page
            }

            # Filtres supplémentaires selon le type de propriété
            if self.search_zone.property_type == PropertyType.APARTMENT:
                search_params['real_estate_type'] = 1  # 1 = appartement
            elif self.search_zone.property_type == PropertyType.HOUSE:
                search_params['real_estate_type'] = 2  # 2 = maison
            # BOTH = pas de filtre sur le type

            # Effectuer la recherche
            search_result = client.search(**search_params)

            listings = []
            for ad in search_result.ads:
                # Extraire les données de l'annonce
                listing_data = self._parse_leboncoin_ad(ad)
                if listing_data:
                    listing = self.save_or_update_listing(listing_data)
                    if listing:
                        listings.append(listing)

            logger.info(f"Scraping terminé : {len(listings)} annonces traitées pour {self.search_zone}")
            return listings

        except Exception as e:
            logger.error(f"Erreur lors du scraping Leboncoin pour {self.search_zone}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _parse_leboncoin_ad(self, ad) -> Optional[Dict]:
        """
        Parse un objet Ad de lbc et retourne un dictionnaire avec les données
        """
        try:
            # Déterminer le type de propriété à partir des attributs
            property_type = PropertyType.APARTMENT  # Par défaut
            surface = None
            rooms = None
            bedrooms = None

            # Extraire les attributs de l'annonce
            for attr in ad.attributes:
                if attr.key == 'real_estate_type':
                    # 1 = appartement, 2 = maison
                    if attr.value == '2':
                        property_type = PropertyType.HOUSE
                    elif attr.value == '1':
                        property_type = PropertyType.APARTMENT
                elif attr.key == 'square':
                    try:
                        surface = float(attr.value) if attr.value else None
                    except (ValueError, TypeError):
                        surface = None
                elif attr.key == 'rooms':
                    try:
                        rooms = int(attr.value) if attr.value else None
                    except (ValueError, TypeError):
                        rooms = None
                elif attr.key == 'bedrooms':
                    try:
                        bedrooms = int(attr.value) if attr.value else None
                    except (ValueError, TypeError):
                        bedrooms = None

            # Extraire les données de localisation
            city = self.search_zone.city
            postal_code = ''
            latitude = None
            longitude = None

            if ad.location:
                city = ad.location.city or city
                postal_code = ad.location.zipcode or ''
                latitude = ad.location.lat
                longitude = ad.location.lng

            return {
                'external_id': f"lbc_{ad.id}",
                'source': Source.LEBONCOIN,
                'url': ad.url,
                'title': ad.subject,
                'description': ad.body or '',
                'property_type': property_type,
                'price': float(ad.price) if ad.price else 0,
                'surface': surface,
                'rooms': rooms,
                'bedrooms': bedrooms,
                'city': city,
                'postal_code': postal_code,
                'latitude': latitude,
                'longitude': longitude,
            }
        except Exception as e:
            logger.error(f"Erreur lors du parsing de l'annonce {ad.id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def scrape_search_zone(search_zone: SearchZone) -> Dict[str, List[Listing]]:
    """
    Scrape toutes les sources pour une zone de recherche donnée
    """
    results = {
        'leboncoin': [],
    }

    # Scraper Leboncoin
    try:
        leboncoin_scraper = LeboncoinScraper(search_zone)
        results['leboncoin'] = leboncoin_scraper.scrape()
        logger.info(f"Leboncoin: {len(results['leboncoin'])} annonces trouvées pour {search_zone}")
    except Exception as e:
        logger.error(f"Erreur Leboncoin pour {search_zone}: {e}")

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
