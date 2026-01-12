# CS2 AI Coach

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.9.0-orange.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-14%2F14%20passing-brightgreen.svg)](tests/)

Advanced performance analytics engine for Counter-Strike 2 demo files. Provides production-grade player ratings, role classification, and coaching feedback through deep statistical analysis.

## Features

- **Role Classification** — Automatic detection of player roles (AWPer, Entry, Trader, Rotator, Anchor) using behavioral analysis
- **Impact Rating** — Composite 0-100 score combining kills, entries, clutches, WPA, and death context
- **Exploit Resistance** — Calibrated penalties for exit farming, low KDR inflation, and stat padding
- **Coaching Feedback** — Mistake detection with actionable drill recommendations
- **Heatmap Generation** — Visual position analysis per player and phase

## Installation

```bash
# Clone repository
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Analyze a single demo
python -m src.main path/to/demo.dem --output ./output

# Batch process multiple demos
python -m src.main path/to/demos/ --output ./output
```

## Output Structure

```
output/
├── demo-name/
│   ├── reports/
│   │   └── match_report_demo-name.json
│   └── heatmaps/
│       └── map-name/
│           ├── kills_player.png
│           └── deaths_player.png
```

## Rating System

### Score Bands

| Rating | Classification |
|--------|----------------|
| 95-100 | Elite (rare) |
| 85-94 | Carry |
| 70-84 | Strong |
| 50-69 | Average |
| 30-49 | Below Average |
| 15-29 | Liability |

### Role Caps

| Role | Maximum Rating | Notes |
|------|---------------|-------|
| AWPer | 95 | Requires positive KDR |
| Entry | 92 | Dying is expected |
| Trader | 88 | Support role ceiling |
| Rotator | 95 | Impact multiplier ceiling |
| Anchor | 85 | Requires breakout conditions |

### Calibration Rules

- **Kill Gate**: raw_impact > 105 with < 18 kills receives 0.90x penalty
- **Exit Tax**: 8+ exit frags receives 0.85x penalty
- **KDR Cap**: KDR < 0.8 capped at 75, Trader < 1.0 capped at 80
- **Breakout**: Requires KDR > 1.15, KAST > 70%, Kills >= 16
- **Floor**: Minimum rating of 15 (no zeros)

## JSON Output Schema

```json
{
  "meta": {
    "match_id": "string",
    "map": "string",
    "version": "2.9.0",
    "metric_definitions": { ... }
  },
  "players": {
    "steam_id": {
      "name": "string",
      "role": "AWPer|Entry|Trader|Rotator|SiteAnchor",
      "final_rating": 0-100,
      "confidence": 0-100,
      "scores": {
        "aim": 0-100,
        "positioning": 0-100,
        "impact": 0-100,
        "raw_impact": "float (uncapped)"
      },
      "stats": { ... },
      "mistakes": [ ... ]
    }
  },
  "team_summary": { ... }
}
```

## API Reference

### ScoreEngine

```python
from src.metrics.scoring import ScoreEngine

# Compute aim score
raw_aim, effective_aim = ScoreEngine.compute_aim_score(
    hs_percent=0.45,
    kpr=0.8,
    adr=85.0,
    counter_strafe=80.0
)

# Compute final rating
rating = ScoreEngine.compute_final_rating(
    scores={"raw_impact": 100},
    role="Entry",
    kdr=1.2,
    untradeable_deaths=5,
    kills=18,
    rounds_played=20,
    kast_percentage=0.7
)
```

### RoleClassifier

```python
from src.metrics.role_classifier import RoleClassifier

classifier = RoleClassifier()
player_features = classifier.classify_roles(player_features_dict)
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run calibration tests only
python -m pytest tests/test_calibration.py -v
```

### Test Coverage

- Exit frag tax trigger (>= 8 frags)
- Low KDR cap (< 0.8)
- Rotator ceiling (max 95)
- Kill-gate trigger (raw > 105, kills < 18)
- Trader ceiling (KDR < 1.0)
- Floor clamp (min 15)
- Smurf detection
- Breakout rule validation

## Project Structure

```
cs2-ai-coach/
├── src/
│   ├── main.py              # Entry point
│   ├── features/
│   │   └── extractor.py     # Demo parsing
│   ├── metrics/
│   │   ├── scoring.py       # Rating engine
│   │   ├── calibration.py   # Baselines and caps
│   │   └── role_classifier.py
│   └── report/
│       ├── json_reporter.py # Output generation
│       ├── drills.py        # Coaching recommendations
│       └── heatmaps.py
├── tests/
│   └── test_calibration.py
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Requirements

- Python 3.10+
- demoparser2
- numpy
- matplotlib
- seaborn

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [demoparser2](https://github.com/LaihoE/demoparser) for CS2 demo parsing
- Community feedback for calibration improvements
