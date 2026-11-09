"""
Tests for topic deduplication and hash computation.
"""

from database.db import Database, compute_content_hash, normalize_string


def test_normalize_string():
    assert normalize_string("The Rule of 72: How Fast?!") == "the rule of 72 how fast"
    assert normalize_string("  Spacing   Test   ") == "spacing test"


def test_compute_content_hash_deterministic():
    h1 = compute_content_hash("The Rule of 72", "Compound interest shortcut")
    h2 = compute_content_hash("The Rule of 72", "Compound interest shortcut")
    h3 = compute_content_hash("The Rule of 72!!", "compound interest shortcut")
    assert h1 == h2
    assert h1 == h3


def test_database_check_duplicate_topic():
    db = Database(":memory:")
    title = "The Rule of 72: How Fast Your Money Doubles"
    summary = "Mathematical shortcut for doubling investments."

    # Initial check: not duplicate
    assert not db.check_duplicate_topic(title, summary, lookback_days=30)

    # Insert topic
    db.insert_topic({
        "title": title,
        "summary": summary,
        "category": "money_secrets",
    })

    # Subsequent check: should be flagged as duplicate
    assert db.check_duplicate_topic(title, summary, lookback_days=30)
    # Even with minor punctuation changes
    assert db.check_duplicate_topic("The Rule of 72: How Fast Your Money Doubles!", summary, lookback_days=30)
