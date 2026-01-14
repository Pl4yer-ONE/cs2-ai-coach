# Technical Documentation

## 1. Introduction

### 1.1 Purpose
FragAudit is a rule-based analysis engine for Counter-Strike 2 (CS2) demo files. It extracts tactical features and provides explainable predictions without machine learning dependencies.

### 1.2 Version
**v3.8.0** — Backend Complete

### 1.3 Definitions
| Term | Definition |
|------|------------|
| Demo File | Binary recording of a CS2 match (.dem format) |
| WPA | Win Probability Added — impact of an action on round outcome |
| Trade | Kill on enemy within 3s of teammate's death |
| Dry Peek | Challenging angle without flash/smoke support |

---

## 2. Backend Pillars

FragAudit is built on 5 core analysis modules:

| # | Module | Version | Purpose |
|---|--------|---------|---------|
| 1 | **Mistakes** | v3.4 | Detect tactical errors (OVERPEEK, NO_TRADE_SPACING) |
| 2 | **Roles** | v3.5 | Classify player roles per round (ENTRY, LURK, ANCHOR) |
| 3 | **WPA** | v3.6 | Contextual win probability with multipliers |
| 4 | **Strategy** | v3.7 | Cluster team patterns (EXECUTE, RUSH, DEFAULT) |
| 5 | **Prediction** | v3.8 | Forecast round/player outcomes (explainable) |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRAGAUDIT v3.8                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Parser  │───▶│   Feature    │───▶│   Backend Pillars    │  │
│  │          │    │   Extractor  │    │                      │  │
│  │demoparser│    │              │    │  ┌────────────────┐  │  │
│  └──────────┘    └──────────────┘    │  │ 1. Mistakes    │  │  │
│                                       │  │ 2. Roles       │  │  │
│                                       │  │ 3. WPA         │  │  │
│                                       │  │ 4. Strategy    │  │  │
│                                       │  │ 5. Prediction  │  │  │
│                                       │  └────────────────┘  │  │
│                                       └──────────────────────┘  │
│                                                 │               │
│                                                 ▼               │
│                                       ┌──────────────────────┐  │
│                                       │   Report Generator   │  │
│                                       │   JSON/HTML/Radar    │  │
│                                       └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 Module Structure

```
src/
├── parser/           # Demo file parsing (demoparser2)
├── mistakes/         # v3.4 - Error detection engine
│   ├── detectors.py  # 5 mistake types
│   └── exporter.py   # JSON export
├── roles/            # v3.5 - Role intelligence
│   └── classifier.py # Evidence-based roles
├── wpa/              # v3.6 - Contextual WPA
│   └── contextual_wpa.py
├── strategy/         # v3.7 - Strategy clustering
│   └── fingerprint.py
├── predict/          # v3.8 - Win/impact prediction
│   ├── win_model.py
│   └── player_model.py
├── radar/            # Custom radar replay (NOT boltobserv)
├── timeline/         # Round event streams
├── synergy/          # Team chemistry
└── report/           # JSON/HTML/CSV output
```

---

## 4. Prediction Model Math

### 4.1 Round Win Predictor

**Type**: Hand-written logistic regression  
**Output**: P(round_win) ∈ [0.05, 0.95]

#### Features:

| Feature | Scaling | Coefficient |
|---------|---------|-------------|
| Economy | tanh(diff/3000) | 0.8 |
| Man Advantage | diff/5 | 0.6 |
| Roles | capped at 1.0 | 0.15 |
| Mistakes | capped at -0.6 | -0.10 each |
| Strategy | categorical | ±0.08 |

#### Economy Scaling (tanh):
```
$1,000 diff → 0.32 → +0.26 contribution
$3,000 diff → 0.76 → +0.61 contribution
$6,000 diff → 0.96 → +0.77 contribution (saturates)
```

#### Confidence:
```python
confidence = min(1.0, abs(log_odds) / 2.0)
```
*Confidence reflects prediction strength, not data presence.*

### 4.2 Player Impact Predictor

**Output**: 
- P(positive_impact) ∈ [0.15, 0.85]
- Expected rating ∈ [0.7, 1.7]

#### Features:

| Feature | Coefficient |
|---------|-------------|
| Historical rating deviation | 0.5 |
| Consistency (low variance) | 0.2 |
| Role match | 0.15 |
| Economy comfort | 0.1 |
| Recent mistakes | -0.2 each (capped) |

---

## 5. Mistake Detection

### 5.1 Error Types

| Type | Trigger | Severity |
|------|---------|----------|
| OVERPEEK | Death without trade within 3s | MED-HIGH |
| NO_TRADE_SPACING | >400u from teammates | HIGH |
| ROTATION_DELAY | Late to site retake | MED |
| UTILITY_WASTE | Flash/smoke unused | LOW |
| POSTPLANT_MISPLAY | Wrong position after plant | MED |

### 5.2 Detection Algorithm

```python
def detect_overpeek(kill_event):
    if kill_event.was_traded:
        return None
    if teammates_within_trade_distance(kill_event) < 1:
        return DetectedMistake(
            type=ErrorType.OVERPEEK,
            severity=Severity.MED,
            wpa_loss=calculate_contextual_wpa(...)
        )
```

---

## 6. Role Classification

### 6.1 Role Types

| Role | Indicators |
|------|------------|
| ENTRY | First contact, high entry_death_ratio |
| LURK | High avg_teammate_dist, flanking |
| ANCHOR | Site holds, low mobility |
| SUPPORT | Flash assists, trades |
| ROTATOR | Cross-map movement |

### 6.2 Confidence Score

```python
confidence = evidence_count / max_evidence
```

Evidence: trade kills, flash assists, opening duels, bomb plants.

---

## 7. Strategy Clustering

### 7.1 T-Side Patterns

| Pattern | Detection Signal |
|---------|------------------|
| EXECUTE_A/B | First contact at site, utility usage |
| RUSH_A/B | Early contact, no utility |
| SPLIT_A/B | Multiple contact points |
| DEFAULT_T | No clear pattern |
| FAKE | Contact opposite to plant site |

### 7.2 CT-Side Patterns

| Pattern | Detection Signal |
|---------|------------------|
| DEFAULT_CT | Standard setup |
| STACK_A/B | Heavy presence at one site |
| AGGRESSIVE | Early map control |

---

## 8. Contextual WPA

### 8.1 Multipliers

| Context | Multiplier |
|---------|------------|
| Eco round | 1.6x |
| Anti-eco | 0.6x |
| 1v1 clutch | 1.5x |
| 1v2 clutch | 2.0x |
| 1v3+ clutch | 2.5-4.0x |
| Late round | 1.3x |
| Bomb planted | 1.5x |

### 8.2 Calculation

```python
weighted_wpa = base_wpa * economy_mult * clutch_mult * time_mult
```

*Multipliers can stack. Max observed: ~9x for eco clutch bomb.*

---

## 9. Output Formats

| Format | Content |
|--------|---------|
| JSON | Raw data, all fields |
| HTML | Visual report, player cards |
| CSV | Timeline events |
| MP4 | Radar replay video |

---

## 10. Limitations

1. **Prediction coefficients are calibrated intuition** — not statistically trained
2. **Strategy detection is v1** — uses first contact only, no utility patterns
3. **No cross-round memory** — each round analyzed independently
4. **WPA can stack high** — consider capping for production
5. **Radar is custom** — not boltobserv, uses matplotlib

---

## 11. Dependencies

| Package | Purpose |
|---------|---------|
| demoparser2 | Demo file parsing |
| pandas | Data manipulation |
| matplotlib | Radar visualization |
| pytest | Testing (174 tests) |

---

*Last updated: 2026-01-14 — v3.8.0*
