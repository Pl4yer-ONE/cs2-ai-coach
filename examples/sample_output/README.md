# Sample Output

This directory contains **pre-generated analysis output** from FragAudit so you can see what the tool produces without needing your own demo file.

## Files

| File | Description |
|------|-------------|
| `match_analysis.json` | Full JSON output with player stats, mistakes, and predictions |
| `player_summary.md` | Human-readable player performance summary |

## Quick Look

The sample analysis is from a **Dust2** competitive match showing:
- 🎯 **10 players** tracked across 24 rounds
- 📊 **Role detection** (Entry, Lurker, Support, AWPer)
- ❌ **Mistake patterns** identified per player
- 📈 **Win probability predictions** per round

## Try It Yourself

```bash
# Analyze your own demo
python main.py analyze --demo your_match.dem --output my_analysis/

# With fast radar generation
python main.py analyze --demo your_match.dem --fast-radar --output my_analysis/
```

## Sample Output Preview

```
Player: "shroud" 
Role: Entry Fragger
Rating: 1.24
Mistakes:
  - Wide peek without utility (3 instances)
  - Isolated positioning (2 instances)
Recommendation: "Pre-flash before peeking Long A"
```
