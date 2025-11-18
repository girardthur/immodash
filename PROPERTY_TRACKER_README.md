# Immodash - Property Tracker

Tracker immobilier pour Leboncoin et SeLoger avec dashboard et statistiques en temps réel.

## Fonctionnalités implémentées

### Backend
- **Modèles Django** :
  - `SearchZone` : Zone de recherche (ville + rayon + type de bien)
  - `Listing` : Annonce immobilière avec toutes les informations
  - `PriceHistory` : Historique des changements de prix

- **Scrapers** :
  - Leboncoin : Utilise la bibliothèque `lbc` (PyPI)
  - SeLoger : Scraper custom avec BeautifulSoup (à adapter selon protection anti-scraping)
  - Détection automatique des changements de prix
  - Marquage automatique des annonces vendues (disparues depuis >24h)

- **Tâches Celery** :
  - Scraping automatique toutes les 30 minutes
  - Vérification des annonces inactives
  - Mise à jour de l'historique des prix

### Frontend
- **Design moderne** : TailwindCSS + Alpine.js
- **Dashboard** :
  - Statistiques globales (annonces actives, vendues, min/max prix, taux de rotation)
  - Graphique : Prix moyen au m² par nombre de pièces
  - Graphique : Évolution des prix dans le temps (30 derniers jours)
  - Liste des zones de recherche

- **Page des annonces** :
  - Filtres : Statut (actives/vendues), Source (Leboncoin/SeLoger), Type de bien
  - Tri : Date, Prix, Prix au m²
  - Indication des changements de prix
  - Popup avec graphique de l'historique des prix (avec Plotly)
  - Pagination

- **Gestion des zones de recherche** :
  - Création/suppression de zones
  - Statistiques par zone

- **Authentification** : Login/logout simple

## Démarrage

### 1. Installation
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### 2. Créer des utilisateurs
L'admin crée les comptes utilisateurs dans l'interface d'administration Django :
```bash
python manage.py runserver
# Aller sur http://127.0.0.1:8000/admin/
```

### 3. Lancer l'application
```bash
# Serveur de développement
python manage.py runserver

# Dans un autre terminal : Celery worker
celery -A config worker -l info

# Dans un autre terminal : Celery beat (pour les tâches périodiques)
celery -A config beat -l info
```

### 4. Utilisation
1. Se connecter avec un compte utilisateur
2. Créer une zone de recherche (ville + rayon + type de bien)
3. Le scraping se lance automatiquement toutes les 30 minutes
4. Consulter le dashboard et la liste des annonces

## Structure du projet

```
property_tracker/
├── models.py          # Modèles Django (SearchZone, Listing, PriceHistory)
├── scrapers.py        # Scrapers Leboncoin et SeLoger
├── tasks.py           # Tâches Celery périodiques
├── views.py           # Vues Django (dashboard, listings, search_zones)
├── urls.py            # URLs de l'application
├── admin.py           # Configuration admin Django
└── templates/
    └── property_tracker/
        ├── dashboard.html
        ├── listings.html
        ├── search_zones.html
        ├── create_search_zone.html
        └── delete_search_zone.html
```

## API des scrapers

### Scraper manuel
```python
from property_tracker.scrapers import scrape_search_zone
from property_tracker.models import SearchZone

# Scraper une zone spécifique
zone = SearchZone.objects.get(id=1)
results = scrape_search_zone(zone)
print(f"Leboncoin: {len(results['leboncoin'])} annonces")
print(f"SeLoger: {len(results['seloger'])} annonces")
```

### Lancer le scraping via Celery
```python
from property_tracker.tasks import scrape_all_search_zones

# Lancer le scraping de toutes les zones
scrape_all_search_zones.delay()
```

## Notes importantes

### Scrapers
- **Leboncoin** : Utilise la bibliothèque `lbc`. L'implémentation actuelle est basique et doit être testée/adaptée selon l'API de `lbc`.
- **SeLoger** : Le scraper est une implémentation de base avec BeautifulSoup. SeLoger a des protections anti-scraping importantes :
  - Protection CAPTCHA
  - Rate limiting
  - Structure HTML qui change régulièrement

Pour une utilisation en production, il faudra :
- Utiliser des proxies rotatifs
- Gérer les CAPTCHAs (services comme 2captcha, anti-captcha)
- Utiliser Playwright/Selenium pour le JavaScript rendering
- Adapter le parsing HTML selon la structure actuelle

### Données
Le système détecte automatiquement :
- Nouvelles annonces (création)
- Changements de prix (avec calcul du pourcentage)
- Annonces vendues (non vues depuis >24h)

L'historique des prix est conservé pour chaque annonce, permettant :
- Affichage des graphiques d'évolution
- Calcul des statistiques temporelles
- Détection des bonnes affaires (fortes baisses)

### Performance
Pour de gros volumes :
- Ajuster la fréquence de scraping dans `config/celery.py`
- Utiliser une base PostgreSQL au lieu de SQLite
- Configurer Redis pour le cache et Celery
- Ajouter des index sur les champs fréquemment filtrés

## Améliorations futures

### Fonctionnalités
- [ ] Système d'alertes (email/push) pour nouvelles annonces ou baisses de prix
- [ ] Filtres avancés (nombre de pièces, prix min/max, surface)
- [ ] Carte interactive des annonces
- [ ] Comparaison de biens
- [ ] Export des données (CSV, Excel)
- [ ] API REST pour accès mobile
- [ ] Favoris et notes sur les annonces

### Technique
- [ ] Améliorer les scrapers (robustesse, gestion d'erreurs)
- [ ] Tests unitaires et d'intégration
- [ ] CI/CD avec GitHub Actions
- [ ] Monitoring et logs (Sentry, DataDog)
- [ ] Cache Redis pour les statistiques
- [ ] Optimisation des requêtes SQL (select_related, prefetch_related)
- [ ] Docker pour le déploiement

## Support

Pour toute question ou problème :
- Vérifier les logs Celery pour les erreurs de scraping
- Consulter les logs Django pour les erreurs applicatives
- Tester les scrapers individuellement avant le déploiement
