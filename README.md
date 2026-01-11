<div align="center">

# 🎮 CS2 AI Coach

**Metrics-driven post-match coaching for Counter-Strike 2**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Pl4yer-ONE/cs2-ai-coach?style=social)](https://github.com/Pl4yer-ONE/cs2-ai-coach)

*Parse demos → Extract features → Classify mistakes → Get AI coaching*

[**Quick Start**](#-quick-start) •
[**How It Works**](examples/HOW_IT_WORKS.md) •
[**Examples**](#-sample-output) •
[**Contributing**](#-contributing)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Demo Parsing** | Parse CS2 `.dem` files using demoparser2 (MIT) |
| 📊 **Feature Extraction** | Extract aim, positioning, utility & economy metrics |
| 🎯 **Smart Classification** | Rule-based mistake detection with confidence scores |
| 🤖 **AI Coaching** | Optional Ollama integration for natural language feedback |
| 📝 **Reports** | Generate JSON + Markdown coaching reports |

## ✅ Verified Working

Tested on **fl0m Mythical LAN 2026 - Phoenix vs Rave (Nuke)**:

```
✓ 10 players analyzed
✓ 103 kills parsed  
✓ 452 damages tracked
✓ 4 issues classified
✓ AI feedback generated
```

## 📸 Sample Output

### Console Summary
```
==================================================
CS2 COACHING REPORT SUMMARY
==================================================
Players analyzed: 10
Issues found: 4

Issues by category:
  - POSITIONING: 3
  - AIM: 1
--------------------------------------------------
Player: 76561198064058958
  K/D: 4.0 | HS%: 62.5%

Player: 76561197963450946
  K/D: 0.36 | HS%: 20.0%
  Focus: headshot_percentage
==================================================
```

### AI Coaching Feedback
> *"Player, focus on improving your positioning to reduce untradeable deaths, as you're currently experiencing an unacceptable 57.1% rate, and aim to get this number below 30%."*

📖 **[See full report →](examples/nlp_report.md)**

---

## 🚀 Quick Start

### Installation

```bash
# Clone
git clone https://github.com/Pl4yer-ONE/cs2-ai-coach.git
cd cs2-ai-coach

# Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt
```

### Usage

```bash
# Basic analysis
python main.py --demo your_match.dem

# With AI coaching + markdown report
python main.py --demo your_match.dem --ollama --markdown --verbose

# Check available parsers
python main.py --check-parsers
```

### Getting Demo Files

| Source | How to Get |
|--------|------------|
| **HLTV** | [hltv.org](https://hltv.org) → Results → Download |
| **FACEIT** | Match history → Download demo |
| **Your Matches** | `Steam/Counter-Strike 2/game/csgo/replays/` |

---

## 📁 Project Structure

```
cs2-ai-coach/
├── 📄 main.py              # CLI entry point
├── ⚙️ config.py            # Thresholds & settings
├── 📋 requirements.txt     # Dependencies
│
├── 📂 src/
│   ├── parser/            # Demo parsing (demoparser2)
│   ├── features/          # Feature extraction
│   ├── metrics/           # Aim, positioning, utility, economy
│   ├── classifier/        # Rule-based classification
│   ├── nlp/               # Ollama integration
│   └── report/            # Report generation
│
└── 📂 examples/
    ├── HOW_IT_WORKS.md    # Technical deep-dive
    ├── nlp_report.md      # Sample AI coaching report
    └── sample_report.md   # Basic analysis report
```

---

## 🎯 Coaching Metrics

| Category | Metric | Target | What It Measures |
|----------|--------|--------|------------------|
| **Aim** | Headshot % | >30% | Crosshair placement |
| **Aim** | Spray Control | - | Damage efficiency |
| **Positioning** | Exposed Deaths | <35% | Cover usage |
| **Positioning** | Untradeable Deaths | <30% | Team proximity |
| **Utility** | Flash Success | >20% | Flash effectiveness |
| **Utility** | Nade Damage/Round | >25 | Grenade value |
| **Economy** | Force Buy Deaths | <50% | Buy decision quality |

---

## 🤖 AI Integration (Optional)

The AI component uses [Ollama](https://ollama.ai) to phrase feedback naturally.

**Important**: AI only phrases output — it **never decides** what mistakes are.

```bash
# Install Ollama
brew install ollama  # macOS

# Pull a model
ollama pull llama3

# Run with AI
python main.py --demo match.dem --ollama
```

Without Ollama, the system uses pre-written fallback messages.

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Thresholds
AIM_THRESHOLDS = {
    "headshot_percentage": {"poor": 0.20, "average": 0.30, "good": 0.45}
}

# Ollama settings
OLLAMA_ENABLED = False
OLLAMA_MODEL = "llama3"
OLLAMA_HOST = "http://localhost:11434"
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [**HOW_IT_WORKS.md**](examples/HOW_IT_WORKS.md) | Architecture & pipeline explanation |
| [**nlp_report.md**](examples/nlp_report.md) | Sample report with AI coaching |
| [**sample_report.md**](examples/sample_report.md) | Basic analysis report |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 Credits

### Dependencies
- [demoparser2](https://github.com/LaihoE/demoparser) - MIT License
- [awpy](https://github.com/pnxenopoulos/awpy) - MIT License

### Inspiration
- [PureSkill.gg](https://pureskill.gg) - Data science approach to CS coaching

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⬆ Back to Top](#-cs2-ai-coach)**

Made with ❤️ for the CS2 community

</div>
