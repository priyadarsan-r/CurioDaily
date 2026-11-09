"""
Tests for publishing flow and idempotency controls.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from database.db import Database
from publishing.instagram_client import InstagramClient
from publishing.publish_reel import publish_reel_post


def test_publishing_idempotency_prevents_duplicate_publish():
    db = Database(":memory:")
    content_id = "test_reel_idempotent"

    # Enqueue and mark published
    db.insert_content({
        "content_id": content_id,
        "format": "reel",
        "category": "money_secrets",
        "script": "Script text",
    })
    qid = db.enqueue_content(content_id, "2026-11-07T00:00:00Z")
    db.update_queue_item(qid, status="published", media_id="ig_media_12345")

    # Calling publish_reel_post should immediately detect already published
    mock_client = MagicMock(spec=InstagramClient)
    res = publish_reel_post(
        content_record={"content_id": content_id},
        video_file_path="mock_path.mp4",
        db=db,
        client=mock_client
    )

    assert res["success"]
    assert res["already_published"]
    # Ensure Instagram API was never called
    mock_client.create_reel_container.assert_not_called()


def test_mock_client_publishing_flow():
    client = InstagramClient()  # No credentials -> mock mode
    container_id = client.create_reel_container("https://example.com/video.mp4", "Caption")
    assert container_id.startswith("mock_container_")

    status = client.poll_container_status(container_id)
    assert status

    media_id = client.publish_container(container_id)
    assert media_id.startswith("mock_media_id_")


def test_emergency_publishing_kill_switch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CURIO_PAUSE_FILE", str(tmp_path / "PAUSE_PUBLISHING"))
    from publishing.publish_queue import is_publishing_paused, set_publishing_pause, process_queue

    # Ensure clean state
    set_publishing_pause(False)
    assert not is_publishing_paused()

    # Activate emergency kill switch
    set_publishing_pause(True)
    assert is_publishing_paused()

    # Verify queue processor halts when paused
    db = Database(":memory:")
    stats = process_queue(db)
    assert stats["paused"] is True
    assert stats["published"] == 0

    # Resume publishing
    set_publishing_pause(False)
    assert not is_publishing_paused()
