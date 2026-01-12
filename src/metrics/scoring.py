"""
Scoring Engine
Normalizes various raw metrics into 0-100 scores using user-defined weighted formulas.
"""

from typing import Dict, Any, Tuple
from src.metrics.calibration import (
    ROLE_BASELINES, MAP_WEIGHTS, get_opponent_multiplier,
    get_kast_bonus, get_dynamic_role_cap, detect_smurf
)

class ScoreEngine:
    """
    Computes normalized scores (0-100) for player performance categories.
    """
    
    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> int:
        """Helper to clamp and normalize value to 0-100."""
        if value <= min_val: return 0
        if value >= max_val: return 100
        return int(((value - min_val) / (max_val - min_val)) * 100)

    @staticmethod
    def _get_cs_multiplier(counter_strafe: float) -> float:
        """
        Non-linear counter-strafe penalty curve.
        Lookup table with interpolation between breakpoints.
        
        | CS%  | Multiplier |
        |------|------------|
        | 95+  | 1.00       |
        | 85   | 0.92       |
        | 75   | 0.82       |
        | 65   | 0.72       |
        | <60  | 0.60       |
        """
        # Breakpoints: (cs_threshold, multiplier)
        breakpoints = [
            (95.0, 1.00),
            (85.0, 0.92),
            (75.0, 0.82),
            (65.0, 0.72),
            (60.0, 0.60),
        ]
        
        # Above highest threshold
        if counter_strafe >= breakpoints[0][0]:
            return breakpoints[0][1]
        
        # Below lowest threshold
        if counter_strafe < breakpoints[-1][0]:
            return breakpoints[-1][1]
        
        # Interpolate between breakpoints
        for i in range(len(breakpoints) - 1):
            upper_cs, upper_mult = breakpoints[i]
            lower_cs, lower_mult = breakpoints[i + 1]
            
            if lower_cs <= counter_strafe < upper_cs:
                # Linear interpolation within this band
                ratio = (counter_strafe - lower_cs) / (upper_cs - lower_cs)
                return lower_mult + ratio * (upper_mult - lower_mult)
        
        return 1.0  # Fallback

    @staticmethod
    def compute_aim_score(hs_percent: float, kpr: float, adr: float, counter_strafe: float = 80.0) -> Tuple[int, int]:
        """
        Aim Score (Properly Normalized).
        
        FIXED: Inputs are normalized to realistic ranges so:
        - Average players get 45-55
        - Good players get 60-75
        - Elite players get 80+
        
        Normalization ranges:
        - HS%: 35-65% (0.35-0.65)
        - KPR: 0.5-1.0
        - ADR: 60-120
        
        Weights: HS 35%, KPR 35%, ADR 30%
        
        Returns:
            Tuple of (raw_aim, effective_aim) - both 0-100
        """
        # Normalize HS% (35% = 0, 65% = 100)
        hs_score = ScoreEngine._normalize(hs_percent, 0.35, 0.65)
        
        # Normalize KPR (0.5 = 0, 1.0 = 100)
        kpr_score = ScoreEngine._normalize(kpr, 0.5, 1.0)
        
        # Normalize ADR (60 = 0, 120 = 100)
        adr_score = ScoreEngine._normalize(adr, 60, 120)
        
        # Weighted combination
        raw_score = (hs_score * 0.35) + (kpr_score * 0.35) + (adr_score * 0.30)
        raw_aim = int(min(100, max(0, raw_score)))
        
        # Non-linear Mechanical Penalty
        cs_mult = ScoreEngine._get_cs_multiplier(counter_strafe)
        effective_score = raw_score * cs_mult
            
        effective_aim = int(min(100, max(0, effective_score)))
        
        return (raw_aim, effective_aim)

    @staticmethod
    def compute_positioning_score(untradeable_ratio: float, trade_success: float = 0.0, survival_rate: float = 0.0) -> int:
        """
        Positioning Score (Brutal).
        
        Bad positioning should HURT.
        Feeders get 20-30, not 40-50.
        
        Formula:
        - Base: 70 (good player starts high)
        - Untradeable deaths: -70 * ratio (brutal penalty)
        - Trade success: +25
        - Survival: +15
        """
        base = 70.0
        penalty = untradeable_ratio * 70.0
        bonus_trade = trade_success * 25.0 
        bonus_surv = survival_rate * 15.0
        
        score = base - penalty + bonus_trade + bonus_surv
        return int(min(100, max(0, score)))

    @staticmethod
    def compute_utility_score(enemies_blinded: int, util_dmg: int, flashes_thrown: int) -> int:
        """
        Utility Score.
        Formula:
        - Enemies Blinded (40%) -> Target 10
        - Utility Dmg (30%) -> Target 200
        - Usage (30%) -> Target 20
        
        Returns -1 IF no usage/data (to signal UI to hide it)
        """
        if enemies_blinded == 0 and util_dmg == 0 and flashes_thrown == 0:
            return -1 # Signal to hide
            
        s_blind = ScoreEngine._normalize(enemies_blinded, 0, 10)
        s_dmg = ScoreEngine._normalize(util_dmg, 0, 200)
        s_use = ScoreEngine._normalize(flashes_thrown, 0, 15)
        
        return int((s_blind * 0.4) + (s_dmg * 0.3) + (s_use * 0.3))
    
    @staticmethod
    def compute_impact_score(
        # Opening duels
        opening_kills_won: int,
        opening_kills_lost: int,
        entry_deaths: int,
        
        # Kill context
        kills_in_won_rounds: int,
        kills_in_lost_rounds: int,
        exit_frags: int,
        swing_score: float,  # Weighted swing score (deficit-based)
        total_wpa: float,    # Win Probability Added (Moneyball)
        
        # Round-winning plays
        multikills: int, 
        clutches_1v1: int, 
        clutches_1vN: int,
        
        # Death context
        untradeable_deaths: int, 
        tradeable_deaths: int,
        
        # Stats for sanity
        total_kills: int,
        kdr: float = 1.0,
        role: str = "Anchor"
    ) -> Tuple[float, int]:
        """
        Impact Rating (Auto-Calibrated).
        
        Component Caps (prevent single-stat gaming):
        - Clutch points: max 25
        - Kill points: max 30  
        - Entry points: max 20
        
        Lone Wolf Penalty:
        - If untradeable > tradeable * 2: -15%
        
        Sanity Caps:
        - kills < 10 and impact > 70: cap at 70
        - kdr < 0.8 and impact > 60: cap at 60
        
        Expected Output:
        - 0-20:  AFK/Bot
        - 20-35: Bad game
        - 40-55: Average
        - 60-75: Good
        - 80-90: Carry
        - 95+:   God
        """
        # 1. Kill Value (CAPPED at 40)
        kill_points = kills_in_won_rounds * 8.0 + kills_in_lost_rounds * 0.5
        kill_points -= exit_frags * 2.0  # Increased penalty
        kill_points = min(kill_points, 40.0)  # Raised cap
        
        # 2. Entry Points (CAPPED at 30)
        entry_points = opening_kills_won * 14.0 + opening_kills_lost * 1.0  # Lost opener = low value
        entry_points -= entry_deaths * 3.0  # Failing entry hurts
        entry_points = min(entry_points, 30.0)  # Raised cap
        
        # 3. Clutch Points (CAPPED at 40)
        clutch_points = clutches_1v1 * 15.0 + clutches_1vN * 35.0  # Big clutches matter
        clutch_points += multikills * 8.0  # Multi-kill rounds matter
        clutch_points = min(clutch_points, 40.0)  # Raised cap
        
        # 4. Death Penalty (increased + progressive)
        death_penalty = tradeable_deaths * 0.5 + untradeable_deaths * 4.0  # Harsh
        # PROGRESSIVE: 20+ deaths = extra punishment
        total_deaths = tradeable_deaths + untradeable_deaths
        if total_deaths >= 20:
            death_penalty += (total_deaths - 19) * 3.0  # Each death over 19 = -3 extra
        
        # 5. Round Contribution Bonus
        round_bonus = 0.0
        if kills_in_won_rounds >= 5:
            round_bonus = 8.0
        
        # 6. SWING BONUS (pre-calculated weighted score)
        # deficit -3+ = +10, -2 = +8, repeat same round = +4
        swing_bonus = swing_score
        
        # 7. WPA BONUS (Win Probability Added)
        # 1.0 WPA = 15.0 pts (1 full round win contrib = high value)
        # DIMINISHING RETURNS: WPA > 2.5 gets halved
        effective_wpa = total_wpa
        if total_wpa > 2.5:
            effective_wpa = 2.5 + (total_wpa - 2.5) * 0.5
        wpa_bonus = effective_wpa * 15.0
        
        # 8. EXIT FRAG WPA DISCOUNT (ROLE-AWARE)
        # Exit frags are low-value kills, reduce their WPA contribution
        # REDUCED for Rotator/Trader - they naturally rotate late
        if exit_frags > 3:
            exit_discount = (exit_frags - 3) * 3.5  # HARSHER (was 2.0)
            # Role-aware: Rotators get 60% reduced penalty (0.4x)
            if swing_score > 5:  # Rotators have high swing kills
                exit_discount *= 0.4  # NERFED from 0.5
            wpa_bonus = max(0, wpa_bonus - exit_discount)
        
        # Sum raw impact (BEFORE any caps/penalties)
        raw_before_caps = kill_points + entry_points + clutch_points + round_bonus + swing_bonus + wpa_bonus - death_penalty
        
        # SOFT CAP: Prevent explosion above 120 to preserve resolution
        if raw_before_caps > 120:
            raw_before_caps = 120 + (raw_before_caps - 120) * 0.3
        
        # Store true raw for calibration
        true_raw = raw_before_caps
        
        processed = raw_before_caps
        
        # 6. Lone Wolf Penalty (-15%)
        if tradeable_deaths > 0 and untradeable_deaths > tradeable_deaths * 2:
            processed *= 0.85
        
        # 7. Sanity Caps (no passengers getting MVP)
        if total_kills < 10 and processed > 70:
            processed = 70.0
        if kdr < 0.8 and processed > 60:
            processed = 60.0
        
        # 8. MULTIPLICATIVE DEATH TAX (high deaths = hard cap)
        # Even carries can't hit 100 if dying too much
        total_deaths = tradeable_deaths + untradeable_deaths
        if total_deaths >= 24:
            processed *= 0.50  # -50% for extreme feeding
        elif total_deaths >= 21:
            processed *= 0.60  # -40% for heavy feeding  
        elif total_deaths >= 18:
            processed *= 0.80  # -20% for high deaths
        
        # DISPLAY CLAMP: [0, 100] for UI
        # (true_raw is kept for calibration, can be negative)
        clamped = int(min(100, max(0, processed)))
        
        # Return (raw, clamped) for calibration
        return (true_raw, clamped)

    @staticmethod
    def compute_final_rating(scores: Dict[str, int], role: str, kdr: float, untradeable_deaths: int,
                             survival_rate: float = 0.0, opening_kills: int = 0, 
                             kast_percentage: float = 0.5, map_name: str = "",
                             kills: int = 0, rounds_played: int = 20) -> int:
        """
        Compute final rating with brutal calibration.
        
        PIPELINE ORDER:
        1. raw_impact
        2. role_zscore
        3. map_weight
        4. kast_adjustment
        5. role_penalties
        6. role_cap (anchors NEVER top leaderboard unless god-tier)
        
        NOTE: opponent_avg removed - was hardcoded to 50 (fake complexity).
        Will reintroduce when real opponent data is available.
        
        Bands:
        - 0-30:  Trash
        - 30-50: Below Average  
        - 50-70: Average/Good
        - 70-85: Strong
        - 85-100: Carry/God
        """
        raw_impact = scores.get("raw_impact", scores.get("impact", 50))
        
        # 1. Role-based z-score normalization
        baseline = ROLE_BASELINES.get(role, {'mean': 35.6, 'std': 22.9, 'max': 90})
        role_mean = baseline['mean']
        role_std = baseline['std']
        role_max = baseline.get('max', 90)  # Role cap
        
        z = (raw_impact - role_mean) / role_std if role_std > 0 else 0
        rating = 50 + (z * 25)
        
        # 2. Map difficulty adjustment (BRUTAL weights)
        map_weights = MAP_WEIGHTS.get(map_name, {})
        map_factor = map_weights.get(role, 1.0)
        rating *= map_factor
        
        # 4. KAST adjustment (NONLINEAR)
        kast_adjustment = get_kast_bonus(kast_percentage)
        rating += kast_adjustment
        
        # 5. Role-specific penalties (FINAL CALIBRATION)
        if role == "Entry":
            if kdr < 0.7:
                rating *= 0.90  # Heavy penalty
            elif kdr < 1.0:
                rating *= 0.90  # Dying tax - HARSHER (was 0.93)
        elif role == "AWPer":
            if kdr < 0.8:
                rating *= 0.85  # Feeding as AWP is expensive
            elif kdr < 0.9:
                rating *= 0.88  # Still too many deaths for AWP
        elif role == "Anchor" and kdr < 0.6:
            rating *= 0.80  # Anchor feeding is worst
        
        # 5b. TRADER CEILING: Mid-KDR traders shouldn't hit 98
        if role == "Trader" and kdr < 1.2:
            rating *= 0.90
        
        # 5c. ROTATOR INFLATION GUARD: Must have real impact
        if role == "Rotator" and raw_impact < 100:
            rating *= 0.95
        
        # 5d. KILL-GATED GOD RATING: Can't be 98 with mediocre kills
        if raw_impact > 105 and kills < 18:
            rating *= 0.90  # HARSHER (was 0.95 at 110)
        
        # 6. Dynamic role cap (map-aware)
        role_cap = get_dynamic_role_cap(role, map_name)
        
        # 7. ANCHOR BREAKOUT RULE: Don't suppress legit carries
        # GUARDED: require KDR > 1.1 AND KAST > 65%
        if role in ("Anchor", "Rotator", "SiteAnchor", "Trader") and raw_impact > role_cap + 15:
            if kdr > 1.1 and kast_percentage > 0.65:  # Must have good fundamentals
                role_cap += 10
        
        rating = min(rating, role_cap)
        
        # 8. SMURF DETECTION: Penalize suspicious stat-padding
        # FIXED: Use REAL rounds_played from parameters
        is_smurf, smurf_mult = detect_smurf(kdr, raw_impact, rounds_played=rounds_played)
        if is_smurf:
            rating *= smurf_mult  # Apply 0.92x penalty
        
        # 9. LOW KILL CAP: Can't be 98 with 10 kills
        if kills < 12:
            rating = min(rating, 75)
        
        # 10. FLOOR CLAMP: No human is 0
        rating = max(15, rating)
        
        # Clamp 0-100
        return int(min(100, rating))


