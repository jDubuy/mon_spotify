# 🎧 Spotify Listening Habits Dashboard

Ce projet est une application de **Data Visualization** personnelle permettant de suivre, stocker et analyser ses habitudes d'écoute Spotify en temps réel. Elle comprend un bot de collecte automatique avec synchronisation Git et un dashboard interactif.



## 🚀 Fonctionnalités
* **Collecte Automatique & Sync Git** : Un script récupère vos 50 dernières écoutes toutes les 5 minutes et synchronise automatiquement la base de données sur GitHub.
* **Dashboard Interactif** : Visualisation complète de vos données via une interface Streamlit.
    * **Statistiques Globales** : Affichage du nombre total de morceaux, des artistes uniques et du temps d'écoute total.
    * **Classements** : Graphiques des tops artistes et des morceaux les plus écoutés.
    * **Habitudes** : Analyse de l'écoute par heure de la journée et par jour de la semaine.
* **Stockage SQLite** : Utilisation d'une base de données locale pour conserver l'historique complet.

## 📁 Structure du Projet
```text
├── 📄 app.py                  # Dashboard Streamlit principal
├── 📁 bot/                    # Scripts de collecte
│   ├── 📄 auto_fetch.py       # Bot avec auto-push GitHub
│   └── 📄 fetch_history.py    # Logique d'extraction API
├── 📁 data_base_tools/        # Utilitaires DB
│   ├── 📄 db.py               # Initialisation de la base
│   └── 📄 check_db.py         # Outil de vérification rapide
├── 📄 requirements.txt        # Librairies requises
├── 📄 .gitignore              # Gestion des exclusions Git
└── 📄 spotify_data.db         # Base de données des écoutes
```

## 🛠️ Installation et Configuration

### ✅ Prérequis Obligatoires

#### Version de Python
- **Python 3.10 minimum** (recommandé : 3.11+)
- Vérifiez votre version : `py --version`

#### Fichiers Obligatoires (avant toute utilisation)
```
✓ requirements.txt       → Liste des dépendances
✓ .env                   → Identifiants API Spotify
✓ spotify_data.db        → Base de données (créée à l'installation)
```

### 1. Installation des dépendances
Installez les bibliothèques nécessaires via le fichier requirements :

```powershell
py -m pip install -r requirements.txt
```

### 2. Configuration API Spotify
Créez un fichier `.env` à la racine avec vos accès Spotify Developer :

```
SPOTIPY_CLIENT_ID='votre_id'
SPOTIPY_CLIENT_SECRET='votre_secret'
SPOTIPY_REDIRECT_URI='http://localhost:8888/callback'

LASTFM_API_KEY='votre_clé_API'
```

### 3. Initialisation de la base de données
Exécutez le script pour créer la table history dans SQLite :

```powershell
py data_base_tools/db.py
```

## 📈 Commandes d'utilisation

### 🎯 Deux modes de lancement disponibles

#### Mode 1 : Dashboard Streamlit (Recommandé pour l'analyse)
Le dashboard Streamlit offre une interface riche avec graphiques interactifs.

```powershell
py -m streamlit run app.py
```

**Accès** : http://localhost:8501

**Avantages** :
- Interface Rich avec graphiques Plotly
- Rechargement automatique en temps réel
- Meilleur pour l'analyse approfondie

---

#### Mode 2 : Frontend HTML + API FastAPI (Recommandé pour le déploiement)
Combine un frontend léger (index.html) avec une API backend FastAPI.

**Étape 1 : Démarrer le serveur API**
```powershell
py api.py
```

**Étape 2 : Accéder au frontend**
Ouvrez votre navigateur et allez à : http://127.0.0.1:8000

**Avantages** :
- Architecture modulaire (Frontend/Backend séparé)
- Plus léger et rapide
- Idéal pour le déploiement en production
- Backend API réutilisable

---

### 🤖 Lancer la collecte automatique (Bot)
Démarre le robot qui récupère vos écoutes et met à jour GitHub toutes les 5 minutes :

```powershell
py bot/auto_fetch.py
```

### 🔍 Vérifier le contenu de la base
Inspectez rapidement les 10 dernières entrées de votre base de données :

```powershell
py data_base_tools/check_db.py
```

##  Installation et Configuration

### 1. Prérequis
Installez les bibliothèques requises :

\\\powershell
pip install -r requirements.txt
\\\

### 2. Configuration API (.env)
Créez un fichier \.env\ à la racine avec vos identifiants :

\\\
SPOTIPY_CLIENT_ID='votre_id'
SPOTIPY_CLIENT_SECRET='votre_secret'
# Note : Utilisez 127.0.0.1 au lieu de localhost pour la stabilité
SPOTIPY_REDIRECT_URI='https://127.0.0.1:8888/callback'

LASTFM_API_KEY='votre_clé_api'
\\\

### 3. Configuration Spotify for Developers
Dans les réglages de votre application sur le dashboard Spotify :

- Ajoutez l'URI de redirection : \https://127.0.0.1:8888/callback\.
- Assurez-vous que le protocole (HTTP/HTTPS) correspond exactement à votre fichier \.env\.

##  Utilisation

### Lancer le Dashboard
\\\powershell
streamlit run app.py
\\\

### Démarrer la collecte automatique
\\\powershell
python bot/auto_fetch.py
\\\

##  Architecture des Données
Le projet utilise une base SQLite structurée pour optimiser les performances :

- **history** : Journal des écoutes (timestamp, track_id).
- **tracks** : Détails des morceaux.
- **artists** : Informations sur les artistes et genres.
- **albums** : Métadonnées des albums et URLs des pochettes.
- **settings** : Stockage des préférences utilisateur (ex: pochette de vitrine choisie).

##  Personnalisation
Le style visuel est géré de manière centralisée dans `assets/style.css`. Vous pouvez y modifier les couleurs (vert Spotify #1DB954), les animations de survol des images ou le design des cartes de titres.
