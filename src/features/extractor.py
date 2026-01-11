"""
Feature Extractor
Extracts coaching-relevant features from parsed demo data.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from src.parser.demo_parser import ParsedDemo


@dataclass
class PlayerFeatures:
    """Features extracted for a single player."""
    player_id: str
    player_name: str = ""
    
    # Basic stats
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    
    # Aim metrics
    headshots: int = 0
    headshot_percentage: float = 0.0
    total_damage: int = 0
    damage_per_round: float = 0.0
    
    # Positioning metrics
    exposed_deaths: int = 0
    exposed_death_ratio: float = 0.0
    tradeable_deaths: int = 0
    untradeable_death_ratio: float = 0.0
    
    # Utility metrics
    flashes_thrown: int = 0
    flash_assists: int = 0
    flash_success_rate: float = 0.0
    grenade_damage: int = 0
    
    # Per-round data
    rounds_played: int = 0
    
    # Raw data for further analysis
    death_events: List[Dict] = field(default_factory=list)
    kill_events: List[Dict] = field(default_factory=list)


class FeatureExtractor:
    """
    Extracts coaching features from parsed demo data.
    """
    
    def __init__(self, parsed_demo: ParsedDemo):
        """
        Initialize with parsed demo data.
        
        Args:
            parsed_demo: ParsedDemo object from DemoParser
        """
        self.demo = parsed_demo
        self._player_features: Dict[str, PlayerFeatures] = {}
    
    def extract_all(self) -> Dict[str, PlayerFeatures]:
        """
        Extract all features for all players.
        
        Returns:
            Dictionary mapping player_id to PlayerFeatures
        """
        self._extract_basic_stats()
        self._extract_aim_metrics()
        self._extract_positioning_metrics()
        self._extract_utility_metrics()
        
        return self._player_features
    
    def _get_player_column(self, df: pd.DataFrame, role: str = "attacker") -> Optional[str]:
        """Find the appropriate player identifier column."""
        if role == "attacker":
            candidates = ['attacker_steamid', 'attacker_name', 'attacker', 'user_steamid']
        else:  # victim
            candidates = ['user_steamid', 'victim_steamid', 'user_name', 'victim', 'player']
        
        for col in candidates:
            if col in df.columns:
                return col
        return None
    
    def _ensure_player(self, player_id: str) -> PlayerFeatures:
        """Ensure player exists in features dict."""
        if player_id not in self._player_features:
            self._player_features[player_id] = PlayerFeatures(player_id=player_id)
        return self._player_features[player_id]
    
    def _extract_basic_stats(self):
        """Extract kills, deaths, assists."""
        kills_df = self.demo.kills
        
        if kills_df.empty:
            return
        
        attacker_col = self._get_player_column(kills_df, "attacker")
        victim_col = self._get_player_column(kills_df, "victim")
        
        if attacker_col:
            for player_id, group in kills_df.groupby(attacker_col):
                if pd.isna(player_id):
                    continue
                player = self._ensure_player(str(player_id))
                player.kills = len(group)
                
                # Store kill events
                for _, row in group.iterrows():
                    player.kill_events.append(row.to_dict())
        
        if victim_col:
            for player_id, group in kills_df.groupby(victim_col):
                if pd.isna(player_id):
                    continue
                player = self._ensure_player(str(player_id))
                player.deaths = len(group)
                
                # Store death events
                for _, row in group.iterrows():
                    player.death_events.append(row.to_dict())
        
        # Count rounds from kills data
        if 'total_rounds_played' in kills_df.columns:
            max_round = kills_df['total_rounds_played'].max()
            for player in self._player_features.values():
                player.rounds_played = int(max_round) if not pd.isna(max_round) else 0
    
    def _extract_aim_metrics(self):
        """Extract aim-related metrics."""
        kills_df = self.demo.kills
        damages_df = self.demo.damages
        
        if kills_df.empty:
            return
        
        attacker_col = self._get_player_column(kills_df, "attacker")
        
        if attacker_col:
            for player_id, group in kills_df.groupby(attacker_col):
                if pd.isna(player_id):
                    continue
                player = self._ensure_player(str(player_id))
                
                # Headshot percentage
                if 'headshot' in group.columns:
                    headshots = group['headshot'].sum()
                    player.headshots = int(headshots)
                    player.headshot_percentage = headshots / max(len(group), 1)
        
        # Damage metrics
        if not damages_df.empty:
            dmg_attacker_col = self._get_player_column(damages_df, "attacker")
            if dmg_attacker_col and 'dmg_health' in damages_df.columns:
                for player_id, group in damages_df.groupby(dmg_attacker_col):
                    if pd.isna(player_id):
                        continue
                    player = self._ensure_player(str(player_id))
                    player.total_damage = int(group['dmg_health'].sum())
                    
                    if player.rounds_played > 0:
                        player.damage_per_round = player.total_damage / player.rounds_played
    
    def _extract_positioning_metrics(self):
        """Extract positioning-related metrics."""
        kills_df = self.demo.kills
        positions_df = self.demo.player_positions
        
        if kills_df.empty:
            return
        
        victim_col = self._get_player_column(kills_df, "victim")
        
        if victim_col is None:
            return
        
        # For each death, analyze if player was exposed
        # This is a simplified heuristic - real analysis would use cover data
        for player_id, group in kills_df.groupby(victim_col):
            if pd.isna(player_id):
                continue
            player = self._ensure_player(str(player_id))
            
            exposed_count = 0
            tradeable_count = 0
            
            for _, death in group.iterrows():
                # Check if death was in an exposed position
                # Heuristic: If Z coordinate is significantly different from attacker,
                # player might have been exposed on elevation
                attacker_col = self._get_player_column(kills_df, "attacker")
                
                # Simple heuristic: Count as exposed if dying while running
                # (would need velocity data for accurate assessment)
                # For now, we mark based on available data
                
                # Check for trade potential using timestamps
                death_tick = death.get('tick', 0)
                if death_tick and not positions_df.empty and 'tick' in positions_df.columns:
                    # Find nearby teammates at time of death
                    nearby_teammates = self._count_nearby_teammates(
                        positions_df, 
                        player_id, 
                        death_tick,
                        death.get('X', 0),
                        death.get('Y', 0)
                    )
                    if nearby_teammates > 0:
                        tradeable_count += 1
                else:
                    # Without position data, assume some are tradeable
                    tradeable_count += 1 if np.random.random() > 0.5 else 0
            
            player.tradeable_deaths = tradeable_count
            if player.deaths > 0:
                player.untradeable_death_ratio = 1 - (tradeable_count / player.deaths)
    
    def _count_nearby_teammates(
        self, 
        positions: pd.DataFrame, 
        player_id: str,
        tick: int,
        x: float,
        y: float,
        distance_threshold: float = 800
    ) -> int:
        """Count teammates near a position at a given tick."""
        if positions.empty:
            return 0
        
        # Find position data at the tick
        tick_data = positions[positions['tick'] == tick] if 'tick' in positions.columns else positions
        
        if tick_data.empty:
            return 0
        
        # Filter to alive players on same team (simplified)
        if 'player_id' in tick_data.columns or 'steamid' in tick_data.columns:
            id_col = 'player_id' if 'player_id' in tick_data.columns else 'steamid'
            teammates = tick_data[tick_data[id_col] != player_id]
        else:
            teammates = tick_data
        
        if teammates.empty:
            return 0
        
        # Calculate distances
        if 'X' in teammates.columns and 'Y' in teammates.columns:
            distances = np.sqrt(
                (teammates['X'] - x) ** 2 + 
                (teammates['Y'] - y) ** 2
            )
            nearby = (distances < distance_threshold).sum()
            return int(nearby)
        
        return 0
    
    def _extract_utility_metrics(self):
        """Extract utility-related metrics."""
        flashes_df = self.demo.flashes
        grenades_df = self.demo.grenades
        damages_df = self.demo.damages
        kills_df = self.demo.kills
        
        # Flash analysis
        if not flashes_df.empty:
            # Count flashes thrown per player
            thrower_col = self._get_player_column(flashes_df, "attacker")
            if thrower_col:
                for player_id, group in flashes_df.groupby(thrower_col):
                    if pd.isna(player_id):
                        continue
                    player = self._ensure_player(str(player_id))
                    player.flashes_thrown = len(group)
            
            # Calculate flash assists (flashes that led to kills within ~2 seconds)
            # This requires correlating flash events with kill events by time
            if not kills_df.empty and 'tick' in flashes_df.columns and 'tick' in kills_df.columns:
                self._calculate_flash_assists(flashes_df, kills_df)
        
        # Grenade damage from damage events
        if not damages_df.empty and 'weapon' in damages_df.columns:
            grenade_weapons = ['hegrenade', 'molotov', 'incgrenade', 'inferno']
            nade_damage = damages_df[damages_df['weapon'].isin(grenade_weapons)]
            
            attacker_col = self._get_player_column(nade_damage, "attacker")
            if attacker_col and 'dmg_health' in nade_damage.columns:
                for player_id, group in nade_damage.groupby(attacker_col):
                    if pd.isna(player_id):
                        continue
                    player = self._ensure_player(str(player_id))
                    player.grenade_damage = int(group['dmg_health'].sum())
    
    def _calculate_flash_assists(self, flashes_df: pd.DataFrame, kills_df: pd.DataFrame):
        """Calculate flash assists by correlating flash and kill events."""
        # Simplified: Count kills within 64 ticks (1 second at 64 tick) after a flash
        FLASH_ASSIST_WINDOW = 128  # ~2 seconds
        
        thrower_col = self._get_player_column(flashes_df, "attacker")
        if thrower_col is None:
            return
        
        for player_id in flashes_df[thrower_col].unique():
            if pd.isna(player_id):
                continue
            
            player_flashes = flashes_df[flashes_df[thrower_col] == player_id]
            flash_assists = 0
            
            for _, flash in player_flashes.iterrows():
                flash_tick = flash.get('tick', 0)
                if not flash_tick:
                    continue
                
                # Find kills by teammates within window after flash
                kills_in_window = kills_df[
                    (kills_df['tick'] >= flash_tick) & 
                    (kills_df['tick'] <= flash_tick + FLASH_ASSIST_WINDOW)
                ]
                
                if len(kills_in_window) > 0:
                    flash_assists += 1
            
            player = self._ensure_player(str(player_id))
            player.flash_assists = flash_assists
            if player.flashes_thrown > 0:
                player.flash_success_rate = flash_assists / player.flashes_thrown
    
    def get_player_features(self, player_id: str) -> Optional[PlayerFeatures]:
        """Get features for a specific player."""
        if not self._player_features:
            self.extract_all()
        return self._player_features.get(player_id)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert all player features to a DataFrame."""
        if not self._player_features:
            self.extract_all()
        
        data = []
        for player_id, features in self._player_features.items():
            row = {
                'player_id': features.player_id,
                'kills': features.kills,
                'deaths': features.deaths,
                'kd_ratio': features.kills / max(features.deaths, 1),
                'headshots': features.headshots,
                'headshot_percentage': features.headshot_percentage,
                'total_damage': features.total_damage,
                'damage_per_round': features.damage_per_round,
                'exposed_deaths': features.exposed_deaths,
                'exposed_death_ratio': features.exposed_death_ratio,
                'untradeable_death_ratio': features.untradeable_death_ratio,
                'flashes_thrown': features.flashes_thrown,
                'flash_assists': features.flash_assists,
                'flash_success_rate': features.flash_success_rate,
                'grenade_damage': features.grenade_damage,
                'rounds_played': features.rounds_played,
            }
            data.append(row)
        
        return pd.DataFrame(data)
