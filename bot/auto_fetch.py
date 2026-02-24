import time
import datetime
import subprocess 
import fetch_history 

def git_push_db():
    try:
        subprocess.run(["git", "add", "spotify_data.db"], check=True, timeout=30)
        maintenant = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Mise à jour automatique de la DB : {maintenant}"
        subprocess.run(["git", "commit", "-m", message], check=True, timeout=30)
        subprocess.run(["git", "push"], check=True, timeout=60)
        print("🚀 Base de données synchronisée sur GitHub !")
    except subprocess.TimeoutExpired:
        print("⏳ Git push a expiré (authentification requise ?). Lance un git push manuel.")
    except subprocess.CalledProcessError:
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
            # 1. On récupère la liste des nouveaux morceaux
            nouveaux_sons = fetch_history.main()
            
            # 2. Si on a des nouveaux sons, on les affiche
            if nouveaux_sons:
                print("🎶 Nouveaux titres détectés :")
                for son in nouveaux_sons:
                    print(f"   • {son}")
                
                # 3. On pousse les changements sur GitHub
                git_push_db()
            else:
                print("💤 Aucun nouveau morceau depuis la dernière vérification.")
            
        except Exception as e:
            print(f"❌ Une erreur est survenue lors de la boucle : {e}")
        
        print("⏳ Prochaine vérification dans 30 minutes (1800 secondes)...\n")
        time.sleep(1800)

if __name__ == "__main__":
    run_auto()