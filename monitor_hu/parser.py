import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


URL = "https://sistemashu.hu.usp.br/reshu/paciente"
COOKIES_FILE = "hu_cookies.pkl"


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

        return webdriver.Chrome(options=options)

    def open(self):
        self.driver.get(URL)

    def load_cookies(self):
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            self.driver.refresh()
            return True
        return False

    def save_cookies(self):
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def manual_login(self):
        wait = WebDriverWait(self.driver, 15)

        matricula = wait.until(
            EC.element_to_be_clickable((By.ID, "PacienteMatricula"))
        )
        matricula.clear()
        matricula.send_keys(self.HU_USER)

        data = wait.until(
            EC.element_to_be_clickable((By.ID, "PacienteDataNascimento"))
        )

        # limpa campo via JS
        self.driver.execute_script(
            "arguments[0].value = '';", data
        )

        data.click()
        data.send_keys(self.HU_DATA)

        print("🔐 Resolva o CAPTCHA manualmente.")
        input("Pressione ENTER após concluir o login...")

        self.save_cookies()

    def ensure_logged(self):
        self.open()

        if self.load_cookies():
            print("Cookies carregados.")
            return

        print("Realizando login manual...")
        self.manual_login()

    def close(self):
        self.driver.quit()
