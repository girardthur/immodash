from django.contrib import admin
from .models import SearchZone, Listing, PriceHistory, UserSearchPreferences


@admin.register(UserSearchPreferences)
class UserSearchPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'radius_km', 'property_type', 'updated_at']
    list_filter = ['property_type', 'created_at']
    search_fields = ['user__username', 'city']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SearchZone)
class SearchZoneAdmin(admin.ModelAdmin):
    list_display = [
        'city', 'radius_km', 'property_type', 'created_by', 'is_active',
        'scraping_status', 'last_successful_scrape_display', 'created_at'
    ]
    list_filter = ['is_active', 'property_type', 'created_at']
    search_fields = ['city', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'last_scraped_at', 'last_successful_scrape_at', 'created_by']

    def scraping_status(self, obj):
        """Affiche le statut du scraping avec des couleurs"""
        from django.utils.html import format_html
        from django.utils import timezone
        from datetime import timedelta

        if not obj.last_scraped_at:
            return format_html('<span style="color: gray;">Jamais scrapé</span>')

        if not obj.last_successful_scrape_at:
            return format_html('<span style="color: red;">❌ Bloqué (Datadome)</span>')

        # Si le dernier scraping réussi est plus ancien que le dernier scraping, c'est bloqué
        if obj.last_scraped_at > obj.last_successful_scrape_at:
            return format_html('<span style="color: orange;">⚠️ Dernièrement bloqué</span>')

        # Si le dernier scraping réussi est récent (< 2h), c'est OK
        if timezone.now() - obj.last_successful_scrape_at < timedelta(hours=2):
            return format_html('<span style="color: green;">✓ OK</span>')

        return format_html('<span style="color: blue;">✓ OK (ancien)</span>')

    scraping_status.short_description = 'Statut scraping'

    def last_successful_scrape_display(self, obj):
        """Affiche la dernière date de scraping réussi de manière lisible"""
        if not obj.last_successful_scrape_at:
            return '-'
        from django.utils import timezone
        from datetime import timedelta

        delta = timezone.now() - obj.last_successful_scrape_at

        if delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f'Il y a {minutes} min'
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f'Il y a {hours}h'
        else:
            days = delta.days
            return f'Il y a {days}j'

    last_successful_scrape_display.short_description = 'Dernier succès'


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'source', 'current_price', 'price_per_sqm',
        'rooms', 'city', 'is_active', 'has_price_changed', 'first_seen_at'
    ]
    list_filter = ['source', 'is_active', 'has_price_changed', 'property_type', 'first_seen_at']
    search_fields = ['title', 'city', 'external_id']
    readonly_fields = ['first_seen_at', 'last_seen_at', 'created_at', 'updated_at', 'price_per_sqm']
    fieldsets = (
        ('Informations de base', {
            'fields': ('search_zones', 'external_id', 'source', 'url')
        }),
        ('Détails du bien', {
            'fields': ('title', 'description', 'property_type')
        }),
        ('Prix et surface', {
            'fields': ('current_price', 'surface', 'price_per_sqm')
        }),
        ('Caractéristiques', {
            'fields': ('rooms', 'bedrooms')
        }),
        ('Localisation', {
            'fields': ('city', 'postal_code', 'latitude', 'longitude')
        }),
        ('Statut', {
            'fields': ('is_active', 'first_seen_at', 'last_seen_at', 'sold_at')
        }),
        ('Changements de prix', {
            'fields': ('has_price_changed', 'last_price_change_date', 'last_price_change_percent')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['listing', 'price', 'price_per_sqm', 'change_percent', 'detected_at']
    list_filter = ['detected_at']
    search_fields = ['listing__title']
    readonly_fields = ['detected_at']
