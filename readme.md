# 🎧 Spotify Listening Habits Dashboard

Ce projet est une application de **Data Visualization** personnelle permettant de suivre, stocker et analyser ses habitudes d'écoute Spotify en temps réel. Elle se compose d'un robot de collecte automatique et d'un tableau de bord interactif.

## 🚀 Fonctionnalités
* **Collecte Automatique** : Un script en arrière-plan récupère vos 50 dernières écoutes toutes les quelques minutes pour ne rien rater.
* **Dashboard Interactif** : Visualisation de vos statistiques via Streamlit.
    * **KPIs** : Nombre total de morceaux, artistes uniques et temps d'écoute total.
    * **Tops** : Classement de vos artistes et morceaux les plus écoutés.
    * **Analyses Temporelles** : Répartition de l'écoute par heure de la journée et par jour de la semaine.
* **Stockage Local** : Utilisation de SQLite pour conserver l'historique de manière sécurisée et privée.

## 📁 Structure du Projet
```text
├── 📄 app.py                  # Dashboard Streamlit principal
├── 📁 bot/                    # Moteur de collecte
│   ├── 📄 auto_fetch.py       # Script de boucle automatique
│   └── 📄 fetch_history.py    # Logique d'appel API Spotify
├── 📁 data_base_tools/        # Utilitaires de base de données
│   ├── 📄 db.py               # Initialisation de la table SQLite
│   └── 📄 check_db.py         # Script d'inspection rapide
├── 📄 requirements.txt        # Dépendances Python
└── 📄 .gitignore              # Sécurité (ignore .env, .db, .cache)