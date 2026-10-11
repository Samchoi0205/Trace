import requests
import time
from datetime import datetime
from tracekpg.config import DATA_DIR, USER_AGENT, REQUEST_DELAY_SECONDS, FETCH_LOG_FILE
from pathlib import Path

# takes a Wikipedia article title, fetches it, and saves the text to a file via Wiki API— skipping the fetch entirely if the file already exists.


url = "https://en.wikipedia.org/w/api.php"
headers = {"USER-AGENT" : USER_AGENT}

target_dir = Path(DATA_DIR)
target_dir.mkdir(parents = True, exist_ok = True)


# prints a failure and appends it, timestamped, to the log file so failures survive after the run ends.
def log_failure(message):
    print(message)
    with open(FETCH_LOG_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} {message}\n")


def fetch_article(title):
    file_path = Path(DATA_DIR) / f"{title}.txt"

    if file_path.exists():
        return

    params = {
        "action" : "query",
        "format" : "json" , 
        "titles" : title,
        "prop" : "extracts",
        "explaintext" : "true" , 
        "redirects" : "1",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
    except requests.exceptions.RequestException as e :
        log_failure(f"Request Failed for {title} : {e}")
        return

    time.sleep(REQUEST_DELAY_SECONDS)

    if response.status_code != 200:
        log_failure(f"HTTP {response.status_code} for {title}")
        return 

    try:
        data = response.json()
        pages = data["query"]["pages"]
        page = list(pages.values())[0]
    except (ValueError, KeyError, IndexError) as e:
        log_failure(f"Unexpected response for {title} : {e}")
        return

    text = page.get("extract", "")

    # an empty extract means the page is missing; writing an empty file would make the skip check ignore it forever.
    if not text:
        log_failure(f"No text returned for {title}")
        return

    with open(file_path, "w") as f:
        f.write(text)

def fetch_companies():
    params = {
          "action" : "query",
          "format" : "json",
          "list" : "categorymembers",
          "cmtitle" : "Category:Defense_companies_of_the_United_States",
          "cmlimit" : "250",
     }

    try:
        response = requests.get(url, params=params, headers=headers)
    except requests.exceptions.RequestException as e:
        log_failure(f"Request Failed for category list : {e}")
        return

    if response.status_code != 200:
        log_failure(f"HTTP {response.status_code} for category list")
        return 
    
    try:
        data = response.json()
        pages = data["query"]["categorymembers"]
    except (ValueError, KeyError) as e:
        log_failure(f"Unexpected response for category list : {e}")
        return

    titles = [page["title"] for page in pages if page.get("ns") == 0]

    for i, title in enumerate(titles, start=1):
        print(f"{i}/{len(titles)}: {title}")
        fetch_article(title)
    
    

if __name__ == "__main__":
    fetch_companies()