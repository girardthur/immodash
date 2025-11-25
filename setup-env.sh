#!/bin/bash

# ===========================================
# Script de génération .env.production
# ===========================================

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Configuration .env.production${NC}"
echo -e "${GREEN}================================${NC}"

# Vérifier si .env.production existe déjà
if [ -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  Le fichier .env.production existe déjà!${NC}"
    read -p "Voulez-vous le remplacer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Opération annulée."
        exit 0
    fi
fi

# Copier le template
cp .env.production.example .env.production

echo -e "\n${YELLOW}🔐 Génération des secrets...${NC}"

# Générer SECRET_KEY (compatible Django)
SECRET_KEY=$(openssl rand -base64 50 | tr -d '/+=' | head -c 50)
echo -e "${GREEN}✓ SECRET_KEY généré${NC}"

# Générer POSTGRES_PASSWORD (sans caractères spéciaux problématiques)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo -e "${GREEN}✓ POSTGRES_PASSWORD généré${NC}"

# Générer REDIS_PASSWORD (sans caractères spéciaux problématiques)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo -e "${GREEN}✓ REDIS_PASSWORD généré${NC}"

# Demander le domaine
echo -e "\n${YELLOW}🌐 Configuration du domaine${NC}"
read -p "Entrez votre nom de domaine (ex: immodash.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "Domaine non fourni. Utilisation de localhost"
    DOMAIN="localhost"
    ALLOWED_HOSTS="localhost,127.0.0.1"
    CSRF_TRUSTED_ORIGINS="http://localhost,http://127.0.0.1"
else
    ALLOWED_HOSTS="${DOMAIN},www.${DOMAIN}"
    CSRF_TRUSTED_ORIGINS="https://${DOMAIN},https://www.${DOMAIN}"
fi

# Remplacer les valeurs dans .env.production
sed -i.bak "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env.production
sed -i.bak "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" .env.production
sed -i.bak "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=${REDIS_PASSWORD}|" .env.production
sed -i.bak "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${ALLOWED_HOSTS}|" .env.production
sed -i.bak "s|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}|" .env.production

# Supprimer le fichier de backup
rm -f .env.production.bak

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ Fichier .env.production créé!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${YELLOW}📋 Configuration générée:${NC}"
echo "  - Domaine: ${DOMAIN}"
echo "  - ALLOWED_HOSTS: ${ALLOWED_HOSTS}"
echo "  - Secrets générés automatiquement"

echo -e "\n${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  - Ne commitez JAMAIS le fichier .env.production"
echo "  - Sauvegardez vos mots de passe dans un gestionnaire sécurisé"
echo "  - Vous pouvez maintenant lancer: ./deploy.sh"
