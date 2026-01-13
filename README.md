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

Be honest with yourself:

- ❌ Not a replacement for watching demos
- ❌ No AI coaching or natural language advice
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

Verify it works:

```bash
python main.py check-parsers
```

Expected:
```
CS2 Demo Parser Status
------------------------------
  demoparser2: ✓ Available
```

---

## Usage

### Analyze a demo

```bash
python main.py analyze --demo match.dem
```

### Generate markdown report

```bash
python main.py analyze --demo match.dem --markdown
```

### Generate HTML report

```bash
python main.py analyze --demo match.dem --html
```

### Watch a demo (visual player)

```bash
python main.py play match.dem
```

---

## Sample Output

```
==================================================
CS2 COACHING REPORT
==================================================
Demo: match/acend-vs-washington-m1-dust2.dem
Map: de_dust2
Players: 10
Mistakes found: 6

--------------------------------------------------
ROUND 5 | 1:18 | B Apartments
--------------------------------------------------
Player: shaiK
Mistake: dry_peek
Details: Challenged angle without flash support
Fix: Wait for teammate flash or jiggle peek first
Severity: 70%

--------------------------------------------------
ROUND 12 | 0:45 | Mid
--------------------------------------------------
Player: Girafffe  
Mistake: untradeable_death
Details: Died 480u from nearest teammate
Fix: Stay within 400u when taking contact
Severity: 85%
==================================================
```

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

## Project Structure

```
FragAudit/
├── main.py              # Entry point
├── src/
│   ├── parser/          # Demo parsing (demoparser2)
│   ├── features/        # Feature extraction
│   ├── classifier/      # Mistake detection rules
│   ├── report/          # JSON/Markdown/HTML output
│   └── player/          # Visual demo player
├── tests/               # 26 unit tests
└── docs/                # Documentation
```

---

## Roadmap

- [x] Basic mistake detection (dry peek, isolated death)
- [x] Markdown reports
- [x] Visual demo player
- [ ] HTML reports with embedded CSS
- [ ] Round-by-round timeline view
- [ ] Team-level analysis
- [ ] Utility usage tracking
- [ ] Comparative player analysis

---

## Contributing

Contributions welcome. This is MIT licensed — do what you want.

Before submitting:
1. Run tests: `python -m pytest tests/ -v`
2. Keep changes focused
3. Add tests for new detection rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Testing

```bash
python -m pytest tests/ -v
```

26 tests covering calibration rules and edge cases.

---

## License

[MIT](LICENSE) — Use it, fork it, sell it, whatever.

---

<div align="center">

*FragAudit — Find out where you died badly.*

</div>
