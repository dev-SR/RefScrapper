from time import sleep
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
import os
import argparse
os.environ['WDM_LOG'] = '0'
parser = argparse.ArgumentParser()
parser.add_argument('h', nargs='?', const=0, type=int)
args = parser.parse_args()


options = webdriver.EdgeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
# disable
# options.add_experimental_option(
#     "excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-logging')
if args.h:
    options.add_argument('--headless')


prefs = {"download.default_directory": "C:\Tutorial"}
options.add_experimental_option("prefs", prefs)
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


PAPER1 = "A Comprehensive Survey of Image-Based Food Recognition and Volume Estimation Methods for Dietary Assessment"
PAPER2 = "Recommending Research Articles: A Multi-Level Chronological Learning-Based Approach Using Unsupervised Keyphrase Extraction and Lexical Similarity Calculation"
PAPER3 = "PositionRank: An Unsupervised Approach to Keyphrase Extraction from Scholarly Documents"
paper = {

    "name": PAPER1,
    "id": uuid4()
}

driver = webdriver.Edge(service=Service(
    EdgeChromiumDriverManager().install()), options=options)

driver.get('https://www.researchgate.net/')


driver.find_element(by=By.CSS_SELECTOR, value=".index-header__log-in").click()
driver.find_element(by=By.CSS_SELECTOR,
                    value="#input-login").send_keys("ema.191902035@green.ac.bd")
driver.find_element(by=By.CSS_SELECTOR,
                    value="#input-password").send_keys("researchgate")
driver.find_element(by=By.CSS_SELECTOR,
                    value="button[type='submit']").click()
driver.find_element(by=By.CSS_SELECTOR,
                    value="#header-search-action").send_keys(paper['name'])
driver.find_element(by=By.CSS_SELECTOR,
                    value="#header-search-action").send_keys(Keys.ENTER)
first_paper = None

try:
    first_paper = driver.find_element(by=By.XPATH,
                                      value="(//div[@class='search-box__result-item'])[1]")
except:
    print("Page not found")
if first_paper:
    first_paper.find_element(by=By.TAG_NAME, value="a").click()

    paper_info_el = driver.find_element(by=By.XPATH,
                                        value="(//div[@class='content-grid__columns--narrow'])[1]")

    paper_infos = paper_info_el.find_elements(
        by=By.CLASS_NAME, value="nova-legacy-o-stack__item")

    try:
        ref_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "(//button[@role='tab'])[5]")))

        ref_button.click()

        print(ref_button.text)
    except:
        pass

    # Wait to load page
    sleep(5)
    # # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        sleep(3)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    showMoreFound = True
    while showMoreFound:
        try:
            showMore = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            "button[class='nova-legacy-c-button nova-legacy-c-button--align-center nova-legacy-c-button--radius-m nova-legacy-c-button--size-m nova-legacy-c-button--color-blue nova-legacy-c-button--theme-bare nova-legacy-c-button--width-full']")))
            # print(showMore)
            if showMore:
                showMore.click()
                driver.implicitly_wait(3)
            else:
                showMoreFound = False
        except:
            showMoreFound = False

    sleep(1)
    # sections = driver.find_element(
    #     by=By.CSS_SELECTOR, value="div[class='nova-legacy-o-stack nova-legacy-o-stack--gutter-xxxl nova-legacy-o-stack--spacing-xl nova-legacy-o-stack--show-divider']")

    allRefs = driver.find_elements(
        By.XPATH, "//div[@class='nova-legacy-o-stack__item']//div[@class='nova-legacy-o-stack nova-legacy-o-stack--gutter-s nova-legacy-o-stack--spacing-none nova-legacy-o-stack--no-gutter-outside']")
    print(len(allRefs))
    items = []

    for ref in allRefs:
        i = ref.find_element(
            by=By.CLASS_NAME, value="nova-legacy-v-publication-item__body")
        items.append(i)
    print()

    # missingBody = sections.find_elements(
    #     by=By.XPATH, value='//div[@class="nova-legacy-e-text nova-legacy-e-text--size-m nova-legacy-e-text--family-sans-serif nova-legacy-e-text--spacing-none nova-legacy-e-text--color-inherit"]/ancestor::div[@class="nova-legacy-o-stack__item"]')
    # downBtn = sections.find_elements(
    #     by=By.XPATH, value="//a[.//span[text()='Download']]")
    # print(len(downBtn))


# # //a[@class="nova-legacy-e-link nova-legacy-e-link--color-inherit nova-legacy-e-link--theme-bare"]

    allRefData = []
    ss = set()

    types = ['Literature Review', 'Conference Paper', 'Article', 'Chapter']
    avoid = types + ['Full-text available', 'File available']
    for s in items:
        links = s.find_elements(by=By.TAG_NAME, value="a")
        # print(link.text)
        paper_info = {
            # "name": "",
            # "type": "",
            "published_date": "",
            # "publisher": "",
            # "id": uuid4(),
            # "paper_link": "",
            # "download_link": "",

        }

        # for link in links:
        #     if 'https://www.researchgate.net/publication/' in link.get_attribute('href'):
        #         if link.text not in avoid:
        #             paper_info['name'] = link.text
        #             paper_info['type'] = link.text
        #             paper_info['paper_link'] = link.get_attribute('href')
        #         elif link.text in types:
        #             paper_info['type'] = link.text

        time = s.find_element(By.XPATH, '//time')
        paper_info['date'] = time.get_attribute('datetime')
        # print(time.text)
        # print(time.get_attribute('datetime'))

        allRefData.append(paper_info)

    # for i, d in enumerate(allRefs):
    #     try:
    #         a = d.find_element(
    #             By.XPATH, ".//a[.//span[text()='Download']]")
    #         if a:
    #             allRefData[i]['download_link'] = a.get_attribute('href')
    #             print(i)
    #             # print(len(a))
    #             print()
    #     except:
    #         print(f"not found {i}")

    with open('write.txt', 'w') as f:
        for p in allRefData:
            # f.write(str(p['name']) + '\n')
            # f.write(str(p['type']) + '\n')
            # f.write(str(p['paper_link']) + '\n')
            # f.write(str(p['download_link']) + '\n')
            f.write(str(p['published_date']) + '\n')
            # f.write(str(p['publisher']) + '\n')
            f.write('\n')
#     print(ss)
#     print(len(ss))

#     print("Done")
#     if not args.h:
#         sleep(50)

"""
https://stackoverflow.com/questions/8577636/select-parent-element-of-known-element-in-selenium



<button>
    <!-- some other els -->
    <span>Close</span>
</button>

Now that you need to select parent tag 'a' based on <span> text, then use

driver.find_element(By.XPATH, "//button[.//span[text()='Close']]")

https://spltech.co.uk/how-to-find-the-parent-element-in-a-page-using-python-selenium-webdriver/


<div class"ancestor">
    <div class="child">
        <div class="grandchild">
            <div class="greatgrandchild">
            Hello World
            </div>
        </div>
    </div>
    <div class="child">
        <div class="grandchild">
            <div class="greatgrandchild">
            Hello World
            </div>
        </div>
    </div>
    <div class="child">
            Hello World
    </div>
</div>

 """
