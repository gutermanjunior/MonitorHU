"""
===============================================================================
Projeto: Monitor HU-USP (Especialidades)
Arquivo: parser.py
Autor: Guterman (guterman.com.br)
Versão: 3.2 (Anti-Kickback & Infinite Wait Edition)
Data: Março de 2026
===============================================================================

Descrição:
    Módulo responsável pela interação direta com o navegador via Selenium.
    Lida com extração de vagas, injeção de JavaScript, gestão de cookies 
    e proteção contra quedas de sessão (kickbacks) e CAPTCHAs.
===============================================================================
"""

import os
import sys
import time
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .logger import get_logger

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

        # Define o tamanho da janela (L x A) - 1080x624 é um retângulo vertical ótimo
        options.add_argument("--window-size=1080,624") 
        
        # Como o Monitor 3 está à esquerda do principal, usamos um X negativo.
        # -1080 vai empurrar a janela para dentro do Monitor 3.
        options.add_argument("--window-position=-1080,0")

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            log.info("WebDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            log.error(f"Falha ao iniciar WebDriver: {e}")
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
                log.info("Cookies carregados.")
                return True
            except Exception:
                return False
        return False

    def save_cookies(self):
        try:
            with open(COOKIES_FILE, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            log.info("Sessão salva em cookies.")
        except Exception: pass

    def manual_login(self):
        """Preenche o formulário e aguarda infinitamente pela resolução do CAPTCHA."""
        log.warning("Sessão perdida ou inicial. Iniciando login manual.")
        wait = WebDriverWait(self.driver, 10)
        
        try:
            # Tenta preencher a matrícula e a data se os campos estiverem visíveis
            matricula = wait.until(EC.element_to_be_clickable((By.ID, "PacienteMatricula")))
            matricula.clear()
            matricula.send_keys(self.HU_USER)

            data_field = wait.until(EC.presence_of_element_located((By.ID, "PacienteDataNascimento")))
            js_script = """
                var el = arguments[0]; var val = arguments[1];
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
            """
            self.driver.execute_script(js_script, data_field, self.HU_DATA)
        except Exception:
            log.info("Campos de login não detectados. Assumindo que a página já está preenchida ou em outro estágio.")

        # Emite um aviso sonoro no Windows para chamar sua atenção
        sys.stdout.write('\a')
        sys.stdout.flush()
        
        # LOOP INFINITO: O cão de guarda da sessão
        log.warning("Aguardando intervenção humana no CAPTCHA...")
        while True:
            try:
                # Ele checa a cada 3 segundos se o menu 'Especialidade' finalmente carregou na tela
                WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "Especialidade")))
                log.info("Login/CAPTCHA detectado e resolvido com sucesso!")
                self.save_cookies()
                break # Sai do loop infinito e devolve o controle ao programa principal
            except Exception:
                # Se não carregou, ele simplesmente não faz nada e tenta de novo. Sem gerar erros.
                time.sleep(1)

    def ensure_logged(self):
        self.open()
        if self.load_cookies():
            try:
                # Se após carregar o cookie o menu de Especialidade aparecer rápido, a sessão está viva.
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "Especialidade")))
                log.info("Sessão restaurada com sucesso via cookies.")
                return
            except Exception: pass
            
        # Se os cookies falharam ou não existem, entramos no modo de login blindado
        log.warning("Necessário login manual ou resolução de Kickback.")
        self.manual_login()

    def get_dropdown_options(self):
        # Se o site der erro do servidor, esse By.ID vai falhar e gerar a exceção 
        # que o monitor.py vai capturar como "Site Indisponível"
        select_element = Select(self.driver.find_element(By.ID, "Especialidade"))
        
        opcoes = set()
        for option in select_element.options:
            texto = option.text.strip().upper()
            if "SELECIONE" not in texto:
                opcoes.add(texto)
        
        return opcoes

    def take_screenshot(self, filename="screenshot.png"):
        try:
            try:
                self.driver.find_element(By.ID, "Especialidade").click()
                time.sleep(0.5)
            except: pass
            path = DATA_DIR / filename
            self.driver.save_screenshot(str(path))
            return str(path)
        except Exception:
            return None

    def close(self):
        try: self.driver.quit()
        except: pass