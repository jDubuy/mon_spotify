import time
import datetime
import subprocess  # Pour lancer les commandes Git
import fetch_history # On importe ton script de récupération

def git_push_db():
    """Fonction pour automatiser la mise à jour de la base sur GitHub"""
    try:
        # Ajoute la base de données à l'index Git
        subprocess.run(["git", "add", "spotify_data.db"], check=True)
        
        # Crée un commit avec un message horodaté
        maintenant = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Mise à jour automatique de la DB : {maintenant}"
        
        # Le commit peut échouer s'il n'y a pas de changements, d'où le try/except
        subprocess.run(["git", "commit", "-m", message], check=True)
        
        # Envoie les modifications sur GitHub
        subprocess.run(["git", "push"], check=True)
        print("🚀 Base de données synchronisée sur GitHub !")
    except subprocess.CalledProcessError:
        # Arrive souvent s'il n'y a rien à committer (0 nouvelles écoutes)
        print("ℹ️ Rien à mettre à jour sur GitHub (pas de nouveaux morceaux).")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'automatisation Git : {e}")

def run_auto():
    print("🤖 Démarrage du robot de récupération automatique Spotify...")
    print("Pour l'arrêter, appuie sur Ctrl+C dans le terminal.\n")
    
    while True:
        maintenant = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{maintenant}] Lancement de la vérification...")
        
        try:
            # 1. On lance la récupération Spotify
            fetch_history.main()
            
            # 2. On tente de pousser la mise à jour sur GitHub
            git_push_db()
            
        except Exception as e:
            print(f"❌ Une erreur est survenue lors de la boucle : {e}")
        
        print("⏳ Prochaine vérification dans 5 minutes (300 secondes)...\n")
        
        # Le script s'endort pendant 300 secondes (5 minutes)
        time.sleep(300)

if __name__ == "__main__":
    run_auto()