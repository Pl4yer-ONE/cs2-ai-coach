"""
Tactical Feedback Generator
No generic advice. Every feedback references: area, count, pattern.

Examples:
- BAD: "Improve positioning"
- GOOD: "5 dry-peeks in A_long without flash support and died untraded"
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from src.classifier.death_classifier import DeathCause, DeathClassification


@dataclass
class TacticalFeedback:
    """A specific, actionable feedback item."""
    category: str  # positioning, utility, timing, etc.
    cause: str  # Specific cause (solo_push, spacing_issue, etc.)
    area: str  # Map callout
    count: int  # Number of incidents
    phase: str  # early, mid, late
    message: str  # Full tactical advice
    priority: int  # Higher = more important
    evidence: Dict  # Supporting data


class TacticalFeedbackGenerator:
    """
    Generates specific, data-driven tactical feedback.
    
    No generic advice allowed. Every feedback must include:
    - Exact map area (callout)
    - Number of incidents
    - Specific pattern/mistake
    - Actionable fix
    """
    
    # Feedback templates by cause
    TEMPLATES = {
        DeathCause.SOLO_PUSH: (
            "{count} solo pushes into {area} during {phase}-round. "
            "Wait for teammate or request flash support."
        ),
        DeathCause.SPACING_ISSUE: (
            "{count} deaths in {area} with no teammate close enough to trade. "
            "Stay within 400 units of trade partner."
        ),
        DeathCause.TIMING_ISSUE: (
            "{count} deaths in {area} where trade took too long or never happened. "
            "Sync push timing with teammate."
        ),
        DeathCause.UTILITY_MISSING: (
            "{count} dry-peeks in {area} without flash support. "
            "Request pop-flash or use own utility."
        ),
        DeathCause.CROSSFIRE: (
            "{count} crossfire deaths in {area}. "
            "Avoid exposing multiple angles simultaneously."
        ),
        # NEW causes
        DeathCause.DRY_PEEK: (
            "{count} dry-peeks in {area} during {phase}-round. "
            "Use utility before peeking or request teammate flash."
        ),
        DeathCause.NO_TRADE_WINDOW: (
            "{count} untradeable deaths in {area}. "
            "Stay within 500 units of trade partner before engaging."
        ),
        DeathCause.DOUBLE_EXPOSED: (
            "{count} deaths in {area} while exposed to 2+ angles. "
            "Clear one angle before exposing to another."
        ),
    }
    
    # Priority by cause
    PRIORITIES = {
        DeathCause.SOLO_PUSH: 9,
        DeathCause.SPACING_ISSUE: 8,
        DeathCause.TIMING_ISSUE: 7,
        DeathCause.UTILITY_MISSING: 6,
        DeathCause.CROSSFIRE: 5,
        DeathCause.DRY_PEEK: 7,
        DeathCause.NO_TRADE_WINDOW: 8,
        DeathCause.DOUBLE_EXPOSED: 6,
        DeathCause.ENTRY_TRADE: 2,
        DeathCause.UNKNOWN: 1,
    }
    
    def generate_feedback(
        self,
        classifications: List[DeathClassification],
        death_areas: Dict[int, str],  # death_index -> callout
        death_phases: Dict[int, str],  # death_index -> phase
    ) -> List[TacticalFeedback]:
        """
        Generate tactical feedback from classified deaths.
        
        Args:
            classifications: List of death classifications
            death_areas: Mapping of death index to map callout
            death_phases: Mapping of death index to round phase
            
        Returns:
            List of TacticalFeedback, sorted by priority
        """
        # Group deaths by (cause, area, phase)
        groups = defaultdict(list)
        
        for i, classification in enumerate(classifications):
            # Skip entry trades and unknown
            if classification.primary_cause in [DeathCause.ENTRY_TRADE, DeathCause.UNKNOWN]:
                continue
            
            area = death_areas.get(i, "unknown")
            phase = death_phases.get(i, "unknown")
            
            key = (classification.primary_cause, area, phase)
            groups[key].append(classification)
        
        # Generate feedback for significant patterns
        feedback_list = []
        
        for (cause, area, phase), deaths in groups.items():
            count = len(deaths)
            
            # Skip if only 1 incident (not a pattern)
            if count < 2:
                continue
            
            # Generate message from template
            template = self.TEMPLATES.get(cause, "{count} issues in {area} during {phase}-round.")
            message = template.format(count=count, area=area, phase=phase)
            
            # Calculate average teammate distance for evidence
            avg_distance = sum(d.teammate_distance for d in deaths) / count if deaths else 0
            
            feedback = TacticalFeedback(
                category="positioning",
                cause=cause.value,
                area=area,
                count=count,
                phase=phase,
                message=message,
                priority=self.PRIORITIES.get(cause, 1) * count,
                evidence={
                    "avg_teammate_distance": round(avg_distance, 1),
                    "traded_count": sum(1 for d in deaths if d.was_traded),
                    "untraded_count": sum(1 for d in deaths if not d.was_traded),
                }
            )
            feedback_list.append(feedback)
        
        # Sort by priority (highest first)
        feedback_list.sort(key=lambda f: f.priority, reverse=True)
        
        return feedback_list
    
    def generate_from_contexts(
        self,
        death_contexts: List,  # DeathContext from extractor
        classifications: List[DeathClassification],
    ) -> List[TacticalFeedback]:
        """
        Generate feedback directly from death contexts.
        
        Convenience method that extracts areas and phases from contexts.
        """
        death_areas = {}
        death_phases = {}
        
        for i, ctx in enumerate(death_contexts):
            death_areas[i] = getattr(ctx, 'map_area', 'unknown')
            death_phases[i] = getattr(ctx, 'round_time', 'unknown')
        
        return self.generate_feedback(classifications, death_areas, death_phases)
    
    def format_summary(self, feedback_list: List[TacticalFeedback]) -> str:
        """
        Format feedback into a readable summary.
        """
        if not feedback_list:
            return "No significant patterns detected."
        
        lines = []
        for fb in feedback_list[:3]:  # Top 3
            lines.append(f"• {fb.message}")
        
        return "\n".join(lines)


class AimFeedbackGenerator:
    """
    Generates aim-specific feedback.
    """
    
    def generate_feedback(
        self,
        headshot_pct: float,
        total_kills: int,
        kill_areas: Dict[str, int],  # area -> kill count
        weapon_breakdown: Dict[str, Dict],  # weapon -> {kills, headshots}
    ) -> Optional[TacticalFeedback]:
        """
        Generate aim feedback if issues detected.
        """
        if total_kills < 5:
            return None
        
        if headshot_pct >= 0.35:
            return None  # Aim is fine
        
        # Find worst weapon
        worst_weapon = None
        worst_hs_pct = 1.0
        
        for weapon, stats in weapon_breakdown.items():
            if stats.get('kills', 0) >= 3:
                hs_pct = stats.get('headshots', 0) / stats['kills']
                if hs_pct < worst_hs_pct:
                    worst_hs_pct = hs_pct
                    worst_weapon = weapon
        
        # Find area with most kills
        if kill_areas:
            primary_area = max(kill_areas.items(), key=lambda x: x[1])[0]
        else:
            primary_area = "unknown"
        
        if headshot_pct < 0.20:
            severity = "Critical"
            message = (
                f"Headshot rate {headshot_pct:.0%} is critically low. "
                f"Focus on crosshair placement at head level in {primary_area}. "
            )
            if worst_weapon:
                message += f"Worst weapon: {worst_weapon} ({worst_hs_pct:.0%} HS)."
        else:
            severity = "Moderate"
            message = (
                f"Headshot rate {headshot_pct:.0%} below average. "
                f"Practice aim discipline in {primary_area} engagements."
            )
        
        return TacticalFeedback(
            category="aim",
            cause="low_headshot_rate",
            area=primary_area,
            count=total_kills,
            phase="overall",
            message=message,
            priority=8 if headshot_pct < 0.20 else 5,
            evidence={
                "headshot_percentage": round(headshot_pct * 100, 1),
                "total_kills": total_kills,
                "worst_weapon": worst_weapon,
                "worst_weapon_hs_pct": round(worst_hs_pct * 100, 1) if worst_weapon else None,
            }
        )
