from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class PropertyType(models.TextChoices):
    APARTMENT = 'apartment', 'Appartement'
    HOUSE = 'house', 'Maison'
    BOTH = 'both', 'Appartement et Maison'


class Source(models.TextChoices):
    LEBONCOIN = 'leboncoin', 'Leboncoin'


class UserSearchPreferences(models.Model):
    """Préférences de recherche d'un utilisateur (une seule zone par utilisateur)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='search_preferences')
    city = models.CharField(max_length=200, verbose_name='Ville', default='Paris')
    radius_km = models.IntegerField(verbose_name='Rayon (km)', default=10)
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.BOTH,
        verbose_name='Type de bien'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Préférences de recherche'
        verbose_name_plural = 'Préférences de recherche'

    def __str__(self):
        return f"{self.user.username} - {self.city} ({self.radius_km}km) - {self.get_property_type_display()}"


@receiver(post_save, sender=User)
def create_user_search_preferences(sender, instance, created, **kwargs):
    """Créer automatiquement les préférences de recherche pour chaque nouvel utilisateur"""
    if created:
        UserSearchPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_search_preferences(sender, instance, **kwargs):
    """Sauvegarder les préférences de recherche quand l'utilisateur est sauvegardé"""
    if hasattr(instance, 'search_preferences'):
        instance.search_preferences.save()


@receiver(post_save, sender=UserSearchPreferences)
def sync_search_zone_from_preferences(sender, instance, **kwargs):
    """
    Synchronise automatiquement une SearchZone unique avec les UserSearchPreferences
    Crée ou met à jour la SearchZone quand les préférences sont modifiées
    """
    # Désactiver toutes les autres zones de recherche de l'utilisateur
    SearchZone.objects.filter(user=instance.user).update(is_active=False)

    # Récupérer la première SearchZone ou en créer une nouvelle
    search_zones = SearchZone.objects.filter(user=instance.user)
    if search_zones.exists():
        # Mettre à jour la première zone existante
        search_zone = search_zones.first()
        search_zone.city = instance.city
        search_zone.radius_km = instance.radius_km
        search_zone.property_type = instance.property_type
        search_zone.is_active = True
        search_zone.save()
    else:
        # Créer une nouvelle SearchZone
        SearchZone.objects.create(
            user=instance.user,
            city=instance.city,
            radius_km=instance.radius_km,
            property_type=instance.property_type,
            is_active=True,
        )


class SearchZone(models.Model):
    """Zone de recherche d'un utilisateur"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_zones')
    city = models.CharField(max_length=200, verbose_name='Ville')
    radius_km = models.IntegerField(verbose_name='Rayon (km)')
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.BOTH,
        verbose_name='Type de bien'
    )
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Zone de recherche'
        verbose_name_plural = 'Zones de recherche'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city} ({self.radius_km}km) - {self.get_property_type_display()}"


class Listing(models.Model):
    """Annonce immobilière"""
    search_zones = models.ManyToManyField(SearchZone, related_name='listings', verbose_name='Zones de recherche')

    # Identifiants externes
    external_id = models.CharField(max_length=200, verbose_name='ID externe', unique=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        verbose_name='Source'
    )
    url = models.URLField(verbose_name='URL de l\'annonce')

    # Informations du bien
    title = models.CharField(max_length=500, verbose_name='Titre')
    description = models.TextField(verbose_name='Description', blank=True)
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        verbose_name='Type de bien'
    )

    # Prix et surface
    current_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix actuel')
    surface = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Surface (m²)', null=True, blank=True)
    price_per_sqm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prix au m²',
        null=True,
        blank=True
    )

    # Caractéristiques
    rooms = models.IntegerField(verbose_name='Nombre de pièces', null=True, blank=True)
    bedrooms = models.IntegerField(verbose_name='Nombre de chambres', null=True, blank=True)

    # Localisation
    city = models.CharField(max_length=200, verbose_name='Ville')
    postal_code = models.CharField(max_length=10, verbose_name='Code postal', blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Statut
    is_active = models.BooleanField(default=True, verbose_name='Annonce active')
    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name='Première détection')
    last_seen_at = models.DateTimeField(auto_now=True, verbose_name='Dernière détection')
    sold_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de vente')

    # Prix
    has_price_changed = models.BooleanField(default=False, verbose_name='Prix a changé')
    last_price_change_date = models.DateTimeField(null=True, blank=True, verbose_name='Date du dernier changement de prix')
    last_price_change_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Dernier % de changement'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['external_id', 'source']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.title} - {self.current_price}€"

    def save(self, *args, **kwargs):
        # Calculer le prix au m² si surface disponible
        if self.surface and self.surface > 0:
            self.price_per_sqm = self.current_price / self.surface
        super().save(*args, **kwargs)

    @property
    def most_recent_date(self):
        """Retourne la date la plus récente entre création et dernier changement de prix"""
        if self.last_price_change_date:
            return max(self.first_seen_at, self.last_price_change_date)
        return self.first_seen_at

    @property
    def days_on_market(self):
        """Nombre de jours depuis la publication"""
        if self.sold_at:
            return (self.sold_at - self.first_seen_at).days
        return (timezone.now() - self.first_seen_at).days

    @property
    def previous_price(self):
        """Retourne le prix précédent (avant le dernier changement)"""
        if not self.has_price_changed:
            return None

        # Récupérer les 2 dernières entrées de l'historique
        history = self.price_history.order_by('-detected_at')[:2]

        if len(history) >= 2:
            # L'avant-dernier prix est le prix précédent
            return history[1].price

        return None


class PriceHistory(models.Model):
    """Historique des changements de prix d'une annonce"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix')
    price_per_sqm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prix au m²',
        null=True,
        blank=True
    )
    change_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='% de changement'
    )
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name='Détecté le')

    class Meta:
        verbose_name = 'Historique de prix'
        verbose_name_plural = 'Historiques de prix'
        ordering = ['detected_at']
        indexes = [
            models.Index(fields=['listing', 'detected_at']),
        ]

    def __str__(self):
        return f"{self.listing.title} - {self.price}€ ({self.detected_at})"
