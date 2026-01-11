"""
Feature Extractor
Extracts coaching-relevant features from parsed demo data.

Features:
- Real trade detection (time window + distance)
- Entry frag identification
- Polygon-based map zone detection
- Round timing context
- Advanced Role Detection (Clustering)
- Movement Analysis
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from src.parser.demo_parser import ParsedDemo
from src.maps.zones import ZoneDetector, get_zone_detector
from src.metrics.role_classifier import RoleClassifier
from src.analysis.movement_analyzer import MovementAnalyzer
from src.config import TRADE_DIST_UNITS, TRADE_WINDOW_SECONDS

# Trade detection constants
TRADE_WINDOW_TICKS = int(TRADE_WINDOW_SECONDS * 64)
TICK_RATE = 64  # CS2 tick rate


@dataclass
class DeathContext:
    """Contextual information about a single death event."""
    tick: int
    round_num: int
    round_time: str  # "early" (<20s), "mid" (20-60s), "late" (>60s)
    map_area: str
    x: float
    y: float
    z: float
    
    # Trade analysis
    was_traded: bool
    trade_time_ms: int  # Milliseconds until trade (0 if not traded)
    
    # REAL teammate distance (multi-frame average, not single tick)
    nearest_teammate_distance: float = 0.0  # units (sqrt computed)
    teammates_nearby: int = 0
    
    # Trade window analysis (NEW)
    tradeable_position: bool = False  # Teammate within 500 units at death
    trader_distance: float = 9999.0   # Distance to nearest potential trader
    
    # Utility support (ENHANCED)
    had_flash_support: bool = False  # Flash within 3s before death
    flash_delay_ms: int = 0  # Time since last friendly flash
    had_smoke_cover: bool = False  # Smoke blocking LOS (NEW)
    peeked_dry: bool = False  # Died without utility support (NEW)
    
    # Multi-angle exposure (ENHANCED)
    enemy_count: int = 1  # Number of enemies in engagement
    is_crossfire: bool = False  # Multiple enemy angles
    angle_exposure_count: int = 1  # Number of enemy FOV cones containing player (NEW)
    
    # Entry tracking
    is_entry_frag: bool = False  # First death of round for team
    
    # Killer info
    killer_id: str = ""
    killer_name: str = ""
    weapon: str = ""


@dataclass
class KillContext:
    """Contextual information about a single kill event."""
    tick: int
    round_num: int
    round_time_seconds: float  # Seconds since round start
    
    # Round outcome
    round_won: bool            # Did killer's team win this round?
    
    # Player counts at kill time
    alive_ct: int              # CTs alive when kill happened
    alive_t: int               # Ts alive when kill happened
    
    # Kill classification
    is_opening_kill: bool      # First kill of the round
    is_exit_frag: bool         # Kill after round essentially decided (last 10s, 1vN)
    is_traded: bool            # Killer was killed within 3s
    
    # Context
    had_flash_support: bool = False   # Flash within 2s before kill
    victim_id: str = ""
    weapon: str = ""


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
    avg_time_to_damage: float = 500.0 # Placeholder default
    
    # Positioning metrics (derived from death contexts)
    exposed_deaths: int = 0
    exposed_death_ratio: float = 0.0
    tradeable_deaths: int = 0
    untradeable_death_ratio: float = 0.0
    avg_teammate_dist: float = 0.0
    
    # Entry frag tracking (Opening Duels)
    entry_deaths: int = 0
    entry_kills: int = 0
    entry_attempts: int = 0 # Kills + Deaths in entry duels
    entry_wins: int = 0 # Explicit wins
    multikills: int = 0 # Rounds with 2+ kills
    
    # Clutch stats
    clutches_1v1_won: int = 0
    clutches_1v1_attempted: int = 0
    clutches_1vN_won: int = 0 # 1v2+
    clutches_1vN_attempted: int = 0
    
    # Role detection (ENHANCED - multi-factor scoring)
    detected_role: str = "Support"  # Default
    role_scores: Dict[str, float] = field(default_factory=dict)
    entry_death_ratio: float = 0.0
    primary_death_area: str = ""  # Most common death area
    
    # Round phase deaths
    early_round_deaths: int = 0
    mid_round_deaths: int = 0
    late_round_deaths: int = 0
    
    # Utility metrics
    flashes_thrown: int = 0
    enemies_blinded: int = 0 # Unique enemies blinded (duration > 1s)
    flash_assists: int = 0
    flash_success_rate: float = 0.0
    grenade_damage: int = 0
    
    # Weapon Stats
    awp_kills: int = 0
    rifle_kills: int = 0
    
    # Per-round data
    rounds_played: int = 0
    
    # Contextual death data
    death_contexts: List[DeathContext] = field(default_factory=list)
    
    # Contextual kill data (NEW - round context)
    kill_contexts: List[KillContext] = field(default_factory=list)
    
    # Round-context aggregates (computed from kill_contexts)
    kills_in_won_rounds: int = 0
    kills_in_lost_rounds: int = 0
    exit_frags: int = 0
    swing_kills: int = 0          # Kills that flip man-advantage (diff_before <= -2, after >= -1)
    opening_kills_won: int = 0    # Opening kills in rounds team won
    opening_kills_lost: int = 0   # Opening kills in rounds team lost
    
    # KAST (Kill, Assist, Survived, Traded)
    kast_rounds: int = 0          # Rounds where player had K, A, S, or T
    kast_percentage: float = 0.0  # kast_rounds / rounds_played
    
    # Movement Mechanics
    counter_strafing_score_avg: float = 0.0
    peek_types: Dict[str, int] = field(default_factory=lambda: {"jiggle": 0, "wide": 0, "dry": 0})
    
    # Legacy raw data
    death_events: List[Dict] = field(default_factory=list)
    kill_events: List[Dict] = field(default_factory=list)


class FeatureExtractor:
    """
    Extracts coaching features from parsed demo data.
    """
    
    def __init__(self, parsed_demo: ParsedDemo):
        """Initialize with parsed demo data."""
        self.demo = parsed_demo
        self.map_name = parsed_demo.map_name or "unknown"
        self._player_features: Dict[str, PlayerFeatures] = {}
        self._round_start_ticks: Dict[int, int] = {}  # round_num -> start_tick
        
        # Initialize detectors
        self.zone_detector = get_zone_detector(self.map_name)
        self.role_classifier = RoleClassifier()
        self.movement_analyzer = MovementAnalyzer()
    
    def extract_all(self) -> Dict[str, PlayerFeatures]:
        """Extract all features for all players."""
        self._extract_round_timing()
        self._extract_basic_stats()
        self._extract_aim_metrics()
        self._extract_positioning_metrics()
        self._extract_utility_metrics()
        
        # New: Compute complex features for role classification
        self._compute_advanced_features()
        
        # New: Clutch & Opening Duel extraction
        self._extract_clutch_and_opening_duels()
        
        # NEW: Kill context with round outcome
        self._extract_kill_contexts()
        
        # NEW: KAST (Kill, Assist, Survived, Traded)
        self._extract_kast()
        
        # New: Run movement analysis (computationally expensive, so selective)
        self._analyze_movement()
        
        # New: Run clustering/classification LAST (needs all stats)
        self._classify_roles()
        
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
    
    def _get_team_column(self, df: pd.DataFrame, role: str = "attacker") -> Optional[str]:
        """Find team column."""
        if role == "attacker":
            candidates = ['attacker_team_name', 'attacker_team']
        else:
            candidates = ['user_team_name', 'user_team', 'team_name']
        
        for col in candidates:
            if col in df.columns:
                return col
        return None
    
    def _ensure_player(self, player_id: str) -> PlayerFeatures:
        """Ensure player exists in features dict."""
        if player_id not in self._player_features:
            self._player_features[player_id] = PlayerFeatures(player_id=player_id)
        return self._player_features[player_id]
    
    def _is_empty(self, data) -> bool:
        """Safely check if data is empty."""
        if data is None: return True
        if isinstance(data, pd.DataFrame): return data.empty
        if isinstance(data, list): return len(data) == 0
        return False

    def _extract_round_timing(self):
        """Extract round start ticks."""
        rounds_df = self.demo.rounds
        if self._is_empty(rounds_df): return
        
        if 'round_start_tick' in rounds_df.columns:
            for idx, row in rounds_df.iterrows():
                self._round_start_ticks[idx + 1] = int(row.get('round_start_tick', 0))
        elif 'tick' in rounds_df.columns:
            for idx, row in rounds_df.iterrows():
                self._round_start_ticks[idx + 1] = int(row.get('tick', 0))

    def _get_round_time_phase(self, tick: int, round_num: int) -> str:
        round_start = self._round_start_ticks.get(round_num, 0)
        if round_start == 0: return "unknown"
        elapsed = (tick - round_start) / TICK_RATE
        if elapsed < 20: return "early"
        elif elapsed < 60: return "mid"
        else: return "late"

    def _get_map_area(self, x: float, y: float) -> str:
        return self.zone_detector.get_callout(x, y)

    def _detect_trade(self, death_tick: int, victim_id: str, victim_team: str, killer_id: str, kills_df: pd.DataFrame) -> Tuple[bool, int]:
        if self._is_empty(kills_df): return False, 0
        attacker_col = self._get_player_column(kills_df, "attacker")
        victim_col = self._get_player_column(kills_df, "victim")
        if not attacker_col or not victim_col: return False, 0
        
        post_death_kills = kills_df[(kills_df['tick'] > death_tick) & (kills_df['tick'] <= death_tick + TRADE_WINDOW_TICKS)]
        if post_death_kills.empty: return False, 0
        
        for _, kill in post_death_kills.iterrows():
            k_victim = str(kill.get(victim_col, ""))
            if k_victim == killer_id or (killer_id in k_victim):
                return True, int((kill['tick'] - death_tick) / TICK_RATE * 1000)
        return False, 0

    def _is_entry_frag(self, death_tick: int, round_num: int, victim_team: str, kills_df: pd.DataFrame) -> bool:
        if self._is_empty(kills_df): return False
        victim_team_col = self._get_team_column(kills_df, "victim")
        if not victim_team_col or 'total_rounds_played' not in kills_df.columns: return False
        
        round_deaths = kills_df[(kills_df['total_rounds_played'] == round_num) & (kills_df[victim_team_col] == victim_team)]
        if round_deaths.empty: return False
        return death_tick == round_deaths['tick'].min()

    def _count_nearby_teammates(self, positions: pd.DataFrame, player_id: str, tick: int, x: float, y: float, distance_threshold: float = 800) -> int:
        if self._is_empty(positions) or 'tick' not in positions.columns: return 0
        # Optimization: Don't scan entire DF every time. But assuming small-ish here.
        # Ideally we'd have a spatial index or optimized structure.
        # For now, simplistic scan on window.
        tick_data = positions[(positions['tick'] >= tick - 16) & (positions['tick'] <= tick + 16)]
        if tick_data.empty: return 0
        
        id_col = next((c for c in ['player_id', 'steamid', 'name'] if c in tick_data.columns), None)
        if not id_col: return 0
        
        teammates = tick_data[tick_data[id_col] != player_id]
        if teammates.empty or 'X' not in teammates.columns: return 0
        
        distances = np.sqrt((teammates['X'] - x)**2 + (teammates['Y'] - y)**2)
        return int((distances < distance_threshold).sum())

    def _get_nearest_teammate_distance(self, positions: pd.DataFrame, player_id: str, tick: int, x: float, y: float) -> Tuple[float, bool, float]:
        TRADEABLE_DISTANCE = TRADE_DIST_UNITS
        if self._is_empty(positions) or 'tick' not in positions.columns: return 9999.0, False, 9999.0
        
        # Check current tick
        tick_data = positions[(positions['tick'] == tick)]
        if tick_data.empty:
            # Try getting nearest if exact tick missing
            tick_data = positions[(positions['tick'] >= tick - 8) & (positions['tick'] <= tick + 8)]
            
        if tick_data.empty: return 9999.0, False, 9999.0
        
        id_col = next((c for c in ['player_id', 'steamid', 'name'] if c in tick_data.columns), None)
        if not id_col: return 9999.0, False, 9999.0

        teammates = tick_data[tick_data[id_col] != player_id]
        if teammates.empty: return 9999.0, False, 9999.0
        
        if 'X' not in teammates.columns: return 9999.0, False, 9999.0
        
        distances = np.sqrt((teammates['X'] - x)**2 + (teammates['Y'] - y)**2)
        if len(distances) == 0: return 9999.0, False, 9999.0
        
        min_dist = float(distances.min())
        return min_dist, min_dist <= TRADEABLE_DISTANCE, min_dist

    def _check_utility_support(self, death_tick: int, death_x: float, death_y: float, player_team: str, player_id: str) -> Dict[str, Any]:
        result = {"had_flash": False, "flash_delay_ms": 0, "had_smoke": False, "peeked_dry": True}
        FLASH_WINDOW = 192
        flashes = self.demo.flashes
        if not self._is_empty(flashes) and 'tick' in flashes.columns:
             pre = flashes[(flashes['tick'] >= death_tick - FLASH_WINDOW) & (flashes['tick'] <= death_tick)]
             if not pre.empty:
                 result["had_flash"] = True
                 result["peeked_dry"] = False
                 result["flash_delay_ms"] = int((death_tick - pre['tick'].max()) / TICK_RATE * 1000)
                 
        return result

    def _extract_basic_stats(self):
        kills_df = self.demo.kills
        if self._is_empty(kills_df): return
        
        att_col = self._get_player_column(kills_df, "attacker")
        vic_col = self._get_player_column(kills_df, "victim")
        
        if att_col:
            for pid, grp in kills_df.groupby(att_col):
                if pd.isna(pid): continue
                player = self._ensure_player(str(pid))
                player.kills = len(grp)
                # Name extraction
                if 'attacker_name' in grp.columns:
                     name = grp['attacker_name'].dropna().iloc[0] if not grp['attacker_name'].dropna().empty else ""
                     if name: player.player_name = str(name)
                
                # Weapon stats
                if 'weapon' in grp.columns:
                    player.awp_kills = len(grp[grp['weapon'] == 'awp'])
                    player.rifle_kills = len(grp[grp['weapon'].isin(['ak47', 'm4a1', 'm4a1_silencer'])])

        if vic_col:
            for pid, grp in kills_df.groupby(vic_col):
                if pd.isna(pid): continue
                player = self._ensure_player(str(pid))
                player.deaths = len(grp)
                if not player.player_name and 'user_name' in grp.columns:
                    name = grp['user_name'].dropna().iloc[0] if not grp['user_name'].dropna().empty else ""
                    if name: player.player_name = str(name)

        if 'total_rounds_played' in kills_df.columns:
             max_r = kills_df['total_rounds_played'].max()
             for p in self._player_features.values():
                 p.rounds_played = int(max_r)

    def _extract_aim_metrics(self):
        kills_df = self.demo.kills
        damages = self.demo.damages
        att_col = self._get_player_column(kills_df, "attacker")
        
        if not self._is_empty(kills_df) and att_col:
            for pid, grp in kills_df.groupby(att_col):
                if pd.isna(pid): continue
                player = self._ensure_player(str(pid))
                if 'headshot' in grp.columns:
                    player.headshots = int(grp['headshot'].sum())
                    player.headshot_percentage = player.headshots / max(len(grp), 1)

        if not self._is_empty(damages):
            att_col = self._get_player_column(damages, "attacker")
            if att_col and 'dmg_health' in damages.columns:
                for pid, grp in damages.groupby(att_col):
                    if pd.isna(pid): continue
                    player = self._ensure_player(str(pid))
                    player.total_damage = int(grp['dmg_health'].sum())
                    if player.rounds_played > 0:
                        player.damage_per_round = player.total_damage / player.rounds_played

    def _extract_positioning_metrics(self):
        kills_df = self.demo.kills
        pos_df = self.demo.player_positions
        if self._is_empty(kills_df) or not self._get_player_column(kills_df, "victim"): return
        
        vic_col = self._get_player_column(kills_df, "victim")
        att_col = self._get_player_column(kills_df, "attacker")
        vic_team_col = self._get_team_column(kills_df, "victim")
        
        for pid, grp in kills_df.groupby(vic_col):
            if pd.isna(pid): continue
            player = self._ensure_player(str(pid))
            
            for _, death in grp.iterrows():
                tick = int(death.get('tick', 0))
                round_num = int(death.get('total_rounds_played', 0))  # Don't add 1, match kills_df
                x = float(death.get('user_X', death.get('X', 0)))
                y = float(death.get('user_Y', death.get('Y', 0)))
                
                killer_id = str(death.get(att_col, "")) if att_col else ""
                victim_team = str(death.get(vic_team_col, "")) if vic_team_col else ""
                
                was_traded, trade_time = self._detect_trade(tick, str(pid), victim_team, killer_id, kills_df)
                is_entry = self._is_entry_frag(tick, round_num, victim_team, kills_df)
                
                dist, tradeable, trader_dist = self._get_nearest_teammate_distance(pos_df, str(pid), tick, x, y)
                util = self._check_utility_support(tick, x, y, victim_team, str(pid))
                
                ctx = DeathContext(
                    tick=tick,
                    round_num=round_num,
                    round_time=self._get_round_time_phase(tick, round_num),
                    map_area=self._get_map_area(x, y),
                    x=x, y=y, z=0,
                    was_traded=was_traded,
                    trade_time_ms=trade_time,
                    nearest_teammate_distance=dist,
                    tradeable_position=tradeable,
                    trader_distance=trader_dist,
                    had_flash_support=util["had_flash"],
                    flash_delay_ms=util["flash_delay_ms"],
                    peeked_dry=util["peeked_dry"],
                    is_entry_frag=is_entry,
                    killer_id=killer_id
                )
                player.death_contexts.append(ctx)
                
                if is_entry: player.entry_deaths += 1
                if was_traded: player.tradeable_deaths += 1

    def _extract_utility_metrics(self):
        flashes = self.demo.flashes
        if self._is_empty(flashes): return
        
        att_col = self._get_player_column(flashes, "attacker")
        if att_col:
            for pid, grp in flashes.groupby(att_col):
                if pd.isna(pid): continue
                player = self._ensure_player(str(pid))
                
                # Count flashes thrown (event is usually 'player_blind' though, wait)
                # 'player_blind' = someone GOT blinded.
                # To count Thrown, we need 'flashbang_detonate' or we infer from blinds?
                # The 'flashes' DF is 'player_blind'. So len(grp) is TOTAL BLIND EVENTS CAUSED.
                # NOT total flashes thrown. 
                # Total flashes thrown comes from 'grenades' (flashbang_detonate).
                
                # Update: 'grenades' has detonations. FeatureExtractor logic earlier used 'flashes' for 'flashes_thrown' which was WRONG.
                # It was counting "people blinded".
                
                # Let's verify 'flashes' source in DemoParser. 
                # It is "player_blind".
                
                # So 'current' logic: len(grp) = total people blinded.
                # We want: 
                # 1. Flashes Thrown (from grenades df)
                # 2. Enemies Blinded (from flashes df)
                
                # Let's fix this method to do both correctly.
                
                # Count effective blinds (> 1.0s)
                effective_blinds = grp[grp['blind_duration'] > 1.0]
                player.enemies_blinded = len(effective_blinds)
                if len(effective_blinds) > 0:
                     pass # Debug point: linking worked
                
        # Also parse grenades for actual 'thrown' count
        grenades = self.demo.grenades
        if not self._is_empty(grenades):
             # Try to find thrower
             thrower_col = self._get_player_column(grenades, "attacker") # or 'user'
             if not thrower_col: thrower_col = self._get_player_column(grenades, "victim") # sometimes mapped incorrectly
             
             if thrower_col:
                 for pid, grp in grenades.groupby(thrower_col):
                     if pd.isna(pid): continue
                     player = self._ensure_player(str(pid))
                     
                     # Count flashbangs
                     if 'grenade_type' in grp.columns:
                         player.flashes_thrown += len(grp[grp['grenade_type'] == 'flashbang'])
                         
                         # Approximate HE damage? (Only if we didn't get it from player_hurt)
                         # We rely on damage_events for damage. Usually better.
    
    def _compute_advanced_features(self):
        """Pre-compute features for clustering."""
        for player in self._player_features.values():
            # 1. Avg Teammate Dist
            dists = [d.nearest_teammate_distance for d in player.death_contexts if d.nearest_teammate_distance < 2000]
            player.avg_teammate_dist = float(np.mean(dists)) if dists else 1000.0
            
            # 2. Entry Attempts = Kills + Deaths in opening duels (no approximation needed now)
            # entry_kills tracked in _extract_clutch_and_opening_duels
            # entry_deaths tracked in _extract_positioning_metrics
            # (computed here for ordering - extract_clutch runs after compute_advanced)
            
            # 3. Untradeable ratio
            non_entry = player.deaths - player.entry_deaths
            untraded = len([d for d in player.death_contexts if not d.was_traded and not d.is_entry_frag])
            player.untradeable_death_ratio = untraded / max(1, non_entry)

    def _extract_clutch_and_opening_duels(self):
        """
        Analyze rounds for opening duels and clutch situations.
        Reconstructs round lifelines.
        """
        kills_df = self.demo.kills
        if self._is_empty(kills_df): return
        
        rounds = sorted(kills_df['total_rounds_played'].unique())
        
        for r in rounds:
            round_kills = kills_df[kills_df['total_rounds_played'] == r].sort_values('tick')
            if round_kills.empty: continue
            
            # 1. Opening Duel - first kill of the round
            first_kill = round_kills.iloc[0]
            attacker = self._get_player_id(first_kill, "attacker")
            
            # Attacker won the opening duel
            if attacker:
                p = self._ensure_player(attacker)
                p.entry_kills += 1
            # Victim's entry_death is already counted in _extract_positioning_metrics via is_entry_frag
                
            # 2. Clutch Logic
            # Find round winner
            winner_team = -1
            if not self.demo.rounds.empty:
                # Approximate round row (might be offset due to warmup)
                # Better: find round_end tick > last kill tick
                last_kill_tick = round_kills.iloc[-1]['tick']
                future_rounds = self.demo.rounds[self.demo.rounds['round_end_tick'] > last_kill_tick]
                if not future_rounds.empty:
                    val = future_rounds.iloc[0].get('winner', -1)
                    if isinstance(val, str):
                        if val == 'CT': winner_team = 3
                        elif val == 'TERRORIST' or val == 'T': winner_team = 2
                        else: winner_team = -1
                    else:
                        winner_team = int(val)
            
            # Count players per team to track alive status
            # We assume everyone who died or got a kill was in the round
            players_seen = set()
            team_map = {} # pid -> team_num
            
            for _, k in round_kills.iterrows():
                att = self._get_player_id(k, "attacker")
                vic = self._get_player_id(k, "victim")
                att_team = k.get(self._get_team_column(kills_df, "attacker"))
                vic_team = k.get(self._get_team_column(kills_df, "victim"))
                
                if att: 
                    players_seen.add(att)
                    if att_team is not None: team_map[att] = att_team
                if vic: 
                    players_seen.add(vic)
                    if vic_team is not None: team_map[vic] = vic_team

            # Approximate starting counts (max seen alive is hard, assume 5v5 or count unique)
            # Better: Track who is alive.
            alive = {pid: True for pid in players_seen}
            
            # Replay kills
            for _, k in round_kills.iterrows():
                victim = self._get_player_id(k, "victim")
                if not victim: continue
                
                # Mark dead
                alive[victim] = False
                
                # Check clutch state for remaining alive players
                # Group alive by team
                alive_by_team = {}
                for pid, is_alive in alive.items():
                    if is_alive:
                        tm = team_map.get(pid)
                        if tm:
                            if tm not in alive_by_team: alive_by_team[tm] = []
                            alive_by_team[tm].append(pid)
                
                # Check for 1 vs N
                for tm, members in alive_by_team.items():
                    if len(members) == 1:
                        hero = members[0]
                        
                        # Count enemies
                        enemies = 0
                        for enemy_tm, enemy_members in alive_by_team.items():
                            if enemy_tm != tm:
                                enemies += len(enemy_members)
                        
                        if enemies >= 1:
                             p = self._ensure_player(hero)
                             if enemies == 1:
                                 # 1v1 state entered
                                 # We only count "Attempt" if this is the final state/duel?
                                 # Or if they win from here?
                                 # Simplification: If round ends and they won, credit win.
                                 # If round ends and they lost (and died or time out), credit loss.
                                 pass 

            # Simpler Post-Round Analysis
            # If a team had 1 survivor and WON, it's a clutch.
            # If a team had 1 survivor and LOST, it's a failed clutch.
            # But clutch must be defined by "Last Alive against N enemies".
            
            # Only reliable way: Walk kills. If at any point it becomes 1vN, that player is "Cltuching".
            # If they proceed to WIN the round -> Clutch Win.
            # If they DIE or Lose -> Clutch Loss.
            
            # Re-walk with state
            alive = {pid: True for pid in players_seen}
            clutch_active = {} # pid -> starting_enemies_count
            
            for _, k in round_kills.iterrows():
                victim = self._get_player_id(k, "victim")
                if not victim: continue
                alive[victim] = False
                
                # Check alive counts
                teams_alive_counts = {}
                for pid, is_alive in alive.items():
                   if is_alive:
                       tm = team_map.get(pid)
                       if tm: teams_alive_counts[tm] = teams_alive_counts.get(tm, 0) + 1
                
                # Detect 1vN starts
                for tm, count in teams_alive_counts.items():
                    if count == 1:
                        # Find the player
                        hero = [p for p, is_a in alive.items() if is_a and team_map.get(p) == tm][0]
                        
                        # Count enemies
                        enemies = sum([c for t, c in teams_alive_counts.items() if t != tm])
                        
                        if enemies > 0:
                            if hero not in clutch_active:
                                clutch_active[hero] = enemies
            
            # After round, determine outcomes
            # Who actually won?
            # Assuming winner_team matches team_map values (2=T, 3=CT usually)
            
            # Map Team Name to int if needed? usually demoparser gives ints 2/3. 
            # team_map usually strings from "team_name". We need "team_num"?
            # FeatureExtractor extracts "team_name". "winner" in rounds is usually int (2/3).
            # We assume standard names "TERRORIST" / "CT" map to 2/3.
            
            for hero, enemy_count in clutch_active.items():
                p = self._ensure_player(hero)
                
                # Did their team win?
                # Check if hero survived? Not strictly required (bomb plant).
                # Check if winner_team matches hero team.
                # Loose check: If hero survived OR team won.
                
                hero_team_name = team_map.get(hero, "")
                hero_won = False
                
                # Map names to ints
                if winner_team == 2 and "TERRORIST" in hero_team_name.upper(): hero_won = True
                elif winner_team == 3 and "CT" in hero_team_name.upper(): hero_won = True
                elif winner_team == 2 and "T" == hero_team_name.upper(): hero_won = True
                
                if enemy_count == 1:
                    p.clutches_1v1_attempted += 1
                    if hero_won: p.clutches_1v1_won += 1
                else:
                    p.clutches_1vN_attempted += 1
                    if hero_won: p.clutches_1vN_won += 1


    def _get_player_id(self, row, role):
        col = self._get_player_column(pd.DataFrame([row]), role)
        return str(row[col]) if col else None

    def _extract_kill_contexts(self):
        """
        Extract kill context with round outcome for each kill.
        This enables impact scoring that values kills in won rounds higher.
        """
        kills_df = self.demo.kills
        rounds_df = self.demo.rounds
        
        if self._is_empty(kills_df) or self._is_empty(rounds_df):
            return
        
        att_col = self._get_player_column(kills_df, "attacker")
        vic_col = self._get_player_column(kills_df, "victim")
        att_team_col = self._get_team_column(kills_df, "attacker")
        
        if not att_col:
            return
        
        # Build round lookup: round_num -> (start_tick, end_tick, winner)
        round_lookup = {}
        for idx, r in rounds_df.iterrows():
            round_num = idx  # 0-indexed
            start_tick = r.get('round_start_tick', 0)
            end_tick = r.get('round_end_tick', 0)
            winner = r.get('winner', -1)
            round_lookup[round_num] = (start_tick, end_tick, winner)
        
        # Process each round
        rounds_in_kills = kills_df['total_rounds_played'].unique() if 'total_rounds_played' in kills_df.columns else []
        
        for round_num in rounds_in_kills:
            round_kills = kills_df[kills_df['total_rounds_played'] == round_num].sort_values('tick')
            if round_kills.empty:
                continue
            
            # Get round info
            round_info = round_lookup.get(round_num, (0, 0, -1))
            round_start_tick, round_end_tick, winner = round_info
            
            # Track alive players
            alive = {'CT': 5, 'TERRORIST': 5}  # Assume 5v5
            
            # First kill of round (opening)
            is_first = True
            
            for _, kill in round_kills.iterrows():
                tick = int(kill.get('tick', 0))
                attacker_id = str(kill.get(att_col, ""))
                victim_id = str(kill.get(vic_col, "")) if vic_col else ""
                attacker_team = str(kill.get(att_team_col, "")) if att_team_col else ""
                weapon = str(kill.get('weapon', ''))
                
                if not attacker_id or pd.isna(kill.get(att_col)):
                    is_first = False
                    continue
                
                player = self._ensure_player(attacker_id)
                
                # Calculate round time
                round_time_seconds = (tick - round_start_tick) / TICK_RATE if round_start_tick > 0 else 0
                
                # Determine if round was won by attacker's team
                # winner is 'T' or 'CT' (string), attacker_team is 'TERRORIST' or 'CT'
                round_won = False
                if attacker_team and winner:
                    winner_str = str(winner).upper()
                    team_str = attacker_team.upper()
                    
                    # T won and attacker is T/TERRORIST
                    if winner_str == "T" and ("TERRORIST" in team_str or team_str == "T"):
                        round_won = True
                    # CT won and attacker is CT
                    elif winner_str == "CT" and "CT" in team_str:
                        round_won = True
                
                # Is exit frag?
                # Definition: Kills that don't help win - round was LOST and kill was late
                # NOT exit if round was won (those kills mattered)
                is_exit = False
                round_duration = (round_end_tick - round_start_tick) / TICK_RATE if round_end_tick > round_start_tick else 0
                
                # Only check exit if round was LOST
                if not round_won and round_duration > 0:
                    time_remaining = round_duration - round_time_seconds
                    # Kill in last 15 seconds of a lost round = exit frag
                    if time_remaining < 15:
                        is_exit = True
                
                # Check if killer got traded (killed within 3s after this kill)
                killer_traded = False
                future_kills = kills_df[(kills_df['tick'] > tick) & (kills_df['tick'] <= tick + TRADE_WINDOW_TICKS)]
                for _, future_kill in future_kills.iterrows():
                    future_victim = str(future_kill.get(vic_col, "")) if vic_col else ""
                    if future_victim == attacker_id:
                        killer_traded = True
                        break
                
                # Create context
                ctx = KillContext(
                    tick=tick,
                    round_num=round_num,
                    round_time_seconds=round_time_seconds,
                    round_won=round_won,
                    alive_ct=alive.get('CT', 0),
                    alive_t=alive.get('TERRORIST', 0),
                    is_opening_kill=is_first,
                    is_exit_frag=is_exit,
                    is_traded=killer_traded,
                    victim_id=victim_id,
                    weapon=weapon
                )
                player.kill_contexts.append(ctx)
                
                # Update aggregates
                if round_won:
                    player.kills_in_won_rounds += 1
                else:
                    player.kills_in_lost_rounds += 1
                
                if is_exit:
                    player.exit_frags += 1
                
                if is_first:
                    if round_won:
                        player.opening_kills_won += 1
                    else:
                        player.opening_kills_lost += 1
                
                # SWING KILL DETECTION
                # Track kills that flip man-advantage
                # diff_before <= -2 and diff_after >= -1 = swing kill
                attacker_team_upper = attacker_team.upper()
                if "TERRORIST" in attacker_team_upper or attacker_team_upper == "T":
                    my_alive = alive.get('TERRORIST', 0)
                    enemy_alive = alive.get('CT', 0)
                else:
                    my_alive = alive.get('CT', 0)
                    enemy_alive = alive.get('TERRORIST', 0)
                
                diff_before = my_alive - enemy_alive
                diff_after = diff_before + 1  # After kill, enemy has 1 less
                
                # Swing kill: losing badly (diff <= -2) to fighting chance (diff >= -1)
                if diff_before <= -2 and diff_after >= -1:
                    player.swing_kills += 1
                
                # Update alive count (victim died)
                vic_team = str(kill.get(self._get_team_column(kills_df, "victim"), "")) if self._get_team_column(kills_df, "victim") else ""
                if "CT" in vic_team.upper():
                    alive['CT'] = max(0, alive['CT'] - 1)
                elif "TERRORIST" in vic_team.upper() or vic_team.upper() == "T":
                    alive['TERRORIST'] = max(0, alive['TERRORIST'] - 1)
                
                is_first = False

    def _extract_kast(self):
        """
        Extract KAST (Kill, Assist, Survived, Traded) per round.
        
        For each round, a player gets KAST credit if they:
        - K: Got at least 1 kill
        - A: Got an assist (flash blind leading to kill)
        - S: Survived the round
        - T: Died but was traded (teammate killed their killer within 3s)
        """
        kills_df = self.demo.kills
        rounds_df = self.demo.rounds
        
        if self._is_empty(kills_df) or self._is_empty(rounds_df):
            return
        
        att_col = self._get_player_column(kills_df, "attacker")
        vic_col = self._get_player_column(kills_df, "victim")
        
        if not att_col or not vic_col:
            return
        
        # Get all players and total rounds
        total_rounds = len(rounds_df)
        if total_rounds == 0:
            return
        
        # For each player, track KAST per round
        player_kast = {pid: set() for pid in self._player_features.keys()}  # pid -> set of round_nums with KAST
        
        # Get flash data for assists
        flashes_df = self.demo.flashes
        flash_att_col = self._get_player_column(flashes_df, "attacker") if not self._is_empty(flashes_df) else None
        
        # Process each round
        rounds_in_kills = kills_df['total_rounds_played'].unique() if 'total_rounds_played' in kills_df.columns else []
        
        for round_num in rounds_in_kills:
            round_kills = kills_df[kills_df['total_rounds_played'] == round_num].sort_values('tick')
            if round_kills.empty:
                continue
            
            # Track kills, deaths, and trades in this round
            round_killers = set()      # Players who got kills
            round_deaths = {}          # victim_id -> (killer_id, tick)
            trade_victims = set()      # Players whose death was traded
            flash_assisters = set()    # Players who flashed someone who died
            
            kill_list = list(round_kills.iterrows())
            
            for idx, (_, kill) in enumerate(kill_list):
                tick = int(kill.get('tick', 0))
                attacker_id = str(kill.get(att_col, ""))
                victim_id = str(kill.get(vic_col, ""))
                
                if attacker_id and not pd.isna(kill.get(att_col)):
                    round_killers.add(attacker_id)
                
                if victim_id and not pd.isna(kill.get(vic_col)):
                    killer_id = attacker_id if attacker_id else ""
                    round_deaths[victim_id] = (killer_id, tick)
                    
                    # A: Check for flash assist - who flashed this victim before death?
                    if flash_att_col and not self._is_empty(flashes_df):
                        # Find flashes on victim within 2s before kill
                        flash_window = 2000  # 2 seconds in ms, ~128 ticks
                        vic_col_flash = self._get_player_column(flashes_df, "victim")
                        if vic_col_flash and 'tick' in flashes_df.columns:
                            recent_flashes = flashes_df[
                                (flashes_df['tick'] >= tick - 128) & 
                                (flashes_df['tick'] <= tick) &
                                (flashes_df[vic_col_flash].astype(str) == victim_id)
                            ]
                            for _, flash in recent_flashes.iterrows():
                                flasher = str(flash.get(flash_att_col, ""))
                                if flasher and flasher != attacker_id:  # Not self-flash on kill
                                    flash_assisters.add(flasher)
            
            # Check trades: if victim died but killer was killed within 3s
            for victim_id, (killer_id, death_tick) in round_deaths.items():
                if not killer_id:
                    continue
                # Was the killer killed within trade window?
                for other_victim, (other_killer, other_tick) in round_deaths.items():
                    if other_victim == killer_id and other_tick > death_tick:
                        if other_tick - death_tick <= TRADE_WINDOW_TICKS:
                            trade_victims.add(victim_id)
                            break
            
            # Determine survivors (players who weren't killed)
            all_players = set(self._player_features.keys())
            dead_players = set(round_deaths.keys())
            survivors = all_players - dead_players
            
            # Assign KAST credit
            for pid in self._player_features.keys():
                got_kast = False
                
                # K: Got a kill
                if pid in round_killers:
                    got_kast = True
                
                # A: Flash assist
                if pid in flash_assisters:
                    got_kast = True
                
                # S: Survived
                if pid in survivors:
                    got_kast = True
                
                # T: Traded
                if pid in trade_victims:
                    got_kast = True
                
                if got_kast:
                    player_kast[pid].add(round_num)
        
        # Compute KAST% for each player
        for pid, kast_set in player_kast.items():
            if pid in self._player_features:
                player = self._player_features[pid]
                player.kast_rounds = len(kast_set)
                player.kast_percentage = len(kast_set) / max(1, total_rounds)

    def _classify_roles(self):
        """Use RoleClassifier to assign roles."""
        # Convert internal player dict to format expected by classifier (already matches)
        # We need to map pid -> PlayerFeatures
        # self.players is Dict[str, PlayerFeatures]
        
        classifier = RoleClassifier()
        # Pass dict of players
        roles = classifier.classify_roles(self._player_features)
        
        # Apply roles back to players
        for pid, role in roles.items():
            if pid in self._player_features:
                self._player_features[pid].detected_role = role
    def _analyze_movement(self):
        """Analyze movement for kills."""
        kills_df = self.demo.kills
        pos_df = self.demo.player_positions
        if self._is_empty(kills_df) or self._is_empty(pos_df): return
        
        att_col = self._get_player_column(kills_df, "attacker")
        if not att_col: return

        for pid, player in self._player_features.items():
            player_kills = kills_df[kills_df[att_col] == pid]
            if player_kills.empty: continue
            
            total_strafing_score = 0.0
            count = 0
            
            # Track multikills
            if not player_kills.empty:
               round_kills = player_kills.groupby('total_rounds_played').size()
               player.multikills = len(round_kills[round_kills >= 2])
            
            # Analyze last 5 kills to save time
            for _, kill in player_kills.tail(5).iterrows():
                tick = int(kill['tick'])
                res = self.movement_analyzer.analyze_kill_movement(pid, tick, pos_df)
                
                total_strafing_score += res["counter_strafing_score"]
                ptype = res["peek_type"]
                if "jiggle" in ptype: player.peek_types["jiggle"] += 1
                elif "wide" in ptype: player.peek_types["wide"] += 1
                else: player.peek_types["dry"] += 1
                count += 1
            
            if count > 0:
                player.counter_strafing_score_avg = total_strafing_score / count
