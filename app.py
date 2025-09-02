import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile

app = Flask(__name__)

@app.route('/ping')
def ping():
    return "Bot is running", 200

class HadariaVoteBot:
    def __init__(self, username, log_callback=None):
        self.username = username
        self.log_callback = log_callback or print
        self.driver = None
        self.user_data_dir = os.path.join(tempfile.gettempdir(), 'chrome_profile')
        self.setup_chrome()

    def setup_chrome(self):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        if 'RENDER' in os.environ:
            self.log_callback("🔧 Initialisation de ChromeDriver pour Render...")
            chrome_options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path, service_args=['--verbose'], log_path=os.devnull)
        else:
            self.log_callback("🔧 Initialisation de ChromeDriver local...")
            service = Service(ChromeDriverManager().install(), service_args=['--verbose'], log_path=os.devnull)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        self.log_callback("✅ ChromeDriver initialisé avec succès")
    except Exception as e:
        self.log_callback(f"❌ Erreur ChromeDriver: {e}")
        raise Exception(f"Impossible d'initialiser le navigateur Chrome: {e}")
        try:
            if 'RENDER' in os.environ:
                self.log_callback("🔧 Initialisation de ChromeDriver pour Render...")
                chrome_bin = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
                chrome_options.binary_location = chrome_bin
                service = Service(
                    ChromeDriverManager(path="/opt/render/project/.render/chrome").install(),
                    service_args=['--verbose'],
                    log_path=os.devnull
                )
            else:
                self.log_callback("🔧 Initialisation de ChromeDriver local...")
                service = Service(
                    ChromeDriverManager().install(),
                    service_args=['--verbose'],
                    log_path=os.devnull
                )
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.log_callback("✅ ChromeDriver initialisé avec succès")
        except Exception as e:
            self.log_callback(f"❌ Erreur ChromeDriver: {e}")
            raise Exception(f"Impossible d'initialiser le navigateur Chrome: {e}")

    def switch_to_new_tab(self):
        time.sleep(2)
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])
            return True
        return False

    def perform_voting(self):
        try:
            self.log_callback(f"--- Nouveau vote à {datetime.now().strftime('%H:%M:%S')} ---")
            self.driver.get("https://hadaria.fr/vote")
            self.log_callback("Page de vote initiale chargée")
            username_field = self.wait.until(
                EC.element_to_be_clickable((By.ID, "name"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            self.log_callback(f"Pseudo '{self.username}' entré")
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Valider')]"))
            )
            submit_button.click()
            self.log_callback("Formulaire soumis")
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "vote-block"))
            )
            self.log_callback("Page de vote prête")
            vote_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@id, 'site_button_')]"))
            )
            vote_button.click()
            self.log_callback("Bouton de vote cliqué - nouvel onglet ouvert")
            if not self.switch_to_new_tab():
                self.log_callback("Échec du basculement vers le nouvel onglet")
                return False
            self.log_callback("Basculé vers le nouvel onglet")
            try:
                vote_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "voteBtn"))
                )
                vote_button.click()
                self.log_callback("Bouton 'Je vote maintenant' cliqué avec succès")
                time.sleep(3)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return True
            except Exception as e:
                self.log_callback(f"Erreur lors du clic final: {str(e)}")
                return False
        except Exception as e:
            self.log_callback(f"Erreur pendant le vote: {str(e)}")
            return False
        finally:
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            if len(self.driver.window_handles) > 0:
                self.driver.switch_to.window(self.driver.window_handles[0])

    def vote(self):
        return self.perform_voting()

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                self.log_callback("Navigateur fermé")
        except Exception as e:
            self.log_callback(f"Erreur lors de la fermeture: {e}")

    def run_continuous(self):
        try:
            while True:
                success = self.perform_voting()
                next_vote = datetime.now() + timedelta(minutes=90)
                if success:
                    self.log_callback(f"Prochain vote à {next_vote.strftime('%H:%M:%S')}")
                else:
                    self.log_callback("Nouvelle tentative dans 5 minutes")
                    next_vote = datetime.now() + timedelta(minutes=5)
                while datetime.now() < next_vote:
                    time.sleep(1)
        except KeyboardInterrupt:
            self.log_callback("\nArrêt du bot par l'utilisateur")
        finally:
            if self.driver:
                self.driver.quit()
                self.log_callback("Navigateur fermé")

def run_bot():
    username = os.getenv('MINECRAFT_USERNAME', '200Pings')
    bot = HadariaVoteBot(username)
    bot.run_continuous()

if __name__ == "__main__":
    # Lancer le bot dans un thread séparé pour ne pas bloquer Flask
    threading.Thread(target=run_bot, daemon=True).start()
    # Lancer le serveur Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
