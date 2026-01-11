"""
Economy Metrics Module
Calculates economy-related performance metrics.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config import ECONOMY_THRESHOLDS


@dataclass
class EconomyAnalysis:
    """Results of economy analysis."""
    # Note: Economy metrics are limited without explicit buy data
    # We can infer some patterns from round outcomes and equipment
    
    estimated_force_buy_deaths: int
    force_buy_death_ratio: float
    economy_rating: str
    
    rounds_analyzed: int
    
    # Evidence for classifier
    samples: int = 0
    confidence: float = 0.0


class EconomyMetrics:
    """Calculate and analyze economy metrics."""
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize with optional custom thresholds.
        
        Args:
            thresholds: Custom threshold dict, defaults to config values
        """
        self.thresholds = thresholds or ECONOMY_THRESHOLDS
    
    def analyze(
        self,
        death_events: List[Dict],
        rounds_played: int
    ) -> EconomyAnalysis:
        """
        Analyze economy performance based on death events and equipment.
        
        Note: This is a simplified analysis. Full economy analysis would
        require buy phase data which may not be available in all demos.
        
        Args:
            death_events: List of death event dictionaries
            rounds_played: Number of rounds played
            
        Returns:
            EconomyAnalysis with metrics and ratings
        """
        # Estimate force buy rounds based on weapon at death
        # This is a heuristic - players dying with pistols/SMGs in later rounds
        # might indicate force buys
        
        force_buy_deaths = 0
        total_deaths = len(death_events)
        
        force_buy_weapons = {
            'glock', 'usp_silencer', 'hkp2000', 'p250', 'tec9', 'cz75a', 'fiveseven',
            'mac10', 'mp9', 'mp7', 'mp5sd', 'ump45', 'bizon', 'p90',
            'nova', 'xm1014', 'sawedoff', 'mag7'
        }
        
        for event in death_events:
            round_num = event.get('total_rounds_played', 1)
            weapon = str(event.get('weapon', '')).lower()
            
            # If dying with a force buy weapon after round 3, might be a force buy
            if round_num > 3 and weapon in force_buy_weapons:
                force_buy_deaths += 1
        
        # Calculate ratio
        force_buy_ratio = force_buy_deaths / max(total_deaths, 1)
        
        # Rate economy
        rating = self._rate_economy(force_buy_ratio)
        
        # Confidence is lower because this is heuristic-based
        confidence = min(0.7, total_deaths / 15)
        
        return EconomyAnalysis(
            estimated_force_buy_deaths=force_buy_deaths,
            force_buy_death_ratio=force_buy_ratio,
            economy_rating=rating,
            rounds_analyzed=rounds_played,
            samples=total_deaths,
            confidence=confidence
        )
    
    def _rate_economy(self, force_buy_death_ratio: float) -> str:
        """Rate economy management."""
        thresholds = self.thresholds["force_buy_death_ratio"]
        if force_buy_death_ratio > thresholds["poor"]:
            return "poor"
        elif force_buy_death_ratio > thresholds["average"]:
            return "below_average"
        elif force_buy_death_ratio > thresholds["good"]:
            return "average"
        else:
            return "good"
    
    def get_improvement_areas(self, analysis: EconomyAnalysis) -> list:
        """Get specific improvement areas based on analysis."""
        areas = []
        
        if analysis.economy_rating in ["poor", "below_average"]:
            areas.append({
                "area": "economy_management",
                "current": f"{analysis.force_buy_death_ratio:.1%} force buy deaths",
                "target": f"<{self.thresholds['force_buy_death_ratio']['average']:.1%}",
                "priority": "low",  # Lower priority due to heuristic nature
                "advice": "Play more conservatively on eco/force buy rounds",
                "note": "Economy analysis is estimated - consider actual buy decisions"
            })
        
        return areas
