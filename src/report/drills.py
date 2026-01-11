"""
Drill Registry
Maps specific mistakes to actionable training drills.
"""

from typing import List, Dict

DRILL_DB = {
    "untradeable_death": [
        "Refrag.gg: Crossfire (Co-op mode) - Practice holding crossfires with a partner.",
        "Server: Execute Retake servers - Focus on trading your teammate on site entry.",
        "Mental Drill: 'Buddy System' - In PUGs, consciously attach yourself to one teammate and never be >3s away."
    ],
    "dry_peek": [
        "Yprac: Prefire Maps - Practice clearing angles with perfect crosshair placement.",
        "Refrag.gg: NADR (Utility) - Learn pop-flashes for every common angle.",
        "Mechanic: Counter-strafing - Practice stopping completely before shooting."
    ],
    "bad_spacing_clump": [
        "Demo Review: Watch your own demos and pause every time you die. Check radar for spacing.",
        "Team Drill: 'The String' - Move through site executing utility while maintaining constant distance."
    ],
    "role_failure_support": [
        "Yprac: Grenade Practice - Learn 3 lineups for every site execute.",
        "Refrag.gg: Utility Hub - Practice effective flash timing."
    ],
    "movement_wide_swing": [
        "CSGOHub: Shuffle/Peek drill - Practice jiggle peeking without committing.",
        "Mechanic: 'A-D' spam - Practice shoulder peeking to bait shots."
    ]
}

def get_drills_for_mistake(mistake_type: str) -> List[str]:
    """Get drills for a specific mistake."""
    return DRILL_DB.get(mistake_type, ["General: Review demo to understand context."])
