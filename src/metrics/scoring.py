"""
Scoring Engine
Normalizes various raw metrics into 0-100 scores using user-defined weighted formulas.
"""

from typing import Dict, Any

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
    def compute_aim_score(hs_percent: float, kpr: float, adr: float, counter_strafe: float = 80.0) -> int:
        """
        Aim Score.
        User Formula: hs_percent*0.3 + kpr*40 + adr*0.3
        PLUS: If mechanic < 70, penalty 15%
        """
        # HS input is 0.0-1.0 usually -> convert to 0-100
        hs_val = hs_percent * 100
        
        score = (hs_val * 0.3) + (kpr * 40) + (adr * 0.3)
        
        # Mechanical Penalty
        if counter_strafe < 70.0:
            score *= 0.85
            
        return int(min(100, max(0, score)))

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
    def compute_impact_score(entry_kills: int, multikills: int, clutches_won: int, untradeable_deaths: int) -> int:
        """
        Impact Rating.
        User Formula:
        - Opening Kills * 5
        - Clutches * 10
        - Untradeable Deaths * -2 (Penalty)
        - Multikills * 5 (Kept as minor bonus)
        """
        # Base impact from events
        score = (entry_kills * 5.0) + (clutches_won * 10.0) + (multikills * 5.0)
        
        # Penalty
        score -= (untradeable_deaths * 2.0)
        
        # Normalize: A good event score might be 20-30. We map this to 0-100?
        # User said "clamp at 85". 
        # If someone has 4 entries (20), 1 clutch (10), 2 multis (10) = 40 raw.
        # 40 raw -> should be high impact?
        # Let's scale raw * 2.0 roughly? 40*2 = 80.
        
        final_score = score * 2.5
        
        return int(min(85, max(0, final_score)))

    @staticmethod
    def compute_final_rating(scores: Dict[str, int]) -> int:
        """Compute aggregate rating."""
        weights = {
            "aim": 0.25,
            "positioning": 0.25,
            "utility": 0.20,
            "impact": 0.30
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for cat, w in weights.items():
            val = scores.get(cat)
            if val is not None and val != -1:
                total_score += val * w
                total_weight += w
                
        if total_weight == 0: return 0
        
        # Re-normalize to 100%
        return int(total_score / total_weight)
