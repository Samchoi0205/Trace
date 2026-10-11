import sqlite3
from pathlib import Path
from tracekpg.config import DB_FILENAME, SCHEMA_FILE

# every SQL statement in the project lives in this file, behind a named function.


def get_connection(db_path=DB_FILENAME):
    Path(db_path).parent.mkdir(parents = True, exist_ok = True)
    conn = sqlite3.connect(db_path)
    # SQLite ignores FOREIGN KEY constraints unless this is switched on, for every connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    schema = Path(SCHEMA_FILE).read_text()
    conn.executescript(schema)
    conn.commit()


# returns True if the document was inserted, False if a document with that title already exists.
def insert_document(conn, title, source_url, fetched_at, raw_text):
    cur = conn.execute(
        "INSERT OR IGNORE INTO documents (title, source_url, fetched_at, raw_text) VALUES (?, ?, ?, ?)",
        (title, source_url, fetched_at, raw_text),
    )
    return cur.rowcount == 1


def count_documents(conn):
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
