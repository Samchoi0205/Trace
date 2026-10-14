-- IF NOT EXISTS lets init_db() run more than once without failing.

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    source_url TEXT,
    fetched_at TEXT NOT NULL,
    raw_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL
);

-- entity_id starts NULL and is filled in by entity resolution (Days 7-9).
-- char_offset is nullable because the model may not give a reliable position.
CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    surface_text TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    char_offset INTEGER,
    entity_id INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    subject_mention_id INTEGER NOT NULL,
    predicate TEXT NOT NULL,
    object_text TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (subject_mention_id) REFERENCES mentions(id)
);

-- lets the database jump straight to one document's mentions instead of scanning every row.
CREATE INDEX IF NOT EXISTS idx_mentions_doc ON mentions(document_id);
