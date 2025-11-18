---
description: Lancer le scraping manuel de toutes les zones
---

Lance le scraping de toutes les zones de recherche via le shell Django.

Exécute le code Python suivant dans le shell Django :
```python
from property_tracker.tasks import scrape_all_search_zones
from property_tracker.models import SearchZone

# Afficher les zones existantes
zones = SearchZone.objects.all()
print(f"Zones de recherche trouvées : {zones.count()}")
for zone in zones:
    print(f"  - {zone.city} ({zone.radius}km) - {zone.property_type}")

# Lancer le scraping
print("\nDémarrage du scraping...")
scrape_all_search_zones()
print("Scraping terminé !")
```
