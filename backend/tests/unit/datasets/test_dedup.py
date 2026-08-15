from app.datasets.dedup import content_hash, dedupe


def test_exact_duplicate_removed_keeps_first():
    records = ["a", "b", "a", "c"]
    kept, removed = dedupe(records)
    assert kept == ["a", "b", "c"]
    assert removed == ["a"]


def test_distinct_records_kept():
    records = ["x", "y", "z"]
    kept, removed = dedupe(records)
    assert kept == ["x", "y", "z"]
    assert removed == []


def test_order_preserved():
    records = ["b", "a", "b", "c", "a"]
    kept, _ = dedupe(records)
    assert kept == ["b", "a", "c"]


def test_content_hash_stable():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("Hello")


def test_dedupe_against_existing_hashes():
    records = ["a", "b"]
    kept, removed = dedupe(records, existing_hashes={content_hash("a")})
    assert kept == ["b"]
    assert removed == ["a"]
