from scrapper.tile_abstract import TitleNAbstractGrabber
import pandas as pd
import argparse
import glob
from utils.loader import (
    console,
    withLoader,
    withLoaderWithParam,
    withLoaderWithParamNew,
)

"""
data/authors.csv:
name,profile_link,done
X,https://www.researchgate.net/profile/X/research,0

Usage:
python run2.py -H -t -a
-t : grab all paper titles with links ; save in `data/paper_titles_abs` folder
-a : grab abstract titles with links ; save in `data/paper_titles_abs` folder


 """
# python run2.py -H -a
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--title", action="store_true", help="Fetch titles")
parser.add_argument("-a", "--abstract", action="store_true", help="Fetch abstracts")
parser.add_argument(
    "-H", "--headless", action="store_true", help="Run in headless mode"
)

# Parse the command-line arguments
args = parser.parse_args()

isTitle = args.title
isAbstract = args.abstract
isHeadless = args.headless


def main():
    first_non_blocked_user = None
    auth_df = None
    try:
        auth_df = pd.read_csv("data/info/auth.csv")
        first_non_blocked_user = auth_df[auth_df["blocked"] == 0].iloc[0].to_dict()
    except:
        if not first_non_blocked_user:
            print("[red] No users found [/]")
        if not auth_df:
            console.log("File not found : data/info/auth.csv")
            console.log(
                """
                Please create a file with the following format:

                email,password,blocked
                X@edu.ac.bd,researchgate,0
            """
            )
    if not first_non_blocked_user:
        return

    email, password = (
        first_non_blocked_user["email"],
        first_non_blocked_user["password"],
    )

    with TitleNAbstractGrabber(headless=isHeadless) as bot:
        withLoader(bot.land_home_page, "Home Page")
        withLoaderWithParamNew(
            bot.login, {"email": email, "password": password}, "Logging in", "dots"
        )
        if isTitle:
            profiles = pd.read_csv("data/info/authors.csv")
            profiles_queue = profiles.query("done == 0")
            profiles_dictArr = profiles_queue.to_dict(orient="records")
            for profile in profiles_dictArr:
                withLoaderWithParamNew(
                    bot.land_on_page, {"url": profile["profile_link"]}, "Home Page"
                )
                # withLoaderWithParamNew(
                #     bot.test,
                #     {
                #         "save_in": f"data/paper_titles_abs/{profile['name']}.csv",
                #         "author_name": profile["name"],
                #     },
                #     "Home Page",
                # )
                # break
                withLoader(bot.keepScrollingToBottom, "Scrolling down")
                withLoader(bot.handleShowMore, "Scrolling down")
                done = withLoaderWithParamNew(
                    bot.fetchTitles,
                    {
                        "save_in": f"data/paper_titles_abs/{profile['name']}.csv",
                        "author_name": profile["name"],
                    },
                    "Fetching Titles",
                )
                # update done ==1 and save csv
                if done:
                    profiles.loc[profiles["name"] == profile["name"], "done"] = 1
                    profiles.to_csv("data/info/authors.csv", index=False)

        if isAbstract:
            authors = glob.glob("data/paper_titles_abs/*")
            for author_path in authors:
                print()
                print(author_path)
                print()
                # author_df = pd.read_csv("data/paper_titles_abs/Dr. Faiz Al Faisal.csv")
                try:
                    author_df = pd.read_csv(author_path)
                except Exception as e:
                    print(f"author file error :{author_path}")
                    print(e)
                save_author = author_df.copy()
                author_df = author_df.query("done == 0")
                papers = author_df.to_dict(orient="records")
                try:
                    for paper in papers:
                        paper_title = paper["paper_title"]
                        paper_link = paper["paper_link"]
                        withLoaderWithParamNew(
                            bot.land_on_page,
                            {"url": paper_link},
                            "Landing on paper page",
                        )
                        abstract = withLoaderWithParamNew(
                            bot.fetchAbstracts,
                            {"paper_link": paper_link},
                            "Fetching abstract",
                        )
                        # update abstract and done
                        save_author.loc[
                            save_author["paper_title"] == paper_title, "abstract"
                        ] = abstract
                        save_author.loc[
                            save_author["paper_title"] == paper_title, "done"
                        ] = 1
                        # break
                except Exception as e:
                    print(e)
                save_author.to_csv(author_path, index=False)


if __name__ == "__main__":
    main()
