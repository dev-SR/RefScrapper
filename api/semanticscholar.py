from dataclasses import dataclass
from collections import deque
from uuid import uuid4
from time import sleep
import requests
from pprint import pprint
import pandas as pd

from utils.loader import withLoader, withLoaderWithParam, console, withLoaderWithParamNew


@dataclass
class Paper:
    uuid: str
    paper_id: str
    parent_id: str
    title: str
    reference_count: int = 0
    citation_count: int = 0
    influential_citation_count: int = 0
    published_date: str = None
    paper_type: str = None
    venue: str = None
    # isOpenAccess: bool = False
    abstract: str = None
    paper_link: str = None
    doi: str = None
    download_link: str = None
    tldr: str = None
    embedding: str = None


class SemanticScholar:
    def __init__(self,
                 api_key=None,
                 waiting_list_path="data/info_ss/waiting_ss.csv",
                 not_found_path="data/info_ss/not_found_ss.csv",
                 final_csv_path="data/info_ss/info_full_ss.csv"):
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper"
        self.waiting_list_path = waiting_list_path
        self.not_found_path = not_found_path
        self.final_csv_path = final_csv_path

    def searchPaperByQuery(self, query):
        endpoint = self.getEndpointForSearch(query)
        res = requests.get(**endpoint)
        self.processSearchResult(res.json().get("data"))

    def getEndpointForSearch(self, query):
        param = {
            "query": query,
            "fields": "paperId,url,title,venue,year,referenceCount,citationCount,influentialCitationCount,abstract",
        }
        return {
            "url": f"{self.base_url}/search",
            "params": param
        }

    def savePaperDetails(self, n=1, sleep_time=0):

        wt = pd.read_csv(self.waiting_list_path)
        next_papers = wt[wt['paper_id'].notnull()][:n]
        next_papers_list = next_papers.to_dict('records')
        q = deque(next_papers_list)
        if n > len(next_papers_list):
            n = len(next_papers_list)
        console.log(f"Fetching {n} at a time")

        while q:
            p = q.popleft()
            # endpoint = self.getEndpointForPaperDetails(p['paper_id'])
            # res = requests.get(**endpoint)
            uuid = p['uuid']
            parent_id = p['parent_id']
            paper_id = p['paper_id']
            paper_title = p['title']

            titleLen = len(paper_title)
            if titleLen > 50:
                paper_title = paper_title[:50] + "..."
            else:
                titleLen = titleLen
                paper_title = paper_title + "." * (53 - titleLen)

            [code, msg, res_data] = withLoaderWithParam(
                self.makeRequest, [paper_id], f"GET: {paper_title}")
            if code != 200:
                console.log(f"[red]Error: uuid:{uuid}; {code}: {msg}")
            if code == 429:
                q.clear()
                break
            if code == 404:
                self.sendToNotFound(p)
                continue

            paperDf = self.processPaperDetails(
                res_data, parent_id=parent_id, uuid=uuid)
            # withLoaderWithParam(
            #     sleep, [s], f"Saving paper: {paper_title}", spinner='dots')
            withLoaderWithParamNew(
                self.handleCSV,
                {
                    'paperDf': paperDf,
                    'res_data': res_data,
                    'uuid': uuid,
                    'sleep_time': sleep_time,
                },
                f"Saving paper: {paper_title}",
                spinner='dots')
            console.log(f"[green] Saved paper: {paper_title}")

        console.log(f"[blue] Queue is empty")

    def sendToNotFound(self, p):
        notFoundDf = pd.DataFrame([p])
        notFoundDf.to_csv(self.not_found_path,
                          index=False, header=False, mode="a")
        self.removePaperFromWaitingList(p['uuid'])

    def handleCSV(self, paperDf, res_data, uuid, sleep_time):
        try:
            self.savePaperDetailsToFinalCsv(paperDf)
            self.awaitsReferences(res_data, parent_id=uuid)
            sleep(sleep_time)
            self.removePaperFromWaitingList(uuid)
            sleep(0.1)
        except Exception as e:
            console.log(f"[red] Error saving paper: {e}")

    def makeRequest(self, paper_id):
        endpoint = self.getEndpointForPaperDetails(paper_id)
        res = requests.get(**endpoint)
        return [
            res.status_code,
            res.reason,
            res.json()]

    def getEndpointForPaperDetails(self, paper_id):
        return {
            "url": f"{self.base_url}/{paper_id}",
            "params": {
                "fields": "paperId,url,title,venue,year,referenceCount,citationCount,influentialCitationCount,abstract,tldr,embedding,references",
            }
        }

    def processPaperDetails(self, data, parent_id, uuid):
        embedding = ""
        tldr = ""
        try:
            embedding_model = data['embedding']['model']
            embedding_vector = ''.join(
                [f"{v}," for v in data['embedding']['vector']])
            embedding = embedding_model + ":" + embedding_vector
            tldr_model = data['tldr']['model']
            tldr_text = data['tldr']['text']
            tldr = tldr_model + ":" + tldr_text
        except:
            pass

        p = Paper(
            uuid=uuid,
            paper_id=data["paperId"],
            parent_id=parent_id,
            title=data["title"],
            reference_count=data["referenceCount"],
            citation_count=data["citationCount"],
            influential_citation_count=data["influentialCitationCount"],
            published_date=data["year"],
            paper_type="Unknown",
            venue=data["venue"],
            # isOpenAccess=data["isOpenAccess"],
            abstract=data["abstract"],
            paper_link=data["url"],
            doi="",
            download_link="",
            tldr=tldr,
            embedding=embedding
        )
        return pd.DataFrame([p])

    def savePaperDetailsToFinalCsv(self, paperDf):
        # save to info_full
        paperDf.to_csv(self.final_csv_path,
                       index=False, header=False, mode="a")

    def awaitsReferences(self, res, parent_id):
        refs = res['references']
        papers = [
            {
                'uuid': uuid4(),
                'paper_id': ref['paperId'],
                'parent_id': parent_id,
                'title': ref['title']
            }
            for ref in refs]

        waitingDf = pd.DataFrame(papers)
        self.saveReferencesToWaitingCsv(waitingDf, parent_id)

    def removePaperFromWaitingList(self, uuid):
        wt = pd.read_csv(self.waiting_list_path)
        indx = wt.index[wt['uuid'] == uuid]
        wt.drop(indx, inplace=True)
        wt.to_csv(self.waiting_list_path, index=False)

    def saveReferencesToWaitingCsv(self, waitingDf, paper_id):
        waitingDf.to_csv(self.waiting_list_path,
                         index=False, header=False, mode="a")
        # waitingDf.to_csv(f"data/info_ss/refs/{paper_id}.csv", index=False)

    # def saveRefsDetails(self, paper_id):
    #     # get references for paper
    #     refsDf, waitingDf = self.getReferencesForPaper(paper_id)
    #     self.saveReferencesToFinalCsv(refsDf)
    #     self.saveReferencesToWaitingCsv(waitingDf)

    # def saveReferencesToFinalCsv(self, refsDf):
    #     # save to info_full
    #     refsDf.to_csv("data/info_ss/info_full_ss.csv",
    #                   index=False, header=False, mode="a")

    # def getReferencesForPaper(self, paper_id):
    #     endpoint = self.getEndpointForReferences(paper_id)
    #     res = requests.get(**endpoint)
    #     refsDf = self.processReferences(
    #         res.json().get("data"), parent_id=paper_id)
    #     return refsDf

    def getEndpointForReferences(self, paper_id):
        return {
            "url": f"{self.base_url}/{paper_id}/references",
            "params": {
                "fields": "paperId,url,title,venue,year,referenceCount,citationCount,influentialCitationCount,abstract",
            }
        }

    # def processReferences(self, references, parent_id):
    #     print(f"{len(references)} references found")
    #     waiting_refs = []
    #     refs = []
    #     for ref in references:
    #         cp = ref.get("citedPaper")
    #         if cp['paperId']:
    #             waiting_refs.append(cp['paperId'])
    #         p = Paper(
    #             paper_id=cp["paperId"],
    #             parent_id=parent_id,
    #             title=cp["title"],
    #             reference_count=cp["referenceCount"],
    #             citation_count=cp["citationCount"],
    #             influential_citation_count=cp["influentialCitationCount"],
    #             published_date=cp["year"],
    #             paper_type="",
    #             venue=cp["venue"],
    #             # isOpenAccess=cp["isOpenAccess"],
    #             abstract=cp["abstract"],
    #             paper_link=cp["url"],
    #             download_link=""
    #         )
    #         refs.append(p)
    #     return [pd.DataFrame(refs), pd.DataFrame(waiting_refs)]
