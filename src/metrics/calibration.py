"""
Calibration Constants
All rating calibration data in one place.
"""

# Role-based calibration data (from 60 players across 6 demos)
ROLE_BASELINES = {
    'Entry':  {'mean': 42.6, 'std': 22.6, 'max': 92},
    'Anchor': {'mean': 28.6, 'std': 24.1, 'max': 88},
    'AWPer':  {'mean': 46.4, 'std': 22.3, 'max': 95},
    'Support': {'mean': 35.0, 'std': 23.0, 'max': 90},
    'Lurker': {'mean': 35.0, 'std': 23.0, 'max': 90},
}

# Map difficulty weights per role (BRUTAL)
MAP_WEIGHTS = {
    'de_nuke': {
        'Entry': 0.85,   # CT-sided, entry suffer
        'Anchor': 1.15,  # CT-sided, anchors rewarded
        'AWPer': 1.00,
    },
    'de_dust2': {
        'Entry': 1.10,   # Aim-heavy, entries thrive
        'Anchor': 0.95,
        'AWPer': 1.05,
    },
    'de_ancient': {
        'Entry': 1.00,
        'Anchor': 1.05,
        'AWPer': 0.90,   # AWP weaker on this map
    },
    'de_train': {
        'Entry': 0.95,
        'Anchor': 1.05,
        'AWPer': 1.00,
    },
    'de_mirage': {
        'Entry': 1.05,
        'Anchor': 0.95,
        'AWPer': 1.00,
    },
    'de_overpass': {
        'Entry': 1.00,
        'Anchor': 1.00,
        'AWPer': 1.00,
    },
    'de_inferno': {
        'Entry': 1.00,
        'Anchor': 1.05,
        'AWPer': 0.95,
    },
}

def get_opponent_multiplier(opponent_avg: float) -> float:
    """
    Smooth opponent strength adjustment.
    Capped at 0.75 - 1.25.
    
    Examples:
    - 80 avg → 1.18x
    - 65 avg → 1.09x
    - 50 avg → 1.00x
    - 35 avg → 0.91x
    - 20 avg → 0.82x
    """
    diff = opponent_avg - 50
    mult = 1 + diff * 0.006
    return max(0.75, min(1.25, mult))

def get_consistency_penalty(raw_scores: list) -> float:
    """
    Punish coinflip merchants.
    If player raw std > 25, penalty of -5.
    """
    if len(raw_scores) < 2:
        return 0.0
    
    import statistics
    std = statistics.stdev(raw_scores)
    
    if std > 25:
        return -5.0
    return 0.0

def detect_smurf(kdr: float, raw_impact: float, opponent_avg: float) -> bool:
    """
    Flag suspected smurfs.
    
    Criteria:
    - KDR > 1.6
    - Impact > 80
    - Opponent avg < 40
    """
    return kdr > 1.6 and raw_impact > 80 and opponent_avg < 40
