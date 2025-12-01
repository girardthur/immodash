#!/bin/bash

# Script de déploiement en production pour Immodash
# Usage: ./deploy-prod.sh

set -e  # Arrêter en cas d'erreur

echo "========================================="
echo "  DÉPLOIEMENT IMMODASH EN PRODUCTION"
echo "========================================="
echo ""

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour logger
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "docker-compose.prod.yml" ]; then
    log_error "Fichier docker-compose.prod.yml introuvable!"
    log_error "Assurez-vous d'être dans le répertoire racine du projet."
    exit 1
fi

# Vérifier que le fichier .env.production existe
if [ ! -f ".env.production" ]; then
    log_error "Fichier .env.production introuvable!"
    log_error "Créez-le avec ./setup-env.sh"
    exit 1
fi

# 1. Arrêter tous les services s'ils tournent
log_info "Arrêt des services Docker..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production down 2>/dev/null || true

# 2. Nettoyer Docker (optionnel - décommenter si besoin)
# log_warn "Nettoyage Docker (images, containers, volumes non utilisés)..."
# sudo docker system prune -af --volumes

# 3. Pull les derniers changements Git
log_info "Récupération des derniers changements Git..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Branche actuelle: $CURRENT_BRANCH"

# Demander confirmation avant de pull
read -p "Voulez-vous pull les changements depuis origin/$CURRENT_BRANCH? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git pull origin $CURRENT_BRANCH
    log_info "Git pull effectué avec succès"
else
    log_warn "Git pull ignoré"
fi

# 4. Rebuild les images Docker
log_info "Reconstruction des images Docker..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production build

# 5. Démarrer tous les services
log_info "Démarrage des services..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Attendre que les services démarrent
log_info "Attente du démarrage des services (15 secondes)..."
sleep 15

# 6. Appliquer les migrations
log_info "Application des migrations..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py migrate

# 7. Collecter les fichiers statiques
log_info "Collecte des fichiers statiques..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py collectstatic --noinput

# 8. Vérifier le statut des services
log_info "Vérification du statut des services..."
sudo docker compose -f docker-compose.prod.yml --env-file .env.production ps

echo ""
echo "========================================="
echo "  ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "========================================="
echo ""
log_info "Services disponibles:"
log_info "  - Application web: https://immodash.pro"
log_info "  - Admin Django: https://immodash.pro/admin/"
log_info "  - Gestion zones: https://immodash.pro/zones/"
echo ""
log_info "Commandes utiles:"
echo "  - Logs web:     sudo docker compose -f docker-compose.prod.yml --env-file .env.production logs -f web"
echo "  - Logs Celery:  sudo docker compose -f docker-compose.prod.yml --env-file .env.production logs -f celery_worker"
echo "  - Logs Nginx:   sudo docker compose -f docker-compose.prod.yml --env-file .env.production logs -f nginx"
echo "  - Shell Django: sudo docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py shell"
echo ""
