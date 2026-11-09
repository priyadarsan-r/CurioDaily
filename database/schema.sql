CREATE TABLE IF NOT EXISTS topics (
    topic_id TEXT PRIMARY KEY,
    title TEXT,
    normalized_title TEXT,
    category TEXT,
    summary TEXT,
    discovered_at DATETIME,
    source_url TEXT,
    source_type TEXT,
    topic_score INTEGER,
    status TEXT,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    topic_id TEXT,
    url TEXT,
    title TEXT,
    publisher TEXT,
    published_at DATETIME,
    retrieved_at DATETIME,
    source_class TEXT,
    reliability_notes TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    topic_id TEXT,
    claim_text TEXT,
    supporting_source_ids TEXT,
    verification_status TEXT,
    confidence_notes TEXT
);

CREATE TABLE IF NOT EXISTS content (
    content_id TEXT PRIMARY KEY,
    topic_id TEXT,
    format TEXT,
    category TEXT,
    script TEXT,
    caption TEXT,
    storyboard_json TEXT,
    asset_manifest_json TEXT,
    quality_status TEXT,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS publishing_queue (
    queue_id TEXT PRIMARY KEY,
    content_id TEXT,
    scheduled_at DATETIME,
    status TEXT,
    attempt_count INTEGER,
    last_error TEXT,
    instagram_container_id TEXT,
    instagram_media_id TEXT,
    published_at DATETIME
);

CREATE TABLE IF NOT EXISTS insights (
    insight_id TEXT PRIMARY KEY,
    content_id TEXT,
    retrieved_at DATETIME,
    reach INTEGER,
    plays INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    saves INTEGER,
    follows INTEGER,
    raw_metrics_json TEXT
);
