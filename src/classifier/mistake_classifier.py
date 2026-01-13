"""
Mistake Classifier
Identifies specific tactical errors from demo analysis.

Detects:
- Dry peeks (challenging angles without flash support)
- Untradeable deaths (dying too far from teammates)
- Bad spacing (stacking on teammates)
- Solo late-round plays (dying alone when should group)
"""

from typing import List
from dataclasses import dataclass

from src.features.extractor import PlayerFeatures, DeathContext

# Tick rate for time calculations
TICK_RATE = 64


@dataclass
class ClassifiedMistake:
    """A mistake with full context for reporting."""
    tick: int
    round_num: int
    round_time_seconds: float
    map_area: str
    player_name: str
    mistake_type: str
    details: str
    severity: float
    correction: str


def _get_round_time_seconds(death: DeathContext) -> float:
    """Convert round_time phase to approximate seconds."""
    phase_map = {"early": 15.0, "mid": 45.0, "late": 75.0, "unknown": 30.0}
    return phase_map.get(death.round_time, 30.0)


class MistakeClassifier:
    """Classifies mistakes from player features."""
    
    def classify(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        mistakes.extend(self._analyze_deaths(features))
        mistakes.extend(self._analyze_utility(features))
        return mistakes

    def _analyze_deaths(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        player_name = features.player_name or "Unknown"
        
        for death in features.death_contexts:
            round_time = _get_round_time_seconds(death)
            map_area = death.map_area or "Unknown"
            
            # 1. Untradeable Death
            if not death.was_traded and death.nearest_teammate_distance > 400:
                is_lurk_exception = (features.detected_role == "Lurker" and death.round_time == "mid")
                is_entry_exception = death.is_entry_frag
                
                if not is_lurk_exception and not is_entry_exception:
                    mistakes.append(ClassifiedMistake(
                        tick=death.tick,
                        round_num=death.round_num,
                        round_time_seconds=round_time,
                        map_area=map_area,
                        player_name=player_name,
                        mistake_type="untradeable_death",
                        details=f"Died {int(death.nearest_teammate_distance)}u from nearest teammate",
                        severity=0.85,
                        correction="Stay within 400u of a teammate when taking fights"
                    ))

            # 2. Dry Peek vs AWP
            if death.killer_id and death.peeked_dry and death.weapon == "awp":
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    round_time_seconds=round_time,
                    map_area=map_area,
                    player_name=player_name,
                    mistake_type="dry_peek_awp",
                    details="Peeked AWP without flash support",
                    severity=0.95,
                    correction="Never dry peek an AWP. Use flash or shoulder peek first"
                ))
                
            # 3. Dry Peek (Standard)
            elif death.peeked_dry and not death.was_traded and death.round_time != "late":
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    round_time_seconds=round_time,
                    map_area=map_area,
                    player_name=player_name,
                    mistake_type="dry_peek",
                    details="Challenged angle without flash support",
                    severity=0.70,
                    correction="Wait for teammate flash or jiggle peek first"
                ))

            # 4. Bad Spacing (Clumping)
            if death.teammates_nearby >= 2 and death.nearest_teammate_distance < 200:
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    round_time_seconds=round_time,
                    map_area=map_area,
                    player_name=player_name,
                    mistake_type="bad_spacing",
                    details=f"Died stacked with {death.teammates_nearby} teammates nearby",
                    severity=0.65,
                    correction="Spread out to avoid multi-kills"
                ))
            
            # 5. Late Round Solo
            if death.round_time == "late" and death.nearest_teammate_distance > 800 and not death.was_traded:
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    round_time_seconds=round_time,
                    map_area=map_area,
                    player_name=player_name,
                    mistake_type="solo_late_round",
                    details=f"Died alone in late round ({int(death.nearest_teammate_distance)}u from team)",
                    severity=0.75,
                    correction="Group up in late rounds instead of solo plays"
                ))

        return mistakes

    def _analyze_utility(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        player_name = features.player_name or "Unknown"
        
        if features.detected_role == "Support" and features.flashes_thrown < 3 and features.rounds_played > 10:
            mistakes.append(ClassifiedMistake(
                tick=0,
                round_num=0,
                round_time_seconds=0.0,
                map_area="Match-wide",
                player_name=player_name,
                mistake_type="low_utility_usage",
                details=f"Only {features.flashes_thrown} flashes thrown as Support",
                severity=0.50,
                correction="Buy and use more flashes to support teammates"
            ))
        return mistakes
