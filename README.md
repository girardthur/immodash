# Immodash - Property Tracker SaaS

Plateforme SaaS de tracking immobilier pour Leboncoin avec dashboard et statistiques en temps réel.

## 🚀 Technologies

- **Python**: 3.11
- **Django**: 5.1
- **Celery**: 5.5 (tâches asynchrones + scraping automatique toutes les 30 min)
- **Redis**: 7.0 (cache et broker Celery)
- **TailwindCSS**: Design moderne
- **HTMX**: Interactions dynamiques
- **Plotly**: Graphiques interactifs
- **Docker**: Containerisation pour développement et production

## ✨ Fonctionnalités

### Backend
- 🔍 **Scraper Leboncoin** : Récupération automatique des annonces avec la bibliothèque `lbc`
- 📊 **Détection des changements** : Prix, nouvelles annonces, annonces vendues
- ⏰ **Scraping automatique** : Toutes les 30 minutes via Celery Beat
- 💾 **Historique complet** : Tous les changements de prix sont enregistrés

### Dashboard
- 📈 Statistiques globales (actives, vendues, min/max prix, taux de rotation)
- 📊 Graphique prix moyen au m² par nombre de pièces
- 📉 Évolution des prix dans le temps (30 derniers jours)
- 🗺️ Gestion des zones de recherche (ville + rayon + type)

### Annonces
- 🔎 Filtres : Statut, Source, Type de bien
- 🔄 Tri : Date, Prix, Prix/m²
- 💰 Badge de changement de prix
- 📊 Popup avec historique détaillé (graphique Plotly)
- 📄 Pagination

### Authentification
- 🔐 Login/logout simple
- 👤 Gestion des utilisateurs via l'admin Django

## 🐳 Démarrage rapide avec Docker (Recommandé)

### Prérequis
- Docker et Docker Compose installés
- Port 8000 disponible

### Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd immodash
```

2. **Créer le fichier .env**
```bash
cp .env.docker .env
```

3. **Lancer l'application**
```bash
docker-compose up -d
```

Cela démarre automatiquement :
- ✅ Django (web) sur http://localhost:8000
- ✅ Celery Worker (tâches de scraping)
- ✅ Celery Beat (planificateur - scraping toutes les 30 min)
- ✅ Redis (cache et broker)

4. **Créer un superutilisateur**
```bash
docker-compose exec web python manage.py createsuperuser
```

5. **Accéder à l'application**
- Application : http://localhost:8000
- Admin Django : http://localhost:8000/admin

### Commandes Docker utiles

```bash
# Voir les logs
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Arrêter l'application
docker-compose down

# Redémarrer un service
docker-compose restart web

# Exécuter une commande Django
docker-compose exec web python manage.py <commande>

# Accéder au shell Django
docker-compose exec web python manage.py shell

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer des migrations
docker-compose exec web python manage.py makemigrations

# Accéder à un shell bash dans le container
docker-compose exec web bash
```

## 💻 Installation sans Docker (Alternative)

### Prérequis
- Python 3.11+
- Redis installé et en cours d'exécution

### Installation

1. **Créer et activer un environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

4. **Appliquer les migrations**
```bash
python manage.py migrate
```

5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

6. **Lancer l'application (3 terminaux)**

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Celery Worker:
```bash
celery -A config worker -l info
```

Terminal 3 - Celery Beat:
```bash
celery -A config beat -l info
```

## 📖 Utilisation

### 1. Créer des utilisateurs
- Connectez-vous à l'admin Django : http://localhost:8000/admin
- Créez des comptes utilisateurs

### 2. Créer une zone de recherche
- Connectez-vous avec un compte utilisateur
- Cliquez sur "Nouvelle zone de recherche"
- Renseignez : ville, rayon (km), type de bien
- Le scraping démarre automatiquement

### 3. Consulter les résultats
- **Dashboard** : Vue d'ensemble avec statistiques et graphiques
- **Annonces** : Liste complète avec filtres et tri
- **Zones** : Gestion de vos zones de recherche

## ⏰ Scraping automatique

Le système scrape automatiquement **toutes les 30 minutes** :
- Nouvelles annonces → Création en base
- Changement de prix → Ajout dans l'historique
- Annonce disparue >24h → Marquée comme vendue

Pour changer la fréquence, modifiez `config/celery.py` :
```python
app.conf.beat_schedule = {
    'scrape-every-30-minutes': {
        'task': 'property_tracker.tasks.periodic_scraping_task',
        'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
    },
}
```

## 📁 Structure du projet

```
immodash/
├── config/                 # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py          # Configuration Celery + Beat
│   └── ...
├── property_tracker/       # Application principale
│   ├── models.py          # SearchZone, Listing, PriceHistory
│   ├── scrapers.py        # Scraper Leboncoin
│   ├── tasks.py           # Tâches Celery
│   ├── views.py           # Vues Django
│   └── templates/         # Templates HTML
├── docker-compose.yml     # Configuration Docker
├── Dockerfile             # Image Docker
├── entrypoint.sh          # Script d'initialisation
├── requirements.txt       # Dépendances Python
└── README.md              # Ce fichier
```

## 🔧 API des scrapers

### Scraper manuel
```python
from property_tracker.scrapers import scrape_search_zone
from property_tracker.models import SearchZone

# Scraper une zone spécifique
zone = SearchZone.objects.get(id=1)
results = scrape_search_zone(zone)
print(f"Leboncoin: {len(results['leboncoin'])} annonces")
```

### Lancer le scraping via Celery
```python
from property_tracker.tasks import scrape_all_search_zones

# Lancer le scraping de toutes les zones
scrape_all_search_zones.delay()
```

## 🚀 Configuration pour la production

### 1. Variables d'environnement
Modifiez `.env` :
```bash
DEBUG=False
SECRET_KEY=<votre-clé-secrète-forte>
ALLOWED_HOSTS=votre-domaine.com
DATABASE_URL=postgres://user:password@db:5432/immodash  # PostgreSQL recommandé
REDIS_URL=redis://redis:6379/0
```

### 2. Base de données PostgreSQL
Modifiez `docker-compose.yml` pour ajouter PostgreSQL :
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: immodash
      POSTGRES_USER: immodash
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 3. Proxy inverse (Nginx)
Utilisez Nginx ou Traefik pour :
- HTTPS (Let's Encrypt)
- Reverse proxy vers Django
- Servir les fichiers statiques

## 🎯 Améliorations futures

- [ ] Système d'alertes (email/push) pour nouvelles annonces
- [ ] Filtres avancés (nombre de pièces, prix min/max)
- [ ] Carte interactive des annonces
- [ ] Export des données (CSV, Excel)
- [ ] API REST pour application mobile
- [ ] Tests automatisés
- [ ] CI/CD avec GitHub Actions
- [ ] Support d'autres sources (SeLoger, PAP, etc.)

## 🔍 Dépannage

### Le scraping ne fonctionne pas
1. Vérifiez que Celery Worker et Beat sont bien lancés
2. Consultez les logs : `docker-compose logs -f celery_worker celery_beat`
3. Testez manuellement le scraper dans le shell Django

### Erreur de migration
```bash
docker-compose exec web python manage.py migrate --fake-initial
```

### Problème de permissions
```bash
docker-compose down -v  # Supprime les volumes
docker-compose up -d    # Recrée tout
```

## 📚 Documentation supplémentaire

- **Property Tracker**: Voir `PROPERTY_TRACKER_README.md` pour plus de détails sur l'architecture
- **Celery**: Configuration dans `config/celery.py`
- **Scrapers**: Implémentation dans `property_tracker/scrapers.py`

## 📝 Licence

À définir
