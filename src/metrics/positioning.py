"""
Positioning Metrics Module
Calculates positioning-related performance metrics.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from config import POSITIONING_THRESHOLDS


@dataclass
class PositioningAnalysis:
    """Results of positioning analysis."""
    exposed_death_ratio: float
    exposed_rating: str
    untradeable_death_ratio: float
    trade_rating: str
    
    total_deaths: int
    exposed_deaths: int
    untradeable_deaths: int
    
    # Death position analysis
    death_locations: List[Dict] = field(default_factory=list)
    
    # Evidence for classifier
    samples: int = 0
    confidence: float = 0.0


class PositioningMetrics:
    """Calculate and analyze positioning metrics."""
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize with optional custom thresholds.
        
        Args:
            thresholds: Custom threshold dict, defaults to config values
        """
        self.thresholds = thresholds or POSITIONING_THRESHOLDS
    
    def analyze(
        self,
        total_deaths: int,
        exposed_deaths: int = 0,
        untradeable_deaths: int = 0,
        death_events: Optional[List[Dict]] = None
    ) -> PositioningAnalysis:
        """
        Analyze positioning performance.
        
        Args:
            total_deaths: Total number of deaths
            exposed_deaths: Deaths while in exposed position
            untradeable_deaths: Deaths without trade potential
            death_events: List of death event dictionaries
            
        Returns:
            PositioningAnalysis with metrics and ratings
        """
        # Calculate ratios
        exposed_ratio = exposed_deaths / max(total_deaths, 1)
        untrade_ratio = untradeable_deaths / max(total_deaths, 1)
        
        # Rate metrics
        exposed_rating = self._rate_exposed(exposed_ratio)
        trade_rating = self._rate_trade(untrade_ratio)
        
        # Analyze death locations if provided
        death_locations = []
        if death_events:
            death_locations = self._analyze_death_locations(death_events)
        
        # Calculate confidence based on sample size
        confidence = min(1.0, total_deaths / 10)  # Full confidence at 10+ deaths
        
        return PositioningAnalysis(
            exposed_death_ratio=exposed_ratio,
            exposed_rating=exposed_rating,
            untradeable_death_ratio=untrade_ratio,
            trade_rating=trade_rating,
            total_deaths=total_deaths,
            exposed_deaths=exposed_deaths,
            untradeable_deaths=untradeable_deaths,
            death_locations=death_locations,
            samples=total_deaths,
            confidence=confidence
        )
    
    def _rate_exposed(self, ratio: float) -> str:
        """Rate exposed death ratio."""
        thresholds = self.thresholds["exposed_death_ratio"]
        if ratio > thresholds["poor"]:
            return "poor"
        elif ratio > thresholds["average"]:
            return "below_average"
        elif ratio > thresholds["good"]:
            return "average"
        else:
            return "good"
    
    def _rate_trade(self, ratio: float) -> str:
        """Rate untradeable death ratio."""
        # Higher untradeable ratio is worse
        if ratio > 0.6:
            return "poor"
        elif ratio > 0.45:
            return "below_average"
        elif ratio > 0.30:
            return "average"
        else:
            return "good"
    
    def _analyze_death_locations(self, death_events: List[Dict]) -> List[Dict]:
        """Analyze death locations for patterns."""
        locations = []
        
        for event in death_events:
            x = event.get('X', 0)
            y = event.get('Y', 0)
            z = event.get('Z', 0)
            
            if x or y:
                locations.append({
                    "x": x,
                    "y": y,
                    "z": z,
                    "round": event.get('total_rounds_played', 0),
                    "weapon": event.get('weapon', 'unknown')
                })
        
        return locations
    
    def get_improvement_areas(self, analysis: PositioningAnalysis) -> list:
        """Get specific improvement areas based on analysis."""
        areas = []
        
        if analysis.exposed_rating in ["poor", "below_average"]:
            areas.append({
                "area": "exposed_positions",
                "current": f"{analysis.exposed_death_ratio:.1%}",
                "target": f"<{self.thresholds['exposed_death_ratio']['average']:.1%}",
                "priority": "high" if analysis.exposed_rating == "poor" else "medium",
                "advice": "Use cover more effectively and avoid over-peeking"
            })
        
        if analysis.trade_rating in ["poor", "below_average"]:
            areas.append({
                "area": "trade_positioning",
                "current": f"{analysis.untradeable_death_ratio:.1%} untradeable",
                "target": "<30% untradeable",
                "priority": "high" if analysis.trade_rating == "poor" else "medium",
                "advice": "Stay closer to teammates and play for trades"
            })
        
        return areas
