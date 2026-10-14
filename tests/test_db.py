import sqlite3
import pytest
from tracekpg import db
from tracekpg.load import load_documents


def make_db(tmp_path):
    conn = db.get_connection(str(tmp_path / "test.db"))
    db.init_db(conn)
    return conn


def test_init_db_can_run_twice(tmp_path):
    conn = make_db(tmp_path)
    db.init_db(conn)
    assert db.count_documents(conn) == 0


def test_insert_document(tmp_path):
    conn = make_db(tmp_path)
    assert db.insert_document(conn, "Anduril Industries", "url", "2026-10-10", "text")
    assert db.count_documents(conn) == 1


def test_duplicate_title_is_ignored(tmp_path):
    conn = make_db(tmp_path)
    db.insert_document(conn, "Anduril Industries", "url", "2026-10-10", "text")
    assert not db.insert_document(conn, "Anduril Industries", "url", "2026-10-10", "text")
    assert db.count_documents(conn) == 1


def test_load_documents_is_idempotent(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "Anduril Industries.txt").write_text("Anduril makes drones.")
    (raw_dir / "Lockheed_Martin.txt").write_text("Lockheed makes jets.")
    db_path = str(tmp_path / "test.db")

    load_documents(str(raw_dir), db_path)
    load_documents(str(raw_dir), db_path)

    conn = db.get_connection(db_path)
    assert db.count_documents(conn) == 2


def add_document(conn, title="Anduril Industries", text="Anduril makes drones."):
    db.insert_document(conn, title, "url", "2026-10-10", text)
    return db.search_documents_by_keyword(conn, title)[0]["id"]


def test_get_document_returns_dict(tmp_path):
    conn = make_db(tmp_path)
    doc_id = add_document(conn)
    doc = db.get_document(conn, doc_id)
    assert doc["title"] == "Anduril Industries"
    assert doc["raw_text"] == "Anduril makes drones."


def test_get_document_missing_returns_none(tmp_path):
    conn = make_db(tmp_path)
    assert db.get_document(conn, 999) is None


def test_insert_and_get_mentions_in_offset_order(tmp_path):
    conn = make_db(tmp_path)
    doc_id = add_document(conn)
    db.insert_mention(conn, doc_id, "Palmer Luckey", "person", 40)
    db.insert_mention(conn, doc_id, "Anduril", "org", 0)

    mentions = db.get_mentions_for_document(conn, doc_id)

    assert [m["surface_text"] for m in mentions] == ["Anduril", "Palmer Luckey"]
    assert all(m["entity_id"] is None for m in mentions)


def test_mention_for_missing_document_is_rejected(tmp_path):
    conn = make_db(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_mention(conn, 999, "Nobody", "person", 0)


def test_join_returns_document_title_with_each_mention(tmp_path):
    conn = make_db(tmp_path)
    anduril = add_document(conn)
    lockheed = add_document(conn, "Lockheed Martin", "Lockheed makes jets.")
    db.insert_mention(conn, anduril, "Palmer Luckey", "person", 0)
    db.insert_mention(conn, lockheed, "Jim Taiclet", "person", 0)

    rows = db.get_mentions_with_document_titles(conn)

    assert {(r["surface_text"], r["title"]) for r in rows} == {
        ("Palmer Luckey", "Anduril Industries"),
        ("Jim Taiclet", "Lockheed Martin"),
    }


def test_search_is_case_insensitive_and_matches_text(tmp_path):
    conn = make_db(tmp_path)
    add_document(conn)
    add_document(conn, "Lockheed Martin", "Lockheed makes jets.")
    assert [r["title"] for r in db.search_documents_by_keyword(conn, "DRONES")] == ["Anduril Industries"]


def test_search_treats_quotes_as_text_not_sql(tmp_path):
    conn = make_db(tmp_path)
    add_document(conn, "O'Gara Group", "Armored vehicles.")
    assert [r["title"] for r in db.search_documents_by_keyword(conn, "O'Gara")] == ["O'Gara Group"]
    assert db.search_documents_by_keyword(conn, "' OR '1'='1") == []


def test_mentions_query_uses_index(tmp_path):
    conn = make_db(tmp_path)
    assert "USING INDEX idx_mentions_doc" in db.explain_mentions_query(conn, 1)
