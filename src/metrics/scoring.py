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
        Aim Score.
        User Formula: hs_percent*0.3 + kpr*40 + adr*0.3
        
        Non-linear mechanical penalty based on counter-strafe quality.
        See _get_cs_multiplier for curve.
        
        Returns:
            Tuple of (raw_aim, effective_aim) - both 0-100
        """
        # HS input is 0.0-1.0 usually -> convert to 0-100
        hs_val = hs_percent * 100
        
        raw_score = (hs_val * 0.3) + (kpr * 40) + (adr * 0.3)
        raw_aim = int(min(100, max(0, raw_score)))
        
        # Non-linear Mechanical Penalty
        cs_mult = ScoreEngine._get_cs_multiplier(counter_strafe)
        effective_score = raw_score * cs_mult
            
        effective_aim = int(min(100, max(0, effective_score)))
        
        return (raw_aim, effective_aim)

    @staticmethod
    def compute_positioning_score(untradeable_ratio: float, trade_success: float = 0.0, survival_rate: float = 0.0) -> int:
        """
        Positioning Score.
        User Formula: 50 - (untradeable_death_ratio * 50) + trade_success * 30 + survival * 20
        """
        base = 50.0
        penalty = untradeable_ratio * 50.0
        bonus_trade = trade_success * 30.0 
        bonus_surv = survival_rate * 20.0
        
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
        entry_kills: int, 
        entry_deaths: int,
        multikills: int, 
        clutches_1v1: int, 
        clutches_1vN: int,
        untradeable_deaths: int, 
        tradeable_deaths: int,
        adr: float, 
        total_kills: int,
        total_deaths: int
    ) -> int:
        """
        Impact Rating (Perfect Form).
        
        CORE PRINCIPLE: Reward SUCCESS, not ATTEMPTS.
        
        Impact Bands:
        - 0-10:  AFK/Useless - literally did nothing
        - 10-30: Failed Entry / Low Impact - tried but failed
        - 30-60: Contributor - average player
        - 60+:   Carry - won rounds for team
        
        Formula:
        1. Opening Pick Value:
           - Entry Kill: +10 (you won the entry)
           - Entry Death: -3 (you lost the entry but created info)
           
        2. Round-Winning Plays:
           - 1v1 Clutch: +15
           - 1vN Clutch: +25
           - Multikill rounds: +6 each
           
        3. Trade Value:
           - Tradeable deaths: +1 each (you died in position to be traded)
           - Untradeable deaths: -2 each (you died alone, waste)
           
        4. Damage Context:
           - (ADR - 75) * 0.2
           
        5. Entry Success Rate Bonus:
           - If entry_attempts > 2 and success_rate > 50%: +8
           - If entry_attempts > 2 and success_rate < 30%: -5 (feeder penalty)
        """
        impact = 0.0
        
        # 1. Opening Pick Value
        impact += entry_kills * 10.0      # Won entry = massive value
        impact -= entry_deaths * 3.0       # Lost entry = some value (info) but net negative
        
        # 2. Round-Winning Plays
        impact += clutches_1v1 * 15.0
        impact += clutches_1vN * 25.0
        impact += multikills * 6.0
        
        # 3. Trade Value
        impact += tradeable_deaths * 1.0   # Died in good position
        impact -= untradeable_deaths * 2.0  # Died alone
        
        # 4. Damage Context
        impact += (adr - 75.0) * 0.2
        
        # 5. Entry Success Rate
        entry_attempts = entry_kills + entry_deaths
        if entry_attempts >= 2:
            success_rate = entry_kills / entry_attempts
            if success_rate >= 0.50:
                impact += 8.0  # Good entry fragger
            elif success_rate < 0.30:
                impact -= 5.0  # Feeder penalty
        
        # Floor: clutch winners are NOT zero impact
        total_clutches = clutches_1v1 + clutches_1vN
        if total_clutches > 0:
            impact = max(impact, 12.0 + (total_clutches * 6.0))
        
        # Minimum: if you have kills, you're not AFK
        if total_kills > 0 and impact < 5:
            impact = 5.0
        
        # Clamp 0-100
        return int(min(100, max(0, impact)))

    @staticmethod
    def compute_final_rating(scores: Dict[str, int], role: str, kdr: float, untradeable_deaths: int,
                             survival_rate: float = 0.0, opening_kills: int = 0) -> int:
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
        """
        aim = scores.get("aim") if scores.get("aim") is not None else 50
        pos = scores.get("positioning") if scores.get("positioning") is not None else 50
        imp = scores.get("impact") if scores.get("impact") is not None else 50
        
        rating = (aim * 0.35) + (pos * 0.25) + (imp * 0.40)
        
        # 1. Death Tax
        rating -= (untradeable_deaths * 0.5)
        
        # 2. Impact Band Caps (graduated, not binary)
        if imp <= 10:
            # Useless band - hard cap
            rating = min(rating, 30.0)
        elif imp <= 30:
            # Low impact band - moderate cap
            rating = min(rating, 45.0)
        # 30-60 = contributor, 60+ = carry - no cap
            
        # 3. Role-Specific Adjustments
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
            
        return int(min(70, max(0, rating)))
