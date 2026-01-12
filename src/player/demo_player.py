"""
CS2 Demo Player - Playback Controller

Controls demo playback with tick-based timeline, round navigation,
and speed controls. Uses existing DemoParser for data extraction.

Tickrate Logic:
    Tickrate is read dynamically from demo header using:
        tickrate = playback_ticks / playback_time
    This handles both 64-tick (matchmaking) and 128-tick (Faceit) demos.
    Falls back to DEFAULT_TICKRATE (64) if header parsing fails.

Performance:
    - O(log n) tick lookup via pre-built sorted index + binary search
    - LRU cache (OrderedDict) for repeated tick lookups
    - Frame skipping at high playback speeds
    - Delta time clamped to prevent huge jumps on focus loss
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
import numpy as np
import pandas as pd

from src.parser.demo_parser import DemoParser, ParsedDemo


@dataclass
class PlayerState:
    """State of a single player at a given tick."""
    steamid: str
    name: str
    x: float
    y: float
    z: float
    health: int
    armor: int
    team: str  # "CT" or "T"
    is_alive: bool
    yaw: float = 0.0  # View angle
    pitch: float = 0.0


@dataclass
class FrameData:
    """All data for a single frame/tick."""
    tick: int
    round_num: int
    players: List[PlayerState]
    events: List[Dict[str, Any]]  # Kills, grenades, bomb events this tick


@dataclass
class RoundInfo:
    """Information about a round."""
    round_num: int
    start_tick: int
    end_tick: int
    winner: Optional[str] = None
    reason: Optional[str] = None


class DemoPlayer:
    """
    Demo playback controller.
    
    Loads a .dem file and provides tick-by-tick frame data
    for rendering with playback controls.
    
    Attributes:
        tickrate: Ticks per second (read from demo header, typically 64 or 128)
        min_tick: First tick in demo
        max_tick: Last tick in demo
        current_tick: Current playback position
        speed: Playback speed multiplier (0.25 to 4.0)
    """
    
    # Default tickrate (will be overridden by demo header)
    DEFAULT_TICKRATE = 64
    TARGET_FPS = 60  # Render target for frame skipping
    MAX_DT = 0.1  # Maximum delta time (100ms) - prevents huge jumps on focus loss
    
    def __init__(self, demo_path: str):
        """
        Initialize player with demo file.
        
        Args:
            demo_path: Path to .dem file
        """
        self.demo_path = Path(demo_path)
        if not self.demo_path.exists():
            raise FileNotFoundError(f"Demo not found: {demo_path}")
        
        # Parse demo
        print(f"Loading demo: {self.demo_path.name}...")
        parser = DemoParser(str(self.demo_path))
        self.data: ParsedDemo = parser.parse()
        print(f"  Map: {self.data.map_name}")
        
        # Use tickrate from demo header (dynamic, not hardcoded)
        self.tickrate = getattr(self.data, 'tickrate', self.DEFAULT_TICKRATE)
        print(f"  Tickrate: {self.tickrate}")
        
        # Extract tick range
        self._setup_ticks()
        self._setup_rounds()
        self._setup_events()
        
        # Playback state
        self.current_tick = self.min_tick
        self.is_playing = False
        self.speed = 1.0  # 1x = realtime
        self._last_frame_time = 0.0
        
        # Build player name lookup
        self._build_player_lookup()
        
        # Performance: LRU cache for tick lookups (actual eviction policy)
        self._tick_cache: OrderedDict[int, List[PlayerState]] = OrderedDict()
        self._cache_max_size = 500
        
        # Frame skip: calculate how many ticks to skip per render
        self._ticks_per_frame = max(1, self.tickrate // self.TARGET_FPS)
        
        # Index available ticks for fast lookup
        self._setup_tick_index()
        
        print(f"  Ticks: {self.min_tick} - {self.max_tick}")
        print(f"  Rounds: {len(self.rounds)}")
        print(f"  Tick skip: {self._ticks_per_frame} (targeting {self.TARGET_FPS} fps)")
        print(f"  Ready for playback!")
    
    def _setup_ticks(self) -> None:
        """Extract tick range from position data."""
        positions = self.data.player_positions
        
        if positions is None or positions.empty:
            # Fallback to kills if no position data
            if self.data.kills is not None and not self.data.kills.empty:
                if 'tick' in self.data.kills.columns:
                    self.min_tick = int(self.data.kills['tick'].min())
                    self.max_tick = int(self.data.kills['tick'].max())
                else:
                    self.min_tick = 0
                    self.max_tick = 10000
            else:
                self.min_tick = 0
                self.max_tick = 10000
            self._has_positions = False
            return
        
        self._has_positions = True
        
        # Get tick column
        tick_col = 'tick' if 'tick' in positions.columns else None
        if tick_col is None:
            for col in positions.columns:
                if 'tick' in col.lower():
                    tick_col = col
                    break
        
        if tick_col:
            self.min_tick = int(positions[tick_col].min())
            self.max_tick = int(positions[tick_col].max())
        else:
            self.min_tick = 0
            self.max_tick = len(positions) - 1
        
        # Sample rate scales with actual tickrate
        self._tick_sample_rate = max(1, self.tickrate // self.TARGET_FPS)
    
    def _setup_rounds(self) -> None:
        """Extract round information."""
        self.rounds: List[RoundInfo] = []
        
        rounds_df = self.data.rounds
        if rounds_df is None or rounds_df.empty:
            # Create single pseudo-round spanning entire demo
            self.rounds.append(RoundInfo(
                round_num=1,
                start_tick=self.min_tick,
                end_tick=self.max_tick
            ))
            return
        
        # Extract round data
        for i, row in rounds_df.iterrows():
            start_tick = row.get('round_start_tick', row.get('tick', self.min_tick))
            end_tick = row.get('round_end_tick', self.max_tick)
            
            self.rounds.append(RoundInfo(
                round_num=i + 1,
                start_tick=int(start_tick) if pd.notna(start_tick) else self.min_tick,
                end_tick=int(end_tick) if pd.notna(end_tick) else self.max_tick,
                winner=row.get('winner'),
                reason=row.get('reason')
            ))
    
    def _setup_tick_index(self) -> None:
        """Build index of available ticks for fast lookup."""
        self._available_ticks: np.ndarray = np.array([])
        
        if not self._has_positions:
            return
        
        positions = self.data.player_positions
        tick_col = None
        for col in ['tick', 'Tick']:
            if col in positions.columns:
                tick_col = col
                break
        
        if tick_col:
            # Get sorted unique ticks
            self._available_ticks = np.sort(positions[tick_col].unique())
    
    def _setup_events(self) -> None:
        """Index events by tick for quick lookup."""
        self._events_by_tick: Dict[int, List[Dict[str, Any]]] = {}
        
        # Index kills
        kills_df = self.data.kills
        if kills_df is not None and not kills_df.empty and 'tick' in kills_df.columns:
            for _, row in kills_df.iterrows():
                tick = int(row['tick'])
                if tick not in self._events_by_tick:
                    self._events_by_tick[tick] = []
                
                self._events_by_tick[tick].append({
                    'type': 'kill',
                    'attacker': row.get('attacker_name', 'Unknown'),
                    'attacker_steamid': row.get('attacker_steamid'),
                    'victim': row.get('user_name', 'Unknown'),
                    'victim_steamid': row.get('user_steamid'),
                    'weapon': row.get('weapon', 'Unknown'),
                    'headshot': row.get('headshot', False),
                    'x': row.get('user_X', row.get('X', 0)),
                    'y': row.get('user_Y', row.get('Y', 0)),
                })
        
        # Index grenades
        grenades_df = self.data.grenades
        if grenades_df is not None and not grenades_df.empty and 'tick' in grenades_df.columns:
            for _, row in grenades_df.iterrows():
                tick = int(row['tick'])
                if tick not in self._events_by_tick:
                    self._events_by_tick[tick] = []
                
                self._events_by_tick[tick].append({
                    'type': 'grenade',
                    'grenade_type': row.get('grenade_type', 'unknown'),
                    'x': row.get('X', 0),
                    'y': row.get('Y', 0),
                })
    
    def _build_player_lookup(self) -> None:
        """Build steamid -> name mapping."""
        self._player_names: Dict[str, str] = {}
        
        # From kills
        kills_df = self.data.kills
        if kills_df is not None and not kills_df.empty:
            if 'attacker_steamid' in kills_df.columns and 'attacker_name' in kills_df.columns:
                for _, row in kills_df.iterrows():
                    sid = str(row.get('attacker_steamid', ''))
                    name = row.get('attacker_name', '')
                    if sid and name:
                        self._player_names[sid] = name
            
            if 'user_steamid' in kills_df.columns and 'user_name' in kills_df.columns:
                for _, row in kills_df.iterrows():
                    sid = str(row.get('user_steamid', ''))
                    name = row.get('user_name', '')
                    if sid and name:
                        self._player_names[sid] = name
    
    @property
    def map_name(self) -> str:
        """Get map name."""
        return self.data.map_name or "unknown"
    
    @property
    def progress(self) -> float:
        """Get playback progress 0.0 - 1.0."""
        total = self.max_tick - self.min_tick
        if total <= 0:
            return 0.0
        return (self.current_tick - self.min_tick) / total
    
    @property
    def current_round(self) -> int:
        """Get current round number based on tick."""
        for r in self.rounds:
            if r.start_tick <= self.current_tick <= r.end_tick:
                return r.round_num
        return 1
    
    def play(self) -> None:
        """Start playback."""
        self.is_playing = True
        self._last_frame_time = time.time()
    
    def pause(self) -> None:
        """Pause playback."""
        self.is_playing = False
    
    def toggle_play(self) -> None:
        """Toggle play/pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def seek(self, tick: int) -> None:
        """
        Seek to specific tick with bounds checking.
        
        Clamps to valid range and snaps to nearest available tick.
        Safe to call with any value (handles edge cases).
        """
        # Clamp to valid range
        clamped = max(self.min_tick, min(self.max_tick, tick))
        
        # Snap to nearest available tick if we have the index
        if len(self._available_ticks) > 0:
            idx = np.searchsorted(self._available_ticks, clamped)
            if idx == 0:
                clamped = int(self._available_ticks[0])
            elif idx >= len(self._available_ticks):
                clamped = int(self._available_ticks[-1])
            else:
                # Snap to nearest
                if abs(self._available_ticks[idx] - clamped) < abs(self._available_ticks[idx-1] - clamped):
                    clamped = int(self._available_ticks[idx])
                else:
                    clamped = int(self._available_ticks[idx-1])
        
        self.current_tick = clamped
    
    def seek_relative(self, delta_ticks: int) -> None:
        """
        Seek relative to current position.
        
        Safe for any delta value - will clamp to valid bounds.
        """
        self.seek(self.current_tick + delta_ticks)
    
    def jump_to_round(self, round_num: int) -> None:
        """Jump to start of a specific round."""
        for r in self.rounds:
            if r.round_num == round_num:
                self.seek(r.start_tick)
                return
    
    def set_speed(self, speed: float) -> None:
        """Set playback speed multiplier."""
        self.speed = max(0.25, min(4.0, speed))
    
    def update(self) -> Optional[FrameData]:
        """
        Update playback and return current frame data.
        Should be called every render frame.
        
        Returns:
            FrameData for current tick, or None if paused at same tick
        """
        if self.is_playing:
            now = time.time()
            dt = now - self._last_frame_time
            self._last_frame_time = now
            
            # CRITICAL: Clamp dt to prevent huge jumps on window focus loss/lag spikes
            dt = min(dt, self.MAX_DT)
            
            # Calculate tick advancement using dynamic tickrate
            ticks_per_second = self.tickrate * self.speed
            tick_delta = int(dt * ticks_per_second)
            
            # Frame skip: at high speeds, skip more aggressively
            if self.speed > 1.0:
                tick_delta = max(tick_delta, int(self._ticks_per_frame * self.speed))
            
            if tick_delta > 0:
                self.current_tick = min(self.max_tick, self.current_tick + tick_delta)
                
                # Stop at end
                if self.current_tick >= self.max_tick:
                    self.is_playing = False
        
        return self._get_frame_data(self.current_tick)
    
    def _get_frame_data(self, tick: int) -> FrameData:
        """Get frame data for a specific tick."""
        players = self._get_players_at_tick(tick)
        events = self._events_by_tick.get(tick, [])
        
        # Also include recent events (last 2 seconds for kill feed)
        recent_events = []
        lookback = self.tickrate * 2  # 2 seconds
        for t in range(max(self.min_tick, tick - lookback), tick):
            if t in self._events_by_tick:
                for evt in self._events_by_tick[t]:
                    evt_copy = evt.copy()
                    evt_copy['age'] = tick - t
                    recent_events.append(evt_copy)
        
        return FrameData(
            tick=tick,
            round_num=self.current_round,
            players=players,
            events=recent_events
        )
    
    def _get_players_at_tick(self, tick: int) -> List[PlayerState]:
        """
        Extract player states at a given tick.
        
        Uses LRU cache with proper eviction to avoid memory growth.
        """
        # Check cache first (LRU: move to end on access)
        if tick in self._tick_cache:
            self._tick_cache.move_to_end(tick)
            return self._tick_cache[tick]
        
        players = []
        
        if not self._has_positions:
            return players
        
        positions = self.data.player_positions
        
        # Find closest tick
        tick_col = None
        for col in ['tick', 'Tick']:
            if col in positions.columns:
                tick_col = col
                break
        
        if tick_col is None:
            return players
        
        # Get rows at this tick (or nearest)
        # Use pre-built index for fast nearest-tick lookup
        tick_mask = positions[tick_col] == tick
        if not tick_mask.any():
            # Use pre-indexed available ticks for O(log n) lookup
            if len(self._available_ticks) == 0:
                return players
            # Binary search for nearest tick
            idx = np.searchsorted(self._available_ticks, tick)
            if idx == 0:
                nearest = self._available_ticks[0]
            elif idx == len(self._available_ticks):
                nearest = self._available_ticks[-1]
            else:
                # Compare neighbors
                if abs(self._available_ticks[idx] - tick) < abs(self._available_ticks[idx-1] - tick):
                    nearest = self._available_ticks[idx]
                else:
                    nearest = self._available_ticks[idx-1]
            tick_mask = positions[tick_col] == nearest
        
        tick_data = positions[tick_mask]
        
        # Group by player
        steamid_col = None
        for col in ['steamid', 'SteamID', 'player_steamid', 'name']:
            if col in tick_data.columns:
                steamid_col = col
                break
        
        if steamid_col is None:
            # Fallback: assume rows are different players
            for i, row in tick_data.iterrows():
                players.append(self._row_to_player_state(row, str(i)))
        else:
            for steamid in tick_data[steamid_col].unique():
                player_row = tick_data[tick_data[steamid_col] == steamid].iloc[-1]
                players.append(self._row_to_player_state(player_row, str(steamid)))
        
        # Store in LRU cache with eviction
        self._tick_cache[tick] = players
        if len(self._tick_cache) > self._cache_max_size:
            # Evict oldest (first) entry
            self._tick_cache.popitem(last=False)
        
        return players
    
    def _row_to_player_state(self, row: pd.Series, steamid: str) -> PlayerState:
        """Convert DataFrame row to PlayerState."""
        # Determine team
        team = "T"
        team_val = row.get('team_name', row.get('team', ''))
        if isinstance(team_val, str):
            if 'CT' in team_val.upper() or 'COUNTER' in team_val.upper():
                team = "CT"
        elif isinstance(team_val, (int, float)):
            if team_val == 3:  # CT team number
                team = "CT"
        
        return PlayerState(
            steamid=steamid,
            name=self._player_names.get(steamid, f"Player_{steamid[-4:]}"),
            x=float(row.get('X', 0)),
            y=float(row.get('Y', 0)),
            z=float(row.get('Z', 0)),
            health=int(row.get('health', 100)),
            armor=int(row.get('armor_value', 0)),
            team=team,
            is_alive=bool(row.get('is_alive', True)),
            yaw=float(row.get('yaw', 0)),
            pitch=float(row.get('pitch', 0))
        )
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get match statistics summary."""
        kills_df = self.data.kills
        
        if kills_df is None or kills_df.empty:
            return {"error": "No kill data available"}
        
        stats = {
            "total_kills": len(kills_df),
            "total_rounds": len(self.rounds),
            "map": self.map_name,
            "duration_ticks": self.max_tick - self.min_tick,
        }
        
        return stats
