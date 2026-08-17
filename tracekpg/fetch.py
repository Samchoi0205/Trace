import requests
from tracekpg.config import DATA_DIR, USER_AGENT
from pathlib import Path

# takes a Wikipedia article title, fetches it, and saves the text to a file via Wiki API— skipping the fetch entirely if the file already exists.

url = "https://en.wikipedia.org/w/api.php"
headers = {"USER-AGENT" : USER_AGENT}

target_dir = Path(DATA_DIR)
target_dir.mkdir(parents = True, exist_ok = True)

def fetch_article(title):
    file_path = Path(DATA_DIR) / f"{title}.txt"

    if file_path.exists():
        return

    params = {
        "action" : "query",
        "format" : "json",
        "titles" : title,
        "prop" : "extracts",
        "explaintext" : "true" , 
    }

    try: 
        response = requests.get(url, params=params, headers=headers)
    except requests.exceptions.RequestException as e :
        print(f"Request Failed for {title} : {e}")
        return 

    if response.status_code != 200:
        print("Access Denied")
        return 

    data = response.json()
    pages = data["query"]["pages"]
    page = list(pages.values())[0]
    text = page.get("extract", "")

    with open(file_path, "w") as f:
        f.write(text)

if __name__ == "__main__":
        fetch_article("Lockheed_Martin")