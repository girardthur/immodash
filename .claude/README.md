# Configuration Claude Code pour Immodash

Ce dossier contient la configuration optimisée de Claude Code pour le projet Immodash.

## Structure

```
.claude/
├── claude.md              # Contexte principal du projet
├── README.md              # Ce fichier
├── commands/              # Slash commands personnalisés
│   ├── test.md           # Lancer les tests avec coverage
│   ├── migrate.md        # Créer et appliquer les migrations
│   ├── scrape.md         # Lancer le scraping manuel
│   ├── docker-logs.md    # Afficher les logs Docker
│   ├── docker-restart.md # Redémarrer les services Docker
│   ├── shell.md          # Ouvrir le shell Django
│   ├── check.md          # Vérifier la santé de l'app
│   └── stats.md          # Afficher les stats DB
└── hooks/                 # Hooks d'événements
    ├── session-start     # Exécuté au démarrage de session
    ├── post-edit         # Exécuté après chaque édition
    └── pre-commit        # Exécuté avant chaque commit
```

## Fichier principal : claude.md

Le fichier `claude.md` contient :
- Vue d'ensemble du projet
- Stack technique détaillée
- Architecture et structure du code
- Description des modèles de données
- Fonctionnalités principales
- Commandes utiles (Django, Celery, Docker)
- Conventions de code
- Variables d'environnement
- Problèmes courants et solutions
- Améliorations prioritaires

## Slash Commands

Les slash commands permettent d'exécuter rapidement des tâches courantes :

### `/test`
Lance tous les tests Django avec coverage et affiche le rapport de couverture.

### `/migrate`
Crée et applique les migrations de base de données Django.

### `/scrape`
Lance le scraping manuel de toutes les zones de recherche.

### `/docker-logs`
Affiche les logs en temps réel de tous les services Docker.

### `/docker-restart`
Redémarre tous les services Docker (web, celery_worker, celery_beat, redis).

### `/shell`
Ouvre un shell Django interactif dans le container Docker.

### `/check`
Vérifie la configuration Django et détecte les problèmes potentiels.

### `/stats`
Affiche les statistiques actuelles de la base de données (zones, annonces, prix).

## Hooks

Les hooks sont des scripts shell qui s'exécutent automatiquement en réponse à des événements.

### session-start
S'exécute au démarrage de chaque session Claude Code :
- Vérifie que Docker est installé et les services sont actifs
- Vérifie la présence de l'environnement virtuel Python
- Vérifie la présence du fichier .env
- Affiche la liste des commandes slash disponibles

### post-edit
S'exécute après chaque édition de fichier :
- Pour les fichiers Python : vérifie la syntaxe avec flake8 (si disponible)
- Pour models.py : rappelle de créer les migrations
- Pour requirements.txt : rappelle de réinstaller les dépendances

### pre-commit
S'exécute avant chaque commit :
- Vérifie la syntaxe Python de tous les fichiers modifiés
- Si models.py modifié : vérifie que les migrations sont à jour
- Empêche le commit si des erreurs sont détectées

## Utilisation

### Avec Claude Code

Les fichiers de ce dossier sont automatiquement chargés par Claude Code au démarrage de chaque session. Claude aura accès à tout le contexte du projet et pourra :

1. Comprendre rapidement l'architecture du projet
2. Utiliser les slash commands pour exécuter des tâches courantes
3. Être alerté par les hooks lors de certaines actions

### Slash commands

Utilisez les slash commands en les tapant directement :
```
/test
/migrate
/scrape
```

### Hooks

Les hooks s'exécutent automatiquement, pas besoin de les lancer manuellement. Vous pouvez les personnaliser en éditant les fichiers dans `.claude/hooks/`.

## Personnalisation

### Ajouter un nouveau slash command

1. Créez un nouveau fichier `.md` dans `.claude/commands/`
2. Ajoutez le front matter avec la description :
```markdown
---
description: Description courte du command
---

Instructions détaillées pour Claude...
```

### Modifier un hook

Les hooks sont des scripts shell standard. Vous pouvez les modifier directement dans `.claude/hooks/`.

N'oubliez pas de les rendre exécutables :
```bash
chmod +x .claude/hooks/nom-du-hook
```

## Notes importantes

- Les hooks doivent être exécutables (`chmod +x`)
- Les slash commands utilisent le format Markdown avec front matter YAML
- Le fichier `claude.md` est chargé en priorité pour le contexte global
- Les hooks peuvent accéder aux variables d'environnement du système

## Ressources

- Documentation Claude Code : https://docs.claude.com/claude-code
- Exemples de configuration : https://github.com/anthropics/claude-code-examples
