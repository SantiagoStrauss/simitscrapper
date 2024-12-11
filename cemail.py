from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from typing import List, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import time
import traceback
###111111
###sin pantallazo
@dataclass
class CompromisedData:
    company_name: str
    domain_name: str
    date_breach_occurred: str
    info_breached: str
    accounts_affected: str
    breach_overview: str 

class CompromisedEmailScraper:
    # Define XPath or CSS selectors
    EMAIL_INPUT_XPATH = '//*[@id="txtemail"]'  # Actualiza si el ID cambia
    SEARCH_BUTTON_XPATH = '//*[@id="btnSubmit"]'
    RESULT_WRAPPER_XPATH = '//div[@class="breach-wrapper"]'

    def __init__(self, headless: bool = False):
        self.logger = self._setup_logger()
        self.options = self._setup_chrome_options(headless)
        self.service = Service(ChromeDriverManager().install())

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('compromised_email_scraper')
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
        if headless:
            options.add_argument('--headless=new')  # Usa el modo headless más reciente
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-webgl')  # Deshabilita WebGL
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.binary_location = "${HOME}/chrome/opt/google/chrome/chrome"  # Ruta típica de Chrome en servidores Linux
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


    def scrape(self, url: str, email: str) -> List[CompromisedData]:
        results = []
        try:
            with self._get_driver() as driver:
                driver.get(url)
                self.logger.info(f"Navigando a {url}")
                
                # Tomar captura de pantalla
                #driver.save_screenshot("screenshot_headless.png")
                #self.logger.info("Captura de pantalla tomada.")

                wait = WebDriverWait(driver, 30)  # Aumenta el tiempo de espera

                # Intentar localizar el campo de correo electrónico
                try:
                    email_input = wait.until(
                        EC.visibility_of_element_located((By.XPATH, self.EMAIL_INPUT_XPATH))
                    )
                    self.logger.info("Campo de correo electrónico encontrado.")
                    email_input.clear()
                    email_input.send_keys(email)
                    self.logger.info(f"Correo ingresado: {email}")

                    search_button = driver.find_element(By.XPATH, self.SEARCH_BUTTON_XPATH)
                    search_button.click()
                    self.logger.info("Botón de búsqueda clickeado.")
                except TimeoutException:
                    self.logger.error("Campo de correo electrónico no encontrado dentro del tiempo de espera.")
                    return results
                except Exception as e:
                    self.logger.error(f"Error al ingresar el correo: {e}")
                    return results

                # Wait for results to load
                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, self.RESULT_WRAPPER_XPATH)))
                    breach_wrappers = driver.find_elements(By.XPATH, self.RESULT_WRAPPER_XPATH)
                    self.logger.info(f"Found {len(breach_wrappers)} breach wrapper(s)")
                except TimeoutException:
                    self.logger.error("No results found")
                    return results
                except Exception as e:
                    self.logger.error(f"Error waiting for results: {e}")
                    return results

                # Extract data from each breach wrapper
                for idx, wrapper in enumerate(breach_wrappers, start=1):
                    try:
                        breach_items = wrapper.find_elements(By.XPATH, './/div[@class="breach-item"]')
                        self.logger.info(f"Processing breach wrapper {idx} with {len(breach_items)} items")

                        current_data = {}
                        for item in breach_items:
                            try:
                                label_element = item.find_element(By.TAG_NAME, 'b')
                                label = label_element.text.strip(':').lower().replace(' ', '_').replace('originally_', '')
                                value = item.text.split(':', 1)[1].strip()
                                
                                if label == 'company_name':
                                    # Si current_data no está vacío, guarda el registro anterior
                                    if current_data:
                                        data = CompromisedData(
                                            company_name=current_data.get('company_name', 'N/A'),
                                            domain_name=current_data.get('domain_name', 'N/A'),
                                            date_breach_occurred=current_data.get('date_breach_occurred', 'N/A'),
                                            info_breached=current_data.get('type_of_information_breached', 'N/A'),
                                            accounts_affected=current_data.get('total_number_of_accounts_affected', 'N/A'),
                                            breach_overview=current_data.get('breach_overview', 'N/A')
                                        )
                                        results.append(data)
                                        self.logger.info(f"Extracted breach: {data}")
                                        current_data = {}
                                
                                current_data[label] = value
                            except NoSuchElementException:
                                self.logger.info("Necessary sub-elements not found in a breach item")
                            except IndexError:
                                self.logger.info("No value found for the label in a breach item")
                            except Exception as e:
                                self.logger.error(f"Unexpected error processing breach item: {e}")
                                self.logger.error(traceback.format_exc())

                        # Después de procesar todos los items, agrega el último registro si existe
                        if current_data:
                            data = CompromisedData(
                                company_name=current_data.get('company_name', 'N/A'),
                                domain_name=current_data.get('domain_name', 'N/A'),
                                date_breach_occurred=current_data.get('date_breach_occurred', 'N/A'),
                                info_breached=current_data.get('type_of_information_breached', 'N/A'),
                                accounts_affected=current_data.get('total_number_of_accounts_affected', 'N/A'),
                                breach_overview=current_data.get('breach_overview', 'N/A') 
                            )
                            results.append(data)
                            self.logger.info(f"Extracted breach: {data}")
                            
                    except Exception as e:
                        self.logger.error(f"Error extracting data from breach wrapper {idx}: {e}")
                        self.logger.error(traceback.format_exc())

                return results

        except Exception as e:
            self.logger.error(f"Error durante el scraping: {e}")
            self.logger.error(traceback.format_exc())
            return results