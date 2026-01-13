# FragAudit Usage Guide

Step-by-step guide to analyze your first CS2 demo.

---

## 1. Get a Demo File

### From Your Matches

1. Open CS2
2. Go to **Watch** → **Your Matches**
3. Click on a match → **Download**
4. Demo saves to: `Steam/steamapps/common/Counter-Strike Global Offensive/csgo/replays/`

### From HLTV/FACEIT

Download `.dem` files from match pages.

---

## 2. Install FragAudit

```bash
git clone https://github.com/Pl4yer-ONE/FragAudit.git
cd FragAudit
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify:
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

## 3. Analyze a Demo

### Basic Analysis

```bash
python main.py analyze --demo path/to/your/match.dem
```

### With Markdown Report

```bash
python main.py analyze --demo match.dem --markdown
```

### With HTML Report (Shareable)

```bash
python main.py analyze --demo match.dem --html
```

### Verbose Output

```bash
python main.py analyze --demo match.dem -v
```

---

## 4. Understanding the Output

### Console Output

```
════════════════════════════════════════════════════════════
  FRAGAUDIT ANALYSIS
════════════════════════════════════════════════════════════

  Map: de_dust2
  Demo: match.dem

  Players: 10    Issues: 6

  Issue Types:
    dry peek             ██████░░░░ 6

────────────────────────────────────────────────────────────
  PLAYER BREAKDOWN
────────────────────────────────────────────────────────────

  shaiK
    K/D: 1.69  HS: 72.7%  Role: Entry
    🟡 R5 0:45 — dry peek

  KalubeR
    K/D: 1.64  HS: 69.6%  Role: Support
    ✓ No issues detected
```

### Mistake Types

| Type | What It Means |
|------|---------------|
| `dry_peek` | Peeked without flash support |
| `dry_peek_awp` | Dry peeked into an AWP |
| `untradeable_death` | Died too far from teammates |
| `bad_spacing` | Stacked on teammates |
| `solo_late_round` | Died alone in late round |

### Severity

| Icon | Level | Meaning |
|------|-------|---------|
| 🔴 | 80%+ | Critical — fix this first |
| 🟡 | 50-79% | Important — work on it |
| 🟢 | <50% | Minor — nice to fix |

---

## 5. View Reports

Reports are saved in `reports/` folder:

- `coaching_report_YYYYMMDD_HHMMSS.json` — Raw data
- `coaching_report_YYYYMMDD_HHMMSS.md` — Readable markdown
- `report_YYYYMMDD_HHMMSS.html` — Shareable HTML

Open HTML in browser:
```bash
open reports/report_*.html   # macOS
start reports\report_*.html  # Windows
xdg-open reports/report_*.html  # Linux
```

---

## 6. Watch a Demo (Visual Player)

```bash
python main.py play path/to/match.dem
```

### Controls

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← / → | Seek 5 seconds |
| ↑ / ↓ | Previous/Next round |
| + / - | Speed (0.25x–4x) |
| 1-9 | Jump to round |
| R | Restart round |
| ESC | Quit |

---

## 7. Tips

### Analyze Specific Player

```bash
python main.py analyze --demo match.dem --player "YourName"
```

### Quick Check

Just want to see if it works?
```bash
python main.py analyze --demo match/acend-vs-washington-m1-dust2.dem -v
```

---

## Troubleshooting

### "Parser not found"

```bash
pip install demoparser2
```

### "Pygame not found" (for visual player)

```bash
pip install pygame
```

### Demo won't load

- Ensure it's a CS2 demo (`.dem`), not CS:GO
- Try a different demo file
- Run with `-v` to see error details

---

## Next Steps

- Share reports with your team
- Track improvement over time
- Open issues on GitHub for bugs/features

---

*Need help?* [Open an issue](https://github.com/Pl4yer-ONE/FragAudit/issues)
