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
import logging
import os
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager
import traceback

# Constants for Chrome setup
DEFAULT_CHROME_PATH = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY', DEFAULT_CHROME_PATH)

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

    def __init__(self, headless: bool = True):
        self.logger = self._setup_logger()
        self.verify_chrome_binary()
        self.options = self._setup_chrome_options(headless)
        self.service = ChromeService(
            ChromeDriverManager(driver_version="131.0.6778.108").install()
        )

    def verify_chrome_binary(self) -> None:
        global CHROME_BINARY_PATH
        if not os.path.isfile(CHROME_BINARY_PATH):
            fallback_path = os.path.join(os.getcwd(), "chrome", "chrome.exe")
            if os.path.isfile(fallback_path):
                CHROME_BINARY_PATH = fallback_path
            else:
                self.logger.error(f"Chrome binary not found at {CHROME_BINARY_PATH}")
                raise FileNotFoundError(f"Chrome binary not found at {CHROME_BINARY_PATH}")
        
        if not os.access(CHROME_BINARY_PATH, os.X_OK):
            self.logger.error(f"Chrome binary not executable at {CHROME_BINARY_PATH}")
            raise PermissionError(f"Chrome binary not executable at {CHROME_BINARY_PATH}")

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('simit_scraper')
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
        
        # Set Chrome binary path
        options.binary_location = CHROME_BINARY_PATH
        
        # Essential options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if headless:
            options.add_argument('--headless=new')
        
        # Performance options
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1024,768')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Memory optimization
        options.add_argument('--memory-pressure-off')
        options.add_argument('--disable-application-cache')
        options.add_argument('--disk-cache-size=1')
        options.add_argument('--media-cache-size=1')
        
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Custom user agent
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.6778.108 Safari/537.36'
        )
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
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

    def _click_element(self, driver, xpath: str, description: str) -> bool:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            driver.execute_script("arguments[0].click();", element)
            self.logger.info(f"{description} clicked")
            return True
        except Exception as e:
            self.logger.error(f"Error clicking {description}: {e}")
            return False

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                try:
                    driver.get(self.URL)
                    self.logger.info(f"Navigating to {self.URL}")
                except TimeoutException:
                    self.logger.error("Page load timed out")
                    return None

                wait = WebDriverWait(driver, 10)

                # Handle banner if present
                try:
                    self._click_element(driver, self.BANNER_CLOSE_XPATH, "Banner close button")
                except Exception:
                    self.logger.info("Banner not found or already closed")

                # Input handling
                try:
                    input_field = wait.until(
                        EC.presence_of_element_located((By.XPATH, self.INPUT_XPATH))
                    )
                    input_field.clear()
                    input_field.send_keys(nuip)
                    self.logger.info(f"NUIP entered: {nuip}")

                    if not self._click_element(driver, self.BUTTON_XPATH, "Search button"):
                        return None

                except TimeoutException:
                    self.logger.error("Search elements not found")
                    return None

                # Result extraction
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

                    data = RegistraduriaData(
                        nuip=nuip,
                        estado=estado_text
                    )
                    self.logger.info(f"Data extracted: {data}")
                    return data

                except TimeoutException:
                    self.logger.error("Results not found within timeout")
                    return None
                except Exception as e:
                    self.logger.error(f"Error extracting data: {e}")
                    self.logger.error(traceback.format_exc())
                    return None

        except Exception as e:
            self.logger.error(f"Scraping error: {e}")
            self.logger.error(traceback.format_exc())
            return None