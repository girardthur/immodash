---
description: Afficher les statistiques de la base de données
---

Affiche les statistiques actuelles de la base de données.

Exécute le code Python suivant dans le shell Django :
```python
from property_tracker.models import SearchZone, Listing, PriceHistory
from django.db.models import Count, Avg, Min, Max

print("=== Statistiques Immodash ===\n")

# Zones de recherche
zones_count = SearchZone.objects.count()
print(f"Zones de recherche : {zones_count}")

# Annonces
active_listings = Listing.objects.filter(status='active').count()
sold_listings = Listing.objects.filter(status='sold').count()
total_listings = Listing.objects.count()

print(f"\nAnnonces totales : {total_listings}")
print(f"  - Actives : {active_listings}")
print(f"  - Vendues : {sold_listings}")

# Prix
if total_listings > 0:
    price_stats = Listing.objects.aggregate(
        avg_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price')
    )
    print(f"\nPrix moyen : {price_stats['avg_price']:.2f}€")
    print(f"Prix min : {price_stats['min_price']}€")
    print(f"Prix max : {price_stats['max_price']}€")

# Changements de prix
price_changes = PriceHistory.objects.count()
print(f"\nChangements de prix enregistrés : {price_changes}")
```
