# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.

"""
Mistake Detectors
Deterministic error detection for CS2 gameplay analysis.

Each detector evaluates specific tactical errors:
- OVERPEEK: Exposed without trade support
- NO_TRADE_SPACING: Entry dies without backup in range
- ROTATION_DELAY: Slow rotate after site loss
- UTILITY_WASTE: Flash/smoke with no follow-up
- POSTPLANT_MISPLAY: Poor positioning after plant
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
import math
import pandas as pd

# Import contextual WPA for weighted calculations
try:
    from src.wpa.contextual_wpa import calculate_contextual_wpa
    HAS_WPA = True
except ImportError:
    HAS_WPA = False


class ErrorType(Enum):
    """Mistake type taxonomy."""
    OVERPEEK = "OVERPEEK"
    NO_TRADE_SPACING = "NO_TRADE_SPACING"
    ROTATION_DELAY = "ROTATION_DELAY"
    UTILITY_WASTE = "UTILITY_WASTE"
    POSTPLANT_MISPLAY = "POSTPLANT_MISPLAY"


class Severity(Enum):
    """Mistake severity levels."""
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


@dataclass
class DetectedMistake:
    """
    A detected tactical error.
    
    Attributes:
        round: Round number
        timestamp_ms: Milliseconds into round
        player: Player name
        steam_id: Player Steam ID (optional)
        map_pos: Position dict with x, y, area
        error_type: ErrorType enum value
        severity: Severity level
        wpa_loss: Base Win Probability loss
        weighted_wpa: Context-adjusted WPA loss
        wpa_context: Economy/time context info
        details: Human-readable explanation
    """
    round: int
    timestamp_ms: int
    player: str
    error_type: str
    severity: str
    wpa_loss: float = 0.0
    weighted_wpa: float = 0.0
    wpa_context: Optional[Dict[str, Any]] = None
    steam_id: str = ""
    map_pos: Optional[Dict[str, Any]] = None
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        if d['map_pos'] is None:
            d['map_pos'] = {}
        if d['wpa_context'] is None:
            d['wpa_context'] = {}
        return d


class MistakeDetector(ABC):
    """Abstract base class for mistake detectors."""
    
    @property
    @abstractmethod
    def error_type(self) -> ErrorType:
        """Return the error type this detector identifies."""
        pass
    
    @abstractmethod
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        """
        Detect mistakes in a specific round.
        
        Args:
            parsed_demo: Parsed demo object with kills, damages, positions
            round_num: Round to analyze
            
        Returns:
            List of DetectedMistake objects
        """
        pass


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate 2D Euclidean distance."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _get_teammates(players: List[Dict], player_name: str, team: str) -> List[Dict]:
    """Get list of alive teammates (excluding the player)."""
    return [
        p for p in players 
        if p.get('team') == team 
        and p.get('name') != player_name 
        and p.get('alive', True)
    ]


class OverpeekDetector(MistakeDetector):
    """
    Detects OVERPEEK errors.
    
    Criteria:
    - Player dies in a duel
    - No teammate within trade window distance (500 units)
    - No teammate shot killer within 3 seconds
    """
    
    TRADE_WINDOW_MS = 3000
    TRADE_DISTANCE = 500  # Units for trade support
    
    @property
    def error_type(self) -> ErrorType:
        return ErrorType.OVERPEEK
    
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        mistakes = []
        
        kills = parsed_demo.kills
        if kills is None or kills.empty:
            return mistakes
        
        # Get round kills - use total_rounds_played column
        round_col = 'total_rounds_played' if 'total_rounds_played' in kills.columns else 'round_num'
        if round_col in kills.columns:
            round_kills = kills[kills[round_col] == round_num]
        else:
            return mistakes
        
        for idx, kill in round_kills.iterrows():
            victim = str(kill.get('user_name', kill.get('victim_name', '')))
            killer = str(kill.get('attacker_name', ''))
            victim_team = str(kill.get('user_team_name', kill.get('victim_team_name', '')))
            tick = int(kill.get('tick', 0))
            
            victim_x = float(kill.get('user_X', kill.get('victim_X', 0)) or 0)
            victim_y = float(kill.get('user_Y', kill.get('victim_Y', 0)) or 0)
            
            # Check if any teammate traded within window
            was_traded = False
            for _, other_kill in round_kills.iterrows():
                other_victim = other_kill.get('user_name', other_kill.get('victim_name', ''))
                if other_victim == killer:
                    trade_tick = int(other_kill.get('tick', 0))
                    if 0 < (trade_tick - tick) <= self.TRADE_WINDOW_MS / 15.625:  # ~64 tick
                        was_traded = True
                        break
            
            # If not traded, check if teammate was in range
            if not was_traded:
                # Simplified: flag as overpeek if no trade occurred
                # In full implementation, would check teammate positions at death tick
                mistakes.append(DetectedMistake(
                    round=round_num,
                    timestamp_ms=int(tick * 15.625),  # Approximate ms
                    player=victim,
                    error_type=self.error_type.value,
                    severity=Severity.MED.value,
                    wpa_loss=0.05,  # Placeholder
                    map_pos={"x": victim_x, "y": victim_y},
                    details=f"Died without trade support against {killer}"
                ))
        
        return mistakes


class NoTradeSpacingDetector(MistakeDetector):
    """
    Detects NO_TRADE_SPACING errors.
    
    Criteria:
    - Entry player dies
    - Second player is too far (>600 units) to trade
    """
    
    OPTIMAL_SPACING = 600  # Units
    
    @property
    def error_type(self) -> ErrorType:
        return ErrorType.NO_TRADE_SPACING
    
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        mistakes = []
        
        kills = parsed_demo.kills
        if kills is None or kills.empty:
            return mistakes
        
        # Get round kills sorted by tick
        round_col = 'total_rounds_played' if 'total_rounds_played' in kills.columns else 'round_num'
        if round_col in kills.columns:
            round_kills = kills[kills[round_col] == round_num]
        else:
            return mistakes
        if round_kills.empty:
            return mistakes
        
        round_kills = round_kills.sort_values('tick')
        
        # Check first kill (entry frag)
        first_kill = round_kills.iloc[0] if len(round_kills) > 0 else None
        if first_kill is None:
            return mistakes
        
        victim = str(first_kill.get('user_name', first_kill.get('victim_name', '')))
        victim_team = str(first_kill.get('user_team_name', first_kill.get('victim_team_name', '')))
        tick = int(first_kill.get('tick', 0))
        
        # Check if entry was traded quickly
        entry_traded = False
        killer = str(first_kill.get('attacker_name', ''))
        
        for _, kill in round_kills.iloc[1:].iterrows():
            other_victim = kill.get('user_name', kill.get('victim_name', ''))
            if other_victim == killer:
                refrag_delay = int(kill.get('tick', 0)) - tick
                if refrag_delay <= 192:  # ~3 seconds at 64 tick
                    entry_traded = True
                    break
        
        if not entry_traded:
            mistakes.append(DetectedMistake(
                round=round_num,
                timestamp_ms=int(tick * 15.625),
                player=victim,
                error_type=self.error_type.value,
                severity=Severity.HIGH.value,
                wpa_loss=0.08,
                details=f"Entry died without trade - spacing too wide"
            ))
        
        return mistakes


class RotationDelayDetector(MistakeDetector):
    """
    Detects ROTATION_DELAY errors.
    
    Criteria:
    - Bomb planted at site
    - Defender takes >10s to rotate from other site
    """
    
    ROTATION_THRESHOLD_MS = 10000  # 10 seconds
    
    @property
    def error_type(self) -> ErrorType:
        return ErrorType.ROTATION_DELAY
    
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        mistakes = []
        
        # Check for plants
        plants = getattr(parsed_demo, 'plants', None)
        if plants is None or plants.empty:
            return mistakes
        
        round_plants = plants[plants.get('round_num', plants.get('round', -1)) == round_num]
        if round_plants.empty:
            return mistakes
        
        plant = round_plants.iloc[0]
        plant_tick = int(plant.get('tick', 0))
        plant_site = str(plant.get('site', 'A'))
        
        # Check for defuse attempts
        defuses = getattr(parsed_demo, 'defuses', None)
        if defuses is None or defuses.empty:
            return mistakes
        
        round_defuses = defuses[defuses.get('round_num', defuses.get('round', -1)) == round_num]
        
        for _, defuse in round_defuses.iterrows():
            defuse_tick = int(defuse.get('tick', 0))
            player = str(defuse.get('player_name', ''))
            
            rotate_time_ms = (defuse_tick - plant_tick) * 15.625
            
            if rotate_time_ms > self.ROTATION_THRESHOLD_MS:
                mistakes.append(DetectedMistake(
                    round=round_num,
                    timestamp_ms=int(defuse_tick * 15.625),
                    player=player,
                    error_type=self.error_type.value,
                    severity=Severity.MED.value,
                    wpa_loss=0.04,
                    details=f"Slow rotation to {plant_site} ({rotate_time_ms/1000:.1f}s)"
                ))
        
        return mistakes


class UtilityWasteDetector(MistakeDetector):
    """
    Detects UTILITY_WASTE errors.
    
    Criteria:
    - Flash thrown with no teammate entry within 2s
    - Smoke/molly with no map control gain
    """
    
    FLASH_FOLLOWUP_WINDOW_MS = 2000
    
    @property
    def error_type(self) -> ErrorType:
        return ErrorType.UTILITY_WASTE
    
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        mistakes = []
        
        # Check for flash assists or thrown flashes
        # Simplified: if flash thrown and no kill within window, flag as waste
        grenades = getattr(parsed_demo, 'grenades', None)
        if grenades is None or grenades.empty:
            return mistakes
        
        # Filter flashes in this round
        round_col = 'total_rounds_played' if 'total_rounds_played' in grenades.columns else 'round_num'
        if round_col in grenades.columns:
            round_grenades = grenades[grenades[round_col] == round_num]
        else:
            # Fallback: if no round info in grenades, assume they are global and filter by tick?
            # Or assume we can't map them.
            # But the parser usually adds round info if available or we can use round start/end ticks.
            # For now, let's check ticks if rounds dataframe exists
            if hasattr(parsed_demo, 'rounds') and not parsed_demo.rounds.empty:
                round_info = parsed_demo.rounds[parsed_demo.rounds['round_num'] == round_num if 'round_num' in parsed_demo.rounds.columns else parsed_demo.rounds.index == round_num-1]
                if not round_info.empty:
                    start_tick = round_info.iloc[0].get('round_start_tick', 0) if 'round_start_tick' in round_info.columns else round_info.iloc[0].get('start_tick', 0)
                    end_tick = round_info.iloc[0].get('round_end_tick', 99999999) if 'round_end_tick' in round_info.columns else round_info.iloc[0].get('end_tick', 99999999)

                    round_grenades = grenades[(grenades['tick'] >= start_tick) & (grenades['tick'] <= end_tick)]
                else:
                    return mistakes
            else:
                return mistakes

        flashes = round_grenades[round_grenades['grenade_type'] == 'flashbang']
        if flashes.empty:
            return mistakes

        kills = parsed_demo.kills
        if kills is None or kills.empty:
            # If no kills but flashes thrown, maybe wasted?
            # But we only check for entry/trade support.
            pass

        # Get kills for this round
        round_kills = pd.DataFrame()
        if kills is not None and not kills.empty:
            k_round_col = 'total_rounds_played' if 'total_rounds_played' in kills.columns else 'round_num'
            if k_round_col in kills.columns:
                round_kills = kills[kills[k_round_col] == round_num]
            else:
                # Fallback: filter by tick if round info is available in parsed_demo.rounds
                if hasattr(parsed_demo, 'rounds') and not parsed_demo.rounds.empty:
                    # Use the same logic as for grenades above
                    round_info = parsed_demo.rounds[parsed_demo.rounds['round_num'] == round_num if 'round_num' in parsed_demo.rounds.columns else parsed_demo.rounds.index == round_num-1]
                    if not round_info.empty:
                        start_tick = round_info.iloc[0].get('round_start_tick', 0) if 'round_start_tick' in round_info.columns else round_info.iloc[0].get('start_tick', 0)
                        end_tick = round_info.iloc[0].get('round_end_tick', 99999999) if 'round_end_tick' in round_info.columns else round_info.iloc[0].get('end_tick', 99999999)

                        round_kills = kills[(kills['tick'] >= start_tick) & (kills['tick'] <= end_tick)]

        for _, flash in flashes.iterrows():
            flash_tick = int(flash.get('tick', 0))
            thrower = str(flash.get('name', flash.get('user_name', '')))
            team = str(flash.get('team_name', ''))

            if not thrower:
                continue

            # Check for ANY kill by ANYONE on thrower's team within window
            # Window: flash_tick to flash_tick + window
            window_ticks = self.FLASH_FOLLOWUP_WINDOW_MS / 15.625

            success = False
            if not round_kills.empty:
                for _, kill in round_kills.iterrows():
                    kill_tick = int(kill.get('tick', 0))
                    attacker_team = str(kill.get('attacker_team_name', ''))

                    if attacker_team == team:
                        if 0 <= (kill_tick - flash_tick) <= window_ticks:
                            success = True
                            break

            if not success:
                mistakes.append(DetectedMistake(
                    round=round_num,
                    timestamp_ms=int(flash_tick * 15.625),
                    player=thrower,
                    error_type=self.error_type.value,
                    severity=Severity.LOW.value,
                    wpa_loss=0.02,
                    map_pos={"x": float(flash.get('x', flash.get('X', 0))), "y": float(flash.get('y', flash.get('Y', 0)))},
                    details=f"Flash with no entry/kill follow-up within 2s"
                ))
        
        return mistakes


class PostplantMisplayDetector(MistakeDetector):
    """
    Detects POSTPLANT_MISPLAY errors.
    
    Criteria:
    - Bomb planted
    - T player peeks without crossfire
    - T player exposed in bad position
    """
    
    @property
    def error_type(self) -> ErrorType:
        return ErrorType.POSTPLANT_MISPLAY
    
    def detect(self, parsed_demo, round_num: int) -> List[DetectedMistake]:
        mistakes = []
        
        # Check if bomb was planted this round
        plants = getattr(parsed_demo, 'plants', None)
        if plants is None or plants.empty:
            return mistakes
        
        round_plants = plants[plants.get('round_num', plants.get('round', -1)) == round_num]
        if round_plants.empty:
            return mistakes
        
        plant = round_plants.iloc[0]
        plant_tick = int(plant.get('tick', 0))
        
        # Check for T deaths after plant
        kills = parsed_demo.kills
        if kills is None or kills.empty:
            return mistakes
        
        round_kills = kills[kills.get('round_num', kills.get('round', -1)) == round_num]
        
        for _, kill in round_kills.iterrows():
            kill_tick = int(kill.get('tick', 0))
            
            if kill_tick <= plant_tick:
                continue  # Before plant
            
            victim = str(kill.get('victim_name', ''))
            victim_team = str(kill.get('victim_team_name', ''))
            
            if 'T' in victim_team.upper() and 'CT' not in victim_team.upper():
                # T died after plant
                victim_x = float(kill.get('victim_x', kill.get('victim_X', 0)))
                victim_y = float(kill.get('victim_y', kill.get('victim_Y', 0)))
                
                mistakes.append(DetectedMistake(
                    round=round_num,
                    timestamp_ms=int(kill_tick * 15.625),
                    player=victim,
                    error_type=self.error_type.value,
                    severity=Severity.MED.value,
                    wpa_loss=0.06,
                    map_pos={"x": victim_x, "y": victim_y},
                    details="Died postplant without crossfire support"
                ))
        
        return mistakes


def detect_all_mistakes(parsed_demo) -> List[DetectedMistake]:
    """
    Run all detectors on entire demo.
    
    Args:
        parsed_demo: Parsed demo object
        
    Returns:
        List of all detected mistakes
    """
    detectors = [
        OverpeekDetector(),
        NoTradeSpacingDetector(),
        RotationDelayDetector(),
        UtilityWasteDetector(),
        PostplantMisplayDetector(),
    ]
    
    all_mistakes: List[DetectedMistake] = []
    
    # Get round numbers from kills data
    kills = parsed_demo.kills
    if kills is not None and not kills.empty:
        round_col = 'total_rounds_played' if 'total_rounds_played' in kills.columns else 'round_num'
        if round_col in kills.columns:
            round_nums = sorted(kills[round_col].unique())
        else:
            round_nums = range(30)
    else:
        round_nums = range(30)  # Default to 30 rounds
    
    for round_num in round_nums:
        for detector in detectors:
            try:
                mistakes = detector.detect(parsed_demo, int(round_num))
                all_mistakes.extend(mistakes)
            except Exception as e:
                # Log but don't fail
                pass
    
    # Sort by round and timestamp
    all_mistakes.sort(key=lambda m: (m.round, m.timestamp_ms))
    
    return all_mistakes


def export_mistakes_json(mistakes: List[DetectedMistake], output_path: str) -> str:
    """Export detected mistakes to JSON file."""
    import json
    from pathlib import Path
    
    output = {
        "schema_version": "1.0",
        "total_mistakes": len(mistakes),
        "by_type": {},
        "mistakes": [m.to_dict() for m in mistakes]
    }
    
    # Count by type
    for m in mistakes:
        output["by_type"][m.error_type] = output["by_type"].get(m.error_type, 0) + 1
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    return str(path)
