from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'property_tracker'

urlpatterns = [
    # Authentification
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Annonces
    path('listings/', views.listings, name='listings'),
    path('listings/<int:listing_id>/price-history/', views.listing_price_history, name='listing_price_history'),

    # Zones de recherche (DEPRECATED - maintenant géré via UserSearchPreferences dans Settings)
    # path('search-zones/', views.search_zones, name='search_zones'),
    # path('search-zones/create/', views.create_search_zone, name='create_search_zone'),
    # path('search-zones/<int:zone_id>/delete/', views.delete_search_zone, name='delete_search_zone'),

    # Paramètres (gestion de la zone de recherche unique via UserSearchPreferences)
    path('settings/', views.settings, name='settings'),
]
