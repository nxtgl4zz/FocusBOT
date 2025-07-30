# FocusBot - Discord Focus Session Manager

Un bot Discord pour gérer des sessions de focus collaboratives avec des intervalles chronométrés et un suivi des membres.

## Fonctionnalités

- 🧠 **Sessions de focus chronométrées** - Créez des sessions de focus avec une durée personnalisée
- 👥 **Gestion collaborative** - Les utilisateurs peuvent rejoindre et quitter les sessions
- ⏰ **Suivi automatique** - Nettoyage automatique des sessions expirées
- 📊 **Statut en temps réel** - Vérifiez le temps restant et les participants
- 🔒 **Contrôles de permissions** - Seuls les créateurs ou modérateurs peuvent terminer les sessions
- 🌐 **Multi-serveurs** - Gère plusieurs sessions simultanées sur différents serveurs

## Commandes

### `/startfocus <minutes>`
Démarre une nouvelle session de focus avec la durée spécifiée (1-480 minutes).

### `/joinfocus`
Rejoint la session de focus en cours sur le serveur.

### `/leavefocus`
Quitte la session de focus en cours.

### `/status`
Affiche le statut de la session actuelle (temps restant, participants, etc.).

### `/endfocus`
Termine la session de focus en cours (réservé au créateur ou aux modérateurs).

## Installation et Configuration

### Prérequis
- Python 3.8+
- Token de bot Discord
- Permissions appropriées sur le serveur Discord

### Installation

1. **Clonez ou téléchargez les fichiers**
   ```bash
   # Si vous avez git
   git clone <repository-url>
   cd focusbot
   
