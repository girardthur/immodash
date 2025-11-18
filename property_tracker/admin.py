from django.contrib import admin
from .models import SearchZone, Listing, PriceHistory


@admin.register(SearchZone)
class SearchZoneAdmin(admin.ModelAdmin):
    list_display = ['city', 'radius_km', 'property_type', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'property_type', 'created_at']
    search_fields = ['city', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


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
            'fields': ('search_zone', 'external_id', 'source', 'url')
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
