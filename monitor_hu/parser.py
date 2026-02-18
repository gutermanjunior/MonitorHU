import os
import time
import pickle
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

COOKIE_FILE = DATA_DIR / "hu_cookies.pkl"

HU_URL = "https://sistemashu.hu.usp.br/"  # ajuste se necessário


class HUParser:

    def __init__(self, headless=False):
        self.driver = self._create_driver(headless)

    def _create_driver(self, headless):
        options = Options()
        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _save_cookies(self):
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def _load_cookies(self):
        if not COOKIE_FILE.exists():
            return False

        self.driver.get(HU_URL)

        with open(COOKIE_FILE, "rb") as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.refresh()
        return True

    def _is_logged_in(self):
        # Ajustar lógica conforme site real
        return "logout" in self.driver.page_source.lower()

    def _manual_login(self):
        print("\n🔐 Realize o login manualmente (resolver CAPTCHA)...")
        self.driver.get(HU_URL)

        # Preencher campos automaticamente
        time.sleep(2)
        self.driver.find_element(By.NAME, HU_USER).send_keys(HU_USER)
        self.driver.find_element(By.NAME, HU_DATA.send_keys(HU_DATA)

        print("Aguardando você resolver o CAPTCHA e clicar em entrar...")
        input("Pressione ENTER após concluir o login...")

        if self._is_logged_in():
            print("✅ Login detectado. Salvando cookies...")
            self._save_cookies()
        else:
            raise Exception("Falha no login.")

    def ensure_authenticated(self):
        if COOKIE_FILE.exists():
            self._load_cookies()
            time.sleep(2)

            if self._is_logged_in():
                return

        self._manual_login()

    def fetch_especialidades(self):
        self.ensure_authenticated()

        # Aqui você navega até o dropdown
        # Ajuste o seletor conforme o site real
        dropdown = self.driver.find_elements(By.TAG_NAME, "option")

        especialidades = [
            option.text.strip()
            for option in dropdown
            if option.text.strip()
        ]

        return especialidades

    def close(self):
        self.driver.quit()
