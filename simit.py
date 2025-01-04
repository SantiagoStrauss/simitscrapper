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
        
        # Aggressive memory optimization flags
        options.add_argument('--headless=new')  # Force headless
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-javascript')  # Disable JavaScript initially
        options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
        options.add_argument('--window-size=800,600')  # Even smaller window
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-popup-blocking')
        
        # Prefs for minimal memory usage
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # Disable images
                'javascript': 2,  # Disable JavaScript
                'css': 2,  # Disable CSS
            },
            'disk-cache-size': 1,
            'media-cache-size': 1,
            'profile.managed_default_content_settings.javascript': 2
        }
        options.add_experimental_option('prefs', prefs)
        
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            driver.set_page_load_timeout(20)  # Reduced timeout
            driver.set_script_timeout(10)  # Add script timeout
            self.logger.info("Chrome browser started successfully")
            yield driver
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass  # Ignore errors on cleanup

    def _enable_javascript(self, driver):
        try:
            driver.execute_cdp_cmd('Emulation.setScriptExecutionDisabled', {'value': False})
            self.logger.info("JavaScript enabled")
        except:
            self.logger.warning("Failed to enable JavaScript")

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                try:
                    # First load without JavaScript
                    driver.get(self.URL)
                    
                    # Then enable JavaScript for interaction
                    self._enable_javascript(driver)
                    
                    wait = WebDriverWait(driver, 8)  # Reduced wait time
                    
                    # Handle banner if present (quick attempt only)
                    try:
                        banner = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, self.BANNER_CLOSE_XPATH)))
                        driver.execute_script("arguments[0].click();", banner)
                    except:
                        pass  # Skip if banner handling fails
                    
                    # Input handling
                    input_field = wait.until(EC.presence_of_element_located(
                        (By.XPATH, self.INPUT_XPATH)))
                    driver.execute_script(
                        "arguments[0].value = arguments[1]", 
                        input_field, 
                        nuip
                    )
                    
                    # Click search
                    search_button = wait.until(EC.presence_of_element_located(
                        (By.XPATH, self.BUTTON_XPATH)))
                    driver.execute_script("arguments[0].click();", search_button)
                    
                    # Quick result extraction
                    result_xpaths = [
                        '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]',
                        '//*[@id="resumenEstadoCuenta"]/div/div'
                    ]
                    
                    estado_text = None
                    for xpath in result_xpaths:
                        try:
                            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                            estado_text = element.get_attribute('textContent')
                            if estado_text:
                                break
                        except:
                            continue
                    
                    if not estado_text:
                        return None
                        
                    return RegistraduriaData(nuip=nuip, estado=estado_text)
                    
                except Exception as e:
                    self.logger.error(f"Error in scraping process: {str(e)}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Critical error: {str(e)}")
            return None