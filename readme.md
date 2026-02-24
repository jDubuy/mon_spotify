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

### 1. Installation des dépendances
Installez les bibliothèques nécessaires via le fichier requirements :

```powershell
pip install -r requirements.txt
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
python data_base_tools/db.py
```

## 📈 Commandes d'utilisation

### Lancer la collecte automatique (Bot)
Démarre le robot qui récupère vos écoutes et met à jour GitHub toutes les 5 minutes :

```powershell
python bot/auto_fetch.py
```

### Lancer le Dashboard
Pour visualiser vos statistiques en temps réel sur votre navigateur :

```powershell
streamlit run app.py
```

### Vérifier le contenu de la base
Inspectez rapidement les 10 dernières entrées de votre base de données :

```powershell
python data_base_tools/check_db.py
```

