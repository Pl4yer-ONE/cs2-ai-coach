"""
Drill Registry
Maps specific mistakes to actionable training drills.
Includes advice randomization to avoid repetitive feedback.
"""

from typing import List
import random

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

# Advice pool for mistake corrections - randomized to avoid repetition
ADVICE_POOL = {
    "dry_peek": [
        "Use a support flash before peeking that angle.",
        "Jiggle peek first to bait out the shot, then swing.",
        "Smoke the angle and play off the smoke edge.",
        "Wait for a teammate to trade you before committing.",
        "Shoulder peek to force the shot, then re-peek with info."
    ],
    "untradeable_death": [
        "Stay within 500 units of at least one teammate.",
        "Check your minimap before pushing - is anyone close?",
        "Play off your teammate's aggression, don't go solo.",
        "If you take space, call it so teammates can rotate.",
        "Never be in a position where you die without info for the team."
    ],
    "bad_spacing_clump": [
        "Spread out - one nade shouldn't kill multiple.",
        "Keep 300+ units between you and nearest teammate.",
        "Stagger your entries - don't peek at the same time.",
        "If teammate is close, one of you should hold the angle.",
        "Watch the minimap - if dots are stacking, call it out."
    ],
    "role_failure_support": [
        "As support, your job is utility first, frags second.",
        "Learn at least 2 flashes for every common take.",
        "Pop flash for your entry, don't wait for the call.",
        "If you're not throwing util, you're playing wrong.",
        "Watch pro demos - count how many nades support throws."
    ],
    "movement_wide_swing": [
        "Jiggle peek instead of wide swinging unknown angles.",
        "Counter-strafe before shooting - full commitment = death.",
        "Use movement to bait shots, not to challenge directly.",
        "Wide swing only when you have info or util advantage.",
        "Practice A-D spam in aim trainers to build muscle memory."
    ]
}

def get_drills_for_mistake(mistake_type: str) -> List[str]:
    """Get drills for a specific mistake."""
    return DRILL_DB.get(mistake_type, ["General: Review demo to understand context."])

def get_random_advice(mistake_type: str) -> str:
    """Get a randomized advice string for a mistake type."""
    pool = ADVICE_POOL.get(mistake_type, [])
    if pool:
        return random.choice(pool)
    return "Review your demo to understand what went wrong here."
