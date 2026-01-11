"""
Death Classifier
Classifies death causes beyond just "positioning".

Categories:
- spacing_issue: Teammate too far to trade
- timing_issue: Trade took too long or no trade
- utility_missing: No flash support before death
- solo_push: Only player in area
- crossfire: Multiple enemy angles
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DeathCause(Enum):
    """Primary causes of death."""
    # Original causes
    SPACING_ISSUE = "spacing_issue"
    TIMING_ISSUE = "timing_issue"
    UTILITY_MISSING = "utility_missing"
    SOLO_PUSH = "solo_push"
    CROSSFIRE = "crossfire"
    ENTRY_TRADE = "entry_trade"  # Expected death, traded
    UNKNOWN = "unknown"
    
    # NEW causes for diverse feedback
    DRY_PEEK = "dry_peek"              # Peeked without flash support
    REPEEK_DEATH = "repeek_death"      # Died peeking same angle twice
    NO_TRADE_WINDOW = "no_trade_window"  # Untradeable position
    DOUBLE_EXPOSED = "double_exposed"    # Exposed to 2+ enemy angles


@dataclass
class DeathClassification:
    """Detailed classification of a death event."""
    
    # Primary classification
    primary_cause: DeathCause
    
    # Context data
    teammate_distance: float  # Nearest teammate distance (units)
    time_to_trade_ms: int  # Time until traded (0 if not traded)
    was_traded: bool
    
    # Flash support
    had_flash_support: bool  # Flash within 3s before death
    flash_delay_ms: int  # Time since last friendly flash
    
    # Team context
    was_solo: bool  # Only player in area
    teammates_in_area: int
    
    # Enemy context
    enemy_count: int  # Known enemies involved
    was_crossfire: bool  # Multiple enemy angles
    
    # Role context
    was_entry: bool  # First death of round
    
    # Feedback hint
    tactical_advice: str = ""


class DeathClassifier:
    """
    Classifies deaths into specific tactical categories.
    """
    
    # Thresholds
    SPACING_THRESHOLD = 600  # units - too far to trade
    TRADE_TIME_THRESHOLD = 4000  # ms - 4 seconds max for "traded"
    FLASH_SUPPORT_WINDOW = 3000  # ms - 3 seconds before death
    SOLO_PUSH_THRESHOLD = 800  # units - no teammate within this range
    
    def classify(
        self,
        death_tick: int,
        was_traded: bool,
        trade_time_ms: int,
        is_entry: bool,
        teammates_nearby: int,
        teammate_distance: float,
        had_flash_before: bool = False,
        flash_delay_ms: int = 0,
        enemy_count: int = 1
    ) -> DeathClassification:
        """
        Classify a death into a tactical category.
        
        Args:
            death_tick: Tick of death
            was_traded: Whether death was traded
            trade_time_ms: Time until trade in ms
            is_entry: Whether this was first death of round
            teammates_nearby: Count of teammates in area
            teammate_distance: Distance to nearest teammate
            had_flash_before: Flash from teammate within 3s
            flash_delay_ms: Time since last flash
            enemy_count: Number of enemies involved
            
        Returns:
            DeathClassification with cause and context
        """
        was_solo = teammate_distance > self.SOLO_PUSH_THRESHOLD
        was_crossfire = enemy_count >= 2
        
        # Determine primary cause
        if is_entry and was_traded:
            cause = DeathCause.ENTRY_TRADE
            advice = "Entry death traded successfully - good spacing from team."
        elif was_crossfire:
            cause = DeathCause.CROSSFIRE
            advice = "Crossfire death - avoid exposing to multiple angles simultaneously."
        elif was_solo:
            cause = DeathCause.SOLO_PUSH
            advice = "Solo push - wait for teammate or communicate entry timing."
        elif not was_traded and teammate_distance > self.SPACING_THRESHOLD:
            cause = DeathCause.SPACING_ISSUE
            advice = f"Teammate {teammate_distance:.0f} units away - stay closer for trade potential."
        elif not was_traded and trade_time_ms == 0:
            cause = DeathCause.TIMING_ISSUE
            advice = "No trade attempt - sync pushes with teammate."
        elif was_traded and trade_time_ms > self.TRADE_TIME_THRESHOLD:
            cause = DeathCause.TIMING_ISSUE
            advice = f"Trade took {trade_time_ms/1000:.1f}s - closer positioning for faster trades."
        elif not had_flash_before and not is_entry:
            cause = DeathCause.UTILITY_MISSING
            advice = "No flash support - request flash or wait for utility."
        else:
            cause = DeathCause.UNKNOWN
            advice = "Standard death - review replay for improvement areas."
        
        return DeathClassification(
            primary_cause=cause,
            teammate_distance=teammate_distance,
            time_to_trade_ms=trade_time_ms,
            was_traded=was_traded,
            had_flash_support=had_flash_before,
            flash_delay_ms=flash_delay_ms,
            was_solo=was_solo,
            teammates_in_area=teammates_nearby,
            enemy_count=enemy_count,
            was_crossfire=was_crossfire,
            was_entry=is_entry,
            tactical_advice=advice
        )
    
    def aggregate_causes(
        self, 
        classifications: List[DeathClassification]
    ) -> Dict[str, int]:
        """
        Aggregate death causes for a player.
        
        Returns count by cause type.
        """
        counts = {}
        for c in classifications:
            key = c.primary_cause.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def get_primary_issue(
        self,
        classifications: List[DeathClassification]
    ) -> Optional[Tuple[DeathCause, int]]:
        """
        Get the most common death cause.
        
        Returns (cause, count) or None if no classifications.
        """
        if not classifications:
            return None
        
        counts = self.aggregate_causes(classifications)
        
        # Remove entry trades and unknown from consideration
        counts.pop("entry_trade", None)
        counts.pop("unknown", None)
        
        if not counts:
            return None
        
        top_cause = max(counts.items(), key=lambda x: x[1])
        return (DeathCause(top_cause[0]), top_cause[1])
