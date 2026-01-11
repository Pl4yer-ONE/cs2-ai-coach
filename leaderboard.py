#!/usr/bin/env python3
"""
Leaderboard Generator
Aggregates player stats across multiple demos.
Uses role-based z-score normalization.
Outputs: name role raw rate
"""

import json
import glob
import sys
import os
from collections import defaultdict, Counter

# Role-based calibration data
ROLE_BASELINES = {
    'Entry':  {'mean': 42.6, 'std': 22.6},
    'Anchor': {'mean': 28.6, 'std': 24.1},
    'AWPer':  {'mean': 46.4, 'std': 22.3},
    'Support': {'mean': 35.0, 'std': 23.0},
    'Lurker': {'mean': 35.0, 'std': 23.0},
}

def generate_leaderboard(output_dir: str):
    """Generate leaderboard from match reports, aggregated per player."""
    
    # Accumulator: player_name -> list of (raw, role)
    bucket = defaultdict(list)
    
    # Find all reports
    pattern = os.path.join(output_dir, '*/reports/*.json')
    reports = glob.glob(pattern)
    
    if not reports:
        print(f"No reports found in {output_dir}")
        return
    
    # Collect player data
    for report in reports:
        with open(report) as f:
            d = json.load(f)
            for pid, p in d['players'].items():
                name = p['name']
                raw = p['scores'].get('raw_impact', 0)
                role = p['role']
                bucket[name].append((raw, role))
    
    # Aggregate: compute mean raw per player with role-based z-score
    aggregated = []
    
    for name, scores in bucket.items():
        mean_raw = sum(s[0] for s in scores) / len(scores)
        
        # Get most common role for this player
        roles = [s[1] for s in scores]
        main_role = Counter(roles).most_common(1)[0][0]
        
        # Role-based z-score
        baseline = ROLE_BASELINES.get(main_role, {'mean': 35.6, 'std': 22.9})
        role_mean = baseline['mean']
        role_std = baseline['std']
        
        z = (mean_raw - role_mean) / role_std if role_std > 0 else 0
        rate = 50 + (z * 25)
        rate = int(max(0, min(100, rate)))
        
        games = len(scores)
        aggregated.append({
            'name': name,
            'role': main_role,
            'raw': round(mean_raw, 1),
            'rate': rate,
            'games': games
        })
    
    # Sort by rate descending
    aggregated.sort(key=lambda x: x['rate'], reverse=True)
    
    # Output
    print("name role raw rate")
    for p in aggregated:
        print(f"{p['name']} {p['role']} {p['raw']} {p['rate']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        output_dir = "outputs/final"
    else:
        output_dir = sys.argv[1]
    
    generate_leaderboard(output_dir)
