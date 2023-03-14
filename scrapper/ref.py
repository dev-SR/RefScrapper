import os
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


class RefScrapper(webdriver.Edge):
    def __init__(self, headless=False):
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
        self.console.log(self.exit_message)
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

        # try:
        #     WebDriverWait(self, 10).until(
        #         EC.presence_of_element_located(
        #             (By.XPATH, "//div[contains(text(),'Sorry, the password you entered is incorrect.')]"))
        #     )
        # Sorry, the email address you entered is incorrect.
        # except:
        #     pass

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
            first_publication_link = ""
            for link in allLinks:
                if 'https://www.researchgate.net/publication/' in link.get_attribute('href'):
                    first_publication_link = link.get_attribute('href')
                    link.click()
                    break
            return first_publication_link

        except:
            return ""

    def findAllRefs(self):
        self.clickOnRefButton()
        self.implicitly_wait(10)
        # sleep(2)
        self.keepScrollingToBottom()
        self.implicitly_wait(10)
        self.handleShowMore()

    def clickOnRefButton(self):
        try:
            ref_button = WebDriverWait(self, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                                            "//button[.//div[contains(text(),'References')]]")))
            ref_button.click()
        except:
            pass

    def keepScrollingToBottom(self):
        last_height = self.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            sleep(3)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def handleShowMore(self):
        showMoreFound = True
        while showMoreFound:
            try:
                showMore = WebDriverWait(self, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//button[.//span[normalize-space()='Show more']]")))
                if showMore:
                    showMore.click()
                    self.implicitly_wait(3)
                else:
                    showMoreFound = False
            except:
                showMoreFound = False

    def getAllRefs(self, paper):
        # v1 = self.fetchReferences(parent_id=paper['id'])
        # v2 = self.fetchMissingReferences(parent_id=paper['id'])
        # return v1 + v2
        try:
            v1 = self.fetchReferences(parent_id=paper['id'])
            v2 = self.fetchMissingReferences(parent_id=paper['id'])
            return v1 + v2
        except:
            return []

    def fetchReferences(self, parent_id=None):
        sections = self.find_element(
            by=By.CSS_SELECTOR, value="div[class='nova-legacy-o-stack nova-legacy-o-stack--gutter-xxxl nova-legacy-o-stack--spacing-xl nova-legacy-o-stack--show-divider']")

        items = sections.find_elements(
            by=By.CLASS_NAME, value="nova-legacy-v-publication-item__body")

        allRefData = []

        types = ['Literature Review', 'Conference Paper',
                 'Article', 'Chapter', 'Book']
        avoid = types + ['Full-text available', 'File available']

        for s in items:
            links = s.find_elements(by=By.TAG_NAME, value="a")
            paper_info = {
                "id": uuid4(),
                'parent_id': parent_id,
                "name": "",
                "type": "",
                "published_date": "",
                "paper_link": "",
            }

            for link in links:
                if 'https://www.researchgate.net/publication/' in link.get_attribute('href'):
                    if link.text not in avoid:
                        paper_info['name'] = link.text
                        paper_info['type'] = link.text
                        paper_info['paper_link'] = link.get_attribute('href')
                    elif link.text in types:
                        paper_info['type'] = link.text
            try:
                time = s.find_element(By.XPATH, './/time')
                if time:
                    paper_info['published_date'] = time.get_attribute(
                        'datetime')
            except:
                pass

            allRefData.append(paper_info)

        return allRefData

    def fetchMissingReferences(self, parent_id=None):
        missingArticles = self.find_elements(
            By.XPATH, '//div[@class="nova-legacy-o-stack__item"]//div[@class="nova-legacy-e-text nova-legacy-e-text--size-m nova-legacy-e-text--family-sans-serif nova-legacy-e-text--spacing-none nova-legacy-e-text--color-inherit"]')

        allRefData = []

        for m in missingArticles:
            paper_info = {
                "id": uuid4(),
                'parent_id': parent_id,
                "name": "",
                "type": "",
                "published_date": "",
                "paper_link": "",
            }
            paper_info['name'] = m.text
            paper_info['type'] = "Unknown"
            allRefData.append(paper_info)

        return allRefData

    def fetchReferencesWithDownloadLink(self, parent_id=None):
        sleep(1)
        allRefs = self.find_elements(
            By.XPATH, "//div[@class='nova-legacy-o-stack__item']//div[@class='nova-legacy-o-stack nova-legacy-o-stack--gutter-s nova-legacy-o-stack--spacing-none nova-legacy-o-stack--no-gutter-outside']")
        items = []

        for ref in allRefs:
            i = ref.find_element(
                by=By.CLASS_NAME, value="nova-legacy-v-publication-item__body")
            items.append(i)

        allRefData = []

        types = ['Literature Review', 'Conference Paper',
                 'Article', 'Chapter', 'Book']
        avoid = types + ['Full-text available', 'File available']

        for s in items:
            links = s.find_elements(by=By.TAG_NAME, value="a")
            paper_info = {
                "id": uuid4(),
                'parent_id': parent_id,
                "name": "",
                "type": "",
                "published_date": "",
                "paper_link": "",
                "download_link": ""
            }

            for link in links:
                if 'https://www.researchgate.net/publication/' in link.get_attribute('href'):
                    if link.text not in avoid:
                        paper_info['name'] = link.text
                        paper_info['type'] = link.text
                        paper_info['paper_link'] = link.get_attribute('href')
                    elif link.text in types:
                        paper_info['type'] = link.text

            allRefData.append(paper_info)

        for i, d in enumerate(allRefs):
            try:
                # The XPath expression in the loop has to start with a dot to be context-specific:
                # https://stackoverflow.com/questions/36452129/python-selenium-find-child-elements-in-loop

                a = d.find_element(
                    By.XPATH, ".//a[.//span[text()='Download']]")
                if a:
                    allRefData[i]['download_link'] = a.get_attribute('href')
            except:
                pass
        return allRefData
