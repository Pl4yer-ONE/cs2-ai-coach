<div align="center">

# 🎮 CS2 AI Coach

**Pro-grade performance analytics for Counter-Strike 2**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Pl4yer-ONE/cs2-ai-coach?style=social)](https://github.com/Pl4yer-ONE/cs2-ai-coach)

> [!NOTE]
> **Current Status: 🧪 Public Test Phase (Beta)**
> The S-Tier Rating System & WPA Analytics are currently undergoing large-scale verification against pro matches.

*Parse demos → Extract features → Calibrate ratings → Expose frauds*

[**Quick Start**](#-quick-start) •
[**Rating System**](#-rating-system) •
[**Examples**](#-sample-output) •
[**Contributing**](#-contributing)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Demo Parsing** | Parse CS2 `.dem` files with full round context |
| 📊 **Feature Extraction** | Kills, deaths, KAST, clutches, swing kills, trades |
| 🎯 **Role Detection** | Auto-classify Entry, Anchor, AWPer, Support, Lurker |
| ⚡ **Swing Kills** | Track momentum-shifting kills (man-advantage flips) |
| 🧮 **Z-Score Rating** | Role-based normalization with brutal calibration |
| 🚨 **Smurf Detection** | Flag and penalize stat-padders |
| 📊 **Leaderboard** | Aggregated player rankings across demos |

---

## 📈 Rating System (S-Tier)

### Pipeline
```
raw_impact → role_zscore → map_weight → opponent_weight → kast_bonus → penalties → role_cap
```

### Role-Based Normalization
| Role | Mean | Std | Max Cap |
|------|------|-----|---------|
| AWPer | 46.4 | 22.3 | 95 |
| Entry | 42.6 | 22.6 | 92 |
| Anchor | 28.6 | 24.1 | 88 |

### Impact Components
| Component | Formula |
|-----------|---------|
| Kill Value | `kills_in_won * 8 + kills_in_lost * 0.5` |
| Entry Points | `opening_won * 14 + opening_lost * 1` |
| Clutch Points | `1v1 * 15 + 1vN * 35 + multikills * 8` |
| **Swing Kills** | `swing_kills * 8` (momentum-shifting) |
| Death Penalty | `tradeable * 0.5 + untradeable * 4` |

### Calibration Features
- ✅ **Role caps** - Anchors can't top leaderboard unless god-tier
- ✅ **Map weights** - Nuke Entry 0.85x, Anchor 1.15x
- ✅ **Consistency penalty** - High variance = -10 max
- ✅ **Smurf detection** - KDR > 1.6 + impact > 80 = 0.85x
- ✅ **Role saturation** - >3 same role in top 10 = penalty

---

## 📸 Sample Output

### Leaderboard
```
=== TOP 10 PLAYERS ===
name          role    raw   rate  swing
hypex         AWPer   87.3  95    10
MarKE         Anchor  78.2  88    4
Cryptic       Anchor  66.0  88    1
REZ           Anchor  71.7  88    7
Qlocuu        Anchor  67.0  88    7
Sobol         Entry   70.7  81    4
junior        AWPer   81.2  75    3  [SMURF]
Pluto         Anchor  58.8  71    3
Dycha         Entry   56.0  64    5
laxiee        Anchor  41.3  53    2
```

### Biggest Swing Players (Momentum Gods)
```
hypex   AWPer   swing=10  rate=95
REZ     Anchor  swing=7   rate=88
Qlocuu  Anchor  swing=7   rate=88
```

### Most Inflated (Exposed by System)
```
junior  AWPer   88 -> 75  (-13)  [SMURF FLAG]
MarKE   Anchor  100 -> 88 (-12)  [ROLE CAP]
Pluto   Anchor  81 -> 71  (-10)  [CONSISTENCY]
```

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach
python3 -m venv venv
source venv/bin/activate
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

## 📁 Project Structure

```
cs2-ai-coach/
├── src/
│   ├── parser/           # Demo parsing (demoparser2)
│   ├── features/         # Feature extraction + swing kills
│   ├── metrics/
│   │   ├── scoring.py    # Impact + rating calculation
│   │   └── calibration.py # Role baselines, map weights
│   ├── classifier/       # Mistake detection
│   └── report/           # JSON report generation
├── leaderboard.py        # Aggregated ranking tool
└── config.py             # Thresholds & settings
```

---

## 🎯 Key Metrics

| Metric | Description |
|--------|-------------|
| **Win Probability Added (WPA)** | "Moneyball" metric. Delta win prob per kill. Includes **Bomb Context** & **Hero Weighting** (1.5x on big plays). |
| **Swing Kills** | Kills that flip man-advantage (e.g. 3v5 -> 3v4). Deficit weighted (+10 for hero swings). |
| **KAST%** | Kill/Assist/Survived/Traded per round |
| **Untradeable Deaths** | Deaths with no teammate nearby |
| **Exit Frags** | Kills in lost rounds with <15s remaining |
| **Opening Kills Won** | First blood in rounds team won |

---

## 🔧 Calibration

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

---

## 📜 Credits

- [demoparser2](https://github.com/LaihoE/demoparser) - MIT License
- Inspired by HLTV rating methodology

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**This is not a toy. This is pro-grade analytics.**

Made for serious competitive play 🎯

</div>
