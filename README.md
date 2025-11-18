# Immodash - SaaS Platform

Plateforme SaaS développée avec Django 5.1 et Python 3.11.

## Technologies

- **Python**: 3.11
- **Django**: 5.1
- **Django REST Framework**: 3.16
- **Celery**: 5.5 (pour les tâches asynchrones)
- **Redis**: 7.0 (cache et broker Celery)
- **PostgreSQL**: Recommandé pour la production
- **Gunicorn**: Serveur WSGI pour la production

## Installation

### Prérequis

- Python 3.11+
- pip
- virtualenv (optionnel mais recommandé)

### Configuration locale

1. Cloner le repository:
```bash
git clone <repository-url>
cd immodash
```

2. Créer et activer un environnement virtuel:
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement:
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. Appliquer les migrations:
```bash
python manage.py migrate
```

6. Créer un superutilisateur:
```bash
python manage.py createsuperuser
```

7. Lancer le serveur de développement:
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse: http://127.0.0.1:8000/

## Structure du projet

```
immodash/
├── config/              # Configuration principale Django
│   ├── settings.py      # Paramètres Django
│   ├── urls.py          # URLs principales
│   ├── wsgi.py          # Configuration WSGI
│   └── asgi.py          # Configuration ASGI
├── manage.py            # Script de gestion Django
├── requirements.txt     # Dépendances Python
├── .env.example         # Exemple de variables d'environnement
└── .gitignore          # Fichiers à ignorer par Git
```

## Fonctionnalités configurées

- ✅ Django 5.1 avec structure modulaire
- ✅ Django REST Framework pour les API
- ✅ CORS configuré pour le développement frontend
- ✅ Celery pour les tâches asynchrones
- ✅ Support PostgreSQL et SQLite
- ✅ Gestion des variables d'environnement avec django-environ
- ✅ Configuration de sécurité pour la production
- ✅ Gestion des fichiers statiques et media

## Commandes utiles

### Développement

```bash
# Lancer le serveur de développement
python manage.py runserver

# Créer une nouvelle migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer le shell Django
python manage.py shell
```

### Tests

```bash
# Lancer les tests
python manage.py test

# Avec coverage
coverage run --source='.' manage.py test
coverage report
```

### Celery

```bash
# Lancer Celery worker
celery -A config worker -l info

# Lancer Celery beat (tâches planifiées)
celery -A config beat -l info
```

## Déploiement

Pour déployer en production:

1. Configurer les variables d'environnement appropriées dans `.env`
2. Mettre `DEBUG=False`
3. Configurer une base de données PostgreSQL
4. Configurer Redis pour Celery
5. Utiliser Gunicorn comme serveur WSGI:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Prochaines étapes

- Développer les applications métier
- Configurer l'authentification utilisateur
- Créer les API endpoints
- Implémenter le frontend
- Configurer les tests automatisés
- Mettre en place le CI/CD

## Contribution

Pour contribuer au projet:

1. Créer une branche feature
2. Faire vos modifications
3. Soumettre une Pull Request

## Licence

À définir
