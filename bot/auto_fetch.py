import time
import datetime
import fetch_history 

def run_auto():
    print("🤖 Robot Spotify actif...")
    print("Mode : Synchro automatique + Nettoyage Last.fm + Push GitHub")
    
    while True:
        maintenant = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{maintenant}] Lancement de la vérification...")
        
        try:
            # fetch_history.main() gère maintenant la DB, les genres ET le push Git
            nouveaux_sons = fetch_history.main()
            
            if nouveaux_sons:
                print(f"🎶 {len(nouveaux_sons)} nouveaux titres enregistrés.")
            else:
                print("💤 Rien de nouveau.")
                
        except Exception as e:
            print(f"❌ Erreur robot : {e}")
        
        print("⏳ Prochaine vérification dans 30 minutes...\n")
        time.sleep(1800)

if __name__ == "__main__":
    run_auto()