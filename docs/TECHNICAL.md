# Technical Documentation

## 1. Introduction

### 1.1 Purpose
FragAudit is a rule-based analysis tool for Counter-Strike 2 (CS2) demo files. It extracts positional and tactical features from match recordings and identifies common positioning mistakes that affect round outcomes.

### 1.2 Scope
This document describes the system architecture, algorithms, and data structures used in FragAudit. It is intended for developers extending the tool and researchers evaluating the methodology.

### 1.3 Definitions
| Term | Definition |
|------|------------|
| Demo File | Binary recording of a CS2 match (.dem format) |
| Trade | When a teammate kills an enemy within 3 seconds of a teammate's death |
| Dry Peek | Challenging an angle without flash or smoke support |
| Trade Potential Score | Percentage of deaths where a teammate was positioned to trade |

---

## 2. System Architecture

### 2.1 Overview

<div align="center">

![Architecture Diagram](architecture.png)

</div>

The system follows a pipeline architecture with five stages:

1. **Parser** — Extracts raw events from demo files
2. **Feature Extractor** — Computes per-player metrics
3. **Mistake Classifier** — Identifies tactical errors
4. **Report Generator** — Produces JSON, HTML, CSV output
5. **NLP Phrasing** (Optional) — Generates natural language advice via Ollama

### 2.2 Module Dependencies

```
src/
├── parser/
│   └── demo_parser.py       # Demo file parsing (demoparser2)
├── features/
│   └── extractor.py         # Feature extraction (1286 lines)
├── classifier/
│   ├── mistake_classifier.py # Rule-based classification
│   └── death_classifier.py   # Death cause analysis
├── report/
│   ├── generator.py         # JSON + Markdown + CLI output
│   └── html_reporter.py     # HTML report generation
├── nlp/
│   └── ollama_phrasing.py   # LLM-based phrasing
└── maps/
    └── zones.py             # Map coordinate → callout mapping
```

---

## 3. Algorithms

### 3.1 Trade Detection

The trade detection algorithm identifies whether a death could be traded:

```
Algorithm: DETECT_TRADE(death_event)
Input: death_event with killer, victim, tick, positions
Output: Boolean (was_traded)

1. Find all kills within TRADE_WINDOW (3 seconds) after death
2. For each subsequent kill K:
   a. If K.victim == death_event.killer:
      - Return TRUE (killer was traded)
3. Return FALSE
```

**Parameters:**
- `TRADE_WINDOW_SECONDS = 3.0`
- `TRADE_DIST_UNITS = 500` (max distance for expected trade)

### 3.2 Trade Potential Score

```
Algorithm: CALCULATE_TRADE_POTENTIAL(player)
Input: PlayerFeatures with death_contexts
Output: Integer 0-100

1. traded_deaths = count(deaths where was_traded == TRUE)
2. total_deaths = player.deaths
3. IF total_deaths == 0: RETURN 100
4. RETURN floor(100 * traded_deaths / total_deaths)
```

**Interpretation:**
| Score | Label | Meaning |
|-------|-------|---------|
| 60-100 | Good | Consistently positioned for trades |
| 30-59 | Average | Some positioning issues |
| 0-29 | Poor | Frequently dying untradeably |

### 3.3 Dry Peek Detection

```
Algorithm: DETECT_DRY_PEEK(death_context)
Input: DeathContext with flash_data, smoke_data, positions
Output: Boolean

1. Check flash support:
   a. Any teammate flash within 2 seconds before death?
   b. Was victim blinded at time of death?
2. Check smoke support:
   a. Any smoke between victim and killer?
3. IF no flash support AND no smoke support:
   RETURN TRUE (dry peek)
4. RETURN FALSE
```

### 3.4 Role Detection

Roles are assigned based on behavioral patterns:

| Role | Primary Indicators |
|------|-------------------|
| Entry | First contact, high entry_death_ratio |
| AWPer | AWP kills > 30% of total |
| Support | High flash_assists, low entry attempts |
| Lurker | High avg_teammate_dist, flanking positions |
| Trader | Deaths in support positions, trades out teammates |

---

## 4. Data Structures

### 4.1 PlayerFeatures

```python
@dataclass
class PlayerFeatures:
    # Identity
    player_id: str
    player_name: str
    
    # Core Stats
    kills: int
    deaths: int
    headshot_percentage: float
    damage_per_round: float
    
    # Trade Metrics
    tradeable_deaths: int
    untradeable_death_ratio: float
    trade_potential_score: int  # 0-100
    
    # Positioning
    avg_teammate_dist: float
    exposed_deaths: int
    
    # Role
    detected_role: str
    entry_deaths: int
    entry_kills: int
```

### 4.2 ClassifiedMistake

```python
@dataclass
class ClassifiedMistake:
    tick: int
    round_num: int
    round_time_seconds: float
    map_area: str
    player_name: str
    mistake_type: str
    details: str
    severity: float        # 0.0-1.0
    severity_label: str    # HIGH, MED, LOW
    correction: str        # Coaching advice
```

### 4.3 DeathContext

```python
@dataclass
class DeathContext:
    tick: int
    round_num: int
    map_area: str
    killer_id: str
    weapon: str
    was_traded: bool
    nearest_teammate_distance: float
    teammates_nearby: int
    had_flash_support: bool
    is_entry_frag: bool
    round_time: str  # "early", "mid", "late"
```

---

## 5. Output Formats

### 5.1 JSON Report

```json
{
  "meta": {
    "map": "de_ancient",
    "demo_file": "match.dem",
    "generated_at": "2026-01-13T21:18:00"
  },
  "summary": {
    "total_players_analyzed": 10,
    "total_mistakes_found": 7,
    "mistakes_by_type": {"dry_peek": 7}
  },
  "players": {
    "76561198088906330": {
      "player_name": "MarKE",
      "stats": {
        "kills": 20,
        "deaths": 8,
        "kd_ratio": 2.5,
        "trade_potential_score": 50
      },
      "mistakes": []
    }
  }
}
```

### 5.2 CSV Export

| Player | Round | Time | Location | Type | Severity | Details | Fix |
|--------|-------|------|----------|------|----------|---------|-----|
| mds | 0 | 0:30 | T Spawn | dry_peek | MED | Challenged without utility | Use teammate flash |

### 5.3 HTML Report

<div align="center">

![Report Overview](report_overview.png)

*Figure 1: HTML report showing issue distribution and player summary*

</div>

<div align="center">

![Player Cards](report_players.png)

*Figure 2: Player cards with Trade Score and mistake details*

</div>

---

## 6. Configuration

### 6.1 Detection Thresholds

| Parameter | Value | Description |
|-----------|-------|-------------|
| TRADE_WINDOW_SECONDS | 3.0 | Max time for trade |
| TRADE_DIST_UNITS | 500 | Max distance for trade potential |
| DRY_PEEK_FLASH_WINDOW | 2.0 | Seconds before death to check flash |
| UNTRADEABLE_DIST | 400 | Distance threshold for untradeable |

### 6.2 Severity Thresholds

| Severity | Threshold | Color |
|----------|-----------|-------|
| HIGH | ≥ 0.80 | Red |
| MED | 0.50-0.79 | Yellow |
| LOW | < 0.50 | Green |

---

## 7. Limitations

1. **Round timing approximation** — Round phase (early/mid/late) is estimated from tick offset, not exact clock
2. **Map callouts** — Coordinate-to-callout mapping may show "Unknown" for unmapped areas
3. **Flash detection** — Only detects teammate flashes, not self-flashes or enemy flashes
4. **Role classification** — Heuristic-based, not validated against coach-labeled data

---

## 8. References

1. demoparser2 — CS2 demo parsing library
2. Valve Developer Wiki — Demo file format specification
3. HLTV — Win probability statistics by player advantage

---

*Last updated: 2026-01-13*
