#!/bin/bash

# ===========================================
# Script de déploiement Immodash
# ===========================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Déploiement Immodash${NC}"
echo -e "${GREEN}================================${NC}"

# Vérifier que nous sommes sur le serveur de production
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Fichier .env.production introuvable!${NC}"
    echo -e "${YELLOW}Créez-le à partir de .env.production.example${NC}"
    exit 1
fi

# Pull des dernières modifications
echo -e "\n${YELLOW}📥 Pull des dernières modifications...${NC}"
git pull origin develop

# Build des images Docker
echo -e "\n${YELLOW}🔨 Build des images Docker...${NC}"
docker compose -f docker-compose.prod.yml build

# Arrêt des anciens containers
echo -e "\n${YELLOW}⏹️  Arrêt des anciens containers...${NC}"
docker compose -f docker-compose.prod.yml down

# Démarrage des nouveaux containers
echo -e "\n${YELLOW}🚀 Démarrage des containers...${NC}"
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Attendre que la DB soit prête
echo -e "\n${YELLOW}⏳ Attente de la base de données...${NC}"
sleep 10

# Migrations de la base de données
echo -e "\n${YELLOW}📊 Application des migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collecte des fichiers statiques
echo -e "\n${YELLOW}📦 Collecte des fichiers statiques...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Vérification du statut
echo -e "\n${YELLOW}🔍 Vérification du statut des services...${NC}"
docker compose -f docker-compose.prod.yml ps

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ Déploiement terminé!${NC}"
echo -e "${GREEN}================================${NC}"

# Afficher les logs
echo -e "\n${YELLOW}📋 Logs récents (Ctrl+C pour quitter):${NC}"
docker compose -f docker-compose.prod.yml logs --tail=50 -f
