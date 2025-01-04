from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.service import Service
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
        # Keeping the original Chrome setup
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
        # Keeping the original Chrome binary location
        options.binary_location = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1024,768')  # Reduced from 1920,1080
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-webgl')
        
        # Memory optimization flags
        options.add_argument('--memory-pressure-off')
        options.add_argument('--disable-application-cache')
        options.add_argument('--disk-cache-size=1')
        options.add_argument('--media-cache-size=1')
        
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
            # Set page load timeout
            driver.set_page_load_timeout(30)
            self.logger.info("Chrome browser started successfully")
            yield driver
        except WebDriverException as e:
            self.logger.error(f"Failed to start Chrome driver: {e}")
            raise
        finally:
            if driver:
                try:
                    driver.quit()
                    self.logger.info("Browser closed")
                except Exception as e:
                    self.logger.error(f"Error closing browser: {e}")

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                try:
                    driver.get(self.URL)
                except TimeoutException:
                    self.logger.error("Page load timed out")
                    return None

                wait = WebDriverWait(driver, 15)  # Reduced from 20 to 15 seconds

                # Banner handling with retry
                try:
                    banner_close = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.BANNER_CLOSE_XPATH)))
                    if not self._retry_click(banner_close, driver, "Banner close button"):
                        self.logger.warning("Banner close failed, continuing anyway")
                except TimeoutException:
                    self.logger.info("Banner not found or already closed")
                except Exception as e:
                    self.logger.warning(f"Banner handling error: {e}")

                # Input handling with validation
                try:
                    input_field = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.INPUT_XPATH)))
                    input_field.clear()
                    time.sleep(0.5)  # Small delay for stability
                    input_field.send_keys(nuip)
                    self.logger.info(f"NUIP ingresado: {nuip}")

                    search_button = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.BUTTON_XPATH)))
                    if not self._retry_click(search_button, driver, "Search button"):
                        self.logger.error("Search button click failed")
                        return None
                except TimeoutException:
                    self.logger.error("Search elements not found")
                    return None

                # Result extraction with fallback
                estado_text = None
                for xpath in [
                    '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]',
                    '//*[@id="resumenEstadoCuenta"]/div/div'
                ]:
                    try:
                        element = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                        estado_text = element.text
                        if estado_text and estado_text.strip():
                            break
                    except TimeoutException:
                        continue

                if not estado_text:
                    self.logger.error("No results found")
                    return None

                data = RegistraduriaData(
                    nuip=nuip,
                    estado=estado_text
                )
                self.logger.info(f"Datos extraídos: {data}")
                return data

        except Exception as e:
            self.logger.error(f"Scraping error: {e}")
            self.logger.error(traceback.format_exc())
            return None

    def _retry_click(self, element, driver, description, retries=3, delay=1):
        for attempt in range(retries):
            try:
                element.click()
                self.logger.info(f"{description} clickeado.")
                return True
            except ElementClickInterceptedException:
                self.logger.warning(f"{description} intento {attempt + 1} fallido. Reintentando...")
                time.sleep(delay)
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
            except Exception as e:
                self.logger.error(f"Error al clicar {description}: {e}")
                return False
        
        try:
            driver.execute_script("arguments[0].click();", element)
            self.logger.info(f"{description} clickeado via JavaScript.")
            return True
        except Exception as e:
            self.logger.error(f"JavaScript click failed for {description}: {e}")
            return False