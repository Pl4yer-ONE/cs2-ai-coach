<div align="center">

<img src="docs/logo.png" alt="FragAudit Logo" width="180"/>

# FragAudit

**Parses CS2 demos and flags positional mistakes using rule-based analysis.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Pl4yer-ONE/FragAudit/actions/workflows/ci.yml/badge.svg)](https://github.com/Pl4yer-ONE/FragAudit/actions)

</div>

---

## What It Does

FragAudit reads CS2 demo files and identifies common positioning mistakes:

- **Dry peeks** — Challenging angles without flash support
- **Isolated deaths** — Dying too far from teammates to be traded
- **Bad spacing** — Stacking on teammates
- **Late-round solo plays** — Dying alone when you should group up

It generates reports showing exactly when and where mistakes happened.

---

## Who It's For

- Players reviewing their own demos
- Coaches analyzing team VODs
- Analysts building match reports
- Developers building on demo parsing

---

## What It Doesn't Do

- ❌ Not a replacement for watching demos
- ❌ No AI coaching or natural language advice (unless you enable Ollama)
- ❌ Won't tell you about crosshair placement or aim
- ❌ Can't detect utility usage quality (yet)
- ❌ Rule-based, not ML — it follows heuristics, not magic

---

## Installation

```bash
git clone https://github.com/Pl4yer-ONE/FragAudit.git
cd FragAudit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify:
```bash
python main.py check-parsers
```

---

## Usage

### Analyze a demo
```bash
python main.py analyze --demo match/your-demo.dem
```

### Generate HTML report (shareable)
```bash
python main.py analyze --demo match.dem --html
```

### Enable AI coaching advice (requires Ollama)
```bash
python main.py analyze --demo match.dem --ollama --html
```

### Watch demo visually
```bash
python main.py play match.dem
```

📖 **Full guide:** [docs/USAGE.md](docs/USAGE.md)

---

## Sample Output

Real output from analyzing `phoenix-vs-rave-m3-ancient.dem`:

```
════════════════════════════════════════════════════════════
  FRAGAUDIT ANALYSIS
════════════════════════════════════════════════════════════

  Map: de_ancient
  Demo: match/phoenix-vs-rave-m3-ancient.dem

  Players: 10    Issues: 7

  Issue Types:
    dry peek             ███████░░░ 7

────────────────────────────────────────────────────────────
  PLAYER BREAKDOWN
────────────────────────────────────────────────────────────

  MarKE
    K/D: 2.5  HS: 66.7%  Role: Trader
    ✓ No issues detected

  jchancE
    K/D: 0.53  HS: 62.5%  Role: Trader
    🟡 R0 0:30 — dry peek
    🟡 R0 0:30 — dry peek

  junior
    K/D: 2.11  HS: 42.1%  Role: AWPer
    ✓ No issues detected

════════════════════════════════════════════════════════════
```

---

## HTML Reports

Generate shareable HTML reports with `--html`:

<div align="center">

![HTML Report](docs/html_report.png)

</div>

Features:
- Player cards with K/D, HS%, ADR, Role
- Mistake breakdown per player
- Varied coaching advice (map-specific)
- Dark theme, mobile responsive

---

## Demo Player

Visual playback without CS2 installed.

<div align="center">

![Demo Player](docs/demo_player.png)

</div>

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← / → | Seek 5 sec |
| ↑ / ↓ | Prev/Next round |
| + / - | Speed |
| ESC | Quit |

---

## Mistake Detection

| Type | Trigger | Severity |
|------|---------|----------|
| `dry_peek` | Peeked without flash support | 70% |
| `dry_peek_awp` | Dry peeked into AWP | 95% |
| `untradeable_death` | Died >400u from teammates | 85% |
| `bad_spacing` | Stacked on 2+ teammates | 65% |
| `solo_late_round` | Died alone in late round | 75% |

---

## AI Coaching (Optional)

Enable Ollama for natural language advice:

```bash
# Start Ollama (must have llama3 model)
ollama run llama3

# Run with AI coaching
python main.py analyze --demo match.dem --ollama --html
```

Without Ollama, you get varied template-based advice (map-specific, context-aware).

---

## Project Structure

```
FragAudit/
├── main.py              # Entry point
├── src/
│   ├── parser/          # Demo parsing (demoparser2)
│   ├── features/        # Feature extraction
│   ├── classifier/      # Mistake detection rules
│   ├── report/          # JSON/Markdown/HTML output
│   ├── nlp/             # Ollama integration
│   └── player/          # Visual demo player
├── tests/               # 26 unit tests
├── match/               # Demo files
└── docs/                # Documentation
```

---

## Roadmap

### Completed
- [x] v3.0 — Mistake detection (dry peek, isolated death)
- [x] v3.0 — Markdown + JSON reports
- [x] v3.0 — Visual demo player
- [x] v3.1 — HTML reports with styling
- [x] v3.1 — Varied coaching advice (map-specific)
- [x] v3.1 — Ollama AI integration
- [x] v3.1.1 — Severity labels (HIGH/MED/LOW)
- [x] v3.1.1 — CSV export

### Planned
- [ ] v3.2 — Trade success % per player
- [ ] v3.2 — Spacing heatmap overlay
- [ ] v3.3 — Clutch decision scoring
- [ ] v3.3 — Round-by-round timeline view
- [ ] v3.4 — Team synergy report
- [ ] v3.4 — Utility effectiveness tracking

---

## Contributing

MIT licensed — contributions welcome.

```bash
# Run tests
python -m pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE) — Use it, fork it, sell it, whatever.

---

<div align="center">

*FragAudit — Find out where you died badly.*

</div>
