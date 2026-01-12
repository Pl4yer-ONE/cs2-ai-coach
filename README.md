<div align="center">

# 🎮 CS2 AI Coach

### Pro-Grade Performance Analytics for Counter-Strike 2

[![Version](https://img.shields.io/badge/version-v2.1.0-brightgreen.svg)](https://github.com/Pl4yer-ONE/cs2-ai-coach/releases/tag/v2.1.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HLTV Alignment](https://img.shields.io/badge/HLTV%20Alignment-80%25-success.svg)](#validation-results)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

**Parse demos → Extract features → Detect roles → Calibrate ratings → Expose frauds**

[Quick Start](#-quick-start) •
[Features](#-features) •
[Rating System](#-rating-system) •
[API Reference](#-api-reference) •
[Contributing](#-contributing)

---

### 🚀 v2.1.0 Release — Public Beta

✅ **80% HLTV Top-3 MVP Alignment** — Validated against pro matches  
✅ **Win Probability Added (WPA)** — Moneyball-style impact metric  
✅ **Per-Team Role Quotas** — Realistic 1 AWP, 2 Entry per team  
✅ **Confidence Scores** — Know when ratings are reliable  
✅ **Production-Grade API** — Clean JSON, documented metrics  

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Demo Parsing** | Parse CS2 `.dem` files with full round context |
| 📊 **Win Probability Added** | Moneyball metric — delta win prob per kill |
| 🎯 **Auto Role Detection** | Entry, Anchor, AWPer, Support, Lurker (per-team quotas) |
| ⚡ **Swing Kills** | Track momentum-shifting kills (man-advantage flips) |
| 🧮 **Z-Score Rating** | Role-based normalization with brutal calibration |
| 🚨 **Exploit Resistance** | Death tax, exit frag discount, smurf detection |
| 📈 **Confidence Metric** | Know when you have enough data |
| 🗺️ **Heatmaps** | Visual death/kill positioning |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Analyze Demos

```bash
# Single demo
python -m src.main your_match.dem --output outputs/

# Batch analyze folder
python -m src.main /path/to/demos/ --output outputs/batch
```

### Generate Leaderboard

```bash
python leaderboard.py outputs/batch
```

---

## 📈 Rating System

### Pipeline
```
raw_impact → role_zscore → map_weight → kast_bonus → penalties → role_cap
```

### Impact Formula

| Component | Formula | Purpose |
|-----------|---------|---------|
| Kill Value | `won_round * 8 + lost_round * 0.5` | Context matters |
| Entry Points | `opening_won * 14 + opening_lost * 1` | First bloods valued |
| Clutch Points | `1v1 * 15 + 1vN * 35` | Hero plays rewarded |
| **WPA Bonus** | `total_wpa * 15` (diminishing >2.5) | Round swing impact |
| Swing Kills | `swing_score * 1.0` | Momentum shifts |
| Death Penalty | `tradeable * 0.5 + untradeable * 4` | Punish feeding |

### Anti-Exploit Features

| Feature | Implementation |
|---------|----------------|
| **Multiplicative Death Tax** | 18+ deaths = -20%, 21+ = -40%, 24+ = -50% |
| **Exit Frag Discount** | >3 exit frags = -2 WPA per extra |
| **Raw Impact Soft Cap** | >120 gets 0.3x excess |
| **WPA Diminishing Returns** | >2.5 WPA gets 0.5x excess |
| **Per-Team Role Quotas** | Max 1 AWP, 2 Entry per team |

### Role Baselines

| Role | Mean | Std | Max Cap |
|------|------|-----|---------|
| AWPer | 46.4 | 22.3 | 95 |
| Entry | 42.6 | 22.6 | 92 |
| Anchor | 28.6 | 24.1 | 88 |

---

## 📊 Sample Output

### JSON Report Structure

```json
{
  "meta": {
    "version": "2.1.0",
    "metric_definitions": {
      "wpa": "Per-match sum of round win probability deltas",
      "final_rating": "Composite score (0-100) with role adjustments",
      "confidence": "Rating reliability (0-100) based on sample size"
    }
  },
  "players": {
    "76561198xxx": {
      "name": "hypex",
      "role": "AWPer",
      "final_rating": 95,
      "confidence": 93,
      "scores": {
        "impact": 100,
        "raw_impact": 129.9,
        "aim": 88,
        "positioning": 45
      },
      "stats": {
        "kills": 27,
        "deaths": 16,
        "wpa": 5.62,
        "kast_percentage": 82.5
      }
    }
  }
}
```

### Leaderboard Example

```
=== TOP 10 PLAYERS ===
name          role     rating  wpa    confidence
hypex         AWPer    95      13.88  93
Dycha         Entry    88      9.75   91
REZ           Anchor   88      7.13   93
MarKE         Entry    85      6.47   89
Qlocuu        Anchor   81      11.41  92
```

---

## 🔬 Validation Results

### HLTV Cross-Validation (13 Matches)

| Metric | Result | Target |
|--------|--------|--------|
| Exact #1 Match | 20% | — |
| Top-2 Capture | 60% | 70% |
| **Top-3 Capture** | **80%** | 70% ✅ |

### Stress Test Results

| Test | Status |
|------|--------|
| Exit Frag Penalty | ✅ Pass |
| Death Tax Working | ✅ Pass |
| Impact Clamping | ✅ Pass |
| WPA Diminishing | ✅ Pass |
| Role Quotas | ✅ Pass |
| Advice Randomization | ✅ Pass |
| Confidence Metric | ✅ Pass |

---

## 📁 Project Structure

```
cs2-ai-coach/
├── src/
│   ├── parser/              # Demo parsing (demoparser2)
│   ├── features/            # Feature extraction + WPA
│   │   └── extractor.py     # WinProbabilityModel
│   ├── metrics/
│   │   ├── scoring.py       # Impact + rating calculation
│   │   ├── calibration.py   # Role baselines, map weights
│   │   └── role_classifier.py # Per-team role detection
│   ├── classifier/          # Mistake detection
│   └── report/
│       ├── json_reporter.py # JSON output + confidence
│       └── drills.py        # Randomized advice
├── leaderboard.py           # Aggregated ranking tool
├── TEST_REPORT.txt          # Full validation report
└── requirements.txt
```

---

## 📖 API Reference

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `final_rating` | `int (0-100)` | Composite score with role adjustments |
| `confidence` | `int (0-100)` | Rating reliability based on sample size |
| `wpa` | `float` | Win Probability Added (per-match sum) |
| `raw_impact` | `float` | Unclamped impact for calibration |
| `kast_percentage` | `float` | Kill/Assist/Survived/Traded % |

### Role Detection Rules

| Role | Criteria |
|------|----------|
| AWPer | AWP kills ≥25% of total AND ≥2 AWP kills |
| Entry | Top 4 entry attempts AND (success ≥25% OR ≥2 entry kills) |
| Support | Flash thrown >1.2x team average AND ≥3 flashes |
| Lurker | Avg teammate distance >800 units |
| Anchor | Default (plays for trades) |

### Per-Team Quotas

- **Max AWPers per team**: 1
- **Max Entries per team**: 2
- Excess demoted to Anchor by qualification score

---

## 🛠️ Configuration

Edit `src/metrics/calibration.py`:

```python
ROLE_BASELINES = {
    'Entry':  {'mean': 42.6, 'std': 22.6, 'max': 92},
    'Anchor': {'mean': 28.6, 'std': 24.1, 'max': 88},
    'AWPer':  {'mean': 46.4, 'std': 22.3, 'max': 95},
}

MAP_WEIGHTS = {
    'de_nuke': {'Entry': 0.85, 'Anchor': 1.15, 'AWPer': 1.00},
    'de_dust2': {'Entry': 1.10, 'Anchor': 0.95, 'AWPer': 1.05},
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development

```bash
# Run tests
pytest tests/

# Analyze single demo
python -m src.main demo.dem --output outputs/
```

---

## 📜 Credits

- [demoparser2](https://github.com/LaihoE/demoparser) — Fast CS2 demo parsing
- Inspired by HLTV rating methodology and Moneyball analytics

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

### ⭐ Star this repo if you find it useful!

**This is not a toy. This is pro-grade analytics.**

Made for serious competitive play 🎯

---

*v2.1.0 — Public Beta — HLTV Validated*

</div>
