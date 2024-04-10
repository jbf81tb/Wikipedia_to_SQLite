import requests
from dataclasses import dataclass
import datetime as dt
import time
import html2text
import sqlite3
from pathlib import Path

@dataclass
class page_data:
    time_fetched: dt.datetime
    most_recent_editor: str
    markdown: str
    url: str
    title: str

# Define the Wikipedia API endpoint
endpoint = "https://en.wikipedia.org/w/api.php"

def get_20_most_viewed_articles() -> list:
    params = {
        "action": "query",
        "format": "json",
        "list": "mostviewed",
        "pvimlimit": "30",  # get more than 20 in order to grab articles and skip meta-pages like "search"
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    url_fstring = lambda title: f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

    pages = []
    for item in data["query"]["mostviewed"]:
        # ns = 0 are articles. 
        # technically, the main page is an article, but we'll skip it because it seems against the spirit
        if item["ns"] != 0 or item["title"] == "Main Page": continue
        pages.append(page_data(None, None, None, url_fstring(item["title"]), item["title"]))
        if len(pages) == 20: break
    
    return pages

def update_page_data(pages: list) -> None:
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "user",
        "rvslots": "main",
        "titles": None,
        "rvlimit": "1",
    }

    for page in pages:
        params['titles'] = page.title
        response = requests.get(endpoint, params=params)
        data = response.json()
        query_pages = list(data["query"]["pages"].values())
        page.most_recent_editor = query_pages[0]["revisions"][0]["user"] # only one page in the list
        html = requests.get(page.url).text
        page.time_fetched = dt.datetime.now()
        page.markdown = html2text.html2text(html)
        time.sleep(.1) # be nice to the API

def create_db(pages: list) -> Path:
    cdir = Path(__file__)
    outPath = cdir.parent / "pages.db"

    conn = sqlite3.connect(outPath)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS pages")
    c.execute("\n".join([
        "CREATE TABLE pages (",
        "  time_fetched TEXT,"
        "  most_recent_editor TEXT,"
        "  markdown TEXT,"
        "  url TEXT"
        ")",
    ]))

    for page in pages:
        c.execute("\n".join([
            "INSERT INTO pages",
            "VALUES (?, ?, ?, ?)"
        ]), 
        (
            # convert datetime to ISO 8601 format
            page.time_fetched.isoformat(), 
            page.most_recent_editor, 
            page.markdown, 
            page.url
        )
    )
    conn.commit()
    conn.close()

    return outPath

def main(verbose: bool) -> None:
    if verbose:
        print("Fetching the 20 most viewed Wikipedia articles...")
    pages = get_20_most_viewed_articles()

    if verbose:
        print("Fetching the most recent editor and page content...")
    update_page_data(pages)
    
    if verbose:
        print("Creating a SQLite database...")
    dbPath = create_db(pages)
    if verbose:
        print(f"SQLite database created as {dbPath.resolve()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch and store the 20 most viewed Wikipedia articles.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print the path to the SQLite database.")
    args = parser.parse_args()

    main(args.verbose)