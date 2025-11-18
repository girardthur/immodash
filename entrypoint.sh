#!/bin/bash

# Attendre que la base de données soit prête (si PostgreSQL)
# if [ "$DATABASE" = "postgres" ]; then
#     echo "Waiting for postgres..."
#     while ! nc -z $SQL_HOST $SQL_PORT; do
#       sleep 0.1
#     done
#     echo "PostgreSQL started"
# fi

# Appliquer les migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Créer un superutilisateur si aucun utilisateur n'existe
echo "Checking for superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("No superuser found. Create one manually using: docker-compose exec web python manage.py createsuperuser")
END

# Exécuter la commande passée en argument
exec "$@"
