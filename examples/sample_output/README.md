# Sample FragAudit Output

This folder contains pre-generated analysis output from a real CS2 demo.

**Demo analyzed:** `acend-vs-washington-m1-dust2.dem`  
**Match:** Acend vs Washington (Map 1 - Dust 2)

---

## Quick Look

### 📊 Player Ratings

| Player | Team | Rating | Role | ADR | K/D |
|--------|------|--------|------|-----|-----|
| MarKE | CT | 1.42 | Entry | 98.3 | 24/16 |
| Nertz | CT | 1.18 | Support | 82.1 | 18/14 |
| Gabe | T | 0.78 | Lurker | 61.2 | 12/19 |
| H0NeST | T | 0.65 | Entry | 54.8 | 9/21 |

### 🎯 Detected Mistakes

```
Round 4: Gabe exposed to 2 angles at Long Doors (multi-angle exposure)
Round 7: H0NeST died without utility, 890u from nearest teammate
Round 11: mds pushed B alone, 0 teammates within 600u
Round 15: Gabe rotated 8.2s late on CT push
```

### 🧠 Win Prediction Examples

| Situation | Predicted | Actual |
|-----------|-----------|--------|
| 5v3, +$2k economy, no plant | CT 62% | CT won |
| 4v4, bomb planted, -$1k | T 58% | T won |
| 3v5, +$4k, post-plant | T 34% | CT won |

---

## Files in This Folder

| File | Description |
|------|-------------|
| `player_breakdown.json` | Full per-player stats |
| `round_summary.json` | Round-by-round analysis |
| `mistakes_detected.json` | All flagged mistakes |
| `role_classifications.json` | Detected playstyles |

---

## Try It Yourself

```bash
# Analyze any demo
python main.py analyze --demo your-match.dem

# With fast radar generation
python main.py analyze --demo your-match.dem --fast-radar

# Generate HTML report
python main.py analyze --demo your-match.dem --html
```
