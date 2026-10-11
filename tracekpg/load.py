from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from tracekpg.config import DATA_DIR, DB_FILENAME, WIKI_ARTICLE_BASE_URL
from tracekpg import db

# reads every saved article in DATA_DIR and inserts it into the documents table — re-running skips documents already loaded.


def load_documents(data_dir=DATA_DIR, db_path=DB_FILENAME):
    conn = db.get_connection(db_path)
    db.init_db(conn)

    files = sorted(Path(data_dir).glob("*.txt"))
    inserted = 0

    for file_path in files:
        # Wikipedia treats "Lockheed_Martin" and "Lockheed Martin" as the same title.
        title = file_path.stem.replace("_", " ")
        source_url = WIKI_ARTICLE_BASE_URL + quote(title.replace(" ", "_"))
        # the fetcher didn't record when it downloaded each file, so the file's modified time stands in.
        fetched_at = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        raw_text = file_path.read_text()

        if db.insert_document(conn, title, source_url, fetched_at, raw_text):
            inserted += 1

    conn.commit()
    total = db.count_documents(conn)
    conn.close()

    print(f"Inserted {inserted} new documents ({len(files)} files, {total} in database)")


if __name__ == "__main__":
    load_documents()
