---
description: Vérifier la santé de l'application Django
---

Vérifie la configuration de l'application Django et détecte les problèmes potentiels.

Exécute les commandes suivantes :
1. Check Django : `python manage.py check`
2. Check des migrations : `python manage.py makemigrations --dry-run --check`
3. Affiche le statut des services si en Docker : `docker-compose ps`
