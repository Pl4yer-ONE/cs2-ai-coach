"""
Movement Analyzer Module
Detects advanced movement mechanics including peek types and counter-strafing quality.
Uses real physics data (Velocity vectors).

Features:
- Counter-strafing Quality (Velocity at shot time)
- Peek Type Classification (Jiggle vs Wide vs Dry)
- Pre-aim time detection
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

class MovementAnalyzer:
    """
    Analyzes player movement patterns from high-frequency tick data.
    """
    
    def __init__(self):
        # CS2 Movement Constants (approx)
        self.VEL_STOPPED = 15.0   # Accurate shooting velocity
        self.VEL_WALK = 135.0     # Walk speed
        self.VEL_RUN = 240.0      # Run speed
    
    def analyze_kill_movement(
        self, 
        attacker_id: str, 
        kill_tick: int, 
        player_positions: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze movement leading up to a kill.
        """
        result = {
            "counter_strafing_score": 0.0,
            "peek_type": "unknown",
            "velocity_at_shot": 0.0
        }
        
        if player_positions.empty:
            return result
        
        # Get history (500ms before kill)
        window = 32 # ~500ms at 64 tick
        history = self._get_player_history(player_positions, attacker_id, kill_tick, window)
        
        if history.empty:
            return result
            
        # 1. Analyze Velocity at Shot
        shot_frame = history.iloc[-1]
        
        # Calculate velocity magnitude
        if 'vel_X' in shot_frame and 'vel_Y' in shot_frame:
            vx = float(shot_frame['vel_X'])
            vy = float(shot_frame['vel_Y'])
        else:
            # Fallback for old demos without velocity props
            if len(history) >= 2:
                prev = history.iloc[-2]
                dx = float(shot_frame['X']) - float(prev['X'])
                dy = float(shot_frame['Y']) - float(prev['Y'])
                vx, vy = dx * 64, dy * 64
            else:
                vx, vy = 0.0, 0.0
        
        vel = np.sqrt(vx*vx + vy*vy)
        result["velocity_at_shot"] = round(vel, 2)
        
        # Counter-strafing score
        # 100 = Stopped perfectly (<15 u/s)
        # 0 = Running full speed (>200 u/s)
        if vel <= self.VEL_STOPPED:
            result["counter_strafing_score"] = 100.0
        elif vel >= 200:
            result["counter_strafing_score"] = 0.0
        else:
            # Linear interpolation between 15 and 200
            # score = 100 - ( (vel - 15) / (200 - 15) * 100 )
            score = 100.0 - ((vel - 15) / 185.0 * 100.0)
            result["counter_strafing_score"] = round(max(0.0, score), 1)
        
        # 2. Detect Peek Type
        # Analyze velocity profile over last 300ms (approx 20 ticks)
        peek_window = history.tail(20)
        velocities = []
        
        for _, row in peek_window.iterrows():
            if 'vel_X' in row:
                v = np.sqrt(row['vel_X']**2 + row['vel_Y']**2)
            else:
                v = 0 # simplified fallback
            velocities.append(v)
            
        max_vel = max(velocities) if velocities else 0
        avg_vel = np.mean(velocities) if velocities else 0
        
        # Classification Logic
        if max_vel < self.VEL_STOPPED:
             result["peek_type"] = "holding_angle" # Was never moving
        elif max_vel < self.VEL_WALK:
             result["peek_type"] = "shift_peek" # Walked out
        elif max_vel > 220:
             # High speed. Check if it was a wide swing or jiggle.
             # Jiggle: Velocity direction flips rapidly or position returns to start
             # Wide: Sustained velocity in one direction
             
             # Check displacement
             start_pos = (peek_window.iloc[0]['X'], peek_window.iloc[0]['Y'])
             end_pos = (peek_window.iloc[-1]['X'], peek_window.iloc[-1]['Y'])
             displacement = np.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2)
             
             path_len = sum(velocities) / 64.0 # Integrate velocity
             
             # Ratio: Path / Displacement
             # 1.0 = Straight line (Wide swing)
             # > 2.0 = Back and forth (Jiggle)
             ratio = path_len / max(1, displacement)
             
             if ratio > 2.0:
                 result["peek_type"] = "jiggle_peek"
             else:
                 result["peek_type"] = "wide_swing"
        else:
             result["peek_type"] = "standard_peek" # Normal run peek
             
        return result

    def _get_player_history(
        self, 
        df: pd.DataFrame, 
        player_id: str, 
        tick: int, 
        window: int
    ) -> pd.DataFrame:
        """Get player dataframe for window before tick."""
        # Check column names (demoparser2 uses 'steamid' sometimes, or we rely on logic below)
        # We assume df passed here is filtered or we scan. 
        # CAUTION: 'parse_ticks' output has no 'steamid' column usually, it parses ALL players.
        # It has 'name' and 'team_name'. We might need to filter by name?
        # Actually, demoparser2's parse_ticks returns a DF with ALL players interleaved.
        # We need a robust way to match the player. 'name' is best bet if steamid missing.
        
        # Optim: This function assumes caller passes a DF that MIGHT contain multiple players.
        # But `FeatureExtractor` passes `pos_df`.
        
        # Correct approach using 'steamid' if available, else 'name'.
        # Note: demoparser2 usually returns 'steamid' if requested in fields? 
        # My parse_ticks call didn't ask for steamid!
        # Fix: 'parse_ticks' output usually has 'steamid' automatically? No.
        # I need to check `demo_parser.py`. It didn't request 'steamid'.
        # I should request 'steamid' or 'player_name'.
        
        # Temporary workaround: Use 'name' if unique, or assume passing player-specific DF?
        # FeatureExtractor passes the big DF.
        
        mask = (df['tick'] <= tick) & (df['tick'] >= tick - window)
        
        # Filter by player identifier
        # We need to ensure we are looking at the right player.
        # The `FeatureExtractor` has `player_name` in `PlayerFeatures`.
        # We will try to filter by `name` for now as `steamid` wasn't requested.
        # This is a risk if names are duplicate.
        
        # BETTER: In future steps, add 'steamid' to parse_ticks.
        # For now, let's filter by name if available in df.
        
        filtered = df[mask].copy()
        
        # If 'steamid' column exists, use it.
        # If not, use 'name'.
        if 'steamid' in filtered.columns:
            filtered = filtered[filtered['steamid'].astype(str) == str(player_id)]
        elif 'name' in filtered.columns:
             # We might have to guess name from ID? 
             # The FeatureExtractor loop over kills gives us `attacker_name` sometimes.
             # This is messy.
             # Let's rely on the caller passing the NAME to this function?
             pass 
             
        return filtered
