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

    # Réglages utilisateur
    path('settings/', views.settings, name='settings'),
]
