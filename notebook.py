#%%
import requests
from dataclasses import dataclass
import datetime as dt
import time

@dataclass
class page_data:
    time_fetched: dt.datetime
    most_recent_editor: str
    html: str
    markdown: str
    url: str
    title: str

# Define the Wikipedia API endpoint
endpoint = "https://en.wikipedia.org/w/api.php"

#%% First get list of most viewed articles
params = {
    "action": "query",
    "format": "json",
    "list": "mostviewed",
    "pvimlimit": "30",  # get more than 20 in order to grab articles and skip meta-pages like "search"
}

response = requests.get(endpoint, params=params)
data = response.json()
#%%
url_fstring = lambda title: f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

pages = []
for item in data["query"]["mostviewed"]:
    # ns = 0 are articles. 
    # technically, the main page is an article, but we'll skip it because it seems against the spirit
    if item["ns"] != 0 or item["title"] == "Main Page": continue
    pages.append(page_data(None, None, None, None, url_fstring(item["title"]), item["title"]))
    if len(pages) == 20: break
    

# %%
pages
# %%
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
    page.html = requests.get(page.url).text
    page.time_fetched = dt.datetime.now()
    time.sleep(.2) # be nice to the API
    


# %%
import html2text

h = html2text.HTML2Text()
with open("page.md", "w", encoding="utf-8") as f:
    f.write(h.handle(pages[0].html))
# %%
import sqlite3

# create a sqlite3 database with the values of pages
conn = sqlite3.connect("pages.db")
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

