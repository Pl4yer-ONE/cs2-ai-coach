# FragAudit: A Deterministic Performance Auditing Engine for Counter-Strike 2 Demo Analysis

---

## Abstract

This paper presents FragAudit, a deterministic performance auditing engine designed for forensic analysis of Counter-Strike 2 (CS2) gameplay demonstrations. The system implements Win Probability Added (WPA)-based impact scoring, exploit-resistant rating calibration, and visual demo playback without requiring the game client. FragAudit addresses critical gaps in existing esports analytics by providing transparent, reproducible performance metrics that resist common stat-padding exploits. The architecture comprises five core modules: demo parsing, feature extraction, scoring engine, mistake classification, and visual playback. Experimental evaluation demonstrates stable rating outputs across diverse match scenarios with 26 unit tests validating edge case handling.

**Keywords**: Esports Analytics, Counter-Strike 2, Performance Metrics, Demo Analysis, Win Probability Added, Reinforcement Learning

---

## I. Introduction

### A. Background

Counter-Strike 2 (CS2) is a competitive first-person shooter with a professional esports ecosystem. Performance evaluation in CS2 traditionally relies on surface-level statistics such as Kill-Death Ratio (KDR) and Average Damage per Round (ADR). These metrics fail to capture contextual performance factors including round phase, teammate positioning, and trade dynamics.

### B. Problem Statement

Existing CS2 analytics tools suffer from three fundamental limitations:

1. **Inflated Metrics**: Exit frags (kills during round cleanup) artificially boost statistics without contributing to round outcomes.
2. **Role Blindness**: A support player and entry fragger are evaluated identically despite fundamentally different objectives.
3. **Exploit Vulnerability**: Players can manipulate statistics through exit hunting, trade baiting, and low-risk positioning.

### C. Contribution

FragAudit addresses these limitations through:

- Deterministic, exploit-resistant rating algorithms
- Behavior-based role classification
- WPA-weighted impact scoring
- Visual demo playback without CS2 installation

---

## II. Related Work

### A. Esports Analytics

Prior work in esports analytics includes HLTV Rating 2.0 [1], which introduced multi-factor rating systems. However, HLTV's methodology remains proprietary and non-reproducible.

### B. Demo Parsing

The demoparser2 library [2] provides low-level access to CS2 demo files. FragAudit extends this foundation with higher-level feature extraction and scoring.

### C. Win Probability Models

Win Probability Added (WPA) originated in baseball analytics [3] and has been adapted for esports contexts. FragAudit implements a CS2-specific WPA model based on round phase and player alive states.

---

## III. System Architecture

### A. Overview

FragAudit follows a modular pipeline architecture:

```
Demo File (.dem)
      │
      ▼
┌─────────────┐
│ Demo Parser │ ← demoparser2 / awpy
└─────┬───────┘
      │ ParsedDemo
      ▼
┌─────────────────┐
│ Feature Extract │ ← PlayerFeatures per player
└─────┬───────────┘
      │
      ▼
┌──────────────┐
│ Score Engine │ ← Impact, Aim, Positioning scores
└─────┬────────┘
      │
      ▼
┌────────────────────┐
│ Mistake Classifier │ ← Behavioral pattern detection
└─────┬──────────────┘
      │
      ▼
┌──────────────────┐
│ Report Generator │ ← JSON, Markdown, Heatmaps
└──────────────────┘
```

### B. Demo Parser Module

The parser module interfaces with demoparser2 and awpy libraries to extract:

- Player positions (x, y, z coordinates per tick)
- Kill events with attacker, victim, weapon, headshot flags
- Round state transitions
- Bomb plant/defuse events

**Tickrate Detection**: FragAudit dynamically detects demo tickrate (64 or 128) from header metadata rather than hardcoding assumptions.

### C. Feature Extraction Module

For each player, the following features are computed:

| Feature | Description |
|---------|-------------|
| `kills` | Total kills |
| `deaths` | Total deaths |
| `kdr` | Kill-death ratio |
| `adr` | Average damage per round |
| `hs_percentage` | Headshot percentage |
| `entry_attempts` | First contact engagements |
| `entry_success` | Successful entry rate |
| `tradeable_deaths` | Deaths with teammate nearby |
| `untradeable_deaths` | Isolated deaths |
| `exit_frags` | Kills during round cleanup |
| `clutch_wins` | 1vN situations won |
| `flash_assists` | Enemies blinded for teammate kills |
| `kast_percentage` | Kill/Assist/Survive/Trade rate |

### D. Role Classification

FragAudit implements behavior-based role detection:

| Role | Detection Criteria |
|------|-------------------|
| AWPer | AWP kills ≥ 5, AWP kill ratio > 0.3 |
| Entry | Entry attempts ≥ 5, entry success > 0.35 |
| Support | Flash assists ≥ 3, low entry involvement |
| Trader | Tradeable ratio > 0.35 |
| Rotator | Swing kills ≥ 2, avg distance > 600u |
| SiteAnchor | Default for defenders |
| Lurker | Avg teammate distance > 650u |

### E. Scoring Engine

The scoring engine computes a composite rating from 0-100:

**Raw Impact Score**:
```
raw_impact = Σ(kill_value × wpa_multiplier) 
           + entry_bonus 
           + clutch_bonus 
           - death_penalty
```

**Role-Adjusted Score**:
```
adjusted = raw_impact × role_multiplier × penalty_factors
```

**Penalty Factors**:

| Rule | Trigger | Effect |
|------|---------|--------|
| Kill Gate | raw > 105, kills < 18 | 0.90× |
| Exit Tax | exit_frags ≥ 8 | 0.85× |
| Low KDR Cap | KDR < 0.8 | max 75 |
| Trader Ceiling | Trader, KDR < 1.0 | max 80 |
| Rotator Ceiling | Rotator role | max 95 |
| Floor Clamp | Always | min 15 |

### F. Demo Player Module

FragAudit includes a standalone visual demo player built with Pygame:

**Features**:
- Player position rendering with team colors
- Kill feed overlay
- Round timeline with seek controls
- Variable playback speed (0.25× to 4×)
- O(log n) tick lookup via binary search
- LRU cache (500 entries) for smooth playback

---

## IV. Implementation

### A. Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Demo Parsing | demoparser2, awpy |
| Data Processing | Polars, Pandas, NumPy |
| Visualization | Matplotlib, Pygame |
| Testing | pytest |

### B. Performance Optimizations

1. **Binary Search Indexing**: Pre-built tick index enables O(log n) frame lookup
2. **LRU Caching**: OrderedDict-based cache with proper eviction
3. **Delta Time Clamping**: MAX_DT = 100ms prevents jumps on window focus loss
4. **Frame Skipping**: Automatic adjustment at high playback speeds

---

## V. Evaluation

### A. Test Coverage

FragAudit includes 26 unit tests covering:

- Exit frag tax triggers
- Low KDR cap enforcement
- Rotator ceiling validation
- Kill gate activation
- Trader ceiling limits
- Floor clamp verification
- Smurf detection logic
- Breakout rule conditions

### B. Rating Calibration

Sample calibration results from professional match analysis:

| Player | Role | Raw | Final | Adjustment |
|--------|------|-----|-------|------------|
| MarKE | Entry | 120 | 92 | Role cap |
| Qlocuu | Rotator | 115 | 80 | Rotator ceiling + Exit tax |
| SaVage | Support | 95 | 75 | Low KDR cap |
| Dycha | Trader | 110 | 79 | Trader ceiling + Kill gate |

---

## VI. Limitations and Future Work

### A. Current Limitations

1. **Map Coverage**: Limited radar images for newer maps
2. **Utility Tracking**: Smoke/molotov impact not fully quantified
3. **Team Context**: Individual ratings, not team synergy metrics

### B. Future Work

1. Timeline analytics with kill event markers
2. Player comparison across multiple matches
3. Trend tracking and performance progression
4. Team composition analysis

---

## VII. Conclusion

FragAudit provides a deterministic, transparent approach to CS2 performance auditing. By implementing exploit-resistant calibration and behavior-based role detection, the system addresses fundamental limitations of existing esports analytics tools. The open-source implementation enables reproducibility and community contribution under the PolyForm Noncommercial License.

---

## References

[1] HLTV.org, "HLTV Rating 2.0," 2017. [Online]. Available: https://www.hltv.org/news/20695/introducing-hltv-rating-20

[2] L. Abramov, "demoparser2: High-performance CS2 demo parser," GitHub, 2023. [Online]. Available: https://github.com/LaihoE/demoparser

[3] T. Tango, M. Lichtman, and A. Dolphin, "The Book: Playing the Percentages in Baseball," Potomac Books, 2007.

[4] PolyForm Project, "PolyForm Noncommercial License 1.0.0," 2019. [Online]. Available: https://polyformproject.org/licenses/noncommercial/1.0.0/

---

## Appendix A: Installation

```bash
git clone https://github.com/Pl4yer-ONE/FragAudit.git
cd FragAudit
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Appendix B: Usage

```bash
# Analyze demo
python main.py analyze --demo match.dem

# Play demo visually
python main.py play match.dem

# Generate heatmaps
python main.py analyze --demo match.dem --heatmap
```

## Appendix C: API Reference

```python
from src.metrics.scoring import ScoreEngine

rating = ScoreEngine.compute_final_rating(
    scores={"raw_impact": 100},
    role="Entry",
    kdr=1.2,
    kills=18,
    exit_frags=3
)
```

---

*Manuscript submitted: January 2026*

*Repository: https://github.com/Pl4yer-ONE/FragAudit*

*License: PolyForm Noncommercial 1.0.0*
