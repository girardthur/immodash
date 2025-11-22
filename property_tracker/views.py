from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.db.models import Avg, Count, Min, Max, Q, F
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from .models import SearchZone, Listing, PriceHistory, PropertyType, UserSearchPreferences
from .forms import UserSearchPreferencesForm


@login_required
def dashboard(request):
    """
    Vue principale du dashboard avec les statistiques globales
    """
    # Récupérer les zones de recherche de l'utilisateur
    search_zones = request.user.search_zones.filter(is_active=True)

    # Récupérer toutes les annonces des zones de l'utilisateur
    all_listings = Listing.objects.filter(search_zone__in=search_zones)

    # Statistiques globales
    active_listings_count = all_listings.filter(is_active=True).count()
    inactive_listings_count = all_listings.filter(is_active=False).count()

    # Prix minimum et maximum
    price_stats = all_listings.filter(is_active=True).aggregate(
        min_price=Min('current_price'),
        max_price=Max('current_price')
    )

    # Prix moyen au m² par nombre de pièces
    avg_price_per_sqm_by_rooms = (
        all_listings.filter(is_active=True, price_per_sqm__isnull=False, rooms__isnull=False)
        .values('rooms')
        .annotate(avg_price_per_sqm=Avg('price_per_sqm'))
        .order_by('rooms')
    )

    # Taux de rotation (durée moyenne sur le marché)
    sold_listings = all_listings.filter(is_active=False, sold_at__isnull=False)
    total_days = sum(listing.days_on_market for listing in sold_listings)
    avg_days_on_market = total_days / sold_listings.count() if sold_listings.count() > 0 else 0

    # Évolution des prix moyens au m² dans le temps (30 derniers jours)
    from datetime import timedelta
    from django.utils import timezone

    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Récupérer l'historique des prix des 30 derniers jours
    price_evolution = (
        PriceHistory.objects.filter(
            listing__search_zone__in=search_zones,
            detected_at__gte=thirty_days_ago,
            price_per_sqm__isnull=False
        )
        .annotate(date=TruncDate('detected_at'))
        .values('date')
        .annotate(avg_price_per_sqm=Avg('price_per_sqm'))
        .order_by('date')
    )

    # Préparer les données pour le graphique d'évolution
    evolution_data = {
        'dates': [entry['date'].strftime('%Y-%m-%d') for entry in price_evolution],
        'prices': [float(entry['avg_price_per_sqm']) for entry in price_evolution]
    }

    # Préparer les données pour le graphique par nombre de pièces
    rooms_data = {
        'rooms': [f"{entry['rooms']} pièces" for entry in avg_price_per_sqm_by_rooms],
        'prices': [float(entry['avg_price_per_sqm']) for entry in avg_price_per_sqm_by_rooms]
    }

    context = {
        'active_listings_count': active_listings_count,
        'inactive_listings_count': inactive_listings_count,
        'min_price': price_stats['min_price'],
        'max_price': price_stats['max_price'],
        'avg_days_on_market': round(avg_days_on_market, 1),
        'evolution_data': json.dumps(evolution_data),
        'rooms_data': json.dumps(rooms_data),
    }

    return render(request, 'property_tracker/dashboard.html', context)


@login_required
def listings(request):
    """
    Liste des annonces avec filtres et tri
    """
    # Récupérer les zones de recherche de l'utilisateur
    search_zones = request.user.search_zones.filter(is_active=True)

    # Query de base avec prefetch de l'historique des prix pour éviter N+1 queries
    listings_query = Listing.objects.filter(search_zone__in=search_zones).select_related('search_zone').prefetch_related('price_history')

    # Filtres
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        listings_query = listings_query.filter(is_active=True)
    elif status_filter == 'inactive':
        listings_query = listings_query.filter(is_active=False)

    source_filter = request.GET.get('source', 'all')
    if source_filter != 'all':
        listings_query = listings_query.filter(source=source_filter)

    property_type_filter = request.GET.get('property_type', 'all')
    if property_type_filter != 'all':
        listings_query = listings_query.filter(property_type=property_type_filter)

    # Tri
    sort_by = request.GET.get('sort', 'recent')
    if sort_by == 'recent':
        # Trier par date la plus récente (création ou changement de prix)
        listings_query = listings_query.order_by('-updated_at', '-last_price_change_date')
    elif sort_by == 'price_change':
        # Trier par date de changement de prix (plus récent en premier, NULL à la fin)
        listings_query = listings_query.order_by(F('last_price_change_date').desc(nulls_last=True))
    elif sort_by == 'price_asc':
        listings_query = listings_query.order_by('current_price')
    elif sort_by == 'price_desc':
        listings_query = listings_query.order_by('-current_price')
    elif sort_by == 'price_per_sqm_asc':
        listings_query = listings_query.order_by('price_per_sqm')
    elif sort_by == 'price_per_sqm_desc':
        listings_query = listings_query.order_by('-price_per_sqm')

    # Pagination (optionnelle)
    from django.core.paginator import Paginator
    paginator = Paginator(listings_query, 50)  # 50 annonces par page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'property_type_filter': property_type_filter,
        'sort_by': sort_by,
    }

    # Si c'est une requête HTMX, renvoyer seulement la partie de la liste
    if request.htmx:
        return render(request, 'property_tracker/partials/listings_list.html', context)

    return render(request, 'property_tracker/listings.html', context)


@login_required
@require_http_methods(["GET"])
def listing_price_history(request, listing_id):
    """
    Retourne l'historique des prix d'une annonce en JSON pour le graphique
    """
    listing = get_object_or_404(
        Listing,
        id=listing_id,
        search_zone__user=request.user
    )

    # Récupérer l'historique des prix
    price_history = listing.price_history.all().order_by('detected_at')

    # Préparer les données pour Plotly
    data = {
        'dates': [entry.detected_at.strftime('%Y-%m-%d %H:%M') for entry in price_history],
        'prices': [float(entry.price) for entry in price_history],
        'price_per_sqm': [float(entry.price_per_sqm) if entry.price_per_sqm else None for entry in price_history],
        'listing_title': listing.title,
        'listing_url': listing.url,
    }

    return JsonResponse(data)


@login_required
def search_zones(request):
    """
    Liste des zones de recherche de l'utilisateur
    """
    zones = request.user.search_zones.all().order_by('-created_at')

    # Ajouter le nombre d'annonces par zone
    zones_with_counts = []
    for zone in zones:
        active_count = zone.listings.filter(is_active=True).count()
        inactive_count = zone.listings.filter(is_active=False).count()
        zones_with_counts.append({
            'zone': zone,
            'active_count': active_count,
            'inactive_count': inactive_count,
        })

    context = {
        'zones_with_counts': zones_with_counts,
    }

    return render(request, 'property_tracker/search_zones.html', context)


@login_required
def create_search_zone(request):
    """
    Créer une nouvelle zone de recherche
    """
    if request.method == 'POST':
        city = request.POST.get('city')
        radius_km = request.POST.get('radius_km')
        property_type = request.POST.get('property_type')

        if city and radius_km and property_type:
            SearchZone.objects.create(
                user=request.user,
                city=city,
                radius_km=int(radius_km),
                property_type=property_type
            )
            messages.success(request, f'Zone de recherche "{city}" créée avec succès!')
            return redirect('property_tracker:search_zones')
        else:
            messages.error(request, 'Tous les champs sont requis.')

    return render(request, 'property_tracker/create_search_zone.html')


@login_required
def delete_search_zone(request, zone_id):
    """
    Supprimer une zone de recherche
    """
    zone = get_object_or_404(SearchZone, id=zone_id, user=request.user)

    if request.method == 'POST':
        zone.delete()
        messages.success(request, 'Zone de recherche supprimée avec succès!')
        return redirect('property_tracker:search_zones')

    return render(request, 'property_tracker/delete_search_zone.html', {'zone': zone})


def logout_view(request):
    """
    Déconnexion de l'utilisateur
    """
    auth_logout(request)
    return redirect('property_tracker:login')


@login_required
def settings(request):
    """
    Page de paramètres utilisateur pour gérer les préférences de recherche
    """
    # Récupérer ou créer les préférences de l'utilisateur
    preferences, created = UserSearchPreferences.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Récupérer les anciennes valeurs AVANT de créer le formulaire
        # (form.is_valid() modifie l'instance)
        old_city = preferences.city if not created else None
        old_radius = preferences.radius_km if not created else None
        old_property_type = preferences.property_type if not created else None

        form = UserSearchPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            # Sauvegarder les nouvelles préférences
            form.save()

            # Vérifier si les préférences ont changé
            has_changed = False
            if not created:
                if (old_city != preferences.city or
                    old_radius != preferences.radius_km or
                    old_property_type != preferences.property_type):
                    has_changed = True
            else:
                has_changed = True

            # Si les préférences ont changé, supprimer les anciennes annonces et lancer un scraping
            if has_changed:
                # Supprimer toutes les annonces existantes de l'utilisateur
                deleted_count, _ = Listing.objects.filter(
                    search_zone__user=request.user
                ).delete()

                # Lancer le scraping de la nouvelle zone
                from .tasks import scrape_single_zone
                search_zone = request.user.search_zones.filter(is_active=True).first()

                if search_zone:
                    # Lancer la tâche Celery en arrière-plan
                    scrape_single_zone.delay(search_zone.id)

                    messages.success(
                        request,
                        f'Vos préférences ont été mises à jour! {deleted_count} anciennes annonces ont été supprimées. '
                        f'Le scraping des nouvelles annonces est en cours...'
                    )
                else:
                    messages.success(request, 'Vos préférences de recherche ont été mises à jour avec succès!')
            else:
                messages.info(request, 'Aucune modification détectée.')

            return redirect('property_tracker:settings')
        else:
            messages.error(request, 'Erreur lors de la mise à jour de vos préférences.')
    else:
        form = UserSearchPreferencesForm(instance=preferences)

    context = {
        'form': form,
        'preferences': preferences,
    }

    return render(request, 'property_tracker/settings.html', context)
