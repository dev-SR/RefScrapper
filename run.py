from datetime import datetime, timedelta
import os
from turtle import title
os.environ['WDM_LOG'] = '0'
os.environ['WDM_LOG_LEVEL'] = '0'
from time import sleep
from rich.console import Console
import inquirer
from scrapper.ref import RefScrapper
from scrapper.dl import DownloadLinkScrapper
from scrapper.info import PaperInfoScrapper
from scrapper.dl_ss import DownloadLinkScrapperSS
from scrapper.info_new import PaperInfoScrapperNew

from api.semanticscholar import SemanticScholar

import pandas as pd
from collections import deque
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pytz import timezone
import subprocess
subprocess.call('cls', shell=True)


from rich.console import Console
import inquirer
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('n', nargs='?', const=0, type=int, default=1)
parser.add_argument('h', nargs='?', const=0, type=int, default=1)
args = parser.parse_args()

console = Console()


def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

# exclude python dictionary properties


def exclude_dict_keys(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def withLoader(cb, message="", spinner='aesthetic'):
    done = False
    returns = None
    with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
        while not done:
            returns = cb()
            done = True
    return returns


def withLoaderWithParam(cb, param, message="", spinner='aesthetic'):
    done = False
    returns = None
    with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
        while not done:
            returns = cb(*param)
            done = True
    return returns


def getRefsComplete():
    first_non_blocked_user = None
    auth_df = None
    try:
        auth_df = pd.read_csv('data/info/auth.csv')
        first_non_blocked_user = auth_df[auth_df["blocked"] == 0].iloc[0].to_dict(
        )
    except:
        if not first_non_blocked_user:
            print("[red] No users found [/]")
        if not auth_df:
            console.log("File not found : data/info/auth.csv")
            console.log("""
                Please create a file with the following format:

                email,password,blocked
                X@edu.ac.bd,researchgate,0
            """)
    if not first_non_blocked_user:
        return

    email, password = first_non_blocked_user['email'], first_non_blocked_user['password']

    wtDf = pd.read_csv("data/info/waiting_list_ref.csv")
    waitingList = wtDf.to_dict(orient='records')
    console.log(f"Still {len(waitingList)} needs to be scraped")
    n = args.n
    if n > len(waitingList):
        n = len(waitingList)
    console.log(f"Fetching {n} at a time")
    q = deque(waitingList[:n])
    if not q:
        console.log("[cyan]Paper queue is empty[/]")
        return

    try:
        with RefScrapper(args.h) as bot:
            withLoader(bot.land_home_page, "Home Page")
            withLoaderWithParam(
                bot.login, [email, password], "Logging in", 'dots')

            requestQuota = withLoader(
                bot.isRequestQuotaExceeded, "Checking Daily Request Quota Limits", 'dots')
            if requestQuota:
                console.log(
                    f"[red]Request Quota Exceeded [/]")
                if auth_df is not None:
                    auth_df.loc[auth_df['email'] == email, 'blocked'] = 1
                    auth_df.to_csv('data/info/auth.csv', index=False)
                return

            q = deque(waitingList[:n])
            while q:

                paper = q.popleft()
                nameLen = len(paper['name'])
                name = paper['name']
                if nameLen > 50:
                    name = name[:50] + "..."
                else:
                    nameLen = nameLen
                    name = name + "." * (53 - nameLen)

                console.log(
                    f"[blue]Processing Paper: {name}[/]")
                foundPaperLink = ""
                if pd.isna(paper["paper_link"]):
                    console.log(
                        f"[yellow]Paper link is not found;Searching Instead [/]")
                    foundPaperLink = withLoaderWithParam(
                        bot.searchPaper, [paper], "Searching Paper", 'point')
                    if not foundPaperLink:
                        console.log(
                            f"[red]Paper link is not found [/]")
                        # remove from waiting list + add to not found list
                        saveRefs([], paper)
                        # move to the next paper
                        continue
                    # update paper link
                    paper["paper_link"] = foundPaperLink
                else:
                    withLoaderWithParam(
                        bot.directLandOnPaperPage, [paper['paper_link']], "Landing on the Paper page", 'point')
                    # use existing paper link
                    foundPaperLink = paper['paper_link']

                requestQuota = withLoader(
                    bot.isRequestQuotaExceeded, "Checking Daily Request Quota Limits", 'dots')
                if requestQuota:
                    console.log(
                        f"[red]Request Quota Exceeded [/]")
                    if auth_df is not None:
                        auth_df.loc[auth_df['email'] == email, 'blocked'] = 1
                        auth_df.to_csv('data/info/auth.csv', index=False)
                    break

                if foundPaperLink:
                    console.log(
                        f"[green]Found Paper: {name}.....[/]")
                    continueRefScrapping(bot, paper)
                else:
                    console.log(
                        f"[red]Not Found Paper: {name}[/]")
            if not q:
                console.log("[cyan]Paper queue is empty[/]")

            if not args.h:
                sleep(50)

    except Exception as e:
        if 'in PATH' in str(e):
            print(
                'You are trying to run the bot from command line \n'
                'Please add to PATH your Selenium Drivers \n'
                'Windows: \n'
                '    set PATH=%PATH%;<C:path-to-your-folder> \n \n'
                'Linux: \n'
                '    PATH=$PATH:</path-to-your-folder \n'
            )
        else:
            raise


def continueRefScrapping(bot, paper):
    withLoader(bot.findAllRefs, "Finding All References", 'point')
    refs = withLoaderWithParam(
        bot.getAllRefs, [paper], "Collecting All References", 'point')

    withLoaderWithParam(saveRefs, [refs, paper],
                        "Saving All References", 'hearts')
    # saveRefs(refs, paper)


def saveRefs(refs, paper):
    wtDf = pd.read_csv("data/info/waiting_list_ref.csv")
    sleep(1)
    if len(refs) == 0:
        console.log("[red]No references found[/]")
        # !save to the not found list
        notFoundDf = pd.DataFrame([paper])
        notFoundDf.to_csv("data/info/not_found_ref.csv",
                          mode='a', header=False, index=False)
        # !remove current paper from waiting list
        # New_wtDf = wtDf[wtDf['id'] != paper['id']]
        # New_wtDf.to_csv("data/info/waiting_list_ref.csv", index=False)
        # or
        idx = wtDf.index[wtDf['id'] == paper['id']]
        wtDf.drop(index=idx, inplace=True)
        wtDf.to_csv("data/info/waiting_list_ref.csv", index=False)

    else:
        # !add current paper to done list
        doneDfNew = pd.DataFrame([paper])
        doneDfNew.to_csv("data/info/done_list_ref.csv", mode='a',
                         header=False, index=False)

        # ?Also, add to info waiting list
        doneDfNew.to_csv("data/info/info_waiting.csv", mode='a',
                         header=False, index=False)

        # !remove current paper from waiting list
        # New_wtDf = wtDf[wtDf['id'] != paper['id']]
        # New_wtDf.to_csv("data/info/waiting_list_ref.csv", index=False)
        # or
        idx = wtDf.index[wtDf['id'] == paper['id']]
        wtDf.drop(index=idx, inplace=True)
        wtDf.to_csv("data/info/waiting_list_ref.csv", index=False)

        # !create file
        refsDf = pd.DataFrame(refs)
        paper_id = paper['id']
        refsDf.to_csv(f"data/papers/{paper_id}.csv", index=False)

        # !add new ref papers of current paper to waiting list
        refsDf.to_csv("data/info/waiting_list_ref.csv", mode='a',
                      header=False, index=False)

        # Create logger
        logs = {
            "paper_id": paper_id,
            "paper_name": paper['name'],
            "ref_id_begin": refs[0]['id'],
            "ref_id_end": refs[-1]['id'],
            "performed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        logsDF = pd.DataFrame([logs])
        logsDF.to_csv("data/info/logs.csv", mode="a",
                      header=False, index=False)

        console.log(f"[yellow]Saved!! [/]")


def getDownLinks():
    try:
        with DownloadLinkScrapper() as bot:
            withLoader(bot.land_home_page, "Landing on Home Page")
            withLoaderWithParam(
                bot.searchPaper, [PAPER3], "Searching Paper")
            console.print(f"[green] Paper found [/]")
            link = withLoader(
                bot.getDownload, "Getting Download Link")
            print(link)
            if not args.h:
                sleep(50)
    except Exception as e:
        if 'in PATH' in str(e):
            print(
                'You are trying to run the bot from command line \n'
                'Please add to PATH your Selenium Drivers \n'
                'Windows: \n'
                '    set PATH=%PATH%;<C:path-to-your-folder> \n \n'
                'Linux: \n'
                '    PATH=$PATH:</path-to-your-folder \n'
            )
        else:
            raise


def paperInfo():

    first_non_blocked_user = None
    auth_df = None
    try:
        auth_df = pd.read_csv('data/info/auth.csv')
        first_non_blocked_user = auth_df[auth_df["blocked"] == 0].iloc[0].to_dict(
        )
    except:
        if not first_non_blocked_user:
            print("[red] No users found [/]")
        if not auth_df:
            console.log("File not found : data/info/auth.csv")
            console.log("""
                Please create a file with the following format:

                email,password,blocked
                X@edu.ac.bd,researchgate,0
            """)
    if not first_non_blocked_user:
        return

    email, password = first_non_blocked_user['email'], first_non_blocked_user['password']

    info_wt = pd.read_csv("data/info/info_waiting.csv")
    info_wt_list = info_wt.to_dict(orient='records')
    console.log(f"{len(info_wt_list)} papers needs to be scraped")
    n = args.n
    if n > len(info_wt_list):
        n = len(info_wt_list)
    console.log(f"Fetching {n} at a time")

    q = deque(info_wt_list[:n])
    if not q:
        console.log("[cyan]Paper queue is empty[/]")
        return
    try:
        with PaperInfoScrapper(args.h) as bot:
            withLoader(bot.land_home_page, "Home Page")
            withLoaderWithParam(
                bot.login, [email, password], "Logging in", 'dots')

            requestQuota = withLoader(
                bot.isRequestQuotaExceeded, "Checking Daily Request Quota Limits", 'dots')
            if requestQuota:
                console.log(
                    f"[red]Request Quota Exceeded [/]")
                if auth_df is not None:
                    auth_df.loc[auth_df['email'] == email, 'blocked'] = 1
                    auth_df.to_csv('data/info/auth.csv', index=False)
                return

            while q:
                paper = q.popleft()
                if pd.isna(paper['name']):
                    console.log(
                        f"[red]Paper name Invalid[/]")
                    # remove paper from info_waiting.csv
                    idx = info_wt.index[info_wt['id'] == paper['id']]
                    info_wt.drop(index=idx, inplace=True)
                    info_wt.to_csv(
                        "data/info/info_waiting.csv", index=False)
                    # save to the not found list
                    notFoundDf = pd.DataFrame([paper])
                    notFoundDf.to_csv("data/info/info_not_found.csv",
                                      mode='a', header=False, index=False)
                    continue

                nameLen = len(paper['name'])
                name = paper['name']
                if nameLen > 50:
                    name = name[:50] + "..."
                else:
                    nameLen = nameLen
                    name = name + "." * (53 - nameLen)
                console.log(
                    f"[blue]Processing Paper: {name}[/]")

                paper_link_new = ""
                if pd.isna(paper["paper_link"]):
                    console.log(
                        f"[yellow]Paper link is not found;Searching Instead [/]")
                    link = withLoaderWithParam(
                        bot.searchPaper, [paper], "Searching Paper", 'point')
                    paper_link_new = link
                else:
                    paper_link_new = paper['paper_link']
                    withLoaderWithParam(
                        bot.directLandOnPaperPage, [paper['paper_link']], "Landing on the Paper page", 'point')

                requestQuota = withLoader(
                    bot.isRequestQuotaExceeded, "Checking Daily Request Quota Limits", 'dots')
                if requestQuota:
                    console.log(
                        f"[red]Request Quota Exceeded [/]")
                    if auth_df is not None:
                        auth_df.loc[auth_df['email'] == email, 'blocked'] = 1
                        auth_df.to_csv('data/info/auth.csv', index=False)
                    break

                continueInfoScrapping(bot, paper, paper_link_new)
                sleep(1)
            if not q:
                console.log("[cyan]Paper queue is empty[/]")

            if not args.h:
                sleep(50)

    except Exception as e:
        if 'in PATH' in str(e):
            print(
                'You are trying to run the bot from command line \n'
                'Please add to PATH your Selenium Drivers \n'
                'Windows: \n'
                '    set PATH=%PATH%;<C:path-to-your-folder> \n \n'
                'Linux: \n'
                '    PATH=$PATH:</path-to-your-folder \n'
            )
        else:
            raise


def continueInfoScrapping(bot, paper, paper_link_new):
    success, info = withLoader(
        bot.getPaperInfo, "Getting All Paper Info", 'point')
    if not success:
        console.print(f"[red] Error Getting Info [/]")
        # remove current paper from waiting list
        info_wt = pd.read_csv("data/info/info_waiting.csv")
        idx = info_wt.index[info_wt['id'] == paper['id']]
        info_wt.drop(index=idx, inplace=True)
        info_wt.to_csv("data/info/info_waiting.csv", index=False)
        # save to the not found list
        notFoundDf = pd.DataFrame([paper])
        notFoundDf.to_csv("data/info/info_not_found.csv",
                          mode='a', header=False, index=False)
        return

    dLink = withLoader(
        bot.getDownloadLink, "Getting All References", 'point')

    full_info = merge_dicts(exclude_dict_keys(paper, ['paper_link']), info, {
        'paper_link': paper_link_new}, {"download_link": dLink})

    # remove current paper from waiting list
    info_wt = pd.read_csv("data/info/info_waiting.csv")
    idx = info_wt.index[info_wt['id'] == paper['id']]
    info_wt.drop(index=idx, inplace=True)
    info_wt.to_csv("data/info/info_waiting.csv", index=False)
    # add to done list
    doneDfNew = pd.DataFrame([paper])
    doneDfNew.to_csv("data/info/info_done.csv", mode='a',
                     header=False, index=False)
    # add to info full list
    full_info_Df = pd.DataFrame([full_info])
    full_info_Df.to_csv("data/info/info_full.csv", mode='a',
                        header=False, index=False)
    console.log(f"[green]Saved!! [/]")


def handleSemanticApi():
    n = args.n
    waiting_list_path = "data/info_2/waiting_2.csv"
    not_found_path = "data/info_2/not_found_2.csv"
    final_csv_path = "data/info_2/info_2.csv"
    ss: SemanticScholar = SemanticScholar(
        waiting_list_path=waiting_list_path,
        not_found_path=not_found_path,
        final_csv_path=final_csv_path)
    ss.savePaperDetails(n, sleep_time=2)


def getDownloadLinksForSemanticS():
    h = args.h
    n = args.n
    try:
        dl: DownloadLinkScrapperSS = DownloadLinkScrapperSS(h)
        dl.getDownloadLink(n)
    except Exception as e:
        console.log(f"[red]Error: {e}[/]")


def getInfoFromResearchGate():
    first_non_blocked_user = None
    auth_df = None
    try:
        auth_df = pd.read_csv('data/info/auth.csv')
        first_non_blocked_user = auth_df[auth_df["blocked"] == 0].iloc[0].to_dict(
        )
    except:
        if not first_non_blocked_user:
            print("[red] No users found [/]")
        if not auth_df:
            console.log("File not found : data/info/auth.csv")
            console.log("""
                Please create a file with the following format:

                email,password,blocked
                X@edu.ac.bd,researchgate,0
            """)
    if not first_non_blocked_user:
        return

    email, password = first_non_blocked_user['email'], first_non_blocked_user['password']
    papers = pd.read_csv("data/info_recover/not_found.csv")
    nextPapers = papers[papers['download_link'] == 'No links found']
    nextPapersList = nextPapers.to_dict('records')
    console.log(f"Still {len(nextPapersList)} needs to be scraped")

    n = args.n
    if n > len(nextPapersList):
        n = len(nextPapersList)
    console.log(f"Fetching {n} at a time")
    q = deque(nextPapersList[:n])
    if not q:
        console.log("[cyan]Paper queue is empty[/]")
        return

    try:
        with PaperInfoScrapperNew(args.h) as bot:
            withLoader(bot.land_home_page, "Home Page")
            withLoaderWithParam(
                bot.login, [email, password], "Logging in", 'dots')

            requestQuota = withLoader(
                bot.isRequestQuotaExceeded, "Checking Daily Request Quota Limits", 'dots')

            if requestQuota:
                console.log(
                    f"[red]Request Quota Exceeded [/]")
                if auth_df is not None:
                    auth_df.loc[auth_df['email'] == email, 'blocked'] = 1
                    auth_df.to_csv('data/info/auth.csv', index=False)
                return

            while q:
                paper = q.popleft()
                title = paper['title']
                uuid = paper['uuid']
                print(f"Scrapping {title}")

                withLoaderWithParam(
                    bot.searchPaper, [title], "Searching Paper", 'dots')
                found = withLoaderWithParam(
                    bot.findDownloadLink, [title], "Finding Download Link", 'dots')

                if not found:
                    console.log(f"[red] Paper not found [/]")
                    papers.loc[papers['uuid'] == uuid,
                               "download_link"] = "No links found;Processed"
                else:
                    console.log(f"[green] Paper found [/]")
                    papers.loc[papers['uuid'] == uuid, "download_link"] = found

            if not q:
                papers.to_csv('data/info_recover/not_found.csv', index=False)
                console.log("[cyan]Paper queue is empty[/]")

            if not args.h:
                sleep(50)

    except Exception as e:
        if 'in PATH' in str(e):
            print(
                'You are trying to run the bot from command line \n'
                'Please add to PATH your Selenium Drivers \n'
                'Windows: \n'
                '    set PATH=%PATH%;<C:path-to-your-folder> \n \n'
                'Linux: \n'
                '    PATH=$PATH:</path-to-your-folder \n'
            )
        else:
            raise


def startJob(answers):
    sched = BlockingScheduler(timezone=timezone('Asia/Dhaka'))
    oldRefDoneLen = 0
    oldInfoDoneLen = 0
    oldSSInfoLen = 0
    oldDlSSLen = 0

    # *register job

    if answers['option'] == 'Get Download Link?':
        sched.add_job(getDownLinks, 'interval',
                      minutes=10,
                      next_run_time=datetime.now(),  # start immediately
                      end_date=datetime.now() + timedelta(hours=1),
                      id='my_job_id')
    elif answers['option'] == 'Get All References?':
        done_list = pd.read_csv("data/info/done_list_ref.csv")
        oldRefDoneLen = done_list.shape[0]

        sched.add_job(getRefsComplete, 'interval',
                      minutes=10,
                      next_run_time=datetime.now(),  # start immediately
                      end_date=datetime.now() + timedelta(hours=3),
                      id='ref_job')
    elif answers['option'] == 'Get Paper Info?':
        info_done = pd.read_csv("data/info/info_done.csv")
        oldInfoDoneLen = info_done.shape[0]

        sched.add_job(paperInfo, 'interval',
                      minutes=7,
                      next_run_time=datetime.now(),  # start immediately
                      id='info_job',
                      end_date=datetime.now() + timedelta(hours=7)
                      )
    elif answers['option'] == 'Get Info Using Semantic Sch. Api?':
        ss_info = pd.read_csv("data/info_ss/info_full_ss.csv")
        oldSSInfoLen = ss_info.shape[0]
        sched.add_job(handleSemanticApi, 'interval',
                      minutes=1,
                      next_run_time=datetime.now(),  # start immediately
                      id='semantic_job',
                      #   end_date=datetime.now() + timedelta(hours=7)
                      #   end_date=datetime.now() + timedelta(minutes=1)
                      )
    elif answers['option'] == 'Get DownloadLinks From Semantic Sch.?':
        ss_info = pd.read_csv("data/info_ss/info_full_ss.csv")
        ss_info = ss_info[ss_info['download_link'].isnull()]
        oldDlSSLen = ss_info.shape[0]
        sched.add_job(getDownloadLinksForSemanticS, 'interval',
                      minutes=6,
                      next_run_time=datetime.now(),  # start immediately
                      id='dl_semantic_sch_job',
                      #  end_date=datetime.now() + timedelta(hours=1)
                      #   end_date=datetime.now() + timedelta(minutes=30)
                      )
    elif answers['option'] == 'Get DownloadLink from ResearchGate?':
        sched.add_job(getInfoFromResearchGate, 'interval',
                      minutes=6,
                      next_run_time=datetime.now(),  # start immediately
                      id='dl_research_job',
                      #  end_date=datetime.now() + timedelta(hours=1)
                      #   end_date=datetime.now() + timedelta(minutes=30)
                      )

        # !Inner Func: register event listener

    def execution_listener(event):
        if event.exception:
            print('The job crashed')
            return

        # console.log('The job executed successfully')
        job = sched.get_job(event.job_id)
        print()
        try:
            if job.id == 'info_job':
                # check if there is any paper in the queue
                iw_list = pd.read_csv("data/info/info_waiting.csv")
                if len(iw_list) > 0:
                    console.log(
                        f"[cyan]{len(iw_list)} papers info are waiting to be scraped[/]")
                    console.log(
                        f"[yellow1]Next Job scheduled to be run at: {job.next_run_time}[/]")
                else:
                    console.log(
                        f"[green1]All papers info are scraped[/]")
                    console.log("[italic b red]Terminating Scheduler [/]")
                    sched.shutdown(wait=False)
            elif job.id == 'ref_job':
                # check if there is any paper in the queue
                pw_list = pd.read_csv("data/info/waiting_list_ref.csv")
                if len(pw_list) > 0:
                    console.log(
                        f"[cyan]{len(pw_list)} papers ref are waiting to be scraped[/]")
                    console.log(
                        f"[yellow1]Next Job scheduled to be run at: {job.next_run_time}[/]")
                else:
                    console.log(
                        f"[green1]All papers info are scraped[/]")
                    console.log("[italic b red]Terminating Scheduler [/]")
                    sched.shutdown(wait=False)
            elif job.id == 'semantic_job':
                # wt = pd.read_csv("data/info_ss/waiting_ss.csv")
                # if len(wt) > 0:
                #     console.log(
                #         f"[cyan]{len(wt)} papers are waiting to be scraped[/]")
                console.log(
                    f"[cyan]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Current Time [/]")
                nxt = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                console.log(
                    f"[yellow1]{nxt} | Next Job scheduled to be run[/]")
                print()
                # else:
                #     console.log(
                #         f"[green1]All papers are scraped[/]")
                #     console.log("[italic b red]Terminating Scheduler [/]")
                #     sched.shutdown(wait=False)
            elif job.id == 'dl_semantic_sch_job':
                # print(job.id)
                ss = pd.read_csv("data/info_ss/info_full_ss.csv")
                ss = ss[ss['download_link'].isnull()]
                if len(ss) > 0:
                    console.log(
                        f"[cyan]{len(ss)} papers still missing download links[/]")
                    console.log(
                        f"[cyan]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Current Time [/]")
                    nxt = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                    console.log(
                        f"[yellow1]{nxt} | Next Job scheduled to be run[/]")
                    print()

                else:
                    console.log(
                        f"[green1]All papers are scraped[/]")
                    console.log("[italic b red]Terminating Scheduler [/]")
                    sched.shutdown(wait=False)
            elif job.id == 'dl_research_job':
                console.log(
                    f"[cyan]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Current Time [/]")
                nxt = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                console.log(
                    f"[yellow1]{nxt} | Next Job scheduled to be run[/]")

        except Exception as e:
            console.log("[bright_red]Scheduler Timeout[/]")

            if answers['option'] == 'Get Download Link?':
                pass

            elif answers['option'] == 'Get All References?':
                done_list = pd.read_csv("data/info/done_list_ref.csv")
                done_listLen = done_list.shape[0]
                if done_listLen > oldRefDoneLen:
                    newRefAdded = done_listLen - oldRefDoneLen
                    process = subprocess.Popen(
                        ["git", "cm", f"{newRefAdded} refs Added [automated commit]"], stdout=subprocess.PIPE)
                    # output = process.communicate()[0]
                    console.log(f"{newRefAdded} refs Added [automated commit]")

            elif answers['option'] == 'Get Paper Info?':
                info_done = pd.read_csv("data/info/info_done.csv")
                info_doneLen = info_done.shape[0]
                if info_doneLen > oldInfoDoneLen:
                    newInfoAdded = info_doneLen - oldInfoDoneLen
                    process = subprocess.Popen(
                        ["git", "cm", f"{newInfoAdded} Info Added [automated commit]"], stdout=subprocess.PIPE)
                    # output = process.communicate()[0]
                    console.log(
                        f"{newInfoAdded} Info Added [automated commit]")

            elif answers['option'] == 'Get Info Using Semantic Sch. Api?':
                ss_info = pd.read_csv("data/info_ss/info_full_ss.csv")
                ss_wtLen = ss_info.shape[0]
                if ss_wtLen > oldSSInfoLen:
                    newSSAdded = ss_wtLen - oldSSInfoLen
                    process = subprocess.Popen(
                        ["git", "cm", f"{newSSAdded} Info Added [automated commit]"], stdout=subprocess.PIPE)
                    # output = process.communicate()[0]
                    console.log(
                        f"{newSSAdded} Info Added [automated commit]")

            elif answers['option'] == 'Get DownloadLinks From Semantic Sch.?':
                ss_info = pd.read_csv("data/info_ss/info_full_ss.csv")
                ss_info = ss_info[ss_info['download_link'].isnull()]
                newDlSSLen = ss_info.shape[0]
                processed = abs(newDlSSLen - oldDlSSLen)
                process = subprocess.Popen(
                    ["git", "cm", f"{processed} Download Links Proceeded [automated commit]"], stdout=subprocess.PIPE)
                # output = process.communicate()[0]
                console.log(
                    f"{processed} Download Links Proceeded [automated commit]")

            sched.shutdown(wait=False)

    sched.print_jobs()
    sched.add_listener(execution_listener,
                       EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    sched.start()


def App():
    questions = [
        inquirer.List('job',
                      message="Run Scheduled Job?",
                      choices=['Yes', 'No'],
                      default='Yes'
                      ),
        inquirer.List('option',
                      message="What do you want to do?",
                      choices=['Get Download Link?',
                               'Get Paper Info?',
                               'Get Info Using Semantic Sch. Api?',
                               'Get DownloadLinks From Semantic Sch.?',
                               'Get All References?',
                               'Get DownloadLink from ResearchGate?'],
                      default='Get Paper Info?'
                      ),
    ]
    answers = inquirer.prompt(questions)
    if answers['job'] == 'Yes':
        startJob(answers)
    else:
        if answers['option'] == 'Get Download Link?':
            getDownLinks()
        elif answers['option'] == 'Get All References?':
            getRefsComplete()
        elif answers['option'] == 'Get Paper Info?':
            paperInfo()
        elif answers['option'] == 'Get Info Using Semantic Sch. Api?':
            handleSemanticApi()
        elif answers['option'] == 'Get DownloadLinks From Semantic Sch.?':
            getDownloadLinksForSemanticS()
        elif answers['option'] == 'Get DownloadLink from ResearchGate?':
            getInfoFromResearchGate()


if __name__ == '__main__':
    App()
