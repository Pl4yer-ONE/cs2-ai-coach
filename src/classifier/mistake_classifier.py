"""
Smart Mistake Classifier
Identifies specific tactical errors using advanced context checking.

Mistakes Detected:
- Untradeable Death: Dying solo > 300u from team.
- Dry Peek (AWP): Peeking an AWP without util.
- Dry Peek (Rifle): Peeking standard angles without util.
- Bad Spacing: Clumping (<200u).
- Solo Play: Dying deep alone in late round.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np

from src.features.extractor import PlayerFeatures, DeathContext
from src.config import TRADE_DIST_UNITS

@dataclass
class ClassifiedMistake:
    """A specific identified mistake."""
    tick: int
    round_num: int
    mistake_type: str  # e.g., "untradeable_death", "dry_peek"
    details: str
    severity: float  # 0.0 to 1.0
    correction: str

class MistakeClassifier:
    """
    Classifies mistakes based on extracted player features.
    """
    
    def classify(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        mistakes.extend(self._analyze_deaths(features))
        mistakes.extend(self._analyze_utility(features))
        return mistakes

    def _analyze_deaths(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        
        for death in features.death_contexts:
            # 1. Untradeable Death (Strict)
            # Logic: Died, wasn't traded, nearest teammate > TRADE_DIST (300u)
            if not death.was_traded and not death.tradeable_position:
                # Valid Exceptions:
                # - Entry Fragger (if they had support nearby but trade failed)
                # - Lurker (late round)
                
                is_lurk_exception = (features.detected_role == "Lurker" and death.round_time == "mid")
                
                if not is_lurk_exception:
                    mistakes.append(ClassifiedMistake(
                        tick=death.tick,
                        round_num=death.round_num,
                        mistake_type="untradeable_death",
                        details=f"Died isolated ({int(death.nearest_teammate_distance)}u). No trade possibility.",
                        severity=0.9,
                        correction="Ensure you are within 300u of a teammate when taking contact."
                    ))

            # 2. Dry Peek vs AWP
            if death.killer_id and death.peeked_dry and death.weapon == "awp":
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    mistake_type="dry_peek_awp",
                    details="Dry peeked into an AWP.",
                    severity=0.95,
                    correction="Never peek an AWP without a flash. Shoulder peek to bait the shot first."
                ))
                
            # 3. Dry Peek (Standard)
            elif death.peeked_dry and not death.was_traded and death.round_time != "late":
                 mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    mistake_type="dry_peek",
                    details="Challenged angle without utility.",
                    severity=0.7,
                    correction="Use support flashes or jiggle peek before committing."
                ))

            # 4. Bad Spacing (Clumping)
            if death.teammates_nearby >= 2 and death.nearest_teammate_distance < 150:
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    mistake_type="bad_spacing_clump",
                    details="Died stacked on teammates (<150u).",
                    severity=0.6,
                    correction="Maintain spacing to avoid spraydowns and collateral damage."
                ))
            
            # 5. Late Round Solo throw
            if death.round_time == "late" and death.nearest_teammate_distance > 1500 and not death.was_traded:
                 mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    mistake_type="solo_late_round",
                    details="Died in late round (>60s) completely alone (>1500u).",
                    severity=0.8,
                    correction="In late rounds, group up. Playing solo makes you an easy target."
                ))

        return mistakes

    def _analyze_utility(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        # Support Role check
        if features.detected_role == "Support" and features.flashes_thrown < 3 and features.rounds_played > 10:
             mistakes.append(ClassifiedMistake(
                tick=0,
                round_num=0, 
                mistake_type="role_failure_support",
                details="Averaged < 0.3 flashes/round as Support.",
                severity=0.5,
                correction="Buy and use more flashes to support your Entry."
            ))
        return mistakes
