"""
Utility Metrics Module
Calculates utility-related performance metrics.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config import UTILITY_THRESHOLDS


@dataclass
class UtilityAnalysis:
    """Results of utility analysis."""
    flash_success_rate: float
    flash_rating: str
    
    nade_damage_per_round: float
    nade_rating: str
    
    flashes_thrown: int
    flash_assists: int
    total_nade_damage: int
    rounds_played: int
    
    # Evidence for classifier
    samples: int = 0
    confidence: float = 0.0


class UtilityMetrics:
    """Calculate and analyze utility metrics."""
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize with optional custom thresholds.
        
        Args:
            thresholds: Custom threshold dict, defaults to config values
        """
        self.thresholds = thresholds or UTILITY_THRESHOLDS
    
    def analyze(
        self,
        flashes_thrown: int,
        flash_assists: int,
        total_nade_damage: int,
        rounds_played: int
    ) -> UtilityAnalysis:
        """
        Analyze utility performance.
        
        Args:
            flashes_thrown: Number of flashbangs thrown
            flash_assists: Flashes that led to kills
            total_nade_damage: Total HE/molly damage
            rounds_played: Number of rounds played
            
        Returns:
            UtilityAnalysis with metrics and ratings
        """
        # Calculate flash success rate
        flash_rate = flash_assists / max(flashes_thrown, 1)
        flash_rating = self._rate_flash(flash_rate)
        
        # Calculate nade damage per round
        nade_dpr = total_nade_damage / max(rounds_played, 1)
        nade_rating = self._rate_nade_damage(nade_dpr)
        
        # Calculate confidence based on sample size
        total_utility_events = flashes_thrown + (total_nade_damage > 0)
        confidence = min(1.0, total_utility_events / 15)
        
        return UtilityAnalysis(
            flash_success_rate=flash_rate,
            flash_rating=flash_rating,
            nade_damage_per_round=nade_dpr,
            nade_rating=nade_rating,
            flashes_thrown=flashes_thrown,
            flash_assists=flash_assists,
            total_nade_damage=total_nade_damage,
            rounds_played=rounds_played,
            samples=total_utility_events,
            confidence=confidence
        )
    
    def _rate_flash(self, rate: float) -> str:
        """Rate flash success rate."""
        thresholds = self.thresholds["flash_success_rate"]
        if rate < thresholds["poor"]:
            return "poor"
        elif rate < thresholds["average"]:
            return "below_average"
        elif rate < thresholds["good"]:
            return "average"
        else:
            return "good"
    
    def _rate_nade_damage(self, dpr: float) -> str:
        """Rate nade damage per round."""
        thresholds = self.thresholds["nade_damage_per_round"]
        if dpr < thresholds["poor"]:
            return "poor"
        elif dpr < thresholds["average"]:
            return "below_average"
        elif dpr < thresholds["good"]:
            return "average"
        else:
            return "good"
    
    def get_improvement_areas(self, analysis: UtilityAnalysis) -> list:
        """Get specific improvement areas based on analysis."""
        areas = []
        
        if analysis.flash_rating in ["poor", "below_average"]:
            areas.append({
                "area": "flash_effectiveness",
                "current": f"{analysis.flash_success_rate:.1%}",
                "target": f">{self.thresholds['flash_success_rate']['average']:.1%}",
                "priority": "medium",
                "advice": "Learn pop-flash lineups and coordinate flashes with team pushes"
            })
        
        if analysis.nade_rating in ["poor", "below_average"]:
            areas.append({
                "area": "nade_damage",
                "current": f"{analysis.nade_damage_per_round:.1f} dmg/round",
                "target": f">{self.thresholds['nade_damage_per_round']['average']} dmg/round",
                "priority": "medium",
                "advice": "Use HE grenades and molotovs to clear common positions"
            })
        
        return areas
