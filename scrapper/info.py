import os
from time import sleep
from tkinter import Button
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


class ResultTable:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.t = Table(show_header=True, header_style="bold magenta")

    def fetch_table(self):
        # self.driver.find_element(
        #     by=By.CSS_SELECTOR, value="a[href='Status.php']").click()
        table = self.driver.find_element(
            by=By.XPATH, value="/html[1]/body[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[3]/div[3]/table[1]")
        for row in table.find_elements(by=By.TAG_NAME, value='tr'):
            try:
                for i, cell in enumerate(row.find_elements(by=By.TAG_NAME, value='th')):
                    if i == 1:
                        self.t.add_column(
                            cell.text, style="dim", justify="center")
                    elif i == 3:
                        self.t.add_column(
                            cell.text, style="bold green", justify="center")
                    else:
                        self.t.add_column(
                            cell.text, justify="center")
            except:
                pass

            cell_list = []
            for cell in row.find_elements(by=By.TAG_NAME, value='td'):
                cell_list.append(cell.text)

            if(len(cell_list) > 0):
                self.t.add_row(*cell_list)


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"


class PaperInfoScrapper(webdriver.Edge):
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
                          value="#header-search-action").send_keys(paper['name'])
        self.find_element(by=By.CSS_SELECTOR,
                          value="#header-search-action").send_keys(Keys.ENTER)
        return self.findSearchResult()

    def findSearchResult(self):
        try:
            first_paper = self.find_element(by=By.XPATH,
                                            value="(//div[@class='search-box__result-item'])[1]")
            allLinks = first_paper.find_elements(
                by=By.TAG_NAME, value="a")
            # first_publication_link = None
            returnLink = ""
            for link in allLinks:
                if 'https://www.researchgate.net/publication/' in link.get_attribute('href'):
                    returnLink = link.get_attribute('href')
                    link.click()
                    break
            return returnLink

        except:
            return ""

    def getPaperInfo(self):
        self.implicitly_wait(10)
        ref_count = 0
        try:
            ref_button = self.find_element(by=By.XPATH,
                                           value="//button[.//div[contains(text(),'References')]]")
            ref_count = ref_button.text.split("(")[1][:-1]
        except:
            pass

        sleep(1)
        try:
            paper_info_el = WebDriverWait(self, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                "(//div[@class='content-grid__columns--narrow'])[1]")))

            # ref_button.click()
            # print(ref_button.text)
            paper_infos = paper_info_el.find_elements(
                by=By.CLASS_NAME, value="nova-legacy-o-stack__item")
            info = {
                "references_count": ref_count,
                "research_interest_score": 0.0,
                "citations_count": 0,
                "recommendations_count": 0,
                "reads_count": 0,
            }
            for item in paper_infos:
                # split all the text
                """
                ['Research Interest', '5.0']
                ['Citations', '2']
                ['Recommendations', '0 new', '5']
                ['Reads', '6 new', '1,120']
                """
                text = item.text.split('\n')
                # print(text)
                if text[0] == 'Research Interest':
                    # print(text[1])
                    n = text[1].replace(',', '')
                    info['research_interest_score'] = float(n)
                elif text[0] == 'Citations':
                    # print(text[1])
                    n = text[1].replace(',', '')
                    info['citations_count'] = int(n)
                elif text[0] == 'Recommendations':
                    # print(text[2])
                    n = text[2].replace(',', '')
                    info['recommendations_count'] = int(n)
                elif text[0] == 'Reads':
                    # print(text[2])
                    n = text[2].replace(',', '')
                    info['reads_count'] = int(n)

            return [1, info]
        except:
            return [0, 0]

    def getDownloadLink(self):
        try:
            down_section = self.find_element(
                by=By.XPATH, value="//div[@class='content-page-header__navigation--actions']")
            link = down_section.find_element(
                by=By.XPATH, value="//a[.//span[@class='nova-legacy-c-button__label'][normalize-space()='Download']]")
            return link.get_attribute('href')
        except:
            return None
