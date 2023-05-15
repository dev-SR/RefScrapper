# pipenv install selenium pandas webdriver-manager rich
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from base.setup import WebDriverSetup
from time import sleep
from uuid import uuid4


class TitleNAbstractGrabber(WebDriverSetup):
    def __init__(self, headless=False):
        super().__init__(headless=headless)
        self.uuid4 = uuid4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def land_home_page(self):
        # self.set_page_load_timeout(10)
        try:
            self.get("https://www.researchgate.net/")
        except:
            return False

    def login(self, email, password):
        self.find_element(by=By.CSS_SELECTOR, value=".index-header__log-in").click()
        self.find_element(by=By.CSS_SELECTOR, value="#input-login").send_keys(email)
        self.find_element(by=By.CSS_SELECTOR, value="#input-password").send_keys(
            password
        )
        # Enter
        self.find_element(by=By.CSS_SELECTOR, value="button[type='submit']").click()

        # try:
        #     WebDriverWait(self, 10).until(
        #         EC.presence_of_element_located(
        #             (By.XPATH, "//div[contains(text(),'Sorry, the password you entered is incorrect.')]"))
        #     )
        # Sorry, the email address you entered is incorrect.
        # except:
        #     pass

    def land_on_page(self, url):
        self.get(url)

    def isRequestQuotaExceeded(self):
        try:
            request_quota = WebDriverWait(self, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='request-quota-exceeded__message-box']")
                )
            )
            if request_quota:
                return True
        except:
            return False

    def keepScrollingToBottom(self):
        last_height = self.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            sleep(3)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def handleShowMore(self):
        showMoreFound = True
        while showMoreFound:
            try:
                showMore = WebDriverWait(self, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[normalize-space()='Show more']]")
                    )
                )
                if showMore:
                    showMore.click()
                    self.implicitly_wait(3)
                else:
                    showMoreFound = False
            except:
                showMoreFound = False

    def fetchTitles(self, save_in, author_name):
        cards = self.find_elements(
            by=By.CSS_SELECTOR,
            value="div[class='nova-legacy-v-publication-item__stack nova-legacy-v-publication-item__stack--gutter-m']",
        )

        papers_df = pd.DataFrame()
        for card in cards:
            titles_links = card.find_elements(
                by=By.CSS_SELECTOR,
                value="a[class='nova-legacy-e-link nova-legacy-e-link--color-inherit nova-legacy-e-link--theme-bare']",
            )
            time = card.find_element(
                by=By.TAG_NAME,
                value="time",
            )
            date_time = time.get_attribute("datetime")

            for link in titles_links:
                if "https://www.researchgate.net/publication/" in link.get_attribute(
                    "href"
                ):
                    paper_info = {
                        "id": str(uuid4()),
                        "author_name": author_name,
                        "paper_title": "",
                        "paper_link": "",
                        "abstract": "",
                        "published_date": "",
                        "done": 0,
                    }
                    paper_info["paper_title"] = link.text
                    paper_info["paper_link"] = link.get_attribute("href")
                    paper_info["published_date"] = date_time
                    papers_df = pd.concat(
                        [papers_df, pd.DataFrame([paper_info])], ignore_index=True
                    )

        papers_df.to_csv(save_in, index=False)
        print(f"Saved in {save_in}")

    def fetchAbstracts(self):
        abstract = ""
        self.implicitly_wait(5)
        try:
            abstract_div = self.find_element(
                by=By.CSS_SELECTOR,
                value="div[class='nova-legacy-e-expandable-text__container'] div:nth-child(1)",
            )
            abstract = abstract_div.text
        except Exception as e:
            print("No abstract found")

        return abstract
