# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3.

"""
Player Impact Predictor
Hand-written model for player performance forecasting.

Predicts:
- P(positive_impact): Probability player will contribute positively
- Expected rating: Projected performance rating

NO sklearn. NO neural nets. Explainable only.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import math


# Player impact coefficients
PLAYER_COEFFICIENTS = {
    # Historical performance
    "avg_rating": 0.30,          # Past rating influence
    "consistency": 0.15,         # Low variance = reliable
    
    # Role fit
    "role_experience": 0.10,     # Playing familiar role
    "role_effectiveness": 0.12,  # How good at this role
    
    # Current round context
    "economy_comfort": 0.08,     # Has preferred weapons
    "man_advantage": 0.10,       # Easier with numbers
    
    # Mistakes (negative)
    "recent_mistakes": -0.15,    # Recent errors hurt confidence
    
    # Team synergy
    "team_synergy": 0.05,        # Good duo partners present
    
    # Intercept
    "intercept": 0.0,
}

# Bounds
MIN_IMPACT = 0.10
MAX_IMPACT = 0.90


def _sigmoid(x: float) -> float:
    """Sigmoid function."""
    x = max(-20, min(20, x))
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class PlayerFeatures:
    """
    Features for player impact prediction.
    """
    # Historical
    avg_rating: float = 1.0      # Historical avg (0.5-2.0 scale)
    rating_variance: float = 0.1 # How consistent
    
    # Role
    current_role: str = ""       # This round's role
    primary_role: str = ""       # Most common role
    role_frequency: float = 0.0  # How often plays this role
    
    # Economy
    equipment_value: int = 0     # Current loadout value
    preferred_value: int = 4000  # Typical full buy value
    
    # Context
    team_alive: int = 5
    enemy_alive: int = 5
    
    # Recent performance
    recent_mistake_count: int = 0
    recent_kills: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlayerPrediction:
    """
    Player impact prediction result.
    """
    impact_probability: float    # P(positive impact)
    expected_rating: float       # Projected rating
    confidence: float
    key_factors: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImpactPredictor:
    """
    Hand-written player impact predictor.
    Fully explainable weights.
    """
    
    def __init__(self, coefficients: Optional[Dict[str, float]] = None):
        self.coef = {**PLAYER_COEFFICIENTS}
        if coefficients:
            self.coef.update(coefficients)
    
    def predict(self, features: PlayerFeatures) -> PlayerPrediction:
        """
        Predict player impact for this round.
        """
        factors = {}
        
        # Historical rating influence
        # Normalize: 1.0 is average, so (rating - 1.0) gives deviation
        rating_contrib = (features.avg_rating - 1.0) * self.coef["avg_rating"]
        factors["historical"] = round(rating_contrib, 3)
        
        # Consistency (low variance = positive)
        consistency_contrib = (0.2 - features.rating_variance) * self.coef["consistency"]
        factors["consistency"] = round(consistency_contrib, 3)
        
        # Role experience
        role_match = 1.0 if features.current_role == features.primary_role else 0.0
        role_contrib = role_match * features.role_frequency * self.coef["role_experience"]
        factors["role_fit"] = round(role_contrib, 3)
        
        # Economy comfort
        if features.preferred_value > 0:
            econ_ratio = features.equipment_value / features.preferred_value
            econ_contrib = (econ_ratio - 0.5) * self.coef["economy_comfort"]
        else:
            econ_contrib = 0.0
        factors["economy"] = round(econ_contrib, 3)
        
        # Man advantage
        man_diff = features.team_alive - features.enemy_alive
        man_contrib = man_diff * self.coef["man_advantage"] / 5
        factors["numbers"] = round(man_contrib, 3)
        
        # Recent mistakes (negative)
        mistake_contrib = features.recent_mistake_count * self.coef["recent_mistakes"]
        factors["mistakes"] = round(mistake_contrib, 3)
        
        # Sum contributions
        log_odds = self.coef["intercept"]
        for v in factors.values():
            log_odds += v
        
        # Impact probability
        raw_impact = _sigmoid(log_odds)
        bounded_impact = max(MIN_IMPACT, min(MAX_IMPACT, raw_impact))
        
        # Expected rating: map impact to rating scale
        # Impact 0.5 = rating 1.0, impact 0.9 = rating ~1.5
        expected_rating = 0.5 + bounded_impact
        
        # Confidence
        has_history = 1 if features.avg_rating != 1.0 else 0
        has_role = 1 if features.current_role else 0
        has_econ = 1 if features.equipment_value > 0 else 0
        confidence = (has_history + has_role + has_econ) / 3
        
        return PlayerPrediction(
            impact_probability=round(bounded_impact, 3),
            expected_rating=round(expected_rating, 2),
            confidence=round(confidence, 2),
            key_factors=factors
        )


def predict_player_impact(
    avg_rating: float = 1.0,
    rating_variance: float = 0.1,
    current_role: str = "",
    primary_role: str = "",
    role_frequency: float = 0.5,
    equipment_value: int = 4000,
    team_alive: int = 5,
    enemy_alive: int = 5,
    recent_mistake_count: int = 0
) -> PlayerPrediction:
    """
    Convenience function for player impact prediction.
    
    Example:
        result = predict_player_impact(
            avg_rating=1.2,      # Above average player
            current_role="ENTRY",
            primary_role="ENTRY",
            role_frequency=0.7,  # Often entries
            equipment_value=4500
        )
        print(f"Expected rating: {result.expected_rating}")
    """
    features = PlayerFeatures(
        avg_rating=avg_rating,
        rating_variance=rating_variance,
        current_role=current_role,
        primary_role=primary_role,
        role_frequency=role_frequency,
        equipment_value=equipment_value,
        team_alive=team_alive,
        enemy_alive=enemy_alive,
        recent_mistake_count=recent_mistake_count
    )
    
    predictor = ImpactPredictor()
    return predictor.predict(features)
