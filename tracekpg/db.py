import sqlite3
from pathlib import Path
from tracekpg.config import DB_FILENAME, SCHEMA_FILE, SEARCH_RESULT_LIMIT

# every SQL statement in the project lives in this file, behind a named function.


def get_connection(db_path=DB_FILENAME):
    Path(db_path).parent.mkdir(parents = True, exist_ok = True)
    conn = sqlite3.connect(db_path)
    # rows come back as sqlite3.Row, so callers can use row["title"] instead of row[1].
    conn.row_factory = sqlite3.Row
    # SQLite ignores FOREIGN KEY constraints unless this is switched on, for every connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    schema = Path(SCHEMA_FILE).read_text()
    conn.executescript(schema)
    conn.commit()


# --- documents ---

# returns True if the document was inserted, False if a document with that title already exists.
def insert_document(conn, title, source_url, fetched_at, raw_text):
    cur = conn.execute(
        "INSERT OR IGNORE INTO documents (title, source_url, fetched_at, raw_text) VALUES (?, ?, ?, ?)",
        (title, source_url, fetched_at, raw_text),
    )
    return cur.rowcount == 1


def count_documents(conn):
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


# returns the document as a dict, or None if no document has that id.
def get_document(conn, doc_id):
    row = conn.execute(
        "SELECT id, title, source_url, fetched_at, raw_text FROM documents WHERE id = ?",
        (doc_id,),
    ).fetchone()
    return dict(row) if row else None


# case-insensitive match on title or text; returns id and title only, since raw_text is large.
def search_documents_by_keyword(conn, keyword, limit=SEARCH_RESULT_LIMIT):
    pattern = f"%{keyword}%"
    rows = conn.execute(
        "SELECT id, title FROM documents WHERE title LIKE ? OR raw_text LIKE ? ORDER BY title LIMIT ?",
        (pattern, pattern, limit),
    ).fetchall()
    return [dict(row) for row in rows]


# --- mentions ---

# returns the new mention's id. Raises sqlite3.IntegrityError if document_id doesn't exist.
def insert_mention(conn, document_id, surface_text, entity_type, char_offset=None):
    cur = conn.execute(
        "INSERT INTO mentions (document_id, surface_text, entity_type, char_offset) VALUES (?, ?, ?, ?)",
        (document_id, surface_text, entity_type, char_offset),
    )
    return cur.lastrowid


# inserts many mentions in one call; each row is (document_id, surface_text, entity_type, char_offset).
def insert_mentions(conn, rows):
    conn.executemany(
        "INSERT INTO mentions (document_id, surface_text, entity_type, char_offset) VALUES (?, ?, ?, ?)",
        rows,
    )


MENTIONS_FOR_DOCUMENT_SQL = "SELECT id, document_id, surface_text, entity_type, char_offset, entity_id FROM mentions WHERE document_id = ? ORDER BY char_offset"


def get_mentions_for_document(conn, document_id):
    rows = conn.execute(MENTIONS_FOR_DOCUMENT_SQL, (document_id,)).fetchall()
    return [dict(row) for row in rows]


# JOIN: each mention row is paired with the documents row whose id matches its document_id.
def get_mentions_with_document_titles(conn):
    rows = conn.execute(
        """
        SELECT mentions.id, mentions.surface_text, mentions.entity_type, documents.title
        FROM mentions
        JOIN documents ON documents.id = mentions.document_id
        ORDER BY documents.title, mentions.char_offset
        """
    ).fetchall()
    return [dict(row) for row in rows]


# --- index (used by the Day 4 benchmark) ---

def create_mentions_index(conn):
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mentions_doc ON mentions(document_id)")


def drop_mentions_index(conn):
    conn.execute("DROP INDEX IF EXISTS idx_mentions_doc")


# returns SQLite's plan for get_mentions_for_document, e.g. "SCAN mentions" or "SEARCH mentions USING INDEX ...".
def explain_mentions_query(conn, document_id):
    rows = conn.execute("EXPLAIN QUERY PLAN " + MENTIONS_FOR_DOCUMENT_SQL, (document_id,)).fetchall()
    return " | ".join(row["detail"] for row in rows)
