# CurioDaily — Zero-Budget Automated Social Media Content Engine

A fully automated, ₹0-budget educational content production and publishing engine built with Python, SQLite, Pillow, FFmpeg, and GitHub Actions.

Discovers intriguing topics, fact-checks claims against credible sources, generates structured scripts and storyboards, produces voice narration and branded motion graphics, and publishes approved content directly to Instagram.

---

## 🎯 Daily Publishing Target (7 Pieces/Day)

| Format | Daily Target | Specification |
|---|---:|---|
| **Reels** | 4 | One per content pillar (45–60s, 9:16 vertical 1080×1920) |
| **Feed Posts** | 2 | Single-image key insights (4:5 portrait 1080×1350) |
| **Carousel** | 1 | Multi-slide educational deep dive (5–8 slides, 1080×1350) |

---

## 🏛️ Four Content Pillars

1. **Money Secrets (`money_secrets`)**: Everyday personal finance, compound interest, purchasing power, behavioural money psychology.
2. **Human Psychology (`human_psychology`)**: Cognitive biases, mental models, decision-making, habit formation.
3. **Future Is Here (`future_is_here`)**: Emerging technologies, clean energy, space exploration, scientific breakthroughs.
4. **The Daily Mystery (`daily_mystery`)**: Geological anomalies, unsolved archaeological puzzles, historical curiosities.

---

## 🏗️ Architecture & Pipeline Flow

```text
GitHub Actions / Local Scheduler
             │
             ▼
      Topic Discovery (Google Trends, Reddit, RSS, NASA, Wikipedia)
             │
             ▼
      Normalize & Deduplicate (SQLite + SHA-256 Hashes)
             │
             ▼
      Claim Extraction & Fact Verification
             │
             ▼
      Topic Scoring (100-Point Quality Gate, >= 70 Pass)
             │
             ▼
      Editorial Selection (4 Reels + 2 Posts + 1 Carousel)
             │
             ▼
      Script & Storyboard Generation + QA Checks
             │
       ┌─────┴─────────────────────┐
       ▼                           ▼
Reel Production            Graphic Rendering
(TTS + Pillow + Subtitles  (Pillow 1080x1350
 + FFmpeg 9:16 MP4)         Feed & Carousel Slides)
       │                           │
       └─────────────┬─────────────┘
                     ▼
           Publishing Queue (SQLite)
                     │
                     ▼
          Instagram Graph API Publisher
                     │
                     ▼
          Insights Sync & Weekly Recommendations
```

---

## 🚀 Quickstart & Usage

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Validate system environment
python scripts/validate_environment.py
```

### 2. Run the Full Daily Pipeline

```bash
# Run all stages end-to-end
python scripts/run_daily.py

# Or run individual stages:
python scripts/run_daily.py --stage discover
python scripts/run_daily.py --stage research
python scripts/run_daily.py --stage generate
python scripts/run_daily.py --stage publish
python scripts/run_daily.py --stage insights
```

### 3. Run the Test Suite

```bash
pytest tests/ -v
```

---

## ⚙️ Configuration Files

All operational parameters are customizable in `config/`:
- [`config/topics.yml`](file:///d:/CurioDaily/config/topics.yml): Pillar configurations, target reels, scoring weights.
- [`config/brand.yml`](file:///d:/CurioDaily/config/brand.yml): Account brand colors, typography, watermark, pillar themes.
- [`config/schedule.yml`](file:///d:/CurioDaily/config/schedule.yml): Daily posting slots in India Standard Time (IST).
- [`config/quality.yml`](file:///d:/CurioDaily/config/quality.yml): Video dimensions, duration thresholds, editorial safeguards.
- [`config/sources.yml`](file:///d:/CurioDaily/config/sources.yml): RSS feeds, subreddits, API endpoints.

---

## 🔐 Credentials & Secrets

Store in GitHub Actions Secrets (or local `.env`):
- `INSTAGRAM_ACCOUNT_ID`: Your Instagram Professional (Creator/Business) Account ID.
- `INSTAGRAM_ACCESS_TOKEN`: Long-lived Meta User or Page Graph API token.

*Note: If credentials are not set, the engine automatically operates in local mock/test mode without failing.*
