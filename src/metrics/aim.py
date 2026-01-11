"""
Aim Metrics Module
Calculates aim-related performance metrics.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from config import AIM_THRESHOLDS


@dataclass
class AimAnalysis:
    """Results of aim analysis."""
    headshot_percentage: float
    headshot_rating: str  # "poor", "average", "good", "excellent"
    spray_control_score: float
    spray_rating: str
    total_kills: int
    total_headshots: int
    
    # Evidence for classifier
    samples: int = 0
    confidence: float = 0.0


class AimMetrics:
    """Calculate and analyze aim metrics."""
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize with optional custom thresholds.
        
        Args:
            thresholds: Custom threshold dict, defaults to config values
        """
        self.thresholds = thresholds or AIM_THRESHOLDS
    
    def analyze(
        self,
        total_kills: int,
        headshots: int,
        total_shots: int = 0,
        total_damage: int = 0
    ) -> AimAnalysis:
        """
        Analyze aim performance.
        
        Args:
            total_kills: Number of kills
            headshots: Number of headshot kills
            total_shots: Total shots fired (if available)
            total_damage: Total damage dealt (if available)
            
        Returns:
            AimAnalysis with metrics and ratings
        """
        # Calculate headshot percentage
        hs_pct = headshots / max(total_kills, 1)
        hs_rating = self._rate_metric(hs_pct, self.thresholds["headshot_percentage"])
        
        # Calculate spray control (damage per shot)
        if total_shots > 0 and total_damage > 0:
            spray_score = total_damage / total_shots / 100  # Normalize
            spray_rating = self._rate_metric(spray_score, self.thresholds["spray_control"])
        else:
            spray_score = 0.0
            spray_rating = "unknown"
        
        # Calculate confidence based on sample size
        confidence = min(1.0, total_kills / 20)  # Full confidence at 20+ kills
        
        return AimAnalysis(
            headshot_percentage=hs_pct,
            headshot_rating=hs_rating,
            spray_control_score=spray_score,
            spray_rating=spray_rating,
            total_kills=total_kills,
            total_headshots=headshots,
            samples=total_kills,
            confidence=confidence
        )
    
    def _rate_metric(self, value: float, thresholds: Dict[str, float]) -> str:
        """Rate a metric value against thresholds."""
        if value < thresholds["poor"]:
            return "poor"
        elif value < thresholds["average"]:
            return "below_average"
        elif value < thresholds["good"]:
            return "average"
        else:
            return "good"
    
    def get_improvement_areas(self, analysis: AimAnalysis) -> list:
        """Get specific improvement areas based on analysis."""
        areas = []
        
        if analysis.headshot_rating in ["poor", "below_average"]:
            areas.append({
                "area": "headshot_percentage",
                "current": f"{analysis.headshot_percentage:.1%}",
                "target": f"{self.thresholds['headshot_percentage']['average']:.1%}",
                "priority": "high" if analysis.headshot_rating == "poor" else "medium"
            })
        
        if analysis.spray_rating == "poor":
            areas.append({
                "area": "spray_control",
                "current": f"{analysis.spray_control_score:.2f}",
                "target": f"{self.thresholds['spray_control']['average']:.2f}",
                "priority": "high"
            })
        
        return areas
