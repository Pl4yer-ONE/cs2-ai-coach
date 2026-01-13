"""
Radar Tick Extractor
Extracts per-tick player positions from demo for radar video generation.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.parser.demo_parser import ParsedDemo


@dataclass
class PlayerFrame:
    """Single player state at a tick."""
    steam_id: str
    name: str
    x: float
    y: float
    z: float
    team: str  # "CT" or "T"
    alive: bool
    health: int


@dataclass
class SmokeFrame:
    """Active smoke grenade."""
    x: float
    y: float
    tick_start: int
    duration_ticks: int = 1152  # ~18 seconds at 64 tick


@dataclass
class FlashFrame:
    """Flash grenade detonation."""
    x: float
    y: float
    tick: int
    duration_ticks: int = 128  # ~2 seconds visible


@dataclass
class KillFrame:
    """Kill event for marker."""
    x: float
    y: float
    tick: int
    attacker_team: str
    victim_name: str
    duration_ticks: int = 192  # ~3 seconds visible


@dataclass
class TickFrame:
    """All player states at a single tick."""
    tick: int
    players: List[PlayerFrame]
    bomb_x: Optional[float] = None
    bomb_y: Optional[float] = None
    smokes: List[SmokeFrame] = None
    flashes: List[FlashFrame] = None
    kills: List[KillFrame] = None
    round_num: int = 0
    
    def __post_init__(self):
        if self.smokes is None:
            self.smokes = []
        if self.flashes is None:
            self.flashes = []
        if self.kills is None:
            self.kills = []


def extract_ticks(
    demo: ParsedDemo,
    tick_interval: int = 32,  # Sample every N ticks (64 tick = 2 per second at 32)
    max_ticks: Optional[int] = None
) -> List[TickFrame]:
    """
    Extract player positions for each tick from demo.
    
    Args:
        demo: Parsed demo data
        tick_interval: Sample every N ticks (lower = more frames, bigger file)
        max_ticks: Optional limit on ticks to process
        
    Returns:
        List of TickFrame objects
    """
    positions = demo.player_positions
    
    if positions is None or positions.empty:
        print("  ⚠️ No position data in demo")
        return []
    
    # Get unique ticks
    if 'tick' not in positions.columns:
        print("  ⚠️ No tick column in positions")
        return []
    
    all_ticks = sorted(positions['tick'].unique())
    
    # Sample ticks
    sampled_ticks = all_ticks[::tick_interval]
    
    if max_ticks:
        sampled_ticks = sampled_ticks[:max_ticks]
    
    print(f"  Processing {len(sampled_ticks)} frames from {len(all_ticks)} ticks...")
    
    # Extract smoke detonations for overlay
    smoke_events = []
    flash_events = []
    grenades = demo.grenades
    if grenades is not None and not grenades.empty:
        # Smokes
        if 'grenade_type' in grenades.columns:
            smoke_df = grenades[grenades['grenade_type'] == 'smoke']
            for _, row in smoke_df.iterrows():
                x = float(row.get('X', row.get('x', 0)))
                y = float(row.get('Y', row.get('y', 0)))
                tick = int(row.get('tick', 0))
                if x != 0 and y != 0:
                    smoke_events.append(SmokeFrame(x=x, y=y, tick_start=tick))
            
            # Flashes
            flash_df = grenades[grenades['grenade_type'] == 'flashbang']
            for _, row in flash_df.iterrows():
                x = float(row.get('X', row.get('x', 0)))
                y = float(row.get('Y', row.get('y', 0)))
                tick = int(row.get('tick', 0))
                if x != 0 and y != 0:
                    flash_events.append(FlashFrame(x=x, y=y, tick=tick))
    
    # Extract kills for markers
    kill_events = []
    kills = demo.kills
    if kills is not None and not kills.empty:
        for _, row in kills.iterrows():
            # Get victim position (where the kill happened)
            x = float(row.get('victim_X', row.get('X', 0)))
            y = float(row.get('victim_Y', row.get('Y', 0)))
            tick = int(row.get('tick', 0))
            attacker_team = str(row.get('attacker_team_name', 'T')).upper()
            victim_name = str(row.get('victim_name', ''))[:10]
            if x != 0 and y != 0:
                kill_events.append(KillFrame(
                    x=x, y=y, tick=tick,
                    attacker_team='CT' if 'CT' in attacker_team else 'T',
                    victim_name=victim_name
                ))
    
    frames = []
    
    for tick in sampled_ticks:
        tick_data = positions[positions['tick'] == tick]
        
        players = []
        for _, row in tick_data.iterrows():
            # Get player info
            steam_id = str(row.get('steamid', row.get('player_steamid', '')))
            name = str(row.get('name', row.get('player_name', steam_id[:8])))
            
            # Get position
            x = float(row.get('X', 0))
            y = float(row.get('Y', 0))
            z = float(row.get('Z', 0))
            
            # Get team
            team_raw = str(row.get('team_name', row.get('team', ''))).upper()
            if 'CT' in team_raw or 'COUNTER' in team_raw:
                team = 'CT'
            elif 'T' in team_raw or 'TERROR' in team_raw:
                team = 'T'
            else:
                team = 'T'  # Default
            
            # Get alive status
            alive = bool(row.get('is_alive', row.get('health', 100) > 0))
            health = int(row.get('health', 100 if alive else 0))
            
            # Skip spectators (no position)
            if x == 0 and y == 0:
                continue
                
            players.append(PlayerFrame(
                steam_id=steam_id,
                name=name,
                x=x,
                y=y,
                z=z,
                team=team,
                alive=alive,
                health=health
            ))
        
        if players:
            # Find active smokes at this tick
            active_smokes = [
                s for s in smoke_events
                if s.tick_start <= tick <= s.tick_start + s.duration_ticks
            ]
            
            # Find active flashes at this tick
            active_flashes = [
                f for f in flash_events
                if f.tick <= tick <= f.tick + f.duration_ticks
            ]
            
            # Find recent kills at this tick (show skull briefly)
            active_kills = [
                k for k in kill_events
                if k.tick <= tick <= k.tick + k.duration_ticks
            ]
            
            frames.append(TickFrame(
                tick=tick,
                players=players,
                smokes=active_smokes,
                flashes=active_flashes,
                kills=active_kills,
                round_num=0
            ))
    
    return frames


def get_round_boundaries(demo: ParsedDemo) -> List[Tuple[int, int]]:
    """Get (start_tick, end_tick) for each round."""
    rounds = demo.rounds
    if rounds is None or rounds.empty:
        return []
    
    boundaries = []
    for _, row in rounds.iterrows():
        start = int(row.get('round_start_tick', 0))
        end = int(row.get('round_end_tick', start + 10000))
        boundaries.append((start, end))
    
    return boundaries
