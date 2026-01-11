"""
Scoring Engine
Normalizes various raw metrics into 0-100 scores using user-defined weighted formulas.
"""

from typing import Dict, Any, Tuple

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
        opening_kills_won: int,     # Opening kills in rounds team won
        opening_kills_lost: int,    # Opening kills in rounds team lost
        entry_deaths: int,          # Deaths in opening duels
        
        # Kill context
        kills_in_won_rounds: int,
        kills_in_lost_rounds: int,
        exit_frags: int,
        
        # Round-winning plays
        multikills: int, 
        clutches_1v1: int, 
        clutches_1vN: int,
        
        # Death context
        untradeable_deaths: int, 
        tradeable_deaths: int,
        
        # Stats
        total_kills: int
    ) -> int:
        """
        Impact Rating (Round-Context Aware - HARDENED).
        
        CORE PRINCIPLE: Kills only count if they help win rounds.
        Exit frag padding is PUNISHED.
        
        Impact Bands:
        - 0-10:  AFK/Useless
        - 10-30: Low Impact / Exit Fragger
        - 30-60: Contributor
        - 60+:   Carry
        
        Formula:
        1. Kill Value (round-context weighted):
           - Kill in won round: +6
           - Kill in lost round: +0.5 (91% reduction - almost worthless)
           - Exit frag: -5 (BRUTAL - stat padding trash)
        
        2. Opening Picks (highest value):
           - Opening kill + round won: +12
           - Opening kill + round lost: +2
           - Entry death: -6 (round-losing)
        
        3. Clutches (earned, no floors):
           - 1v1: +15
           - 1vN: +25
           - Multikill rounds: +5
        
        4. Trade Value:
           - Died traded: -1 (team got value, minor penalty)
           - Died untraded: -6 (pure waste)
        
        NO FLOORS. Earn every point.
        """
        impact = 0.0
        
        # 1. Kill Value (round-context)
        impact += kills_in_won_rounds * 6.0      # Full value
        impact += kills_in_lost_rounds * 0.5     # Almost worthless
        impact -= exit_frags * 5.0               # BRUTAL padding penalty
        
        # 2. Opening Picks (critical plays)
        impact += opening_kills_won * 12.0       # Round-winning opener
        impact += opening_kills_lost * 2.0       # Failed to convert
        impact -= entry_deaths * 6.0             # Round-losing
        
        # 3. Clutches (earned value, no free floors)
        impact += clutches_1v1 * 15.0
        impact += clutches_1vN * 25.0
        impact += multikills * 5.0
        
        # 4. Death Value
        impact -= tradeable_deaths * 1.0         # Died but traded (minor)
        impact -= untradeable_deaths * 6.0       # Died alone (waste)
        
        # No artificial floor - let rating handle punishment
        # Just prevent true negatives
        return int(min(100, max(0, impact)))

    @staticmethod
    def compute_final_rating(scores: Dict[str, int], role: str, kdr: float, untradeable_deaths: int,
                             survival_rate: float = 0.0, opening_kills: int = 0, 
                             kast_percentage: float = 0.5) -> int:
        """
        Compute aggregate rating with penalties.
        
        LOCKED WEIGHTS (do not change):
        - Aim: 0.35
        - Positioning: 0.25  
        - Impact: 0.40
        
        Impact Bands:
        - 0-10:  Useless - cap at 30
        - 10-30: Low Impact - cap at 45
        - 30-60: Contributor - no cap
        - 60+:   Carry - no cap
        
        Role Adjustments:
        - Entry: KDR<0.8 penalty (*0.75)
        - AWPer: Survival bonus (space denial proxy), opening kill bonus
                 KDR<0.8 penalty (*0.80) - expensive role to feed on
        
        Other Penalties:
        - Death Tax: -0.5 per untradeable death
        
        KAST Adjustment:
        - KAST% < 50%: Penalty up to -10
        - KAST% > 70%: Bonus up to +10
        
        FULL 0-100 SCALE (no arbitrary cap)
        Bands:
        - 0-40:  Bad
        - 40-60: Average  
        - 60-80: Strong
        - 80-100: Carry
        """
        aim = scores.get("aim") if scores.get("aim") is not None else 50
        pos = scores.get("positioning") if scores.get("positioning") is not None else 50
        imp = scores.get("impact") if scores.get("impact") is not None else 50
        
        rating = (aim * 0.35) + (pos * 0.25) + (imp * 0.40)
        
        # 1. Death Tax
        rating -= (untradeable_deaths * 0.5)
        
        # 2. KAST Adjustment (new)
        # KAST 70%+ = +10, KAST 50% = 0, KAST 30% = -10
        # Linear scale: (kast - 0.5) * 50
        kast_adjustment = (kast_percentage - 0.5) * 20.0
        rating += kast_adjustment
        
        # 3. Impact Compression (not hard caps - preserve nuance)
        if imp <= 10:
            # Useless band - compress, don't nuke
            rating *= 0.75
        elif imp <= 30:
            # Low impact band - moderate compression
            rating *= 0.90
        # 30-60 = contributor, 60+ = carry - no compression
            
        # 4. Role-Specific Adjustments
        if role == "Entry" and kdr < 0.8:
            rating *= 0.75
        elif role == "AWPer":
            # AWPer space-denial: survival = map control
            # +5 bonus if survival > 50% (stayed alive, denied space)
            if survival_rate > 0.5:
                rating += 5.0
            # Opening picks are high-value for AWPers
            rating += opening_kills * 2.0
            # But feeding as AWP is expensive
            if kdr < 0.8:
                rating *= 0.80
            
        # FULL 0-100 SCALE - no arbitrary cap
        return int(min(100, max(0, rating)))
