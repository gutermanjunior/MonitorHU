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

# Caminhos organizados (Salva cookies na pasta data/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
COOKIES_FILE = DATA_DIR / "hu_cookies.pkl"
URL = "https://sistemashu.hu.usp.br/reshu/paciente"


class HUParser:

    def __init__(self, HU_USER, HU_DATA):
        self.HU_USER = HU_USER
        self.HU_DATA = HU_DATA
        self.driver = self._init_driver()

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--log-level=3")
        
        # Disfarça o bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

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
                return True
            except Exception as e:
                return False
        return False

    def save_cookies(self):
        try:
            with open(COOKIES_FILE, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
        except Exception:
            pass

    def manual_login(self):
        wait = WebDriverWait(self.driver, 15)

        print("Aguardando formulário...")
        matricula = wait.until(
            EC.element_to_be_clickable((By.ID, "PacienteMatricula"))
        )
        matricula.clear()
        matricula.send_keys(self.HU_USER)

        data_field = wait.until(
            EC.element_to_be_clickable((By.ID, "PacienteDataNascimento"))
        )

        # Método antigo: Digitação Humana (Tecla por tecla)
        # Isso evita quebra da máscara de data do site
        data_field.click()
        data_field.clear()
        
        for digito in self.HU_DATA:
            data_field.send_keys(digito)
            time.sleep(0.1)  # Pequeno delay para a máscara processar

        print("🔐 Resolva o CAPTCHA manualmente no navegador.")
        print("Aguardando login ser concluído...")
        
        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, "Especialidade"))
            )
            print("Login detectado!")
            self.save_cookies()
        except:
            print("Tempo esgotado para login.")

    def ensure_logged(self):
        self.open()

        if self.load_cookies():
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "Especialidade"))
                )
                return
            except:
                pass

        print("Necessário login manual.")
        self.manual_login()

    def get_dropdown_options(self):
        """Lê as opções disponíveis no Dropdown de especialidades"""
        try:
            wait = WebDriverWait(self.driver, 10)
            select_elem = wait.until(
                EC.presence_of_element_located((By.ID, "Especialidade"))
            )
            
            options = select_elem.find_elements(By.TAG_NAME, "option")
            
            results = set()
            ignore_list = {"Selecione a Especialidade...", "", "Selecione..."}
            
            for opt in options:
                text = opt.text.strip()
                if text and text not in ignore_list:
                    results.add(text)
            
            return results
            
        except Exception:
            return set()

    def close(self):
        self.driver.quit()