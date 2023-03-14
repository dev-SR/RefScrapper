import os
from time import sleep
from tkinter import Button
from traceback import print_tb
from turtle import down
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from rich.console import Console
from rich.table import Table
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from uuid import uuid4
from fuzzywuzzy import fuzz


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"


class PaperInfoScrapperNew(webdriver.Edge):
    def __init__(self, headless=0):
        self.result = None
        self.console = Console()
        self.exit_message = "[red]Terminating Browser Session...[/]"
        options = webdriver.EdgeOptions()
        os.environ['WDM_LOG'] = '0'
        if headless:
            print("Headless mode")
            options.add_argument('--headless')

        options.add_argument("start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # disable logs
        options.add_argument('--disable-logging')
        prefs = {"download.default_directory": "C:\Tutorial"}
        options.add_experimental_option("prefs", prefs)
        # options.add_experimental_option(
        #     "excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={USER_AGENT}')
        options.add_argument('--allow-running-insecure-content')

        super().__init__(service=Service(
            EdgeChromiumDriverManager().install()), options=options)
        # self.implicitly_wait(10)        # seconds
        # This is a global wait time and applied to every element in the page.

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.console.print(self.exit_message)
        self.close()

    def land_home_page(self):
        # self.set_page_load_timeout(10)
        try:
            self.get('https://www.researchgate.net/')
        except:
            return False

    def login(self, email, password):
        self.find_element(by=By.CSS_SELECTOR,
                          value=".index-header__log-in").click()

        self.find_element(by=By.CSS_SELECTOR,
                          value="#input-login").send_keys(email)
        self.find_element(by=By.CSS_SELECTOR,
                          value="#input-password").send_keys(password)
        self.find_element(by=By.CSS_SELECTOR,
                          value="button[type='submit']").click()

    def isRequestQuotaExceeded(self):
        try:
            request_quota = WebDriverWait(self, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='request-quota-exceeded__message-box']"))
            )
            if request_quota:
                return True
        except:
            return False

        # sleep(50)

    def directLandOnPaperPage(self, paper_link):
        try:
            self.get(paper_link)
            self.implicitly_wait(2)
            return True
        except:
            return False

    def searchPaper(self, paper):
        self.find_element(by=By.CSS_SELECTOR,
                          value="#header-search-action").send_keys(paper)
        self.find_element(by=By.CSS_SELECTOR,
                          value="#header-search-action").send_keys(Keys.ENTER)

    def findDownloadLink(self, paper_name):
        # try:
        #     on_publication_nav = self.find_element(by=By.XPATH,
        #                                            value='//li[contains(@class,\'nova-legacy-e-list__item search-box-filter-menu__item search-box-filter-menu__item--selected\') and contains(.,"publications")]')

        # except Exception as e:
        #     return None
        try:
            papers = self.find_elements(by=By.XPATH,
                                        value="//div[@data-testid='searchResultItem']")
            for p in papers:
                a = None
                self.implicitly_wait(2)
                try:
                    a = p.find_element(by=By.XPATH,
                                       value=".//div[@class='nova-legacy-e-text nova-legacy-e-text--size-l nova-legacy-e-text--family-sans-serif nova-legacy-e-text--spacing-none nova-legacy-e-text--color-inherit nova-legacy-e-text--clamp-3 nova-legacy-v-publication-item__title']//a[contains(@href,\"publication\")]")
                    paper_name_found = a.text
                except:
                    return None
                # paper_link = a.get_attribute('href')
                ratio = fuzz.partial_ratio(
                    paper_name.lower(), paper_name_found.lower())
                if ratio > 80:
                    download_link = None
                    try:
                        download_link = p.find_element(by=By.XPATH,
                                                       value=".//a[contains(.,'Download')]").get_attribute('href')
                    except:
                        pass
                    # paper_type = ""
                    # try:
                    #     paper_type = p.find_element(by=By.XPATH,
                    #                                 value="//div[@class='nova-legacy-l-flex__item']//a[contains(@href,\"publication\")]").text
                    # except:
                    #     pass
                    return download_link
        except Exception as e:
            print(e)
            return None


"""
//li[contains(@class,'nova-legacy-e-list__item search-box-filter-menu__item search-box-filter-menu__item--selected') and contains(.,"publications")]

//div[@data-testid='searchResultItem']

//div[@class='nova-legacy-e-text nova-legacy-e-text--size-l nova-legacy-e-text--family-sans-serif nova-legacy-e-text--spacing-none nova-legacy-e-text--color-inherit nova-legacy-e-text--clamp-3 nova-legacy-v-publication-item__title']//a[contains(@href,"publication")]

 """
