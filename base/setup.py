import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"


class WebDriverSetup(webdriver.Edge):
    def __init__(self, headless=False):
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





