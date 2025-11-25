# Guide de Déploiement - Immodash

Ce guide détaille toutes les étapes pour déployer Immodash en production sur un VPS.

## Prérequis

- Un VPS (DigitalOcean, Hetzner, OVH, etc.) avec au minimum 2 GB RAM
- Ubuntu 22.04 LTS ou Debian 12
- Un nom de domaine pointant vers votre VPS
- Accès SSH au serveur

## Table des matières

1. [Configuration initiale du serveur](#1-configuration-initiale-du-serveur)
2. [Installation de Docker](#2-installation-de-docker)
3. [Clonage et configuration du projet](#3-clonage-et-configuration-du-projet)
4. [Configuration des variables d'environnement](#4-configuration-des-variables-denvironnement)
5. [Premier déploiement](#5-premier-déploiement)
6. [Configuration SSL avec Let's Encrypt](#6-configuration-ssl-avec-lets-encrypt)
7. [Configuration du pare-feu](#7-configuration-du-pare-feu)
8. [Création d'un superutilisateur](#8-création-dun-superutilisateur)
9. [Mises à jour ultérieures](#9-mises-à-jour-ultérieures)
10. [Monitoring et maintenance](#10-monitoring-et-maintenance)
11. [Dépannage](#11-dépannage)

---

## 1. Configuration initiale du serveur

### Se connecter au serveur

```bash
ssh root@VOTRE_IP_SERVEUR
```

### Mettre à jour le système

```bash
apt update && apt upgrade -y
```

### Créer un utilisateur non-root (recommandé)

```bash
adduser immodash
usermod -aG sudo immodash
usermod -aG docker immodash  # Après installation de Docker
```

### Configurer SSH pour l'utilisateur

```bash
# Copier les clés SSH de root vers le nouvel utilisateur
rsync --archive --chown=immodash:immodash ~/.ssh /home/immodash
```

### Se reconnecter avec le nouvel utilisateur

```bash
ssh immodash@VOTRE_IP_SERVEUR
```

---

## 2. Installation de Docker

### Installer Docker

```bash
# Installer les dépendances
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Ajouter la clé GPG officielle de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le repository Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Vérifier l'installation
docker --version
docker compose version
```

### Permettre à l'utilisateur d'utiliser Docker sans sudo

```bash
sudo usermod -aG docker $USER
newgrp docker  # Ou se déconnecter/reconnecter
```

---

## 3. Clonage et configuration du projet

### Installer Git (si nécessaire)

```bash
sudo apt install -y git
```

### Cloner le repository

```bash
cd ~
git clone https://github.com/girardthur/immodash.git
cd immodash
```

### Checkout sur la branche develop

```bash
git checkout develop
```

---

## 4. Configuration des variables d'environnement

### Créer le fichier .env.production

```bash
cp .env.production.example .env.production
nano .env.production
```

### Générer les secrets nécessaires

```bash
# Générer SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Générer mots de passe PostgreSQL et Redis
openssl rand -base64 32
```

### Exemple de configuration .env.production

```env
DEBUG=False
SECRET_KEY=votre-secret-key-generee
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

POSTGRES_DB=immodash
POSTGRES_USER=immodash
POSTGRES_PASSWORD=votre-mot-de-passe-postgres

REDIS_PASSWORD=votre-mot-de-passe-redis
```

### Configurer Nginx avec votre domaine

```bash
nano nginx/conf.d/immodash.conf
```

Remplacer `_` par votre domaine dans `server_name`.

---

## 5. Premier déploiement

### Créer les répertoires nécessaires

```bash
mkdir -p staticfiles media certbot/conf certbot/www
```

### Lancer le déploiement

```bash
./deploy.sh
```

OU manuellement :

```bash
# Build des images
docker compose -f docker-compose.prod.yml build

# Lancer les services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Attendre que PostgreSQL soit prêt
sleep 15

# Appliquer les migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collecter les fichiers statiques
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Vérifier que tout fonctionne

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

Visiter http://VOTRE_IP ou http://votre-domaine.com

---

## 6. Configuration SSL avec Let's Encrypt

### Obtenir le certificat SSL

```bash
# Arrêter temporairement nginx si nécessaire
docker compose -f docker-compose.prod.yml stop nginx

# Obtenir le certificat
docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email votre-email@exemple.com \
    --agree-tos \
    --no-eff-email \
    -d votre-domaine.com \
    -d www.votre-domaine.com

# Redémarrer nginx
docker compose -f docker-compose.prod.yml start nginx
```

### Activer HTTPS dans Nginx

```bash
nano nginx/conf.d/immodash.conf
```

1. Commenter la section HTTP temporaire
2. Décommenter la section HTTPS
3. Remplacer `VOTRE_DOMAINE` par votre domaine réel
4. Activer la redirection HTTP → HTTPS

```bash
# Redémarrer nginx pour appliquer les changements
docker compose -f docker-compose.prod.yml restart nginx
```

### Tester le renouvellement automatique

```bash
docker compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

Le renouvellement automatique est configuré pour se faire tous les 12h.

---

## 7. Configuration du pare-feu

### Installer et configurer UFW

```bash
# Installer UFW
sudo apt install -y ufw

# Autoriser SSH (IMPORTANT - ne pas oublier sinon vous serez bloqué!)
sudo ufw allow 22/tcp

# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activer le pare-feu
sudo ufw enable

# Vérifier le statut
sudo ufw status
```

---

## 8. Création d'un superutilisateur

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Suivre les instructions pour créer votre compte admin.

Accéder à l'admin : https://votre-domaine.com/admin/

---

## 9. Mises à jour ultérieures

### Méthode simple avec le script

```bash
cd ~/immodash
./deploy.sh
```

### Méthode manuelle

```bash
# Pull des modifications
git pull origin develop

# Rebuild et redéployer
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Migrations et static
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 10. Monitoring et maintenance

### Voir les logs

```bash
# Tous les services
docker compose -f docker-compose.prod.yml logs -f

# Service spécifique
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery_worker
docker compose -f docker-compose.prod.yml logs -f celery_beat
```

### Voir l'état des services

```bash
docker compose -f docker-compose.prod.yml ps
```

### Sauvegarder la base de données

```bash
# Créer un backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U immodash immodash > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer depuis un backup
docker compose -f docker-compose.prod.yml exec -T db psql -U immodash immodash < backup_20241124_120000.sql
```

### Automatiser les sauvegardes avec un cron

```bash
crontab -e
```

Ajouter :
```
0 2 * * * cd ~/immodash && docker compose -f docker-compose.prod.yml exec db pg_dump -U immodash immodash > ~/backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

### Nettoyage des anciennes images Docker

```bash
docker system prune -a --volumes
```

---

## 11. Dépannage

### Les containers ne démarrent pas

```bash
# Vérifier les logs
docker compose -f docker-compose.prod.yml logs

# Vérifier les ressources
docker stats

# Vérifier l'espace disque
df -h
```

### Erreur de connexion à la base de données

```bash
# Vérifier que PostgreSQL est démarré
docker compose -f docker-compose.prod.yml ps db

# Se connecter à la DB
docker compose -f docker-compose.prod.yml exec db psql -U immodash immodash

# Recréer la DB si nécessaire
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

### Le site est lent

```bash
# Vérifier les ressources
htop
docker stats

# Augmenter le nombre de workers Gunicorn dans docker-compose.prod.yml
# Ligne : command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
# Augmenter le nombre si vous avez plus de CPU
```

### Erreurs 502 Bad Gateway

```bash
# Vérifier que le service web fonctionne
docker compose -f docker-compose.prod.yml ps web

# Vérifier les logs nginx
docker compose -f docker-compose.prod.yml logs nginx

# Redémarrer nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Le scraping ne fonctionne pas

```bash
# Vérifier les logs Celery
docker compose -f docker-compose.prod.yml logs celery_worker
docker compose -f docker-compose.prod.yml logs celery_beat

# Vérifier Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping

# Lancer un scraping manuel
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "from property_tracker.tasks import scrape_all_search_zones; scrape_all_search_zones()"
```

---

## Commandes utiles

```bash
# Redémarrer tous les services
docker compose -f docker-compose.prod.yml restart

# Redémarrer un service spécifique
docker compose -f docker-compose.prod.yml restart web

# Voir les logs en temps réel
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Entrer dans un container
docker compose -f docker-compose.prod.yml exec web bash

# Ouvrir le shell Django
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Voir l'utilisation des ressources
docker stats
```

---

## Checklist finale

- [ ] DNS configuré et pointant vers le VPS
- [ ] Pare-feu configuré (UFW)
- [ ] SSL/HTTPS activé avec Let's Encrypt
- [ ] Variables d'environnement configurées
- [ ] Base de données PostgreSQL fonctionnelle
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Superutilisateur créé
- [ ] Scraping Celery fonctionnel
- [ ] Sauvegardes automatiques configurées
- [ ] Monitoring en place

---

## Support

Pour toute question ou problème, consultez :
- Les logs : `docker compose -f docker-compose.prod.yml logs`
- La documentation Django : https://docs.djangoproject.com/
- La documentation Docker : https://docs.docker.com/
