"""
Tests for quality control, factual safeguards, and editorial gates.
"""

from ai.quality_check import check_script_quality
from research.score_topics import score_topic


def test_quality_check_detects_forbidden_superlatives():
    bad_script = {
        "format": "reel",
        "script": "Scientists are baffled by this shocking discovery that guarantees you get rich quick! " * 10,
        "caption": "Valid caption for testing.",
        "storyboard_json": [{"scene": 1}] * 6,
    }
    qa = check_script_quality(bad_script)
    assert not qa["passed"]
    assert any("scientists are baffled" in err for err in qa["errors"])


def test_quality_check_validates_duration_and_word_count():
    # Too short
    too_short = {
        "format": "reel",
        "script": "Just twenty words here not enough content to fill a vertical reel video.",
        "caption": "Caption here.",
        "storyboard_json": [{"scene": 1}] * 6,
    }
    qa_short = check_script_quality(too_short)
    assert not qa_short["passed"]
    assert any("too short" in err for err in qa_short["errors"])

    # Approved script
    valid_script = {
        "format": "reel",
        "script": (
            "Most people misunderstand how the rule of seventy two shapes their financial future. "
            "When dealing with compounding, small percentages make massive differences. "
            "To estimate how fast your money doubles, divide seventy two by your annual interest rate. "
            "At eight percent, your capital doubles in nine years. "
            "Understanding this principle shifts you from losing to inflation to building wealth. "
            "Have you applied this math to your portfolio yet? Save this for later."
        ),
        "caption": "A deep dive into compound interest math. #curiodaily #money",
        "storyboard_json": [{"scene_number": i} for i in range(1, 7)],
    }
    qa_valid = check_script_quality(valid_script)
    assert qa_valid["passed"]
    assert len(qa_valid["errors"]) == 0


def test_score_topic_threshold():
    topic = {
        "title": "Why Solid-State Batteries Will Double EV Range",
        "summary": "Solid-state electrolytes replace flammable liquid solutions, offering 2x energy density.",
        "category": "future_is_here",
    }
    sources = [{"source_class": "primary", "url": "https://nature.com/articles/123"}]
    claims = [{"claim_text": "2x energy density", "verification_status": "verified"}]

    res = score_topic(topic, sources, claims)
    assert res["total_score"] >= 70
    assert res["passed_threshold"]
