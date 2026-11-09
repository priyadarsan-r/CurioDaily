# Zero-Budget Automated Social Media Content Engine
## Detailed Product, Architecture and Implementation Plan

**Document type:** Technical project plan and implementation specification  
**Target platform:** Instagram  
**Orchestration and source control:** GitHub + GitHub Actions  
**Budget:** ₹0 recurring spend; no paid APIs, subscriptions, hosted databases, paid AI services or paid media-generation services  
**Primary language:** English  
**Daily publishing target:** 4 Reels + 2 single-image feed posts + 1 carousel  
**Content strategy:** One account with four content pillars  
**Status:** Proposed plan; account credentials, repository choice and Meta API setup remain to be confirmed

---

# 1. Executive summary

Build a fully automated, zero-budget content production and publishing system using a GitHub repository, GitHub Actions, Python, open-source local models, FFmpeg and the official Instagram publishing API.

The system discovers interesting topics, researches and verifies claims, scores topics, creates scripts and visual storyboards, generates narration, assembles short-form videos and static graphics, and publishes approved content to Instagram. It also records publishing results and uses available performance metrics to improve future content.

The system is designed around a strict constraint: **no paid services or paid API calls**. It must not quietly depend on free trials, expiring credits, or services whose free plans are unsuitable for the expected volume.

The system targets seven content pieces every day:

- 4 Reels, one for each content pillar.
- 2 single-image feed posts.
- 1 carousel, normally 5–8 slides.

Seven daily pieces is an ambitious production target. The design must prioritize reliability, quality and account safety over blindly meeting a quota. If research, verification, rendering or publishing fails, the item must be held for retry rather than publishing inaccurate or broken content.

A zero-cost solution can automate discovery, scripting, voice generation, graphic creation, motion-based video editing and publishing. It cannot guarantee unlimited, fully generative cinematic video production. Heavy AI video generation generally requires GPU resources and should not be a mandatory dependency.

---

# 2. Product goals and non-goals

## 2.1 Goals

1. Run the content pipeline automatically from GitHub Actions.
2. Avoid paid APIs, paid AI subscriptions, paid hosting and paid databases.
3. Publish 4 Reels, 2 feed posts and 1 carousel per day when sufficient quality-approved content exists.
4. Operate one Instagram account across four content pillars.
5. Use open-source tools and public data sources.
6. Generate original scripts, narration, captions, visual layouts and edits.
7. Verify factual claims and preserve source references.
8. Prevent duplicate topics and duplicate publishing.
9. Record workflow status, errors and available post-performance metrics.
10. Make the system modular so tools can be replaced without rewriting the entire project.

## 2.2 Non-goals

- No promise of unlimited AI-generated video clips.
- No use of paid APIs or free-trial credits as a hidden dependency.
- No scraping behind logins, bypassing rate limits or violating platform terms.
- No automated likes, follows, comments, direct messages or engagement manipulation.
- No financial advice, medical advice or sensational claims presented as established facts.
- No guarantee of reach, virality, follower growth or monetization.
- No assumption that GitHub Pages is an unlimited media CDN.

---

# 3. Content strategy

## 3.1 Account strategy

Use **one Instagram account**, not four separate accounts. The four pillars are related through a common promise: make people curious and help them learn something interesting.

Start with an approximately balanced mix. Review performance after 30 days; do not permanently assume all four categories will perform equally.

## 3.2 The four content pillars

### Pillar 1 — Money Secrets: Personal Finance

**Purpose:** Explain everyday money concepts in an accessible, engaging way.

Topic examples:
- Why compound interest becomes powerful over time.
- How inflation changes purchasing power.
- The difference between assets and liabilities.
- How credit-card interest works.
- Why emergency funds matter.
- Common behavioural mistakes with money.

**Voice:** Smart, authoritative, practical and intriguing.

**Editorial safeguards:**
- Explain assumptions and dates when using rates or prices.
- Do not present forecasts as guaranteed outcomes.
- Do not give personalized investment recommendations.
- Distinguish education from financial advice.
- Prefer official regulators, central banks, company filings and original research.

### Pillar 2 — Human Psychology: The Human Mind

**Purpose:** Explain evidence-based psychology and everyday human behaviour.

Topic examples:
- Why people procrastinate.
- How habits become automatic.
- Why familiar information feels more believable.
- The psychology of first impressions.
- How attention and memory work.
- Why social comparison affects decisions.

**Voice:** Relatable, conversational and thought-provoking.

**Editorial safeguards:**
- Avoid diagnosing viewers.
- Do not overgeneralize study results.
- Distinguish correlation from causation.
- Do not invent psychological effects or misattribute named experiments.
- Prefer peer-reviewed research, universities and professional associations.

### Pillar 3 — Future Is Here: Future Technology

**Purpose:** Make emerging technology understandable and visually exciting.

Topic examples:
- Robotics and automation.
- Space exploration.
- AI capabilities and limitations.
- Energy storage and new materials.
- Medical technology research.
- Computing and scientific breakthroughs.

**Voice:** Futuristic, exciting and grounded in evidence.

**Editorial safeguards:**
- Separate demonstrated capabilities from prototypes and predictions.
- State when a development is experimental.
- Avoid exaggerated claims about AI or science.
- Prefer research papers, official project pages, technical documentation and reputable science journalism.

### Pillar 4 — The Daily Mystery: Curiosity and Mysteries

**Purpose:** Tell compelling stories about unexplained phenomena, unusual places, history, geography and science.

Topic examples:
- Unusual geological formations.
- Historical puzzles with competing explanations.
- Strange but documented natural phenomena.
- Archaeological discoveries.
- Unusual places and their origins.
- Scientific questions that remain open.

**Voice:** Suspenseful, documentary-style and curious.

**Editorial safeguards:**
- Do not present folklore as proven history.
- Clearly label unresolved questions.
- Include the best-supported explanation where one exists.
- Avoid conspiracy theories and fabricated mysteries.
- Prefer museums, archives, academic sources, scientific institutions and original historical documents.

## 3.3 Brand and editorial identity

The account name is not finalized. Do not hard-code a proposed name into the software. Store the approved name, logo, colors, fonts, watermark and handle in `config/brand.yml`.

All content should feel like it belongs to one recognizable publication:
- Consistent typography and caption styling.
- Consistent opening and closing visual language.
- A recognizable watermark.
- Category-specific accent styles without creating four unrelated brands.
- Clear, readable captions on mobile screens.

---

# 4. Daily publishing plan

## 4.1 Daily target

| Format | Daily quantity | Specification |
|---|---:|---|
| Reels | 4 | One per content pillar |
| Single-image feed posts | 2 | One clear insight per post |
| Carousel | 1 | Normally 5–8 slides |
| **Total** | **7** | Target, subject to quality gate |

## 4.2 Initial publishing schedule

Use these as test slots in India Standard Time (IST), not as guaranteed optimal times.

| Time (IST) | Content |
|---|---|
| 9:00 AM | Money Secrets Reel |
| 11:00 AM | Single-image post 1 |
| 12:30 PM | Human Psychology Reel |
| 3:00 PM | Carousel |
| 5:00 PM | Future Is Here Reel |
| 6:30 PM | Single-image post 2 |
| 8:30 PM | The Daily Mystery Reel |

The schedule must be configurable in `config/schedule.yml`. After 30 days, compare performance by category, format and posting time, then adjust based on account insights.

## 4.3 Reuse research intelligently

Do not research seven unrelated topics every day. Discover and research enough distinct topics to support the four Reels. Select the strongest additional ideas for the two feed posts and carousel.

A post may expand on a Reel's topic only when it adds genuine value. Do not publish the same script as a Reel, image and carousel with superficial changes.

---

# 5. Recommended technology stack

The stack below prioritizes no-cost operation, open-source software, replaceable components and compatibility with GitHub Actions.

| Area | Primary choice | Purpose and rationale |
|---|---|---|
| Repository | GitHub | Source control, issue tracking, workflow definitions and project documentation |
| Automation | GitHub Actions | Scheduled and manually triggered jobs; no separate orchestration server |
| Main language | Python 3 | Strong ecosystem for research, media processing and APIs |
| Configuration | YAML | Human-readable schedules, topic settings and brand configuration |
| State/database | SQLite + JSON | No hosted database or service required |
| HTTP | `requests` / `httpx` | Retrieve public feeds and APIs |
| HTML parsing | BeautifulSoup | Parse permitted public web pages |
| RSS | `feedparser` | Consume public RSS feeds |
| Topic deduplication | SQLite + normalized hashes | Prevent repeated stories |
| Text model | `llama.cpp` with a small quantized open model, if runner capacity allows | Local inference without a paid LLM API |
| TTS | Kokoro TTS; Piper as a fallback | Open-source local speech synthesis |
| Image/graphics | Pillow + SVG | Create branded static assets and visual explainers |
| Video editing | FFmpeg | Assemble video, narration, captions, transitions and music |
| Optional transcription | faster-whisper | Optional QA or timestamp recovery; not required for script-aligned captions |
| Publishing | Official Meta Instagram Graph API | Supported publishing route for professional accounts |
| Public media hosting | GitHub Pages, conditionally | Public URLs for Instagram to fetch assets; subject to strict storage and bandwidth limits |
| Testing | pytest | Validate modules and media outputs |
| Logging | Python logging + JSON run reports | Diagnose workflow failures |
| Analytics | Official Meta insights endpoints where available | Record available performance metrics |

## 5.1 Language model selection

Start with a small quantized model compatible with `llama.cpp`, for example a Qwen-family 1.5B or 3B instruction model, subject to current model licence and hardware testing.

Do not assume that a model will run within GitHub Actions memory, CPU and time limits. Benchmark it on the actual runner. If local inference is too slow or unreliable:
- Use deterministic templates and Python rules for the initial release.
- Generate scripts from structured research inputs with a small model only when feasible.
- Never substitute an undisclosed paid API.
- Keep the LLM interface modular so another genuinely free execution option can be introduced later.

A local model is not automatically free to execute: runner minutes and resource limits still apply.

## 5.2 TTS selection

Test Kokoro first for natural narration. Keep Piper as an alternative if Kokoro's runtime or dependency footprint is unsuitable.

Before integrating either:
- Verify the current model and code licence.
- Verify commercial-use rights for the selected voice/model.
- Pin model versions and checksums.
- Cache model files where permitted to avoid repeated downloads.
- Test pronunciation of numbers, abbreviations, currency and technical terms.

## 5.3 Video generation strategy

The default production approach is **cinematic motion design**, not full text-to-video generation.

Build visual sequences from:
- Public-domain or appropriately licensed photographs and footage.
- Original charts, diagrams and maps created from researched data.
- SVG illustrations and vector animations.
- Animated text and kinetic typography.
- Slow zooms, pans, parallax-like movement and transitions.
- Original AI-generated still images only if they can be generated locally without a paid service and the model licence permits the intended use.

Do not download random images from search results and assume they are free to reuse. Record each asset's source, licence and attribution requirements.

Full AI video generation is optional and must not be a required component of the seven-piece daily pipeline.

---

# 6. System architecture

## 6.1 High-level workflow

```text
GitHub Actions Scheduler
          |
          v
Topic Discovery
          |
          v
Normalize + Deduplicate
          |
          v
Research + Source Collection
          |
          v
Claim Verification + Topic Scoring
          |
          v
Daily Editorial Selection
          |
          v
Script + Storyboard Generation
          |
          +-----------------------------+
          |              |              |
          v              v              v
      Reel Builder   Feed Builder   Carousel Builder
          |              |              |
          v              v              v
       TTS + FFmpeg   Pillow/SVG     Pillow/SVG
          |              |              |
          +--------------+--------------+
                         |
                         v
                 Quality-Control Gate
                         |
                         v
                  Publishing Queue
                         |
                         v
                Public Asset Hosting
                         |
                         v
               Instagram Graph API
                         |
                         v
                 Publishing Records
                         |
                         v
               Insights + Optimizer
```

## 6.2 Core design principles

1. Each workflow should be independently runnable.
2. Every content item must have a unique stable ID.
3. Every publishing action must be idempotent: retrying a job must not publish the same item twice.
4. Research evidence must travel with the content record.
5. Media generation must be deterministic where practical.
6. Secrets must never be committed to the repository or written to logs.
7. The workflow should recover from transient failures.
8. Quality checks must happen before publishing.
9. The system must support manual workflow dispatch for testing and recovery.
10. Generated media should not be committed to Git history indefinitely.

---

# 7. Repository structure

Recommended repository name: `zero-budget-content-engine` (rename freely).

```text
zero-budget-content-engine/
│
├── .github/
│   └── workflows/
│       ├── discover.yml
│       ├── research-and-plan.yml
│       ├── generate-reels.yml
│       ├── generate-feed-posts.yml
│       ├── generate-carousel.yml
│       ├── publish.yml
│       ├── collect-insights.yml
│       └── maintenance.yml
│
├── config/
│   ├── topics.yml
│   ├── schedule.yml
│   ├── brand.yml
│   ├── sources.yml
│   └── quality.yml
│
├── discovery/
│   ├── google_trends.py
│   ├── reddit.py
│   ├── rss_sources.py
│   ├── nasa.py
│   ├── wikipedia.py
│   └── collect.py
│
├── research/
│   ├── fetch_sources.py
│   ├── extract_claims.py
│   ├── verify_claims.py
│   ├── score_topics.py
│   └── editorial_selection.py
│
├── ai/
│   ├── llm.py
│   ├── script_generator.py
│   ├── storyboard_generator.py
│   ├── prompts/
│   │   ├── money.md
│   │   ├── psychology.md
│   │   ├── future_tech.md
│   │   ├── mystery.md
│   │   ├── feed_post.md
│   │   └── carousel.md
│   └── quality_check.py
│
├── media/
│   ├── tts.py
│   ├── kokoro_engine.py
│   ├── piper_engine.py
│   ├── asset_manager.py
│   ├── create_visuals.py
│   ├── create_reel.py
│   ├── create_feed_post.py
│   ├── create_carousel.py
│   ├── create_captions.py
│   └── ffmpeg_utils.py
│
├── publishing/
│   ├── instagram_client.py
│   ├── upload_assets.py
│   ├── publish_reel.py
│   ├── publish_image.py
│   ├── publish_carousel.py
│   └── publish_queue.py
│
├── analytics/
│   ├── fetch_insights.py
│   ├── aggregate.py
│   └── recommendations.py
│
├── database/
│   ├── schema.sql
│   ├── db.py
│   └── migrations/
│
├── scripts/
│   ├── run_daily.py
│   ├── validate_environment.py
│   ├── cleanup.py
│   └── export_report.py
│
├── tests/
│   ├── test_discovery.py
│   ├── test_deduplication.py
│   ├── test_quality.py
│   ├── test_media.py
│   └── test_publishing.py
│
├── assets/
│   ├── fonts/
│   ├── music/
│   ├── templates/
│   └── logo/
│
├── output/                 # Temporary; do not commit generated media
├── reports/                # Small JSON run summaries only
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── README.md
└── plan.md
```

---

# 8. Topic discovery

## 8.1 Discovery requirements

Discovery must find candidate topics for all four pillars. It should collect:
- Topic/title.
- Category.
- Short summary.
- Source URL.
- Source publication date, if available.
- Discovery timestamp.
- Source type.
- Relevant keywords.
- Any available engagement or trend signal.
- Whether the source is primary, secondary or community-generated.

Discovery is not verification. A trending post or Reddit thread is a lead, not proof.

## 8.2 Source strategy

Use free public feeds and APIs where available. Examples include:

| Pillar | Discovery sources | Preferred verification sources |
|---|---|---|
| Money | Google Trends public trends/RSS where available; financial news RSS; public company and regulator updates | Central banks, regulators, government statistics, company filings, original research |
| Psychology | Psychology and science RSS feeds; university publications; Reddit discussions as idea discovery | Peer-reviewed papers, APA, universities, original studies |
| Future technology | NASA, research institution and technology publication feeds; public project updates | Research papers, official technical documentation, NASA and other primary institutions |
| Mystery | Museum, archive, geography, science and history feeds; community questions as idea discovery | Museums, archives, academic papers, official scientific institutions |

Do not assume that every website offers an unrestricted API or RSS feed. Verify each source's current access rules, rate limits, robots policy and terms before integrating it.

## 8.3 Discovery workflow

1. Retrieve source feeds.
2. Normalize titles and URLs.
3. Extract candidate topics.
4. Assign a tentative pillar.
5. Compute a normalized title/content hash.
6. Check for duplicates in SQLite.
7. Store candidate records.
8. Pass new candidates to research.

## 8.4 Topic deduplication

Use several checks:
- Exact normalized title hash.
- Canonical URL uniqueness.
- Similarity of topic keywords.
- Recent topic history by pillar.
- Optional text embedding or similarity check only if a free local model is practical.

Default policy: do not publish substantially the same topic within 30 days unless there is a meaningful update or a clearly different angle.

---

# 9. Research, fact-checking and topic scoring

## 9.1 Research process

For each selected topic:
1. Retrieve at least two credible sources where practical.
2. Prefer primary sources.
3. Extract factual claims separately from opinions.
4. Record dates and numerical values.
5. Identify disagreements or uncertainty.
6. Create a concise evidence summary.
7. Generate the script only from the evidence summary.
8. Preserve source URLs in the final content record.

For important claims, aim for two independent sources, including at least one primary source. If only one reliable source exists, label the claim carefully or reject the topic.

## 9.2 Topic scoring

Initial scoring model (100 points):

| Factor | Weight | Meaning |
|---|---:|---|
| Curiosity and surprise | 30 | Does the idea make people want to know more? |
| Visual potential | 25 | Can it be explained with compelling visuals? |
| Audience relevance | 20 | Is it broadly understandable and useful? |
| Shareability | 15 | Is it likely to be saved or shared? |
| Source reliability | 10 | Is the evidence credible and traceable? |

Initial threshold: **70/100**, plus a mandatory evidence-quality pass.

A high engagement score must never override a failed factual check.

## 9.3 Quality gate

Reject or hold a topic when:
- The central claim cannot be verified.
- The story depends on a misleading headline.
- Sources conflict and the disagreement cannot be explained.
- The topic is a duplicate.
- The content is defamatory, invasive or unsafe.
- The topic requires professional financial or medical advice.
- The script invents statistics, quotations or citations.

---

# 10. Script and storyboard generation

## 10.1 Reel format

Target length: 45–60 seconds.

Suggested narration length: approximately 100–135 words, adjusted for the chosen voice and pacing.

Structure:
1. Hook (0–3 seconds): create a clear curiosity gap.
2. Context (3–12 seconds): explain why the topic matters.
3. Development (12–35 seconds): reveal evidence and explain the idea.
4. Payoff (35–52 seconds): deliver the most interesting takeaway.
5. Close (last seconds): ask a relevant question or invite a save/share without engagement bait.

Each script must include:
- Working title.
- Pillar.
- Hook.
- Narration.
- Scene-by-scene storyboard.
- On-screen text.
- Visual asset requirements.
- Source URLs.
- Key factual claims.
- Caption and hashtags.
- AI-generated or reconstructed visual disclosure where appropriate.

## 10.2 Storyboard format

Create 6–8 scenes per Reel, usually 5–8 seconds each.

Each scene record should include:
- Scene number.
- Start and end time.
- Narration segment.
- Visual description.
- Asset source or generation method.
- Camera/motion effect.
- On-screen text.
- Transition.

## 10.3 Prompt rules

The language model must:
- Use only facts in the supplied evidence packet.
- Never fabricate source URLs, statistics, quotes or named studies.
- Mark uncertain information explicitly.
- Avoid unsupported superlatives such as “first ever” or “scientists are baffled.”
- Use plain conversational English.
- Avoid repeating the same hook structure every day.
- Generate original wording, not copy source articles.

## 10.4 Feed post format

Each of the two daily posts should contain one strong takeaway:
- One clear headline.
- One concise explanation.
- One or two supporting facts.
- A source note in the caption where relevant.
- Consistent branding and readable mobile typography.

## 10.5 Carousel format

Default: 5–8 slides.

Suggested structure:
1. Cover: compelling question or promise.
2. Context: why the subject matters.
3. Key idea or fact 1.
4. Key idea or fact 2.
5. Key idea or fact 3.
6. Evidence, example or comparison.
7. Practical takeaway or reveal.
8. Closing question and sources, if needed.

Avoid overcrowding slides. Each slide should communicate one main idea.

---

# 11. Media production

## 11.1 Reel video specifications

| Property | Target |
|---|---|
| Aspect ratio | 9:16 |
| Resolution | 1080 × 1920 |
| Frame rate | 30 fps |
| Container | MP4 |
| Video codec | H.264 |
| Audio codec | AAC |
| Duration | 45–60 seconds |
| Captions | Burned-in, readable and synchronized |
| Audio | Narration clearly above background music |

Validate the current Instagram publishing specifications before deployment; platform requirements can change.

## 11.2 Narration

Pipeline:
1. Split script into scene-aligned narration segments.
2. Generate speech using the selected local TTS engine.
3. Normalize sample rate and channel layout.
4. Remove excessive silence.
5. Measure duration.
6. Align scene timing to the actual narration.
7. Mix licensed or original background audio at a low level.
8. Run audio QA.

Keep pronunciation dictionaries for:
- Currency.
- Percentages.
- Dates and years.
- Acronyms.
- Technical and scientific names.
- Indian and international place names.

## 11.3 Visual assets

Preferred order:
1. Original graphics and charts.
2. Public-domain material.
3. Creative Commons or other assets whose licence permits the intended use.
4. Original locally generated illustrations where the model licence permits use.

Every downloaded asset must have an asset record:
- Asset ID.
- File path.
- Source URL.
- Creator, if known.
- Licence.
- Attribution text, if required.
- Download date.
- Related content ID.

Do not use watermarked assets or copyrighted music without permission.

## 11.4 Motion design

Use FFmpeg filters and Python-generated images for:
- Slow zoom and pan.
- Ken Burns effects.
- Animated title cards.
- Scene transitions.
- Gradient backgrounds and overlays.
- Animated charts and diagrams.
- Subtitle highlights.
- Progress indicators.
- Consistent outro and watermark.

Use category-specific visual presets:
- Money: clean, editorial, data-led.
- Psychology: human-centered, warm, minimal.
- Future technology: modern, technical, futuristic.
- Mystery: documentary, atmospheric, suspenseful.

## 11.5 Captions

Prefer script-aligned word or phrase timing generated from scene segments. If precise word-level timing is unavailable, use short phrase-level captions rather than claiming false word-perfect synchronization.

Caption requirements:
- High contrast.
- Safe margins from UI overlays.
- Maximum two lines at a time.
- Readable mobile font size.
- Correct punctuation and spelling.
- No text cut off by frame edges.

---

# 12. GitHub Actions design

## 12.1 Workflow files

### `discover.yml`

Purpose:
- Run source discovery.
- Normalize and deduplicate topics.
- Store candidate topics.
- Upload a small state artifact or commit a controlled database update.

### `research-and-plan.yml`

Purpose:
- Select candidate topics.
- Retrieve source evidence.
- Verify claims.
- Score topics.
- Create the daily editorial plan.
- Hold insufficiently supported topics.

### `generate-reels.yml`

Purpose:
- Generate four Reel scripts and storyboards.
- Generate narration.
- Create visual assets.
- Render MP4 files.
- Validate duration, resolution, codecs, audio and captions.

### `generate-feed-posts.yml`

Purpose:
- Create two single-image posts.
- Generate captions and source notes.
- Validate dimensions and text readability.

### `generate-carousel.yml`

Purpose:
- Create a 5–8 slide carousel.
- Validate slide dimensions, ordering and text.
- Create a caption and source notes.

### `publish.yml`

Purpose:
- Read approved publishing queue.
- Check idempotency.
- Make media publicly accessible.
- Create Instagram media containers.
- Poll processing status.
- Publish content.
- Save returned media IDs and timestamps.
- Record failures for retry.

### `collect-insights.yml`

Purpose:
- Fetch available metrics for previously published content.
- Save snapshots.
- Calculate per-pillar and per-format summaries.
- Suggest editorial adjustments.

### `maintenance.yml`

Purpose:
- Clean temporary files and expired assets.
- Validate database integrity.
- Check expiring credentials where possible.
- Produce system health reports.

## 12.2 Scheduling strategy

Use cron schedules in UTC, because GitHub Actions cron is UTC. Convert the desired IST schedule carefully (IST = UTC + 5:30).

Do not create seven separate heavyweight runners unless necessary. Prefer:
- One daily discovery/research job.
- Separate media jobs by format or category.
- One publishing scheduler that reads the queue.
- A manual dispatch option for testing and recovery.

GitHub scheduled workflows can be delayed, particularly during busy periods. Do not rely on them for second-level timing precision.

## 12.3 Runner usage optimization

GitHub Actions minutes are a limited resource, especially for private repositories. Design for:
- Public repository if the source code and prompts can safely be public.
- Small dependency sets.
- Caching Python packages and model files when permitted.
- Avoiding repeated model downloads.
- Avoiding repeated installation of FFmpeg.
- Rendering only missing assets.
- Parallel jobs only when total runner usage remains reasonable.
- Saving intermediate outputs as artifacts only when necessary.
- Cleaning up large outputs after successful publishing.

Do not commit generated MP4 files or large model weights to Git history.

## 12.4 State persistence

GitHub-hosted runners are ephemeral. Files created during one job do not automatically persist to the next job.

Use:
- SQLite for compact structured state.
- GitHub Actions artifacts for short-lived job handoffs.
- A controlled repository state branch or small JSON files for durable state if needed.
- A backup/export process for publishing history.

Do not assume a SQLite file in one runner will exist in a later scheduled run. Implement explicit persistence and concurrency protection.

---

# 13. Instagram publishing

## 13.1 Account requirements

Use an Instagram Professional account (Creator or Business) and a properly configured Meta developer app.

Before development, confirm:
- Account type and eligibility.
- Required Meta app configuration.
- Instagram account linkage.
- Required publishing permissions.
- Token acquisition and refresh process.
- Current supported media types and publishing limits.

Use only official Meta APIs. Do not automate the Instagram website with browser bots.

## 13.2 Publishing flow

For each approved item:
1. Confirm it has not already been published.
2. Upload or expose the media at a publicly accessible URL.
3. Create the appropriate Instagram media container.
4. Poll the container status where required.
5. Publish the container.
6. Store the returned media ID.
7. Store timestamp, format, caption, topic ID and source references.
8. Mark the queue item as published.

For carousels:
- Create child media containers for each slide.
- Create the parent carousel container.
- Publish the parent after all children are ready.
- Preserve slide order.

## 13.3 Idempotency and retries

Use a stable `content_id` and a unique publishing key. Before any publish call:
- Check whether the item already has a successful media ID.
- Check whether a container is already pending.
- Avoid creating duplicate containers unnecessarily.
- Retry only failures known to be transient.
- Record every API response status without logging secrets.

Never retry a publish call blindly when the response is ambiguous. First check whether the item was published.

## 13.4 Public media hosting constraints

Instagram's API requires accessible media URLs for its publishing workflow.

GitHub Pages may be used as a zero-cost public asset host for a small initial workload, subject to its current terms and published limits. It is not a purpose-built media CDN.

Plan for:
- Public repository/site visibility.
- Predictable asset URLs.
- Correct MIME types.
- Enough time for Instagram to fetch media.
- Asset retention and cleanup.
- Site build and deployment limits.
- Storage and bandwidth monitoring.

Do not assume GitHub Pages provides unlimited media hosting. If it becomes unreliable or exceeds its limits, the strict ₹0 requirement may prevent scaling the current publishing architecture without a different free host or a change in requirements.

---

# 14. Security and privacy

## 14.1 GitHub Secrets

Store all credentials in GitHub Actions Secrets, for example:
- `META_APP_ID`
- `META_APP_SECRET`
- `INSTAGRAM_ACCOUNT_ID`
- `INSTAGRAM_ACCESS_TOKEN`
- Any optional external service credentials (none required for the core zero-cost design)

Never place secrets in:
- Source code.
- YAML literals.
- Committed `.env` files.
- Logs.
- Prompt files.
- Public artifacts.

## 14.2 Permissions

Use least-privilege GitHub workflow permissions. Avoid giving every workflow write access to the repository.

Pin third-party GitHub Actions to reviewed commit SHAs where practical. Review dependency changes and use a dependency lock file.

## 14.3 Public repository considerations

A public repository is useful for free Actions minutes, but all committed code and data are public. Never commit:
- Tokens.
- Personal information.
- Private account data.
- Unpublished sensitive material.
- Private source content that cannot be redistributed.

Publishing records should contain only the minimum information needed for operation and analytics.

---

# 15. Database design

SQLite is sufficient for the initial system.

## 15.1 `topics`

Suggested fields:
- `topic_id` — primary key.
- `title`.
- `normalized_title`.
- `category`.
- `summary`.
- `discovered_at`.
- `source_url`.
- `source_type`.
- `topic_score`.
- `status`.
- `content_hash`.

## 15.2 `sources`

Suggested fields:
- `source_id`.
- `topic_id`.
- `url`.
- `title`.
- `publisher`.
- `published_at`.
- `retrieved_at`.
- `source_class` (primary, secondary, community).
- `reliability_notes`.

## 15.3 `claims`

Suggested fields:
- `claim_id`.
- `topic_id`.
- `claim_text`.
- `supporting_source_ids`.
- `verification_status`.
- `confidence_notes`.

## 15.4 `content`

Suggested fields:
- `content_id`.
- `topic_id`.
- `format` (reel, image, carousel).
- `category`.
- `script`.
- `caption`.
- `storyboard_json`.
- `asset_manifest_json`.
- `quality_status`.
- `created_at`.

## 15.5 `publishing_queue`

Suggested fields:
- `queue_id`.
- `content_id`.
- `scheduled_at`.
- `status`.
- `attempt_count`.
- `last_error`.
- `instagram_container_id`.
- `instagram_media_id`.
- `published_at`.

## 15.6 `insights`

Suggested fields:
- `insight_id`.
- `content_id`.
- `retrieved_at`.
- `reach`.
- `plays`.
- `likes`.
- `comments`.
- `shares`.
- `saves`.
- `follows`, if available.
- `raw_metrics_json`.

Do not assume every metric is available for every media type or API version.

---

# 16. Quality assurance

Every generated item must pass format-specific tests before it enters the publishing queue.

## 16.1 Editorial QA

- Claims are supported by stored sources.
- Sources are accessible and relevant.
- No fabricated quotations or numbers.
- No misleading framing.
- No duplicated recent topic.
- No spelling or grammar errors.
- Caption matches the actual media.
- Required attribution is present.

## 16.2 Reel QA

- MP4 exists and is non-empty.
- Resolution is 1080 × 1920.
- Aspect ratio is 9:16.
- Video and audio codecs are supported.
- Duration is within the configured range.
- Narration is audible and not clipped.
- Background music does not overpower speech.
- Captions are readable and within safe margins.
- No black or unintended blank frames.
- No watermark or asset with unclear rights.

## 16.3 Feed post QA

- Correct aspect ratio and dimensions.
- Text is not clipped.
- Contrast and font size are readable.
- Branding is consistent.
- Caption and source notes are correct.

## 16.4 Carousel QA

- All slides have matching dimensions.
- Slide order is correct.
- First slide is a clear cover.
- Text is readable.
- No accidental duplicate slides.
- Final slide includes a suitable conclusion or source note.

## 16.5 Publishing QA

- Correct account ID.
- Correct content format.
- Correct caption.
- Media URL is publicly reachable.
- Container processing succeeded.
- No duplicate media ID.
- Publishing result is stored.

---

# 17. Analytics and continuous improvement

## 17.1 Metrics

Collect metrics supported by the current Meta API and account permissions:
- Reach.
- Plays or views.
- Likes.
- Comments.
- Shares.
- Saves.
- Follows attributed to content, if available.
- Retention or watch-time metrics, if available.

## 17.2 Evaluation

Compare:
- Pillar.
- Format.
- Hook type.
- Video duration.
- Posting time.
- Visual template.
- Topic category.
- Shares and saves relative to reach.
- Follows relative to reach.
- Retention, where available.

Do not optimize for views alone. Shares, saves, retention and follows can provide better signals of audience value.

## 17.3 Learning loop

Every week:
1. Aggregate the latest available insights.
2. Identify the best-performing topics and formats.
3. Identify weak hooks and high-drop-off content where data exists.
4. Suggest changes to topic selection and scripts.
5. Keep a record of experiments.
6. Avoid changing many variables simultaneously.

Analytics should recommend changes; it should not automatically make risky editorial or account-setting changes.

---

# 18. Cost and capacity reality

## 18.1 What can be zero-cost

- Git repository and source control.
- GitHub Actions within the applicable free allowance and policy.
- Python libraries.
- FFmpeg.
- SQLite.
- Local open-source models and TTS software.
- Original SVG/Pillow graphics.
- Public-domain and appropriately licensed media.
- Official Meta API access, subject to eligibility and platform requirements.

## 18.2 What is not guaranteed

- Unlimited GitHub Actions compute.
- Unlimited model downloads or model execution.
- GPU acceleration.
- Unlimited public media hosting.
- Guaranteed availability of public feeds and APIs.
- Unlimited Instagram publishing.
- Free access to every website or research database.
- Fully generative cinematic video at seven posts per day.

## 18.3 Capacity test before full launch

Run a 3-day pilot:
- Discover topics for all four pillars.
- Generate four scripts per day.
- Render one Reel per pillar per day.
- Generate two posts and one carousel per day.
- Measure total Actions minutes.
- Measure model inference duration and memory.
- Measure media size and hosting bandwidth.
- Test Instagram publishing in a controlled manner.
- Check all outputs manually.

If the measured runner usage exceeds the free allowance, reduce inference and rendering frequency, simplify visuals, or change the production cadence. Do not assume the seven-piece target is feasible until the pilot proves it.

## 18.4 Cost policy

The system must never call a paid API as a fallback. If a free component is unavailable, it should:
1. Log the failure.
2. Retry within safe limits.
3. Use an approved local fallback.
4. Hold the content if no safe fallback exists.

---

# 19. Implementation roadmap

## Phase 0 — Repository and account readiness

Deliverables:
- Repository created.
- Project structure committed.
- GitHub Actions permissions configured.
- Instagram Professional account and Meta app requirements documented.
- Secrets checklist prepared.
- Brand settings left configurable.

Acceptance criteria:
- A manual workflow can run successfully.
- No secrets exist in Git history.
- Environment validation reports missing prerequisites clearly.

## Phase 1 — Discovery and editorial database

Deliverables:
- Four discovery pipelines.
- Source configuration.
- Normalization and deduplication.
- SQLite schema.
- Topic scoring.
- Research evidence storage.

Acceptance criteria:
- Each pillar can produce candidate topics.
- Duplicate topics are rejected.
- Every selected topic has source references.
- Unsupported topics are held.

## Phase 2 — Scripts and storyboards

Deliverables:
- Local model adapter or deterministic template fallback.
- Four pillar-specific script prompts.
- Storyboard generator.
- Script QA.
- Captions and source notes.

Acceptance criteria:
- Each script has a hook, coherent explanation and payoff.
- Word count and duration are reasonable.
- Claims map to stored evidence.
- No invented sources or statistics.

## Phase 3 — TTS and Reel renderer

Deliverables:
- Kokoro or Piper integration.
- Audio normalization.
- Visual templates.
- FFmpeg renderer.
- Subtitle generation.
- Media QA.

Acceptance criteria:
- All four Reel types render correctly.
- Output meets target dimensions and codecs.
- Narration is intelligible.
- Captions remain inside safe margins.
- Rendering works within the runner resource budget.

## Phase 4 — Feed posts and carousel

Deliverables:
- Two branded post templates.
- Carousel slide generator.
- Captions and sources.
- Image QA.

Acceptance criteria:
- Two single-image posts and one carousel can be generated.
- All images have valid dimensions.
- Text is readable and not clipped.
- Slide ordering is correct.

## Phase 5 — Hosting and Instagram publishing

Deliverables:
- Public asset publishing mechanism.
- Meta API client.
- Reel publishing.
- Image publishing.
- Carousel publishing.
- Retry and idempotency controls.

Acceptance criteria:
- Test media can be published to the intended account.
- Media IDs and timestamps are recorded.
- Retrying a successful job does not duplicate the post.
- API errors are safely recorded.

## Phase 6 — Scheduling and analytics

Deliverables:
- Daily schedules.
- Publishing queue.
- Insights collection.
- Performance report.
- Weekly optimization recommendations.

Acceptance criteria:
- Scheduled workflows execute.
- Missed or failed items remain visible in the queue.
- Metrics are stored when the API provides them.
- The system produces a useful weekly report.

## Phase 7 — Production hardening

Deliverables:
- Monitoring and run summaries.
- Dependency pinning.
- Model caching.
- Cleanup routines.
- Backup/export.
- Documentation.

Acceptance criteria:
- The pipeline can recover from transient failures.
- No secrets appear in logs or artifacts.
- Storage and Actions usage are monitored.
- A failed content item does not block unrelated items.

---

# 20. Operational policies

1. Start with a controlled pilot before enabling all seven daily publications.
2. Use a manual approval mode during development.
3. Switch to automatic publishing only after repeated successful QA and test publishing.
4. Hold any item with uncertain factual support.
5. Do not publish merely to meet a quota.
6. Do not reuse copyrighted music, images or video without appropriate rights.
7. Respect source terms, rate limits and robots policies.
8. Do not use deceptive AI-generated depictions of real events or people.
9. Label synthetic or altered media when required by platform policy or when needed to avoid misleading viewers.
10. Keep a human override to pause all publishing immediately.

---

# 21. Configuration examples

These are illustrative settings, not final production values.

## `config/topics.yml`

```yaml
pillars:
  money_secrets:
    enabled: true
    display_name: "Money Secrets"
    target_reels_per_day: 1
    voice_style: "smart, authoritative, intriguing"

  human_psychology:
    enabled: true
    display_name: "Human Psychology"
    target_reels_per_day: 1
    voice_style: "relatable, conversational, thought-provoking"

  future_is_here:
    enabled: true
    display_name: "Future Is Here"
    target_reels_per_day: 1
    voice_style: "futuristic, exciting, evidence-led"

  daily_mystery:
    enabled: true
    display_name: "The Daily Mystery"
    target_reels_per_day: 1
    voice_style: "suspenseful, documentary-style"

topic_scoring:
  minimum_score: 70
  weights:
    curiosity: 30
    visual_potential: 25
    audience_relevance: 20
    shareability: 15
    source_reliability: 10

deduplication:
  lookback_days: 30
```

## `config/schedule.yml`

```yaml
timezone: "Asia/Kolkata"

daily_targets:
  reels: 4
  feed_posts: 2
  carousels: 1

publishing_slots:
  - time: "09:00"
    format: "reel"
    pillar: "money_secrets"

  - time: "11:00"
    format: "image"
    pillar: "editorial"

  - time: "12:30"
    format: "reel"
    pillar: "human_psychology"

  - time: "15:00"
    format: "carousel"
    pillar: "editorial"

  - time: "17:00"
    format: "reel"
    pillar: "future_is_here"

  - time: "18:30"
    format: "image"
    pillar: "editorial"

  - time: "20:30"
    format: "reel"
    pillar: "daily_mystery"
```

## `config/quality.yml`

```yaml
reel:
  min_duration_seconds: 45
  max_duration_seconds: 60
  width: 1080
  height: 1920
  fps: 30
  video_codec: "h264"
  audio_codec: "aac"

carousel:
  min_slides: 5
  max_slides: 8

editorial:
  minimum_reliable_sources: 2
  require_source_urls: true
  reject_unverified_claims: true
  reject_recent_duplicates: true

publishing:
  require_quality_pass: true
  require_public_media_url: true
  prevent_duplicate_publish: true
```

---

# 22. Definition of done

The project is considered production-ready only when all of the following are true:

- [ ] One GitHub repository contains the complete source and documentation.
- [ ] GitHub Actions runs the workflows without a paid external service.
- [ ] Four content pillars have independent discovery and editorial rules.
- [ ] Topic research preserves traceable source URLs.
- [ ] Duplicate topics are prevented.
- [ ] Scripts and storyboards are generated and checked.
- [ ] Local TTS generates narration.
- [ ] FFmpeg creates valid vertical Reels.
- [ ] Two feed posts and one carousel are generated.
- [ ] All content passes editorial and media QA.
- [ ] Media is hosted at a public URL accessible to Meta.
- [ ] Official Meta API publishing works for the configured account.
- [ ] Idempotency prevents duplicate publishing.
- [ ] Publishing history survives across ephemeral runners.
- [ ] Available insights are stored.
- [ ] Failures are logged and recoverable.
- [ ] No paid API, subscription, trial credit or hidden paid fallback is required.
- [ ] Actual Actions minutes, model runtime, asset storage and bandwidth have been measured in a pilot.
- [ ] A human can pause publishing immediately.

---

# 23. Key risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| GitHub runner resource limits | Model or rendering jobs time out | Benchmark early; use small models and motion graphics |
| Actions minute allowance | Daily pipeline may exceed free usage | Prefer eligible public repository; measure usage and cache dependencies |
| Ephemeral runners | Database and media disappear between jobs | Explicit artifact/state persistence and backups |
| GitHub Pages limits | Media hosting may become unreliable | Monitor bandwidth and storage; treat Pages as a constrained initial option |
| Meta token expiry or permissions | Publishing stops | Secure token management, health checks and clear alerts |
| Poor AI scripts | Low trust and weak engagement | Evidence-first generation and strict QA |
| Copyright violations | Account or content risk | Asset provenance and licence checks |
| Duplicate publishing | Repeated posts | Stable IDs, idempotency and publication records |
| Feed/API changes | Discovery stops | Modular source adapters and graceful failure |
| Low-quality automation at scale | Audience trust declines | Quality gate overrides quantity target |

---

# 24. Final recommendation

Build the system in this order:

1. **Discovery + research + SQLite first.**
2. **Script and storyboard generation second.**
3. **Kokoro/Piper + FFmpeg Reel production third.**
4. **Feed posts and carousel fourth.**
5. **Public media hosting and Meta publishing fifth.**
6. **Analytics and optimization last.**

Do not start by attempting full AI text-to-video generation. It is the least compatible part of the project with a strict ₹0 budget.

The best zero-cost version is a reliable editorial automation engine with strong research, natural narration, original graphics, cinematic motion design and official publishing. Prove the complete daily workload with a three-day pilot before committing to seven posts every day.

**Core principle:** use automation to increase consistency, not to manufacture content regardless of quality.
