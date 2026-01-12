"""
Calibration Constants
All rating calibration data in one place.
"""

# Role-based calibration data (from 60 players across 6 demos)
# v2.2: Split Anchor into SiteAnchor/Trader for better granularity
ROLE_BASELINES = {
    'Entry':      {'mean': 42.6, 'std': 22.6, 'max': 92},
    'AWPer':      {'mean': 46.4, 'std': 22.3, 'max': 95},
    'Support':    {'mean': 35.0, 'std': 23.0, 'max': 90},
    'Lurker':     {'mean': 35.0, 'std': 23.0, 'max': 90},
    'Rotator':    {'mean': 38.0, 'std': 21.0, 'max': 90},
    'Trader':     {'mean': 32.0, 'std': 20.0, 'max': 88},   # NEW: close-mid distance
    'SiteAnchor': {'mean': 28.6, 'std': 19.3, 'max': 86},   # NEW: site holder, tightest cap
    'Anchor':     {'mean': 28.6, 'std': 19.3, 'max': 88},   # Fallback for old code
}

# Dynamic role caps per map (anchors on Nuke deserve more ceiling)
MAP_ROLE_CAPS = {
    'de_nuke': {'Anchor': 92, 'Entry': 88, 'AWPer': 95},
    'de_dust2': {'Entry': 94, 'AWPer': 95, 'Anchor': 85},
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
    """
    diff = opponent_avg - 50
    mult = 1 + diff * 0.006
    return max(0.75, min(1.25, mult))

def get_consistency_penalty(raw_scores: list) -> float:
    """
    SCALED consistency penalty (not binary).
    penalty = min(10, (std-20)*0.4)
    
    Examples:
    - std 25 → -2
    - std 35 → -6
    - std 45 → -10
    """
    if len(raw_scores) < 2:
        return 0.0
    
    import statistics
    std = statistics.stdev(raw_scores)
    
    if std <= 20:
        return 0.0
    
    penalty = min(10, (std - 20) * 0.4)
    return -penalty

def get_kast_bonus(kast_pct: float) -> float:
    """
    NONLINEAR KAST bonus.
    - Low KAST = heavy punishment
    - High KAST = diminishing returns
    """
    if kast_pct > 0.75:
        return (kast_pct - 0.75) * 25  # e.g., 80% = +1.25
    else:
        return (kast_pct - 0.75) * 40  # e.g., 50% = -10

def detect_smurf(kdr: float, raw_impact: float, hs_pct: float = 0.0, 
                 opening_success: float = 0.0) -> tuple:
    """
    Detect and PUNISH smurfs.
    
    Returns: (is_smurf, multiplier)
    - is_smurf: bool
    - multiplier: 0.85 if smurf, 1.0 otherwise
    
    Criteria:
    - KDR > 1.6
    - Impact > 80
    - Optional: HS% > 65% or opening success > 50%
    """
    is_smurf = kdr > 1.6 and raw_impact > 80
    
    # Enhanced detection
    if hs_pct > 0.65 or opening_success > 0.5:
        is_smurf = is_smurf and True
    
    multiplier = 0.85 if is_smurf else 1.0
    return (is_smurf, multiplier)

def get_role_saturation_penalty(role: str, role_counts: dict) -> float:
    """
    Penalize role clustering in top rankings.
    
    If top rankings have:
    - >3 Anchors → each extra -3 pts
    - >3 AWPers → each extra -2 pts
    - >4 Entries → each extra -1 pt
    """
    thresholds = {'Anchor': (3, 3), 'AWPer': (3, 2), 'Entry': (4, 1)}
    
    if role not in thresholds:
        return 0.0
    
    max_count, penalty_per = thresholds[role]
    count = role_counts.get(role, 0)
    
    if count > max_count:
        return -(count - max_count) * penalty_per
    
    return 0.0

def get_dynamic_role_cap(role: str, map_name: str) -> int:
    """
    Get dynamic role cap based on map.
    Nuke anchors get higher ceiling.
    """
    # Check map-specific caps first
    if map_name in MAP_ROLE_CAPS:
        if role in MAP_ROLE_CAPS[map_name]:
            return MAP_ROLE_CAPS[map_name][role]
    
    # Default to role baseline cap
    return ROLE_BASELINES.get(role, {'max': 90}).get('max', 90)

