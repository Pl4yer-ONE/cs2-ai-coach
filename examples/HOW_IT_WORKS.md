# How CS2 AI Coach Works

A technical walkthrough of the CS2 coaching pipeline with real demo results.

## Demo Analyzed

**Match:** fl0m Mythical LAN Las Vegas 2026 - Phoenix vs Rave (Nuke)  
**Source:** HLTV demo download  
**File Size:** ~300MB  

> ⚠️ Demo files are too large for GitHub. Download from [HLTV](https://hltv.org) or [FACEIT](https://faceit.com).

---

## Pipeline Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Demo File     │────▶│   Demo Parser    │────▶│ Feature Extractor │
│   (.dem)        │     │  (demoparser2)   │     │                   │
└─────────────────┘     └──────────────────┘     └─────────┬─────────┘
                                                           │
                              ┌────────────────────────────▼────────────────────────────┐
                              │                    Metrics Modules                       │
                              │  ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐    │
                              │  │   Aim   │ │ Positioning │ │ Utility │ │ Economy │    │
                              │  │  HS%    │ │  Exposed    │ │ Flashes │ │ Force   │    │
                              │  │  Spray  │ │  Untrade    │ │ Nades   │ │ Buys    │    │
                              │  └─────────┘ └─────────────┘ └─────────┘ └─────────┘    │
                              └────────────────────────────┬────────────────────────────┘
                                                           │
                              ┌─────────────────────────────▼─────────────────────────────┐
                              │                  Mistake Classifier                        │
                              │  • Rule-based thresholds                                   │
                              │  • Confidence scoring                                      │
                              │  • Severity levels (🔴 high, 🟡 medium, 🟢 low)            │
                              └─────────────────────────────┬─────────────────────────────┘
                                                           │
                        ┌──────────────────────────────────┼──────────────────────────────┐
                        │                                  │                              │
                        ▼                                  ▼                              ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │  Fallback Msgs  │              │  Ollama (LLM)   │              │ Report Generator│
              │  (no Ollama)    │              │  Phrases only   │              │  JSON + MD      │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
```

---

## Real Test Results

### Input
```bash
python main.py --demo phoenix-vs-rave-m1-nuke.dem --ollama --markdown --verbose
```

### Output Summary
| Metric | Value |
|--------|-------|
| Players Analyzed | 10 |
| Kills Parsed | 103 |
| Damages Parsed | 452 |
| Issues Classified | 4 |
| Processing Time | ~5 seconds |

### Issues Found
| Category | Count | Severity |
|----------|-------|----------|
| POSITIONING (untradeable deaths) | 3 | 🟡 medium, 🔴 high |
| AIM (low headshot %) | 1 | 🟡 medium |

---

## Sample NLP Coaching Feedback

The classifier identifies issues → Ollama phrases them naturally.

### Player with 57.1% untradeable deaths:
> *"Player, focus on improving your positioning to reduce untradeable deaths, as you're currently experiencing an unacceptable 57.1% rate, and aim to get this number below 30%."*

### Player with 20% headshot rate:
> *"Player, to improve your headshot percentage from 20% to over 30%, focus on increasing your headshots per match by taking calculated risks and aiming for at least one headshot every 2-3 kills."*

### Player with 62.5% untradeable deaths (🔴 high severity):
> *"Player, you're currently experiencing an untradeable death rate of 62.5%...focus on improving your positioning to reduce this statistic by at least 32 percentage points."*

---

## Key Design Decisions

### 1. NLP Never Decides
The LLM (Ollama) **only phrases** the output. It cannot:
- Change what mistakes are identified
- Modify confidence scores
- Add new categories

### 2. Deterministic Classification
All mistakes are identified by **rule-based thresholds**:
```python
# Example from config.py
AIM_THRESHOLDS = {
    "headshot_percentage": {
        "poor": 0.20,      # Below 20% = needs improvement
        "average": 0.30,   # 20-30% = average
        "good": 0.45,      # 30-45% = good
    }
}
```

### 3. Confidence Scoring
Every classification includes confidence based on:
- Sample size (more events = higher confidence)
- Consistency of the issue
- Severity impact

### 4. Fallback When Offline
If Ollama is unavailable, pre-written messages are used:
```python
FALLBACK_MESSAGES = {
    MistakeCategory.AIM: {
        "headshot_low": "Your headshot percentage is below average. Focus on crosshair placement..."
    }
}
```

---

## Files Generated

| File | Description |
|------|-------------|
| [`sample_report.md`](sample_report.md) | Basic analysis (no NLP) |
| [`nlp_report.md`](nlp_report.md) | Analysis with Ollama coaching |
| [`sample_report.json`](sample_report.json) | JSON export |
| [`nlp_report.json`](nlp_report.json) | JSON with NLP feedback |

---

## How to Reproduce

```bash
# 1. Get a demo file
# Download from HLTV, FACEIT, or your Steam replays

# 2. Run analysis
cd cs2-ai-coach
source venv/bin/activate
python main.py --demo your_match.dem --ollama --markdown --verbose

# 3. View results
cat reports/coaching_report_*.md
```
