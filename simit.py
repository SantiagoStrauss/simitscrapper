from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
    ElementNotInteractableException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager
import traceback
import time

@dataclass
class RegistraduriaData:
    nuip: str
    fecha_consulta: Optional[str] = None
    documento: Optional[str] = None
    estado: Optional[str] = None

class simitScraper:
    URL = 'https://www.fcm.org.co/simit/#/home-public'
    INPUT_XPATH = '//*[@id="txtBusqueda"]'
    BUTTON_XPATH = '//*[@id="consultar"]'
    BANNER_CLOSE_XPATH = '//*[@id="modalInformation"]/div/div/div[1]/button/span'

    def __init__(self, headless: bool = False):
        self.logger = self._setup_logger()
        self.options = self._setup_chrome_options(headless)
        self.service = ChromeService(
            ChromeDriverManager(driver_version="131.0.6778.108").install()
        )

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('registraduria_scraper')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)
        return logger

    @staticmethod
    def _setup_chrome_options(headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        options.binary_location = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-webgl')
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-logging')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/98.0.4758.102 Safari/537.36'
        )
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            driver.maximize_window()
            self.logger.info("Chrome browser started successfully")
            yield driver
        except WebDriverException as e:
            self.logger.error(f"Failed to start Chrome driver: {e}")
            raise
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser closed")

    def _retry_click(self, element, driver, description, retries=3, delay=1):
        for attempt in range(retries):
            try:
                element.click()
                self.logger.info(f"{description} clickeado.")
                return True
            except ElementClickInterceptedException:
                self.logger.warning(f"{description} intento {attempt + 1} fallido. Reintentando en {delay} segundos...")
                time.sleep(delay)
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
            except Exception as e:
                self.logger.error(f"Error al clicar {description}: {e}")
                self.logger.error(traceback.format_exc())
                return False
        try:
            driver.execute_script("arguments[0].click();", element)
            self.logger.info(f"{description} clickeado via JavaScript.")
            return True
        except Exception as e:
            self.logger.error(f"No se pudo clicar {description} incluso vía JavaScript: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                driver.get(self.URL)
                self.logger.info(f"Navegando a {self.URL}")

                wait = WebDriverWait(driver, 20)

                try:
                    banner_close = wait.until(EC.element_to_be_clickable((By.XPATH, self.BANNER_CLOSE_XPATH)))
                    actions = ActionChains(driver)
                    actions.move_to_element(banner_close).perform()
                    if not self._retry_click(banner_close, driver, "Banner close button"):
                        self.logger.error("No se pudo cerrar el banner después de varios intentos.")
                        return None
                    wait.until(EC.invisibility_of_element_located((By.XPATH, self.BANNER_CLOSE_XPATH)))
                except TimeoutException:
                    self.logger.info("No se encontró el banner o ya está cerrado.")
                except Exception as e:
                    self.logger.error(f"Error al cerrar el banner: {e}")
                    self.logger.error(traceback.format_exc())

                try:
                    input_field = wait.until(EC.visibility_of_element_located((By.XPATH, self.INPUT_XPATH)))
                    input_field.clear()
                    input_field.send_keys(nuip)
                    self.logger.info(f"NUIP ingresado: {nuip}")

                    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, self.BUTTON_XPATH)))
                    if not self._retry_click(search_button, driver, "Search button"):
                        self.logger.error("No se pudo clicar el botón de búsqueda después de varios intentos.")
                        return None
                except TimeoutException:
                    self.logger.error("Campo NUIP no encontrado dentro del tiempo de espera.")
                    return None
                except Exception as e:
                    self.logger.error(f"Error al ingresar NUIP o clicar el botón: {e}")
                    self.logger.error(traceback.format_exc())
                    return None

                try:
                    resultados_xpath = '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]'
                    resultado_element = wait.until(EC.visibility_of_element_located((By.XPATH, resultados_xpath)))
                    estado_text = resultado_element.text if resultado_element else None
                    if not estado_text or not estado_text.strip():
                        alt_xpath = '//*[@id="resumenEstadoCuenta"]/div/div'
                        alt_element = wait.until(EC.visibility_of_element_located((By.XPATH, alt_xpath)))
                        estado_text = alt_element.text if alt_element else None

                    self.logger.info(f"Información extraída: {estado_text}")
                    data = RegistraduriaData(nuip=nuip, estado=estado_text)
                    return data
                except TimeoutException:
                    self.logger.error("No se encontraron resultados dentro del tiempo de espera.")
                    return None
                except Exception as e:
                    self.logger.error(f"Error al extraer resultados: {e}")
                    self.logger.error(traceback.format_exc())
                    return None
        except Exception as e:
            self.logger.error(f"Error general en el proceso de scraping: {e}")
            self.logger.error(traceback.format_exc())
            return None
