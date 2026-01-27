# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.

"""
CS2 Demo Parser Wrapper
Uses demoparser2 as primary parser with awpy as alternative.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

try:
    from demoparser2 import DemoParser as DP2
    DEMOPARSER2_AVAILABLE = True
except ImportError:
    DEMOPARSER2_AVAILABLE = False

try:
    from awpy import Demo
    AWPY_AVAILABLE = True
except ImportError:
    AWPY_AVAILABLE = False

import pandas as pd


@dataclass
class ParsedDemo:
    """Container for parsed demo data."""
    # Metadata
    demo_path: str
    map_name: str = ""
    match_duration: int = 0
    tickrate: int = 64  # Default, will be read from header

    
    # Core DataFrames
    kills: pd.DataFrame = field(default_factory=pd.DataFrame)
    deaths: pd.DataFrame = field(default_factory=pd.DataFrame)
    damages: pd.DataFrame = field(default_factory=pd.DataFrame)
    rounds: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # Position/Tick data
    player_positions: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # Utility data
    grenades: pd.DataFrame = field(default_factory=pd.DataFrame)
    flashes: pd.DataFrame = field(default_factory=pd.DataFrame)
    bomb: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # Player info
    players: Dict[str, Any] = field(default_factory=dict)
    
    # Raw parser output for advanced queries
    _raw: Any = None


class DemoParser:
    """
    Unified demo parser interface.
    Supports demoparser2 (primary) and awpy (fallback).
    """
    
    def __init__(self, demo_path: str, parser: str = "auto"):
        """
        Initialize parser with demo file path.
        
        Args:
            demo_path: Path to .dem file
            parser: "demoparser2", "awpy", or "auto" (try demoparser2 first)
        """
        self.demo_path = Path(demo_path)
        if not self.demo_path.exists():
            raise FileNotFoundError(f"Demo file not found: {demo_path}")
        
        self.parser_type = self._select_parser(parser)
        self._parsed_data: Optional[ParsedDemo] = None
    
    def _select_parser(self, preference: str) -> str:
        """Select available parser based on preference."""
        if preference == "auto":
            if DEMOPARSER2_AVAILABLE:
                return "demoparser2"
            elif AWPY_AVAILABLE:
                return "awpy"
            else:
                raise ImportError(
                    "No demo parser available. Install demoparser2 or awpy:\n"
                    "  pip install demoparser2\n"
                    "  pip install awpy"
                )
        elif preference == "demoparser2":
            if not DEMOPARSER2_AVAILABLE:
                raise ImportError("demoparser2 not installed: pip install demoparser2")
            return "demoparser2"
        elif preference == "awpy":
            if not AWPY_AVAILABLE:
                raise ImportError("awpy not installed: pip install awpy")
            return "awpy"
        else:
            raise ValueError(f"Unknown parser: {preference}")
    
    def parse(self) -> ParsedDemo:
        """Parse the demo file and return structured data."""
        if self._parsed_data is not None:
            return self._parsed_data
        
        if self.parser_type == "demoparser2":
            self._parsed_data = self._parse_with_demoparser2()
        else:
            self._parsed_data = self._parse_with_awpy()
        
        return self._parsed_data
    
    def _parse_with_demoparser2(self) -> ParsedDemo:
        """Parse using demoparser2 library."""
        parser = DP2(str(self.demo_path))
        
        result = ParsedDemo(demo_path=str(self.demo_path))
        
        # Extract map name and tickrate from header
        try:
            header = parser.parse_header()
            if header and "map_name" in header:
                result.map_name = header["map_name"]
            else:
                result.map_name = "Unknown"
            
            # Extract tickrate (playback_ticks / playback_time gives tickrate)
            if header:
                playback_ticks = header.get("playback_ticks", 0)
                playback_time = header.get("playback_time", 0)
                if playback_time > 0 and playback_ticks > 0:
                    result.tickrate = int(round(playback_ticks / playback_time))
                elif "tickrate" in header:
                    result.tickrate = int(header["tickrate"])
        except Exception as e:
            print(f"Warning: Could not extract header info: {e}")
            result.map_name = "Unknown"
        
        # Parse kills with player data
        try:
            kills_df = parser.parse_event(
                "player_death",
                player=["X", "Y", "Z", "team_name", "health"],
                other=["total_rounds_played", "headshot", "weapon"]
            )
            result.kills = kills_df if kills_df is not None else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not parse kills: {e}")
            result.kills = pd.DataFrame()
        
        # Parse damage events
        try:
            damages_df = parser.parse_event(
                "player_hurt",
                player=["X", "Y", "Z", "team_name"],
                other=["dmg_health", "dmg_armor", "weapon", "hitgroup"]
            )
            result.damages = damages_df if damages_df is not None else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not parse damages: {e}")
            result.damages = pd.DataFrame()
        
        # Parse round events for timing context
        try:
            round_start_df = parser.parse_event("round_start")
            round_end_df = parser.parse_event("round_end")
            
            if round_start_df is not None and round_end_df is not None:
                # Ensure lengths match or trim to min
                min_len = min(len(round_start_df), len(round_end_df))
                result.rounds = pd.DataFrame({
                    "round_start_tick": round_start_df.get("tick", pd.Series())[:min_len],
                    "round_end_tick": round_end_df.get("tick", pd.Series())[:min_len],
                    "winner": round_end_df.get("winner", pd.Series())[:min_len],
                    "reason": round_end_df.get("reason", pd.Series())[:min_len]
                })
            elif round_start_df is not None:
                result.rounds = round_start_df
        except Exception as e:
            print(f"Warning: Could not parse round events: {e}")
            result.rounds = pd.DataFrame()
        
        # Parse flash events
        try:
            blind_df = parser.parse_event(
                "player_blind",
                player=["X", "Y", "Z", "team_name"],
                other=["blind_duration", "attacker_steamid", "attacker_name", "attacker_team_name"]
            )
            result.flashes = blind_df if blind_df is not None else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not parse flashes: {e}")
            result.flashes = pd.DataFrame()
        
        # Parse grenade detonations
        try:
            he_df = parser.parse_event("hegrenade_detonate", player=["X", "Y", "Z", "name", "team_name"])
            smoke_df = parser.parse_event("smokegrenade_detonate", player=["X", "Y", "Z", "name", "team_name"])
            flash_det_df = parser.parse_event("flashbang_detonate", player=["X", "Y", "Z", "name", "team_name"])
            
            grenades_list = []
            if he_df is not None and len(he_df) > 0:
                he_df["grenade_type"] = "hegrenade"
                grenades_list.append(he_df)
            if smoke_df is not None and len(smoke_df) > 0:
                smoke_df["grenade_type"] = "smoke"
                grenades_list.append(smoke_df)
            if flash_det_df is not None and len(flash_det_df) > 0:
                flash_det_df["grenade_type"] = "flashbang"
                grenades_list.append(flash_det_df)
            
            if grenades_list:
                result.grenades = pd.concat(grenades_list, ignore_index=True)
        except Exception as e:
            print(f"Warning: Could not parse grenades: {e}")
            result.grenades = pd.DataFrame()
        
        # Parse bomb events
        try:
            bomb_df = parser.parse_event("bomb_planted")
            result.bomb = bomb_df if bomb_df is not None else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not parse bomb events: {e}")
            result.bomb = pd.DataFrame()
        
        # Parse tick data for positions (sample)
        try:
            ticks_df = parser.parse_ticks(
                ["X", "Y", "Z", "health", "armor_value", "team_name", "is_alive", "vel_X", "vel_Y", "pitch", "yaw", "steamid"]
            )
            result.player_positions = ticks_df if ticks_df is not None else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not parse ticks: {e}")
            result.player_positions = pd.DataFrame()
        
        result._raw = parser
        return result
    
    def _parse_with_awpy(self) -> ParsedDemo:
        """Parse using awpy library."""
        demo = Demo(str(self.demo_path))
        demo.parse()
        
        result = ParsedDemo(demo_path=str(self.demo_path))
        
        # Map awpy output to our structure
        if hasattr(demo, 'kills') and demo.kills is not None:
            result.kills = demo.kills.to_pandas() if hasattr(demo.kills, 'to_pandas') else pd.DataFrame(demo.kills)
        
        if hasattr(demo, 'damages') and demo.damages is not None:
            result.damages = demo.damages.to_pandas() if hasattr(demo.damages, 'to_pandas') else pd.DataFrame(demo.damages)
        
        if hasattr(demo, 'rounds') and demo.rounds is not None:
            result.rounds = demo.rounds.to_pandas() if hasattr(demo.rounds, 'to_pandas') else pd.DataFrame(demo.rounds)
        
        if hasattr(demo, 'grenades') and demo.grenades is not None:
            result.grenades = demo.grenades.to_pandas() if hasattr(demo.grenades, 'to_pandas') else pd.DataFrame(demo.grenades)
        
        if hasattr(demo, 'ticks') and demo.ticks is not None:
            result.player_positions = demo.ticks.to_pandas() if hasattr(demo.ticks, 'to_pandas') else pd.DataFrame(demo.ticks)
        
        # Get header info
        if hasattr(demo, 'header') and demo.header:
            result.map_name = demo.header.get('map_name', '')
        
        result._raw = demo
        return result
    
    def get_player_stats(self, steam_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated stats for a player or all players.
        
        Args:
            steam_id: Optional Steam ID to filter to specific player
            
        Returns:
            Dictionary of player stats
        """
        data = self.parse()
        stats = {}
        
        kills_df = data.kills
        damages_df = data.damages
        
        if kills_df.empty:
            return stats
        
        # Identify player column
        player_col = None
        for col in ['attacker_steamid', 'attacker_name', 'attacker']:
            if col in kills_df.columns:
                player_col = col
                break
        
        if player_col is None:
            return stats
        
        # Get unique players
        players = kills_df[player_col].unique() if steam_id is None else [steam_id]
        
        for player in players:
            player_kills = kills_df[kills_df[player_col] == player]
            
            # Find victim column for deaths
            victim_col = None
            for col in ['user_steamid', 'user_name', 'victim', 'player']:
                if col in kills_df.columns:
                    victim_col = col
                    break
            
            player_deaths = kills_df[kills_df.get(victim_col, pd.Series()) == player] if victim_col else pd.DataFrame()
            
            # Check for headshot column
            headshots = 0
            if 'headshot' in player_kills.columns:
                headshots = player_kills['headshot'].sum()
            
            total_kills = len(player_kills)
            total_deaths = len(player_deaths)
            
            stats[player] = {
                "kills": total_kills,
                "deaths": total_deaths,
                "kd_ratio": total_kills / max(total_deaths, 1),
                "headshots": headshots,
                "headshot_percentage": headshots / max(total_kills, 1),
            }
        
        return stats


def check_parser_availability() -> Dict[str, bool]:
    """Check which parsers are available."""
    return {
        "demoparser2": DEMOPARSER2_AVAILABLE,
        "awpy": AWPY_AVAILABLE,
    }
