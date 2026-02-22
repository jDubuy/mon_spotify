import time
import datetime
import fetch_history # On importe ton script précédent !

def run_auto():
    print("🤖 Démarrage du robot de récupération automatique Spotify...")
    print("Pour l'arrêter, appuie sur Ctrl+C dans le terminal.\n")
    
    while True:
        maintenant = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{maintenant}] Lancement de la vérification...")
        
        try:
            # On appelle la fonction main() de ton script fetch_history.py
            fetch_history.main()
        except Exception as e:
            print(f"❌ Une erreur est survenue : {e}")
        
        print("⏳ Prochaine vérification dans 1 heure...\n")
        
        # Le script s'endort pendant 3600 secondes (1 heure)
        time.sleep(300)

if __name__ == "__main__":
    run_auto()