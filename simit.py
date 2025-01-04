from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
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

    def __init__(self, headless: bool = True):  # Changed default to True
        self.logger = self._setup_logger()
        self.options = self._setup_chrome_options(headless)
        self.service = Service(ChromeDriverManager().install())

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('registraduria_scraper')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger

    @staticmethod
    def _setup_chrome_options(headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        options.binary_location = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
        options.add_argument('--headless=new')  # Always run headless on Render
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        
        # Memory optimization flags
        options.add_argument('--memory-pressure-off')
        options.add_argument('--single-process')  # Reduce memory usage
        options.add_argument('--disable-javascript')  # If possible for your use case
        options.add_argument('--disable-images')  # If possible for your use case
        options.add_argument('--disk-cache-size=1')
        options.add_argument('--media-cache-size=1')
        options.add_argument('--disable-application-cache')
        
        # Set smaller window size to reduce memory
        options.add_argument('--window-size=1024,768')
        
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            self.logger.info("Chrome browser started successfully")
            yield driver
        except WebDriverException as e:
            self.logger.error(f"Failed to start Chrome driver: {e}")
            raise
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.error(f"Error closing browser: {e}")

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                # Set page load timeout
                driver.set_page_load_timeout(30)
                
                try:
                    driver.get(self.URL)
                except TimeoutException:
                    self.logger.error("Page load timed out")
                    return None

                wait = WebDriverWait(driver, 10)  # Reduced timeout from 20 to 10

                # Simplified banner handling
                try:
                    banner_close = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.BANNER_CLOSE_XPATH)))
                    banner_close.click()
                except TimeoutException:
                    self.logger.info("Banner not found or already closed")
                except Exception as e:
                    self.logger.warning(f"Banner close error: {e}")

                # Input handling
                try:
                    input_field = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.INPUT_XPATH)))
                    input_field.clear()
                    input_field.send_keys(nuip)
                    
                    search_button = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, self.BUTTON_XPATH)))
                    search_button.click()
                except TimeoutException:
                    self.logger.error("Search elements not found")
                    return None

                # Result extraction with timeout
                try:
                    result_xpaths = [
                        '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]',
                        '//*[@id="resumenEstadoCuenta"]/div/div'
                    ]
                    
                    estado_text = None
                    for xpath in result_xpaths:
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

                    return RegistraduriaData(nuip=nuip, estado=estado_text)

                except TimeoutException:
                    self.logger.error("Results not found")
                    return None
                except Exception as e:
                    self.logger.error(f"Error extracting results: {e}")
                    return None

        except Exception as e:
            self.logger.error(f"Scraping error: {e}")
            return None