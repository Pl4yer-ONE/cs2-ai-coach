# CS2 AI Coach

A metrics-driven post-match coaching system for Counter-Strike 2. Parses demo files, extracts structured data, classifies mistakes using deterministic rules, and generates explainable coaching feedback.

## ✅ Verified Working

Successfully tested on **fl0m Mythical LAN - Phoenix vs Rave (Nuke)**:

| Metric | Result |
|--------|--------|
| Players Analyzed | 10 |
| Kills Parsed | 103 |
| Damages Parsed | 452 |
| Issues Classified | 4 |
| Processing Time | ~5 seconds |

See [`examples/sample_report.md`](examples/sample_report.md) for full output.

## Features

- **Demo Parsing**: Uses `demoparser2` (MIT licensed) to parse CS2 .dem files
- **Feature Extraction**: Extracts aim, positioning, utility, and economy metrics
- **Deterministic Classification**: Rule-based mistake detection with confidence scores
- **Explainable Feedback**: Every recommendation is backed by evidence metrics
- **Optional NLP**: Uses Ollama locally to phrase feedback naturally (never decides mistakes)
- **Report Generation**: JSON and Markdown coaching reports

## Installation

```bash
# Clone the repository
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Activate environment
source venv/bin/activate

# Analyze a demo file
python main.py --demo your_match.dem

# With markdown report
python main.py --demo your_match.dem --markdown --verbose

# With Ollama NLP feedback
python main.py --demo your_match.dem --ollama

# Check parser status
python main.py --check-parsers
```

## Project Structure

```
cs2-ai-coach/
├── main.py                    # CLI entry point
├── config.py                  # Thresholds and settings
├── requirements.txt           # Dependencies
├── examples/                  # Sample outputs
│   ├── sample_report.md
│   └── sample_report.json
└── src/
    ├── parser/               # Demo parsing (demoparser2)
    ├── features/             # Feature extraction
    ├── metrics/              # Metric analyzers
    │   ├── aim.py            # HS%, spray control
    │   ├── positioning.py    # Exposed/untradeable deaths
    │   ├── utility.py        # Flash success, nade damage
    │   └── economy.py        # Force buy analysis
    ├── classifier/           # Rule-based classification
    ├── nlp/                  # Optional Ollama phrasing
    └── report/               # JSON/Markdown generation
```

## Coaching Metrics

| Category | Metric | Target |
|----------|--------|--------|
| **Aim** | Headshot % | >30% |
| **Aim** | Spray control | Damage/shot ratio |
| **Positioning** | Exposed deaths | <35% |
| **Positioning** | Untradeable deaths | <30% |
| **Utility** | Flash success rate | >20% |
| **Utility** | Nade damage/round | >25 |
| **Economy** | Force buy deaths | <50% |

## Getting Demo Files

- **HLTV**: Download from match pages at [hltv.org](https://hltv.org)
- **FACEIT**: Download from match history
- **Your matches**: `~/Library/Application Support/Steam/steamapps/common/Counter-Strike 2/game/csgo/replays/`

## Using NLP (Optional)

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Run with `--ollama` flag

**Important**: NLP only phrases the deterministic output - it never decides what mistakes are.

## Sources & Credits

This project uses open-source tools:
- [demoparser2](https://github.com/LaihoE/demoparser) - MIT License
- [awpy](https://github.com/pnxenopoulos/awpy) - MIT License (alternative parser)

Inspired by [PureSkill.gg](https://pureskill.gg) documentation and data science resources.

## License

MIT License - See [LICENSE](LICENSE)
