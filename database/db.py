"""
Database interface for the Zero-Budget Content Engine using SQLite.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "content_engine.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def normalize_string(text: str) -> str:
    """Normalize text for hash generation and deduplication."""
    cleaned = "".join(c.lower() for c in text if c.isalnum() or c.isspace())
    return " ".join(cleaned.split())


def compute_content_hash(title: str, summary: str = "") -> str:
    """Create a deterministic SHA-256 hash for deduplication."""
    normalized = f"{normalize_string(title)}::{normalize_string(summary)}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class Database:
    """SQLite Database helper class with connection management and repository queries."""

    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path == ":memory:":
            self.db_path = Path(":memory:")
            self._is_memory = True
            self._mem_conn: Optional[sqlite3.Connection] = None
        else:
            self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
            self._is_memory = False
            self._mem_conn = None
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if self._is_memory:
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
                self._mem_conn.execute("PRAGMA foreign_keys = ON;")
            return self._mem_conn

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        """Initialize database tables from schema.sql if they don't exist."""
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema_sql)

    # ---------------------------------------------------------
    # Topic Operations
    # ---------------------------------------------------------
    def insert_topic(self, topic: Dict[str, Any]) -> str:
        topic_id = topic.get("topic_id") or hashlib.md5(f"{topic.get('title')}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        discovered_at = topic.get("discovered_at") or datetime.now(timezone.utc).isoformat()
        content_hash = topic.get("content_hash") or compute_content_hash(topic.get("title", ""), topic.get("summary", ""))

        sql = """
        INSERT OR REPLACE INTO topics (
            topic_id, title, normalized_title, category, summary,
            discovered_at, source_url, source_type, topic_score,
            status, content_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (
                topic_id,
                topic.get("title"),
                normalize_string(topic.get("title", "")),
                topic.get("category"),
                topic.get("summary", ""),
                discovered_at,
                topic.get("source_url"),
                topic.get("source_type", "rss"),
                topic.get("topic_score", 0),
                topic.get("status", "discovered"),
                content_hash
            ))
        return topic_id

    def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM topics WHERE topic_id = ?;"
        with self.get_connection() as conn:
            row = conn.execute(sql, (topic_id,)).fetchone()
            return dict(row) if row else None

    def get_topics_by_status(self, status: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM topics WHERE status = ?"
        params: List[Any] = [status]
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY topic_score DESC, discovered_at DESC;"
        with self.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def update_topic_status(self, topic_id: str, status: str, score: Optional[int] = None) -> None:
        if score is not None:
            sql = "UPDATE topics SET status = ?, topic_score = ? WHERE topic_id = ?;"
            params = (status, score, topic_id)
        else:
            sql = "UPDATE topics SET status = ? WHERE topic_id = ?;"
            params = (status, topic_id)
        with self.get_connection() as conn:
            conn.execute(sql, params)

    def check_duplicate_topic(self, title: str, summary: str = "", lookback_days: int = 30) -> bool:
        """Check if topic hash exists within lookback_days."""
        content_hash = compute_content_hash(title, summary)
        normalized = normalize_string(title)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

        sql = """
        SELECT 1 FROM topics
        WHERE (content_hash = ? OR normalized_title = ?)
        AND discovered_at >= ?
        LIMIT 1;
        """
        with self.get_connection() as conn:
            row = conn.execute(sql, (content_hash, normalized, cutoff)).fetchone()
            return row is not None

    # ---------------------------------------------------------
    # Sources Operations
    # ---------------------------------------------------------
    def insert_source(self, source: Dict[str, Any]) -> str:
        source_id = source.get("source_id") or hashlib.md5(f"{source.get('url')}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        retrieved_at = source.get("retrieved_at") or datetime.now(timezone.utc).isoformat()

        sql = """
        INSERT OR REPLACE INTO sources (
            source_id, topic_id, url, title, publisher,
            published_at, retrieved_at, source_class, reliability_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (
                source_id,
                source.get("topic_id"),
                source.get("url"),
                source.get("title", ""),
                source.get("publisher", ""),
                source.get("published_at"),
                retrieved_at,
                source.get("source_class", "secondary"),
                source.get("reliability_notes", "")
            ))
        return source_id

    def get_sources_by_topic(self, topic_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM sources WHERE topic_id = ? ORDER BY retrieved_at ASC;"
        with self.get_connection() as conn:
            rows = conn.execute(sql, (topic_id,)).fetchall()
            return [dict(r) for r in rows]

    # ---------------------------------------------------------
    # Claims Operations
    # ---------------------------------------------------------
    def insert_claim(self, claim: Dict[str, Any]) -> str:
        claim_id = claim.get("claim_id") or hashlib.md5(f"{claim.get('claim_text')}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        supporting = claim.get("supporting_source_ids", [])
        if isinstance(supporting, list):
            supporting = json.dumps(supporting)

        sql = """
        INSERT OR REPLACE INTO claims (
            claim_id, topic_id, claim_text, supporting_source_ids,
            verification_status, confidence_notes
        ) VALUES (?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (
                claim_id,
                claim.get("topic_id"),
                claim.get("claim_text"),
                supporting,
                claim.get("verification_status", "pending"),
                claim.get("confidence_notes", "")
            ))
        return claim_id

    def get_claims_by_topic(self, topic_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM claims WHERE topic_id = ?;"
        with self.get_connection() as conn:
            rows = conn.execute(sql, (topic_id,)).fetchall()
            res = []
            for r in rows:
                item = dict(r)
                try:
                    item["supporting_source_ids"] = json.loads(item["supporting_source_ids"])
                except Exception:
                    item["supporting_source_ids"] = []
                res.append(item)
            return res

    # ---------------------------------------------------------
    # Content Operations
    # ---------------------------------------------------------
    def insert_content(self, content: Dict[str, Any]) -> str:
        content_id = content.get("content_id") or hashlib.md5(f"{content.get('topic_id')}_{content.get('format')}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        created_at = content.get("created_at") or datetime.now(timezone.utc).isoformat()
        storyboard = content.get("storyboard_json", {})
        if not isinstance(storyboard, str):
            storyboard = json.dumps(storyboard)
        manifest = content.get("asset_manifest_json", {})
        if not isinstance(manifest, str):
            manifest = json.dumps(manifest)

        sql = """
        INSERT OR REPLACE INTO content (
            content_id, topic_id, format, category, script,
            caption, storyboard_json, asset_manifest_json,
            quality_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (
                content_id,
                content.get("topic_id"),
                content.get("format"),
                content.get("category"),
                content.get("script", ""),
                content.get("caption", ""),
                storyboard,
                manifest,
                content.get("quality_status", "draft"),
                created_at
            ))
        return content_id

    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM content WHERE content_id = ?;"
        with self.get_connection() as conn:
            row = conn.execute(sql, (content_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["storyboard_json"] = json.loads(res["storyboard_json"])
            except Exception:
                pass
            try:
                res["asset_manifest_json"] = json.loads(res["asset_manifest_json"])
            except Exception:
                pass
            return res

    def get_content_by_status(self, quality_status: str, format_type: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM content WHERE quality_status = ?"
        params: List[Any] = [quality_status]
        if format_type:
            sql += " AND format = ?"
            params.append(format_type)
        sql += " ORDER BY created_at DESC;"
        with self.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            res = []
            for r in rows:
                item = dict(r)
                try:
                    item["storyboard_json"] = json.loads(item["storyboard_json"])
                except Exception:
                    pass
                try:
                    item["asset_manifest_json"] = json.loads(item["asset_manifest_json"])
                except Exception:
                    pass
                res.append(item)
            return res

    def update_content_quality(self, content_id: str, quality_status: str) -> None:
        sql = "UPDATE content SET quality_status = ? WHERE content_id = ?;"
        with self.get_connection() as conn:
            conn.execute(sql, (quality_status, content_id))

    # ---------------------------------------------------------
    # Publishing Queue Operations
    # ---------------------------------------------------------
    def enqueue_content(self, content_id: str, scheduled_at: str) -> str:
        queue_id = hashlib.md5(f"{content_id}_{scheduled_at}".encode()).hexdigest()[:12]
        sql = """
        INSERT OR IGNORE INTO publishing_queue (
            queue_id, content_id, scheduled_at, status, attempt_count,
            last_error, instagram_container_id, instagram_media_id, published_at
        ) VALUES (?, ?, ?, 'pending', 0, NULL, NULL, NULL, NULL);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (queue_id, content_id, scheduled_at))
        return queue_id

    def get_pending_queue(self, before_time: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT q.*, c.format, c.category, c.caption, c.script, c.asset_manifest_json FROM publishing_queue q JOIN content c ON q.content_id = c.content_id WHERE q.status = 'pending'"
        params: List[Any] = []
        if before_time:
            sql += " AND q.scheduled_at <= ?"
            params.append(before_time)
        sql += " ORDER BY q.scheduled_at ASC;"
        with self.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            res = []
            for r in rows:
                item = dict(r)
                try:
                    item["asset_manifest_json"] = json.loads(item["asset_manifest_json"])
                except Exception:
                    pass
                res.append(item)
            return res

    def update_queue_item(
        self,
        queue_id: str,
        status: str,
        attempt_increment: bool = False,
        last_error: Optional[str] = None,
        container_id: Optional[str] = None,
        media_id: Optional[str] = None,
        published_at: Optional[str] = None
    ) -> None:
        updates = ["status = ?"]
        params: List[Any] = [status]
        if attempt_increment:
            updates.append("attempt_count = attempt_count + 1")
        if last_error is not None:
            updates.append("last_error = ?")
            params.append(last_error)
        if container_id is not None:
            updates.append("instagram_container_id = ?")
            params.append(container_id)
        if media_id is not None:
            updates.append("instagram_media_id = ?")
            params.append(media_id)
        if published_at is not None:
            updates.append("published_at = ?")
            params.append(published_at)

        sql = f"UPDATE publishing_queue SET {', '.join(updates)} WHERE queue_id = ?;"
        params.append(queue_id)
        with self.get_connection() as conn:
            conn.execute(sql, params)

    def is_content_published(self, content_id: str) -> bool:
        sql = "SELECT 1 FROM publishing_queue WHERE content_id = ? AND status = 'published' LIMIT 1;"
        with self.get_connection() as conn:
            row = conn.execute(sql, (content_id,)).fetchone()
            return row is not None

    # ---------------------------------------------------------
    # Insights Operations
    # ---------------------------------------------------------
    def record_insights(self, content_id: str, metrics: Dict[str, Any]) -> str:
        insight_id = hashlib.md5(f"{content_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        retrieved_at = datetime.now(timezone.utc).isoformat()
        raw_json = json.dumps(metrics)

        sql = """
        INSERT INTO insights (
            insight_id, content_id, retrieved_at, reach, plays,
            likes, comments, shares, saves, follows, raw_metrics_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            conn.execute(sql, (
                insight_id,
                content_id,
                retrieved_at,
                metrics.get("reach", 0),
                metrics.get("plays", 0),
                metrics.get("likes", 0),
                metrics.get("comments", 0),
                metrics.get("shares", 0),
                metrics.get("saves", 0),
                metrics.get("follows", 0),
                raw_json
            ))
        return insight_id

    def get_latest_insights(self, limit: int = 50) -> List[Dict[str, Any]]:
        sql = """
        SELECT i.*, c.category, c.format
        FROM insights i
        JOIN content c ON i.content_id = c.content_id
        ORDER BY i.retrieved_at DESC
        LIMIT ?;
        """
        with self.get_connection() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
            return [dict(r) for r in rows]
