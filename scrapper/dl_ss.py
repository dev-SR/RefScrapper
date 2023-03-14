import os
from collections import deque
from time import sleep
import pandas as pd
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
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from utils.loader import withLoader, withLoaderWithParam, console, withLoaderWithParamNew


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"


class DownloadLinkScrapperSS(webdriver.Edge):
    def __init__(self, headless=0):
        self.result = None
        self.console = Console()
        self.exit_message = "[red]Terminating Browser Session...[/]"
        self.inf = withLoaderWithParam(
            pd.read_csv, ["data/info_ss/info_full_ss.csv"], "Initializing Paper Info Dataframe", 'dots')

        options = webdriver.EdgeOptions()
        os.environ['WDM_LOG'] = '0'
        os.environ['WDM_LOG_LEVEL'] = '0'
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

    def isRequestQuotaExceeded(self):
        pass

    def getDownloadLink(self, n):
        not_processed = self.inf[self.inf['download_link'].isnull()][:n]
        not_processed_list = not_processed.to_dict('records')
        if n > len(not_processed_list):
            n = len(not_processed_list)
        console.log(f"Fetching {n} at a time")

        q = deque(not_processed_list)

        while q:
            p = q.popleft()
            paper_url = p['paper_link']
            uuid = p['uuid']
            paper_title = p['title']
            ln = len(paper_title)
            if ln > 100:
                ln = 100
            print()
            console.log(f"Paper: {paper_title[:ln]}{'.'*(93-ln)}")
            withLoaderWithParam(self.land_on_paper, [
                                paper_url], f"Landing on {paper_title}", 'point')

            links = withLoader(self.getLinks, f"Getting Links", 'dots')
            doi = self.getDoiLink()

            if not doi:
                console.log(
                    f"[yellow]No doi found[/]")
            else:
                console.log(f"DOI: {doi}")

            if links == "No links found":
                # get the download link from scihub
                if doi:
                    links = withLoaderWithParam(self.get_download_link_from_scihub, [
                                                doi], f"No Links Found at S.S. ; trying to get from SciHub", 'point')
                    if links == "No links found":
                        console.log(
                            f"[yellow]No download links found[/]")
                    else:
                        console.log(f"[green]Download links found: [/]")
                        console.log(f"[magenta]{links}[/]")
                else:
                    console.log(
                        f"[yellow]No download links found")
            else:
                console.log(f"[green]Download links found: [/]")
                console.log(f"[magenta]{links}[/]")
            try:
                withLoaderWithParam(
                    self.saveLinks, [uuid, links, doi], f"Saving Links/Info", 'dots')
            except Exception as e:
                console.log(f"Error: {e}")

        # withLoaderWithParam(self.inf.to_csv, [
        #     "data/info_ss/info_full_ss.csv", False], "Saving Paper Info Dataframe", 'dots')
        print()
        # self.inf.to_csv("data/info_ss/info_full_ss.csv", index=False)
        withLoaderWithParamNew(self.inf.to_csv,
                               {
                                   'path_or_buf': "data/info_ss/info_full_ss.csv",
                                   'index': False
                               },
                               "Saving Paper Info in CSV file",
                               'point')
        console.log("[bright_green]Saved Final Result in CSV file[/]")

        self.console.print(self.exit_message)
        self.close()

    def land_on_paper(self, paper_url):
        try:
            self.get(paper_url)
        except:
            return False

    def getLinks(self):
        try:
            dropdown = WebDriverWait(self, 2).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Dropdown menu']")))

            if dropdown:
                dropdown.click()
        except:
            pass
        try:
            paper_links = self.find_elements(
                By.XPATH, "//a[contains(@data-selenium-selector,'paper-link')]")
            paper_links = [link.get_attribute(
                'href') for link in paper_links if link.get_attribute('href').endswith('.pdf')]
            # print(paper_links)

            links = ";".join(paper_links)

            if not links:
                links = "No links found"
                # print(first_visible_a.tag_name)

            return links
        except:
            return "No links found"

    def getDoiLink(self):
        try:
            doi_link = WebDriverWait(self, 1).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='doi__link']")))

            if doi_link:
                return doi_link.get_attribute('href')
            else:
                return None
        except:
            return None

    def get_download_link_from_scihub(self, doi):
        sci_hubs = [
            {"ee": "https://sci-hub.ee/"},
            {"se": "https://sci-hub.se/"},
            {"st": "https://sci-hub.st/"},
            # {"ru": "https://sci-hub.ru/"},
        ]
        links = []
        for sci_hub in sci_hubs:
            code = list(sci_hub.keys())[0]
            url = sci_hub[code]
            self.land_on_paper(f"{url}{doi}")
            # self.implicitly_wait(1.25)

            if code == "ee":
                link = self.handleSciHubEE()
                if link:
                    links.append(link)

            elif code == "st":
                link = self.handleSciHubST()
                if link:
                    links.append(link)

            elif code == "ru":
                link = self.handleSciHubRU()
                if link:
                    links.append(link)

            elif code == "se":
                link = self.handleSciHubSE()
                if link:
                    links.append(link)

        links = ";".join(links)
        if not links:
            links = "No links found"
        return links

    def handleSciHubEE(self):

        try:
            iframe = self.find_element(By.XPATH, "//iframe[@id='pdf']")
            if iframe:
                return iframe.get_attribute('src')
            else:
                return None
        except Exception as e:
            # print(e)
            # print("handleSciHubEE")
            return None

    def handleSciHubST(self):
        try:
            embed = self.find_element(By.XPATH, "//embed[@id='pdf']")
            if embed:
                link = embed.get_attribute('src')
                if link.find("https:") != -1:
                    return link
                return "https:" + link
            else:
                return None
        except Exception as e:
            # print(e)
            # print("handleSciHubST")
            return None

    def handleSciHubRU(self):
        try:
            embed = self.find_element(By.XPATH, "//embed[@id='pdf']")
            if embed:
                link = embed.get_attribute('src')
                if link.find("https:") != -1:
                    return link
                return "https:" + link
            else:
                return None
        except Exception as e:
            # print(e)
            # print("handleSciHubRU")
            return None

    def handleSciHubSE(self):
        try:
            embed = self.find_element(By.XPATH, "//embed[@id='pdf']")
            if embed:
                link = embed.get_attribute('src')
                if link.find("https:") != -1:
                    return link
                return "https:" + link
            else:
                return None
        except Exception as e:
            # print(e)
            # print("handleSciHubSE")
            return None

    def saveLinks(self, uuid, dLinks, doi_link):
        sleep(0.25)
        # inf = pd.read_csv("data/info_ss/info_full_ss.csv")
        self.inf.loc[self.inf['uuid'] == uuid, 'download_link'] = dLinks
        sleep(0.1)
        self.inf.loc[self.inf['uuid'] == uuid, 'doi'] = doi_link
        # self.inf.to_csv("data/info_ss/info_full_ss.csv", index=False)
        # sleep(0.2)
