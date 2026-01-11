"""
Mistake Classifier
Rule-based classification of gameplay mistakes.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from config import (
    MistakeCategory,
    MIN_EVENTS_FOR_CLASSIFICATION,
    CONFIDENCE_WEIGHTS,
    FALLBACK_MESSAGES
)
from src.features.extractor import PlayerFeatures
from src.metrics import AimMetrics, PositioningMetrics, UtilityMetrics, EconomyMetrics


@dataclass
class ClassifiedMistake:
    """A classified gameplay mistake."""
    category: str
    subcategory: str
    severity: str  # "low", "medium", "high"
    confidence: float  # 0.0 - 1.0
    
    # Evidence
    evidence_metrics: Dict[str, Any] = field(default_factory=dict)
    current_value: str = ""
    target_value: str = ""
    
    # Feedback
    feedback_key: str = ""  # Key for fallback message
    priority: int = 0  # For sorting (higher = more important)


class MistakeClassifier:
    """
    Deterministic rule-based classifier for gameplay mistakes.
    
    The classifier analyzes player features against thresholds and
    produces classified mistakes with evidence and confidence scores.
    """
    
    def __init__(self):
        """Initialize the classifier with metric analyzers."""
        self.aim_metrics = AimMetrics()
        self.positioning_metrics = PositioningMetrics()
        self.utility_metrics = UtilityMetrics()
        self.economy_metrics = EconomyMetrics()
    
    def classify(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        """
        Classify mistakes for a player based on their features.
        
        Args:
            features: PlayerFeatures object from FeatureExtractor
            
        Returns:
            List of ClassifiedMistake objects, sorted by priority
        """
        mistakes = []
        
        # Classify aim mistakes
        aim_mistakes = self._classify_aim(features)
        mistakes.extend(aim_mistakes)
        
        # Classify positioning mistakes
        pos_mistakes = self._classify_positioning(features)
        mistakes.extend(pos_mistakes)
        
        # Classify utility mistakes
        util_mistakes = self._classify_utility(features)
        mistakes.extend(util_mistakes)
        
        # Classify economy mistakes
        econ_mistakes = self._classify_economy(features)
        mistakes.extend(econ_mistakes)
        
        # Sort by priority (highest first)
        mistakes.sort(key=lambda m: m.priority, reverse=True)
        
        return mistakes
    
    def _classify_aim(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        """Classify aim-related mistakes."""
        mistakes = []
        
        # Check if enough samples
        if features.kills < MIN_EVENTS_FOR_CLASSIFICATION["aim"]:
            return mistakes
        
        # Analyze aim
        analysis = self.aim_metrics.analyze(
            total_kills=features.kills,
            headshots=features.headshots,
            total_damage=features.total_damage
        )
        
        # Check headshot percentage
        if analysis.headshot_rating in ["poor", "below_average"]:
            severity = "high" if analysis.headshot_rating == "poor" else "medium"
            confidence = self._calculate_confidence(
                sample_size=features.kills,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["aim"],
                base_confidence=analysis.confidence
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.AIM,
                subcategory="headshot_percentage",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "headshot_percentage": analysis.headshot_percentage,
                    "total_kills": features.kills,
                    "headshots": features.headshots
                },
                current_value=f"{analysis.headshot_percentage:.1%}",
                target_value=">30%",
                feedback_key="headshot_low",
                priority=8 if severity == "high" else 5
            ))
        
        # Check spray control if data available
        if analysis.spray_rating == "poor":
            confidence = self._calculate_confidence(
                sample_size=features.kills,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["aim"],
                base_confidence=0.6  # Lower base confidence for spray
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.AIM,
                subcategory="spray_control",
                severity="medium",
                confidence=confidence,
                evidence_metrics={
                    "spray_score": analysis.spray_control_score,
                },
                current_value=f"{analysis.spray_control_score:.2f}",
                target_value=">0.25",
                feedback_key="spray_poor",
                priority=4
            ))
        
        return mistakes
    
    def _classify_positioning(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        """Classify positioning-related mistakes."""
        mistakes = []
        
        # Check if enough samples
        if features.deaths < MIN_EVENTS_FOR_CLASSIFICATION["positioning"]:
            return mistakes
        
        # Analyze positioning
        analysis = self.positioning_metrics.analyze(
            total_deaths=features.deaths,
            exposed_deaths=features.exposed_deaths,
            untradeable_deaths=int(features.deaths * features.untradeable_death_ratio),
            death_events=features.death_events
        )
        
        # Check exposed deaths
        if analysis.exposed_rating in ["poor", "below_average"]:
            severity = "high" if analysis.exposed_rating == "poor" else "medium"
            confidence = self._calculate_confidence(
                sample_size=features.deaths,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["positioning"],
                base_confidence=analysis.confidence
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.POSITIONING,
                subcategory="exposed_positions",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "exposed_death_ratio": analysis.exposed_death_ratio,
                    "total_deaths": features.deaths,
                    "exposed_deaths": analysis.exposed_deaths
                },
                current_value=f"{analysis.exposed_death_ratio:.1%}",
                target_value="<35%",
                feedback_key="exposed_deaths",
                priority=9 if severity == "high" else 6
            ))
        
        # Check untradeable deaths
        if analysis.trade_rating in ["poor", "below_average"]:
            severity = "high" if analysis.trade_rating == "poor" else "medium"
            confidence = self._calculate_confidence(
                sample_size=features.deaths,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["positioning"],
                base_confidence=analysis.confidence
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.POSITIONING,
                subcategory="untradeable_deaths",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "untradeable_death_ratio": analysis.untradeable_death_ratio,
                    "total_deaths": features.deaths
                },
                current_value=f"{analysis.untradeable_death_ratio:.1%}",
                target_value="<30%",
                feedback_key="untradeable",
                priority=7 if severity == "high" else 5
            ))
        
        return mistakes
    
    def _classify_utility(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        """Classify utility-related mistakes."""
        mistakes = []
        
        # Check if enough samples
        if features.flashes_thrown < MIN_EVENTS_FOR_CLASSIFICATION["utility"]:
            return mistakes
        
        # Analyze utility
        analysis = self.utility_metrics.analyze(
            flashes_thrown=features.flashes_thrown,
            flash_assists=features.flash_assists,
            total_nade_damage=features.grenade_damage,
            rounds_played=features.rounds_played
        )
        
        # Check flash effectiveness
        if analysis.flash_rating in ["poor", "below_average"]:
            severity = "medium" if analysis.flash_rating == "poor" else "low"
            confidence = self._calculate_confidence(
                sample_size=features.flashes_thrown,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["utility"],
                base_confidence=analysis.confidence
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.UTILITY,
                subcategory="flash_effectiveness",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "flash_success_rate": analysis.flash_success_rate,
                    "flashes_thrown": features.flashes_thrown,
                    "flash_assists": features.flash_assists
                },
                current_value=f"{analysis.flash_success_rate:.1%}",
                target_value=">20%",
                feedback_key="flash_ineffective",
                priority=3
            ))
        
        # Check nade damage
        if analysis.nade_rating in ["poor", "below_average"]:
            severity = "low"
            confidence = self._calculate_confidence(
                sample_size=features.rounds_played,
                min_samples=MIN_EVENTS_FOR_CLASSIFICATION["utility"],
                base_confidence=analysis.confidence
            )
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.UTILITY,
                subcategory="nade_damage",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "nade_damage_per_round": analysis.nade_damage_per_round,
                    "total_nade_damage": features.grenade_damage
                },
                current_value=f"{analysis.nade_damage_per_round:.1f}/round",
                target_value=">25/round",
                feedback_key="low_nade_damage",
                priority=2
            ))
        
        return mistakes
    
    def _classify_economy(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        """Classify economy-related mistakes."""
        mistakes = []
        
        # Check if enough samples
        if features.deaths < MIN_EVENTS_FOR_CLASSIFICATION["economy"]:
            return mistakes
        
        # Analyze economy
        analysis = self.economy_metrics.analyze(
            death_events=features.death_events,
            rounds_played=features.rounds_played
        )
        
        # Check force buy deaths
        if analysis.economy_rating in ["poor", "below_average"]:
            severity = "low"  # Economy is heuristic-based
            confidence = analysis.confidence * 0.8  # Lower confidence
            
            mistakes.append(ClassifiedMistake(
                category=MistakeCategory.ECONOMY,
                subcategory="force_buy_deaths",
                severity=severity,
                confidence=confidence,
                evidence_metrics={
                    "force_buy_death_ratio": analysis.force_buy_death_ratio,
                    "estimated_force_buy_deaths": analysis.estimated_force_buy_deaths
                },
                current_value=f"{analysis.force_buy_death_ratio:.1%}",
                target_value="<50%",
                feedback_key="force_buy_deaths",
                priority=1
            ))
        
        return mistakes
    
    def _calculate_confidence(
        self,
        sample_size: int,
        min_samples: int,
        base_confidence: float
    ) -> float:
        """
        Calculate confidence score based on sample size and base confidence.
        
        Uses the weights from config to combine factors.
        """
        # Sample size factor (0-1)
        sample_factor = min(1.0, sample_size / (min_samples * 4))
        
        # Combine with base confidence
        confidence = (
            CONFIDENCE_WEIGHTS["sample_size"] * sample_factor +
            CONFIDENCE_WEIGHTS["consistency"] * base_confidence +
            CONFIDENCE_WEIGHTS["severity"] * 0.5  # Default severity weight
        )
        
        return min(1.0, confidence)
    
    def get_fallback_message(self, mistake: ClassifiedMistake) -> str:
        """Get fallback feedback message for a mistake."""
        category_messages = FALLBACK_MESSAGES.get(mistake.category, {})
        return category_messages.get(
            mistake.feedback_key,
            "Review your gameplay and focus on improvement."
        )
    
    def get_summary(self, mistakes: List[ClassifiedMistake]) -> Dict[str, Any]:
        """
        Get a summary of classified mistakes.
        
        Args:
            mistakes: List of ClassifiedMistake objects
            
        Returns:
            Summary dictionary with counts and priorities
        """
        if not mistakes:
            return {
                "total_mistakes": 0,
                "categories": {},
                "top_priority": None
            }
        
        # Count by category
        categories = {}
        for mistake in mistakes:
            if mistake.category not in categories:
                categories[mistake.category] = {
                    "count": 0,
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 0
                }
            categories[mistake.category]["count"] += 1
            categories[mistake.category][f"{mistake.severity}_severity"] += 1
        
        return {
            "total_mistakes": len(mistakes),
            "categories": categories,
            "top_priority": mistakes[0] if mistakes else None,
            "average_confidence": sum(m.confidence for m in mistakes) / len(mistakes)
        }
