# CS2 AI Coach

A metrics-driven post-match coaching system for Counter-Strike 2. Parses demo files, extracts structured data, classifies mistakes using deterministic rules, and generates explainable coaching feedback.

## Features

- **Demo Parsing**: Uses `demoparser2` or `awpy` to parse CS2 .dem files
- **Feature Extraction**: Extracts aim, positioning, utility, and economy metrics
- **Deterministic Classification**: Rule-based mistake detection with confidence scores
- **Explainable Feedback**: Every recommendation is backed by evidence metrics
- **Optional NLP**: Uses Ollama locally to phrase feedback naturally (never decides mistakes)
- **Report Generation**: JSON and Markdown coaching reports

## Installation

```bash
# Clone the repository
cd "CS2 AI COACH"

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Analyze a demo file
python main.py --demo your_match.dem

# With Ollama NLP feedback
python main.py --demo your_match.dem --ollama

# Generate markdown report
python main.py --demo your_match.dem --markdown

# Analyze specific player
python main.py --demo your_match.dem --player "YourSteamID"

# Check parser status
python main.py --check-parsers
```

## Project Structure

```
cs2-ai-coach/
├── main.py                    # Entry point
├── config.py                  # Thresholds and settings
├── requirements.txt           # Dependencies
├── src/
│   ├── parser/               # Demo parsing
│   │   └── demo_parser.py
│   ├── features/             # Feature extraction
│   │   └── extractor.py
│   ├── metrics/              # Metric analysis
│   │   ├── aim.py
│   │   ├── positioning.py
│   │   ├── utility.py
│   │   └── economy.py
│   ├── classifier/           # Mistake classification
│   │   └── mistake_classifier.py
│   ├── nlp/                  # Optional NLP phrasing
│   │   └── ollama_phrasing.py
│   └── report/               # Report generation
│       └── generator.py
└── reports/                  # Output directory
```

## Coaching Metrics

### Aim
- Headshot percentage (target: >30%)
- Spray control efficiency

### Positioning
- Exposed death ratio (target: <35%)
- Untradeable death ratio (target: <30%)

### Utility
- Flash success rate (target: >20%)
- Grenade damage per round (target: >25)

### Economy
- Force buy death patterns (heuristic-based)

## Configuration

Edit `config.py` to adjust:
- Metric thresholds
- Ollama settings (host, model, timeout)
- Minimum samples for classification
- Fallback coaching messages

## Using NLP (Optional)

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Run with `--ollama` flag or set `OLLAMA_ENABLED = True` in config

NLP only phrases the deterministic output - it never decides what mistakes are.

## Getting Demo Files

- Download from HLTV, FACEIT, or CS2Stats
- Use your own matchmaking demos from Steam
- Location: `Steam/steamapps/common/Counter-Strike 2/game/csgo/replays`

## Sources & Credits

This project uses:
- [demoparser2](https://github.com/LaihoE/demoparser) - MIT License
- [awpy](https://github.com/pnxenopoulos/awpy) - MIT License

Inspired by:
- [PureSkill.gg](https://pureskill.gg) documentation and data science resources

## License

MIT License
