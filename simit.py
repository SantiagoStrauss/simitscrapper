from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
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
import time

DEFAULT_CHROME_PATH = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY', DEFAULT_CHROME_PATH)

@dataclass
class RegistraduriaData:
    nuip: str
    estado: Optional[str] = None

class simitScraper:
    URL = 'https://www.fcm.org.co/simit/#/home-public'
    INPUT_XPATH = '//*[@id="txtBusqueda"]'
    BUTTON_XPATH = '//*[@id="consultar"]'
    BANNER_CLOSE_XPATH = '//*[@id="modalInformation"]/div/div/div[1]/button/span'

    def __init__(self, headless: bool = True):
        self.logger = self._setup_logger()
        self.options = self._setup_chrome_options(headless)
        self.service = ChromeService(
            ChromeDriverManager(driver_version="131.0.6778.108").install()
        )

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('simit_scraper')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger

    @staticmethod
    def _setup_chrome_options(headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        options.binary_location = CHROME_BINARY_PATH
        
        # Basic essential flags
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Renderer optimization flags
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--window-size=800,600')
        
        # Memory management
        options.add_argument('--js-flags=--max-old-space-size=128')
        options.add_argument('--single-process')
        options.add_argument('--disable-site-isolation-trials')
        
        # Renderer specific settings
        options.add_argument('--renderer-process-limit=1')
        options.add_argument('--disable-renderer-backgrounding')
        
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            # Set page load timeout directly using the standard method
            driver.set_page_load_timeout(45)
            driver.implicitly_wait(10)  # Add implicit wait
            
            self.logger.info("Chrome browser started successfully")
            yield driver
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.error(f"Error closing driver: {str(e)}")

    def _safe_execute_script(self, driver, script, *args):
        try:
            return driver.execute_script(script, *args)
        except Exception as e:
            self.logger.warning(f"Script execution failed: {e}")
            return None

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with self._get_driver() as driver:
                    try:
                        # Load page with retry
                        for _ in range(2):
                            try:
                                driver.get(self.URL)
                                break
                            except TimeoutException:
                                driver.refresh()
                                time.sleep(2)
                        
                        wait = WebDriverWait(driver, 15)
                        
                        # Wait for page to be fully loaded
                        wait.until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        time.sleep(2)
                        
                        # Handle banner if present
                        try:
                            banner = wait.until(EC.element_to_be_clickable(
                                (By.XPATH, self.BANNER_CLOSE_XPATH)))
                            banner.click()
                        except:
                            pass

                        # Input handling with retry
                        for _ in range(2):
                            try:
                                input_field = wait.until(EC.presence_of_element_located(
                                    (By.XPATH, self.INPUT_XPATH)))
                                input_field.clear()
                                input_field.send_keys(nuip)
                                break
                            except TimeoutException:
                                time.sleep(1)
                        
                        # Click search with retry
                        for _ in range(2):
                            try:
                                search_button = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, self.BUTTON_XPATH)))
                                search_button.click()
                                break
                            except TimeoutException:
                                time.sleep(1)
                        
                        # Result extraction
                        time.sleep(2)
                        result_xpaths = [
                            '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]',
                            '//*[@id="resumenEstadoCuenta"]/div/div'
                        ]
                        
                        estado_text = None
                        for xpath in result_xpaths:
                            try:
                                element = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                                estado_text = element.text
                                if estado_text:
                                    break
                            except:
                                continue
                        
                        if estado_text:
                            return RegistraduriaData(nuip=nuip, estado=estado_text)
                            
                    except Exception as e:
                        self.logger.error(f"Error in scraping process (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        return None
                        
            except Exception as e:
                self.logger.error(f"Critical error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        return None