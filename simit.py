from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging
from typing import Optional, Dict
from dataclasses import dataclass
from contextlib import contextmanager
import time
import gc

@dataclass(slots=True)  # Using slots for memory efficiency
class RegistraduriaData:
    nuip: str
    estado: Optional[str] = None

class SimitScraper:
    # Store XPaths as class-level constants to avoid repeated string creation
    XPATHS: Dict[str, str] = {
        'input': '//*[@id="txtBusqueda"]',
        'button': '//*[@id="consultar"]',
        'banner': '//*[@id="modalInformation"]/div/div/div[1]/button/span',
        'results': '//*[@id="mainView"]/div/div[1]/div/div[2]/div[2]/p[1]',
        'alt_results': '//*[@id="resumenEstadoCuenta"]/div/div'
    }
    
    def __init__(self, headless: bool = True):  # Default to headless for lower memory usage
        self.logger = self._get_logger()
        self.options = self._get_chrome_options(headless)
        self.service = Service(ChromeDriverManager(driver_version="131.0.6778.108").install())
        
    @staticmethod
    def _get_logger() -> logging.Logger:
        logger = logging.getLogger('simit_scraper')
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)  # Reduce logging overhead
        return logger

    @staticmethod
    def _get_chrome_options(headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        options.binary_location = "/opt/render/project/.chrome/chrome-linux64/chrome-linux64/chrome"
        if headless:
            options.add_argument('--headless=new')
        
        # Memory optimization arguments
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-images')
        options.add_argument('--disable-canvas-aa')
        options.add_argument('--disable-2d-canvas-clip-aa')
        options.add_argument('--disable-gl-drawing-for-tests')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-zygote')
        options.add_argument('--single-process')
        options.add_argument('--disable-pinch')
        options.add_argument('--window-size=1280,720')  # Fixed window size
        options.add_argument('--disable-features=NetworkService')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Disable unnecessary features
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
                'plugins': 2,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'auto_select_certificate': 2,
                'fullscreen': 2,
                'mouselock': 2,
                'mixed_script': 2,
                'media_stream': 2,
                'media_stream_mic': 2,
                'media_stream_camera': 2,
                'protocol_handlers': 2,
                'ppapi_broker': 2,
                'automatic_downloads': 2,
                'midi_sysex': 2,
                'push_messaging': 2,
                'ssl_cert_decisions': 2,
                'metro_switch_to_desktop': 2,
                'protected_media_identifier': 2,
                'app_banner': 2,
                'site_engagement': 2,
                'durable_storage': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            yield driver
        finally:
            if driver:
                driver.quit()
                gc.collect()  # Force garbage collection

    def _safe_click(self, element, driver) -> bool:
        try:
            element.click()
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                driver.get('https://www.fcm.org.co/simit/#/home-public')
                wait = WebDriverWait(driver, 10)

                # Handle banner
                try:
                    banner = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATHS['banner'])))
                    ActionChains(driver).move_to_element(banner).click().perform()
                except Exception:
                    pass  # Ignore banner errors

                # Input NUIP
                input_field = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATHS['input'])))
                input_field.send_keys(nuip)
                
                # Click search
                search_button = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATHS['button'])))
                if not self._safe_click(search_button, driver):
                    return None

                # Get results
                try:
                    result = wait.until(EC.visibility_of_element_located(
                        (By.XPATH, self.XPATHS['results']))).text
                except Exception:
                    try:
                        result = wait.until(EC.visibility_of_element_located(
                            (By.XPATH, self.XPATHS['alt_results']))).text
                    except Exception:
                        return None

                return RegistraduriaData(nuip=nuip, estado=result)

        except Exception as e:
            self.logger.error(f"Scraping error: {str(e)}")
            return None