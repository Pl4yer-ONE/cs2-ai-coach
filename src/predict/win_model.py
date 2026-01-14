# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3.

"""
Round Win Predictor
Hand-written logistic regression for round outcome prediction.

NO sklearn. NO neural nets. Explainable coefficients only.

Features used:
- Economy differential
- Man advantage
- Role composition
- Mistake count
- Strategy type

Output: P(round_win) bounded [0.05, 0.95]
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
import math


# Explicit, explainable coefficients
# These are calibrated weights - can be tuned empirically
COEFFICIENTS = {
    # Economy (normalized to $1000 units)
    "economy_diff": 0.15,        # +15% per $1000 advantage
    
    # Man advantage
    "man_advantage": 0.20,       # +20% per player advantage
    
    # Role quality (presence of key roles)
    "has_entry": 0.05,           # Entry fragger present
    "has_support": 0.03,         # Support/anchor present
    "role_diversity": 0.02,      # Multiple distinct roles
    
    # Mistakes (negative)
    "mistake_count": -0.08,      # -8% per mistake
    "high_severity_mistakes": -0.12,  # -12% per HIGH mistake
    
    # Strategy (T-side advantage for good strats)
    "execute_strat": 0.05,       # Coordinated execute
    "rush_strat": -0.03,         # Rush = risky
    "default_strat": 0.02,       # Default = safe
    
    # Intercept (base probability)
    "intercept": 0.0,            # Centered at 50%
}

# Bounds to prevent extreme predictions
MIN_PROBABILITY = 0.05
MAX_PROBABILITY = 0.95


def _sigmoid(x: float) -> float:
    """Sigmoid function for logistic regression."""
    # Clamp to prevent overflow
    x = max(-20, min(20, x))
    return 1.0 / (1.0 + math.exp(-x))


def _logit(p: float) -> float:
    """Inverse sigmoid (log-odds)."""
    p = max(0.001, min(0.999, p))
    return math.log(p / (1 - p))


@dataclass
class RoundFeatures:
    """
    Features extracted for round prediction.
    """
    # Economy
    team_economy: int = 0        # Team avg equipment value
    enemy_economy: int = 0       # Enemy avg equipment value
    
    # Players alive at round start
    team_alive: int = 5
    enemy_alive: int = 5
    
    # Role composition (counts)
    entry_count: int = 0
    support_count: int = 0
    lurk_count: int = 0
    anchor_count: int = 0
    
    # Mistakes made this round
    mistake_count: int = 0
    high_severity_count: int = 0
    
    # Strategy
    strategy: str = ""           # EXECUTE_A, RUSH_B, etc.
    
    # Side
    is_t_side: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoundPrediction:
    """
    Round win probability prediction.
    """
    probability: float           # P(win) for team
    confidence: float            # How reliable is this prediction
    features_used: int           # Number of features with data
    dominant_factor: str         # Most influential factor
    factors: Dict[str, float]    # Individual factor contributions
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WinPredictor:
    """
    Hand-written logistic regression predictor.
    No ML libraries. Fully explainable.
    """
    
    def __init__(self, coefficients: Optional[Dict[str, float]] = None):
        self.coef = {**COEFFICIENTS}
        if coefficients:
            self.coef.update(coefficients)
    
    def predict(self, features: RoundFeatures) -> RoundPrediction:
        """
        Predict round win probability.
        
        Returns:
            RoundPrediction with bounded probability and factor breakdown.
        """
        factors = {}
        features_used = 0
        
        # Economy differential (normalized to $1000)
        econ_diff = (features.team_economy - features.enemy_economy) / 1000
        econ_contrib = econ_diff * self.coef["economy_diff"]
        factors["economy"] = round(econ_contrib, 3)
        if features.team_economy > 0 or features.enemy_economy > 0:
            features_used += 1
        
        # Man advantage
        man_diff = features.team_alive - features.enemy_alive
        man_contrib = man_diff * self.coef["man_advantage"]
        factors["man_advantage"] = round(man_contrib, 3)
        if features.team_alive != 5 or features.enemy_alive != 5:
            features_used += 1
        
        # Role composition
        role_contrib = 0.0
        if features.entry_count > 0:
            role_contrib += self.coef["has_entry"]
            features_used += 1
        if features.support_count > 0 or features.anchor_count > 0:
            role_contrib += self.coef["has_support"]
            features_used += 1
        
        distinct_roles = sum([
            1 for c in [
                features.entry_count,
                features.support_count,
                features.lurk_count,
                features.anchor_count
            ] if c > 0
        ])
        role_contrib += distinct_roles * self.coef["role_diversity"]
        factors["roles"] = round(role_contrib, 3)
        
        # Mistakes (negative contribution)
        mistake_contrib = (
            features.mistake_count * self.coef["mistake_count"] +
            features.high_severity_count * self.coef["high_severity_mistakes"]
        )
        factors["mistakes"] = round(mistake_contrib, 3)
        if features.mistake_count > 0:
            features_used += 1
        
        # Strategy
        strat = features.strategy.upper()
        strat_contrib = 0.0
        if "EXECUTE" in strat:
            strat_contrib = self.coef["execute_strat"]
        elif "RUSH" in strat:
            strat_contrib = self.coef["rush_strat"]
        elif "DEFAULT" in strat:
            strat_contrib = self.coef["default_strat"]
        factors["strategy"] = round(strat_contrib, 3)
        if features.strategy:
            features_used += 1
        
        # Sum all contributions (log-odds scale)
        log_odds = self.coef["intercept"]
        for v in factors.values():
            log_odds += v
        
        # Convert to probability via sigmoid
        raw_prob = _sigmoid(log_odds)
        
        # Bound the probability
        bounded_prob = max(MIN_PROBABILITY, min(MAX_PROBABILITY, raw_prob))
        
        # Find dominant factor
        dominant = max(factors, key=lambda k: abs(factors[k]))
        
        # Confidence based on features available
        confidence = min(1.0, features_used / 5)  # Max confidence at 5+ features
        
        return RoundPrediction(
            probability=round(bounded_prob, 3),
            confidence=round(confidence, 2),
            features_used=features_used,
            dominant_factor=dominant,
            factors=factors
        )


def predict_round_win(
    team_economy: int = 4000,
    enemy_economy: int = 4000,
    team_alive: int = 5,
    enemy_alive: int = 5,
    entry_count: int = 0,
    support_count: int = 0,
    mistake_count: int = 0,
    high_severity_count: int = 0,
    strategy: str = ""
) -> RoundPrediction:
    """
    Convenience function for round win prediction.
    
    Example:
        result = predict_round_win(
            team_economy=1500,   # eco
            enemy_economy=4500,  # gun round
            team_alive=5,
            enemy_alive=4,       # man advantage
            mistake_count=1
        )
        print(f"Win probability: {result.probability}")
    """
    features = RoundFeatures(
        team_economy=team_economy,
        enemy_economy=enemy_economy,
        team_alive=team_alive,
        enemy_alive=enemy_alive,
        entry_count=entry_count,
        support_count=support_count,
        mistake_count=mistake_count,
        high_severity_count=high_severity_count,
        strategy=strategy
    )
    
    predictor = WinPredictor()
    return predictor.predict(features)
