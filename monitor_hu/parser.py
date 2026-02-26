import os
import time
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .logger import get_logger

# Caminhos organizados
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
COOKIES_FILE = DATA_DIR / "hu_cookies.pkl"
URL = "https://sistemashu.hu.usp.br/reshu/paciente"

log = get_logger("Parser")

class HUParser:
    def __init__(self, HU_USER, HU_DATA):
        self.HU_USER = HU_USER
        self.HU_DATA = HU_DATA
        log.info("Inicializando WebDriver...")
        self.driver = self._init_driver()

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            log.info("WebDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            log.error(f"Falha crítica ao iniciar WebDriver: {e}")
            raise

    def open(self):
        self.driver.get(URL)

    def load_cookies(self):
        if COOKIES_FILE.exists():
            try:
                with open(COOKIES_FILE, "rb") as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                self.driver.refresh()
                log.info("Cookies carregados. Tentando restaurar sessão...")
                return True
            except Exception as e:
                log.warning(f"Erro ao ler arquivo de cookies: {e}")
                return False
        return False

    def save_cookies(self):
        try:
            with open(COOKIES_FILE, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            log.info("Sessão salva em cookies (hu_cookies.pkl).")
        except Exception as e:
            log.error(f"Erro ao salvar cookies: {e}")

    def manual_login(self):
        log.info("Iniciando processo de login manual (automação do form).")
        wait = WebDriverWait(self.driver, 15)

        print("Aguardando formulário...")
        matricula = wait.until(EC.element_to_be_clickable((By.ID, "PacienteMatricula")))
        matricula.clear()
        matricula.send_keys(self.HU_USER)

        print("Preenchendo data via injeção JavaScript...")
        data_field = wait.until(EC.presence_of_element_located((By.ID, "PacienteDataNascimento")))
        
        js_script = """
            var el = arguments[0]; var val = arguments[1];
            el.value = val;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
        """
        self.driver.execute_script(js_script, data_field, self.HU_DATA)

        print("🔐 Resolva o CAPTCHA manualmente no navegador.")
        log.info("Formulário preenchido. Aguardando resolução do CAPTCHA pelo usuário.")
        
        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, "Especialidade"))
            )
            print("Login detectado!")
            log.info("Login realizado com sucesso! Dropdown detectado.")
            self.save_cookies()
        except Exception as e:
            print("Tempo esgotado para login.")
            log.error(f"Timeout de 5 minutos aguardando login manual/CAPTCHA. Erro: {e}")

    def ensure_logged(self):
        self.open()

        if self.load_cookies():
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "Especialidade"))
                )
                log.info("Sessão restaurada com sucesso via Cookies.")
                return
            except:
                log.warning("Cookies expiraram ou foram invalidados pelo servidor.")

        print("Necessário login manual.")
        self.manual_login()

    def get_dropdown_options(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            select_elem = wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
            options = select_elem.find_elements(By.TAG_NAME, "option")
            
            results = set()
            ignore_list = {"Selecione a Especialidade...", "", "Selecione..."}
            
            for opt in options:
                text = opt.text.strip()
                if text and text not in ignore_list:
                    results.add(text)
            
            return results
        except Exception as e:
            log.warning(f"Erro ao extrair opções do dropdown: {e}")
            return set()

    def take_screenshot(self, filename="screenshot.png"):
        try:
            try:
                dropdown = self.driver.find_element(By.ID, "Especialidade")
                dropdown.click()
                time.sleep(0.5)
            except: pass

            path = DATA_DIR / filename
            self.driver.save_screenshot(str(path))
            log.info(f"Screenshot gerado: {filename}")
            return str(path)
        except Exception as e:
            log.error(f"Erro ao gerar screenshot: {e}")
            return None

    def close(self):
        log.info("Encerrando WebDriver.")
        try: self.driver.quit()
        except: pass