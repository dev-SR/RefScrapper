import os
from time import sleep
from traceback import print_tb
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

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"


class DownloadLinkScrapper(webdriver.Edge):
    def __init__(self, headless=False):
        self.result = None
        self.console = Console()
        self.exit_message = "Done"
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
            request_quota = WebDriverWait(self, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "//div[@class='request-quota-exceeded__message-box']"))
            )
            if request_quota:
                return True
        except:
            return False

        # sleep(50)

    def searchPaper(self, paper):
        self.find_element(by=By.CSS_SELECTOR,
                          value="#header-search-action").send_keys(paper['name'])
        self.find_element(by=By.CSS_SELECTOR,
                          value="#header-search-action").send_keys(Keys.ENTER)
        return self.findSearchResult()

    def findSearchResult(self):
        try:
            first_paper = self.find_element(by=By.XPATH,
                                            value="(//div[@class='search-box__result-item'])[1]")
            first_paper.find_element(by=By.TAG_NAME, value="a").click()
            return True
        except:
            return False

    def getDownload(self):
        down_section = self.find_element(
            by=By.XPATH, value="//div[@class='content-page-header__navigation--actions']")

        link = down_section.find_element(
            by=By.XPATH, value="//a[.//span[@class='nova-legacy-c-button__label'][normalize-space()='Download']]").click()

        print(link.text)

    def searchPaperWithOutLogin(self, paper):
        self.find_element(by=By.CSS_SELECTOR,
                          value="input[placeholder='Search publications']").send_keys(paper['name'])

        self.find_element(by=By.CSS_SELECTOR,
                          value="input[placeholder='Search publications']").send_keys(Keys.ENTER)  # Keys.ENTER or u'\ue007'
        self.implicitly_wait(7)
        try:
            links = self.find_elements(by=By.TAG_NAME, value='a')
            links[7].click()
        except:
            print("Failed to find the paper")
            return False
