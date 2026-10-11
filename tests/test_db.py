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
