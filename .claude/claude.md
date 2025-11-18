# Immodash - Property Tracker SaaS

## Vue d'ensemble du projet

Immodash est une plateforme SaaS de tracking immobilier pour Leboncoin avec dashboard et statistiques en temps réel. Le système scrape automatiquement les annonces immobilières et détecte les changements (prix, nouvelles annonces, ventes).

## Stack technique

- **Backend**: Django 5.1 + Python 3.11
- **Base de données**: SQLite (dev), PostgreSQL recommandé (prod)
- **Tâches asynchrones**: Celery 5.5 + Redis 7.0
- **Frontend**: TailwindCSS + HTMX + Alpine.js
- **Graphiques**: Plotly
- **Containerisation**: Docker + Docker Compose
- **Scraping**: Bibliothèque `lbc` pour Leboncoin

## Architecture du projet

```
immodash/
├── config/                 # Configuration Django & Celery
│   ├── settings.py        # Settings Django
│   ├── urls.py            # URLs principales
│   ├── celery.py          # Configuration Celery + Beat
│   └── wsgi.py
├── property_tracker/       # Application principale
│   ├── models.py          # SearchZone, Listing, PriceHistory, UserSearchPreferences
│   ├── scrapers.py        # Scraper Leboncoin
│   ├── tasks.py           # Tâches Celery (scraping automatique)
│   ├── views.py           # Vues Django
│   ├── forms.py           # Formulaires Django
│   ├── urls.py            # URLs de l'app
│   ├── admin.py           # Admin Django
│   └── templates/         # Templates HTML
├── templates/             # Templates globaux (base, auth)
├── docker-compose.yml     # Orchestration Docker
├── Dockerfile             # Image Docker
├── entrypoint.sh          # Script d'initialisation Docker
└── requirements.txt       # Dépendances Python
```

## Modèles de données

### SearchZone
Zone de recherche définie par un utilisateur :
- `user`: Utilisateur propriétaire
- `city`: Ville
- `radius`: Rayon de recherche (km)
- `property_type`: Type de bien (appartement/maison)

### Listing
Annonce immobilière :
- `search_zone`: Zone de recherche liée
- `external_id`: ID externe (Leboncoin)
- `title`, `description`, `price`, `surface`, `rooms`
- `city`, `postal_code`, `url`, `image_url`
- `source`: Source (leboncoin)
- `status`: active/sold
- `last_seen`: Dernière fois vue (pour détecter les ventes)

### PriceHistory
Historique des changements de prix :
- `listing`: Annonce liée
- `old_price`, `new_price`
- `change_percentage`: Pourcentage de changement
- `timestamp`: Date du changement

### UserSearchPreferences
Préférences de recherche utilisateur :
- `user`: Utilisateur
- `min_price`, `max_price`
- `min_surface`, `max_surface`
- `min_rooms`, `max_rooms`
- `cities`: Liste de villes

## Fonctionnalités principales

### Scraping automatique
- Scraping toutes les 30 minutes via Celery Beat
- Détection automatique des nouvelles annonces
- Détection des changements de prix (avec historique)
- Marquage automatique des annonces vendues (disparues >24h)

### Dashboard
- Statistiques globales (actives, vendues, min/max prix, taux de rotation)
- Graphique prix moyen au m² par nombre de pièces
- Évolution des prix dans le temps (30 derniers jours)
- Gestion des zones de recherche

### Page des annonces
- Filtres : Statut, Source, Type de bien
- Tri : Date, Prix, Prix/m²
- Badge de changement de prix
- Popup avec historique détaillé (graphique Plotly)
- Pagination

## Commandes utiles

### Django
```bash
# Créer migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Créer superutilisateur
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Lancer serveur dev
python manage.py runserver
```

### Celery
```bash
# Worker
celery -A config worker -l info

# Beat (tâches périodiques)
celery -A config beat -l info
```

### Docker
```bash
# Lancer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Exécuter une commande Django
docker-compose exec web python manage.py <commande>

# Arrêter les services
docker-compose down
```

## Conventions de code

### Python
- PEP 8 pour le style
- Type hints recommandés pour les fonctions
- Docstrings pour les fonctions complexes
- Imports triés : stdlib, third-party, local

### Django
- Class-based views préférées aux function-based views
- Utiliser `select_related()` et `prefetch_related()` pour optimiser les requêtes
- Toujours utiliser `get_object_or_404()` pour les objets uniques
- Formulaires Django pour la validation

### Templates
- TailwindCSS pour le styling
- HTMX pour les interactions dynamiques
- Alpine.js pour les interactions client-side simples

## Tests

### Lancer les tests
```bash
# Tous les tests
python manage.py test

# Tests d'une app spécifique
python manage.py test property_tracker

# Avec coverage
coverage run --source='.' manage.py test
coverage report
```

## Variables d'environnement importantes

- `DEBUG`: Mode debug Django
- `SECRET_KEY`: Clé secrète Django
- `ALLOWED_HOSTS`: Hôtes autorisés (production)
- `DATABASE_URL`: URL de la base de données (optionnel)
- `REDIS_URL`: URL Redis pour Celery

## Problèmes courants

### Le scraping ne fonctionne pas
1. Vérifier que Celery Worker et Beat sont lancés
2. Consulter les logs : `docker-compose logs -f celery_worker celery_beat`
3. Tester manuellement dans le shell Django :
```python
from property_tracker.tasks import scrape_all_search_zones
scrape_all_search_zones()
```

### Erreur de migration
```bash
python manage.py migrate --fake-initial
```

### Problème de permissions Docker
```bash
docker-compose down -v
docker-compose up -d
```

## Améliorations prioritaires

1. **Alertes** : Système d'email/push pour nouvelles annonces
2. **Filtres avancés** : Plus de critères de recherche
3. **Tests** : Couverture de tests complète
4. **Performance** : Optimisation des requêtes SQL
5. **API REST** : Pour application mobile future

## Ressources

- Documentation Django : https://docs.djangoproject.com/
- Documentation Celery : https://docs.celeryproject.org/
- TailwindCSS : https://tailwindcss.com/docs
- HTMX : https://htmx.org/docs/
