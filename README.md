# CS2 AI Coach

A metrics-driven post-match coaching system for Counter-Strike 2. Parses demo files, extracts structured data, classifies mistakes using deterministic rules, and generates explainable coaching feedback with optional AI-powered phrasing.

## ✅ Verified Working

Successfully tested on **fl0m Mythical LAN - Phoenix vs Rave (Nuke)**:

| Metric | Result |
|--------|--------|
| Players Analyzed | 10 |
| Kills Parsed | 103 |
| Damages Parsed | 452 |
| Issues Classified | 4 |
| NLP Feedback | ✅ Generated |

📖 **[See How It Works →](examples/HOW_IT_WORKS.md)**

## Sample AI Coaching Output

> *"Player, focus on improving your positioning to reduce untradeable deaths, as you're currently experiencing an unacceptable 57.1% rate, and aim to get this number below 30%."*

See full reports: [`examples/nlp_report.md`](examples/nlp_report.md)

## Features

- **Demo Parsing**: Uses `demoparser2` (MIT) to parse CS2 .dem files
- **Feature Extraction**: Aim, positioning, utility, and economy metrics
- **Deterministic Classification**: Rule-based mistake detection with confidence scores
- **Explainable Feedback**: Every recommendation backed by evidence
- **Optional NLP**: Ollama locally phrases feedback (never decides mistakes)
- **Report Generation**: JSON and Markdown coaching reports

## Installation

```bash
# Clone the repository
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
source venv/bin/activate

# Basic analysis
python main.py --demo your_match.dem

# With NLP + markdown
python main.py --demo your_match.dem --ollama --markdown --verbose

# Check parser status
python main.py --check-parsers
```

## Project Structure

```
cs2-ai-coach/
├── main.py                    # CLI entry point
├── config.py                  # Thresholds and settings
├── examples/                  # Sample outputs & docs
│   ├── HOW_IT_WORKS.md        # Technical walkthrough
│   ├── nlp_report.md          # Report with AI coaching
│   └── sample_report.md       # Basic report
└── src/
    ├── parser/               # Demo parsing
    ├── features/             # Feature extraction  
    ├── metrics/              # Aim, positioning, utility, economy
    ├── classifier/           # Rule-based classification
    ├── nlp/                  # Ollama integration
    └── report/               # Report generation
```

## Coaching Metrics

| Category | Metric | Target |
|----------|--------|--------|
| **Aim** | Headshot % | >30% |
| **Positioning** | Untradeable deaths | <30% |
| **Utility** | Flash success rate | >20% |
| **Economy** | Force buy deaths | <50% |

## Getting Demo Files

- **HLTV**: [hltv.org](https://hltv.org) → Results → Download demo
- **FACEIT**: Match history downloads
- **Your matches**: `~/Library/Application Support/Steam/steamapps/common/Counter-Strike 2/game/csgo/replays/`

## Using NLP (Optional)

```bash
# Install Ollama
brew install ollama

# Pull model
ollama pull llama3

# Run with NLP
python main.py --demo match.dem --ollama
```

**Important**: NLP only phrases output - it never decides mistakes.

## Sources & Credits

- [demoparser2](https://github.com/LaihoE/demoparser) - MIT License
- [awpy](https://github.com/pnxenopoulos/awpy) - MIT License
- Inspired by [PureSkill.gg](https://pureskill.gg)

## License

MIT License - See [LICENSE](LICENSE)
