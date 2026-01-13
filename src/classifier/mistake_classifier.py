"""
Mistake Classifier
Identifies specific tactical errors with context-aware coaching advice.
"""

from typing import List
from dataclasses import dataclass
import random

from src.features.extractor import PlayerFeatures, DeathContext


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
    severity: float  # 0.0-1.0
    severity_label: str  # HIGH, MED, LOW
    correction: str


def _get_severity_label(severity: float) -> str:
    """Convert severity float to label."""
    if severity >= 0.8:
        return "HIGH"
    elif severity >= 0.5:
        return "MED"
    return "LOW"


# Varied advice templates
DRY_PEEK_ADVICE = {
    "default": [
        "Use a teammate flash before taking this fight",
        "Jiggle peek to bait shots before committing",
        "Wait for info before challenging this angle",
        "Consider using a smoke to cross instead",
        "Coordinate with teammate utility before peeking",
    ],
    "A Long": [
        "Ask for a long flash from CT spawn",
        "Use your own flash off the wall at long doors",
        "Wait for AWP info before wide peeking",
    ],
    "Mid": [
        "Smoke mid before crossing",
        "Use teammate flash from catwalk",
        "Shoulder peek to bait the AWP shot first",
    ],
    "B Apartments": [
        "Flash over apartments before pushing",
        "Let teammate entry first with flash support",
        "Pop flash around the corner",
    ],
    "unknown": [
        "Coordinate utility with teammates before engaging",
        "Use your utility to create an advantage",
    ]
}

AWP_PEEK_ADVICE = [
    "Never wide peek an AWP. Shoulder peek to bait the shot first",
    "Use a flash to blind the AWP before peeking",
    "Smoke off the AWP angle and push through",
    "Trade with a teammate instead of dry peeking solo",
    "Ask teammate to flash for you or peek together",
    "Jiggle peek repeatedly to waste the AWP's patience",
]

UNTRADEABLE_ADVICE = {
    "entry": [
        "You're entry fragging — make sure support is ready to trade",
        "Call out your push so teammates can follow up",
        "Wait an extra second for teammate to get position",
    ],
    "solo": [
        "Don't take solo fights this far from team",
        "Fall back to a tradeable position",
        "Group up before taking contact",
        "Your team can't help you from this distance",
    ],
}

SPACING_ADVICE = [
    "Spread out to avoid multi-kills from nades or sprays",
    "One well-placed HE could kill your whole stack",
    "Maintain 2-3 second spacing when pushing",
    "Stacking makes it easy for the enemy to trade you all",
    "Give your teammates room to swing and trade",
]

SOLO_LATE_ADVICE = [
    "In clutch situations, group up with remaining teammates",
    "Don't give the enemy free 1v1s in late round",
    "Wait for teammate rotation before engaging",
    "Late round = stick together, not solo hero plays",
    "Trade potential is crucial in late rounds",
]


def _get_round_time_seconds(death: DeathContext) -> float:
    """Convert round_time phase to approximate seconds."""
    phase_map = {"early": 15.0, "mid": 45.0, "late": 75.0, "unknown": 30.0}
    return phase_map.get(death.round_time, 30.0)


def _get_dry_peek_advice(map_area: str) -> str:
    """Get context-aware dry peek advice."""
    area_key = map_area if map_area in DRY_PEEK_ADVICE else "default"
    return random.choice(DRY_PEEK_ADVICE.get(area_key, DRY_PEEK_ADVICE["default"]))


def _get_untradeable_advice(is_entry: bool) -> str:
    """Get advice for untradeable deaths."""
    key = "entry" if is_entry else "solo"
    return random.choice(UNTRADEABLE_ADVICE[key])


class MistakeClassifier:
    """Classifies mistakes with varied, contextual advice."""
    
    def classify(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        mistakes.extend(self._analyze_deaths(features))
        mistakes.extend(self._analyze_utility(features))
        return mistakes

    def _analyze_deaths(self, features: PlayerFeatures) -> List[ClassifiedMistake]:
        mistakes = []
        player_name = features.player_name or "Unknown"
        role = features.detected_role or "Unknown"
        
        for death in features.death_contexts:
            round_time = _get_round_time_seconds(death)
            map_area = death.map_area or "Unknown"
            
            # 1. Untradeable Death
            if not death.was_traded and death.nearest_teammate_distance > 400:
                is_lurk_exception = (role == "Lurker" and death.round_time == "mid")
                is_entry = death.is_entry_frag
                
                if not is_lurk_exception and not is_entry:
                    dist = int(death.nearest_teammate_distance)
                    mistakes.append(ClassifiedMistake(
                        tick=death.tick,
                        round_num=death.round_num,
                        round_time_seconds=round_time,
                        map_area=map_area,
                        player_name=player_name,
                        mistake_type="untradeable_death",
                        details=f"Died {dist}u from nearest teammate — no trade possible",
                        severity=0.85,
                        severity_label=_get_severity_label(0.85),
                        correction=_get_untradeable_advice(is_entry)
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
                    details=f"Dry peeked into AWP at {map_area}",
                    severity=0.95,
                    severity_label=_get_severity_label(0.95),
                    correction=random.choice(AWP_PEEK_ADVICE)
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
                    details=f"Challenged {map_area} without utility",
                    severity=0.70,
                    severity_label=_get_severity_label(0.70),
                    correction=_get_dry_peek_advice(map_area)
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
                    details=f"Died stacked with {death.teammates_nearby} teammates at {map_area}",
                    severity=0.65,
                    severity_label=_get_severity_label(0.65),
                    correction=random.choice(SPACING_ADVICE)
                ))
            
            # 5. Late Round Solo
            if death.round_time == "late" and death.nearest_teammate_distance > 800 and not death.was_traded:
                dist = int(death.nearest_teammate_distance)
                mistakes.append(ClassifiedMistake(
                    tick=death.tick,
                    round_num=death.round_num,
                    round_time_seconds=round_time,
                    map_area=map_area,
                    player_name=player_name,
                    mistake_type="solo_late_round",
                    details=f"Died {dist}u from team in late round at {map_area}",
                    severity=0.75,
                    severity_label=_get_severity_label(0.75),
                    correction=random.choice(SOLO_LATE_ADVICE)
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
                details=f"Only {features.flashes_thrown} flashes thrown in {features.rounds_played} rounds",
                severity=0.50,
                severity_label=_get_severity_label(0.50),
                correction="Support players should average 1+ flash per round"
            ))
        return mistakes
