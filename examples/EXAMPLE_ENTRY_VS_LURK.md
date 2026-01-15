# Example Analysis: Entry vs Lurk Behavior

**Demo:** Acend vs Washington (dust2)

This example shows how FragAudit detects and differentiates Entry vs Lurk playstyles.

---

## Player Roles Detected

| Player | Role | Confidence | Key Signals |
|--------|------|------------|-------------|
| MarKE | Entry | 0.78 | First contact 80% of rounds, avg dist from team: 320u |
| AwaykeN | AWPer | 0.85 | 12 AWP kills, AWP kill ratio: 0.54 |
| Girafffe | SiteAnchor | 0.72 | Avg distance: 180u, late contact timing |
| Gabe | Lurker | 0.68 | Avg team distance: 890u, contact timing >8s |
| bevve | Support | 0.65 | 4 flash assists, low entry involvement |

---

## Role Detection Logic

### Entry Fragger
FragAudit classifies a player as Entry when:
- First contact in round ≥60% of the time
- Average teammate distance <400 units
- Contact timing <5 seconds into round

### Lurker
FragAudit classifies a player as Lurk when:
- Average teammate distance >800 units
- Contact timing >8 seconds into round
- Often on opposite side of map from team

---

## Visual Evidence

### Radar Replay
![Radar](../docs/radar_preview.gif)

In the radar replay, notice:
- **MarKE (1)** enters site first, teammates follow
- **Gabe (8)** stays mid/lurk position alone
- **AwaykeN (3)** holds angles, doesn't entry

---

## Mistake Detection

| Player | Issue | Severity | Description |
|--------|-------|----------|-------------|
| Gabe | DRY_PEEK | MEDIUM | Round 15: Peeked A long without flash |
| MarKE | OVERPEEK | HIGH | Round 8: Overextended into crossfire |

---

## Understanding the Output

### JSON Output (excerpt)
```json
{
  "players": [
    {
      "name": "MarKE",
      "role": "Entry",
      "role_confidence": 0.78,
      "stats": {
        "kills": 18,
        "deaths": 15,
        "entry_attempts": 12,
        "entry_success_rate": 0.58
      }
    }
  ]
}
```

### Key Metrics Explained

| Metric | Meaning |
|--------|---------|
| `entry_attempts` | Times player was first to contact enemy |
| `entry_success_rate` | % of entry attempts where player got kill |
| `avg_teammate_distance` | Average distance to nearest teammate |
| `contact_timing` | Seconds into round when player contacts enemy |

---

## Try It Yourself

```bash
# Analyze a demo
python main.py analyze --demo your-demo.dem --html

# Generate radar video
python main.py analyze --demo your-demo.dem --radar --fast-radar

# View reports
open reports/report_*.html
```

---

## Discussion

- Does the Entry/Lurk classification match your understanding?
- Are there edge cases where the role detection fails?
- What additional signals should inform role classification?

Share your findings in [GitHub Discussions](https://github.com/Pl4yer-ONE/FragAudit/discussions)!
