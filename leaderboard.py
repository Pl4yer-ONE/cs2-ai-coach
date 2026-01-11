#!/usr/bin/env python3
"""
Leaderboard Generator
Aggregates player stats across multiple demos.
Outputs: name raw rate
"""

import json
import glob
import sys
import os
from collections import defaultdict

def generate_leaderboard(output_dir: str):
    """Generate leaderboard from match reports, aggregated per player."""
    
    # Accumulator: player_name -> list of (raw, rate)
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
                rate = p['rating']
                bucket[name].append((raw, rate))
    
    # Aggregate: compute mean raw per player
    aggregated = []
    
    # Calibration constants
    IMPACT_MEAN = 35.6
    IMPACT_STD = 22.9
    
    for name, scores in bucket.items():
        mean_raw = sum(s[0] for s in scores) / len(scores)
        
        # Compute rate from mean_raw using z-score (not averaging rates!)
        z = (mean_raw - IMPACT_MEAN) / IMPACT_STD
        rate = 50 + (z * 25)
        rate = int(max(0, min(100, rate)))
        
        games = len(scores)
        aggregated.append({
            'name': name,
            'raw': round(mean_raw, 1),
            'rate': rate,
            'games': games
        })
    
    # Sort by mean raw descending
    aggregated.sort(key=lambda x: x['raw'], reverse=True)
    
    # Output
    print("name raw rate")
    for p in aggregated:
        print(f"{p['name']} {p['raw']} {p['rate']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        output_dir = "outputs/final"
    else:
        output_dir = sys.argv[1]
    
    generate_leaderboard(output_dir)
