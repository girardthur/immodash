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
    path('listings/<int:listing_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),

    # Favoris
    path('favorites/<int:listing_id>/remove/', views.remove_favorite, name='remove_favorite'),

    # Paramètres (sélection de zone de recherche)
    path('settings/', views.settings, name='settings'),

    # Gestion des zones de recherche (accessible aux admins uniquement)
    path('zones/', views.admin_zone_list, name='admin_zone_list'),
    path('zones/create/', views.admin_zone_create, name='admin_zone_create'),
    path('zones/<int:zone_id>/delete/', views.admin_zone_delete, name='admin_zone_delete'),
]
