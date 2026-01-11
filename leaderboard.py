#!/usr/bin/env python3
"""
Leaderboard Generator
Outputs player rankings in format: name raw rate
"""

import json
import glob
import sys
import os

def generate_leaderboard(output_dir: str):
    """Generate leaderboard from match reports."""
    data = []
    
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
                data.append({
                    'name': p['name'],
                    'raw': p['scores'].get('raw_impact', 0),
                    'rate': p['rating']
                })
    
    # Sort by raw impact descending
    data.sort(key=lambda x: x['raw'], reverse=True)
    
    # Output
    print("name raw rate")
    for p in data:
        print(f"{p['name']} {p['raw']} {p['rate']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        output_dir = "outputs/zscore"
    else:
        output_dir = sys.argv[1]
    
    generate_leaderboard(output_dir)
