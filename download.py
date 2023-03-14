from datetime import datetime, timedelta
import os
from time import sleep
# from rich.console import Console
import pandas as pd
from collections import deque
# from apscheduler.schedulers.background import BlockingScheduler
# from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pytz import timezone

import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

# from rich.console import Console
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('n', nargs='?', const=0, type=int, default=1)
args = parser.parse_args()

# console = Console()


# def withLoaderWithParam(cb, param, message="", spinner='aesthetic'):
#     done = False
#     returns = None
#     with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
#         while not done:
#             returns = cb(*param)
#             done = True
#     return returns


CIPHERS = "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"


class TLSAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, *args, **kwargs):
        self.ssl_options = ssl_options
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = ssl_.create_urllib3_context(
            ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*args, ssl_context=context, **kwargs)


def download(fileName, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
    }
    adapter = TLSAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)

    with requests.session() as session:
        session.mount("https://www.researchgate.net/", adapter)
        response = session.get(url, headers=headers)
        # print(response.status_code)  # 200
        if response.status_code == 200:
            with open(f"data/papers_pdf/{fileName}.pdf", 'wb') as f:
                f.write(response.content)
            return []
        else:
            return [response.status_code, response.reason]


def downloadManager():
    papers_list = pd.read_csv("data/info/info_full.csv")
    # get all papers with download links
    paperDown = papers_list[papers_list['download_link'].notnull()]

    # already downloaded papers
    downloaded = pd.read_csv("data/info/downloaded.csv")
    downloadedIds = downloaded['id'].tolist()

    # get the list of papers that are not downloaded
    paperDownNext = paperDown[~paperDown['id'].isin(downloadedIds)]
    paperDownNextList = paperDownNext.head(n=args.n).to_dict(orient='records')

    for paper in paperDownNextList:
        link = paper['download_link']
        id = paper['id']
        status = download(id, link)
        if not status:
            print(f"{id} is downloaded")
            info = {
                'id': id
            }
            df = pd.DataFrame([info])
            df.to_csv("data/info/downloaded.csv",
                      mode='a', header=False, index=False)
        else:
            for s in status:
                print(s)


downloadManager()


# def startJob():
#     sched = BlockingScheduler(timezone=timezone('Asia/Dhaka'))

#     sched.add_job(downloadManager, 'interval',
#                   minutes=10,
#                   next_run_time=datetime.now(),  # start immediately
#                   end_date=datetime.now() + timedelta(hours=1),
#                   id='my_job_id')

#     def execution_listener(event):
#         if event.exception:
#             print('The job crashed')
#             return

#         # console.log('The job executed successfully')
#         job = sched.get_job(event.job_id)
#         print()
#         try:
#             pass
#             # if job.id == 'info_job':
#             # check if there is any paper in the queu

#         except:
#             # all the jobs are done
#             sched.shutdown(wait=False)

#     sched.print_jobs()
#     sched.add_listener(execution_listener,
#                        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
#     sched.start()


# startJob()
