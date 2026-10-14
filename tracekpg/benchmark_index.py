import random
import tempfile
import time
from pathlib import Path
from tracekpg.config import BENCHMARK_MENTION_COUNTS, BENCHMARK_MENTIONS_PER_DOCUMENT, BENCHMARK_REPEATS
from tracekpg import db

# times get_mentions_for_document with and without idx_mentions_doc, on a throwaway database of fake rows.


def time_lookups(conn, document_ids):
    start = time.perf_counter()
    for doc_id in document_ids:
        db.get_mentions_for_document(conn, doc_id)
    return time.perf_counter() - start


# documents grow with mentions, so each lookup returns about the same number of rows at every size.
def run_benchmark(num_mentions, repeats=BENCHMARK_REPEATS):
    num_documents = num_mentions // BENCHMARK_MENTIONS_PER_DOCUMENT
    with tempfile.TemporaryDirectory() as tmp:
        conn = db.get_connection(str(Path(tmp) / "benchmark.db"))
        db.init_db(conn)

        for i in range(num_documents):
            db.insert_document(conn, f"Fake Document {i}", None, "2026-01-01", "fake text")

        rng = random.Random(0)
        rows = [(rng.randint(1, num_documents), f"Name {i}", "person", i) for i in range(num_mentions)]
        db.insert_mentions(conn, rows)
        conn.commit()

        # the same random document ids are looked up in both runs, so the only difference is the index.
        lookups = [rng.randint(1, num_documents) for _ in range(repeats)]

        db.drop_mentions_index(conn)
        plan_without = db.explain_mentions_query(conn, 1)
        seconds_without = time_lookups(conn, lookups)

        db.create_mentions_index(conn)
        plan_with = db.explain_mentions_query(conn, 1)
        seconds_with = time_lookups(conn, lookups)

        conn.close()

    print(f"{num_mentions:,} mentions, {repeats} lookups by document_id")
    print(f"  without index: {seconds_without * 1000:8.1f} ms   plan: {plan_without}")
    print(f"  with index:    {seconds_with * 1000:8.1f} ms   plan: {plan_with}")
    print(f"  speed-up:      {seconds_without / seconds_with:8.1f}x")

    return seconds_without, seconds_with


if __name__ == "__main__":
    for num_mentions in BENCHMARK_MENTION_COUNTS:
        run_benchmark(num_mentions)
