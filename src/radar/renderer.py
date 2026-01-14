# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3.

"""
Radar Frame Renderer
Renders player positions on map radar as PNG frames.
Uses boltobserv radar images (GPL-3) from https://github.com/boltgolt/boltobserv
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image



from src.radar.extractor import TickFrame, PlayerFrame, SmokeFrame, FlashFrame, KillFrame, GrenadeFrame
from src.visualization.map_coords import world_to_radar, load_map_registry


# Boltobserv config cache
_boltobserv_config: Optional[Dict] = None


def load_boltobserv_config() -> Dict:
    """Load boltobserv map coordinate configs."""
    global _boltobserv_config
    if _boltobserv_config is None:
        config_path = Path(__file__).parent / "boltobserv_maps" / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                _boltobserv_config = json.load(f)
        else:
            _boltobserv_config = {}
    return _boltobserv_config


def boltobserv_to_radar(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    map_name: str,
    img_size: int = 1024
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert CS2 world coordinates to radar pixels using boltobserv formula.
    
    Boltobserv formula:
        px = (world_x + offset_x) / resolution
        py = (offset_y - world_y) / resolution  # Y is inverted
    
    Returns pixel coordinates for the 1024x1024 boltobserv radar.
    """
    config = load_boltobserv_config()
    map_cfg = config.get(map_name, {})
    
    if not map_cfg:
        # Fallback to zeros if no config
        return np.zeros_like(x), np.zeros_like(y)
    
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    
    offset_x = map_cfg.get("offset_x", 0)
    offset_y = map_cfg.get("offset_y", 0)
    resolution = map_cfg.get("resolution", 1.0)  # Units per pixel
    
    # Boltobserv coordinate transform
    # Y is inverted (positive Y goes up in-game, down on radar)
    pixel_x = (x + offset_x) / resolution
    pixel_y = (offset_y - y) / resolution
    
    # Scale if radar image is not 1024
    if img_size != 1024:
        scale = img_size / 1024.0
        pixel_x *= scale
        pixel_y *= scale
    
    return pixel_x, pixel_y


# Colors
CT_COLOR = '#5C7AEA'      # Blue
T_COLOR = '#E94560'       # Red  
BOMB_COLOR = '#FFD93D'    # Yellow
SMOKE_COLOR = '#AAAAAA'   # Gray
FLASH_COLOR = '#FFFFFF'   # White flash
KILL_COLOR = '#FF0000'    # Red for kill marker
HE_COLOR = '#FF8C00'      # Orange for HE grenade
MOLLY_COLOR = '#FF4500'   # Fire red for molotov
TRAIL_ALPHA = 0.3         # Faded trail
DEAD_ALPHA = 0.25
ALIVE_ALPHA = 0.9
SMOKE_RADIUS = 30         # Radar pixels (~144 units in-game)
FLASH_RADIUS = 40         # Flash effect radius
HE_RADIUS = 25            # HE grenade explosion
MOLLY_RADIUS = 20         # Molotov fire area


class RadarRenderer:
    """Renders radar frames from tick data."""
    
    def __init__(
        self,
        map_name: str,
        output_dir: str = "tmp_frames",
        resolution: int = 1024,
        player_size: int = 12,
        show_names: bool = False
    ):
        self.map_name = map_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resolution = resolution
        self.player_size = player_size
        self.show_names = show_names
        
        # Check if boltobserv map is available
        boltobserv_config = load_boltobserv_config()
        self.use_boltobserv = map_name in boltobserv_config
        
        # Load map config (fallback for non-boltobserv)
        self._registry = load_map_registry()
        self.map_config = self._registry.get(map_name)
        
        # Load map image
        self.map_image = self._load_map_image()
    
    def _convert_coords(
        self,
        x: Union[float, np.ndarray],
        y: Union[float, np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert world coordinates to radar pixels using appropriate method."""
        if self.use_boltobserv:
            return boltobserv_to_radar(x, y, self.map_name, self.resolution)
        else:
            return world_to_radar(
                np.asarray(x), np.asarray(y), 
                self.map_config, self.resolution
            )
        
    def _load_map_image(self) -> Optional[Image.Image]:
        """Load radar map image. Prioritizes boltobserv assets (GPL-3)."""
        # First: check boltobserv maps (GPL-3 licensed from https://github.com/boltgolt/boltobserv)
        boltobserv_dir = Path(__file__).parent / "boltobserv_maps"
        boltobserv_path = boltobserv_dir / f"{self.map_name}.png"
        
        if boltobserv_path.exists():
            img = Image.open(boltobserv_path).convert("RGBA")
            if img.size != (self.resolution, self.resolution):
                img = img.resize((self.resolution, self.resolution), Image.Resampling.LANCZOS)
            return img
        
        # Fallback: original assets
        assets_dir = Path(__file__).parent.parent.parent / "assets" / "maps"
        for name in [f"{self.map_name}_radar.png", f"{self.map_name}.png"]:
            path = assets_dir / name
            if path.exists():
                img = Image.open(path).convert("RGBA")
                if img.size != (self.resolution, self.resolution):
                    img = img.resize((self.resolution, self.resolution), Image.Resampling.LANCZOS)
                return img
        
        print(f"  ⚠️ No radar image for {self.map_name}")
        return None
    
    def render_frame(self, frame: TickFrame, frame_num: int) -> str:
        """
        Render a single frame.
        
        Returns:
            Path to saved frame PNG
        """
        # Use resolution-based figsize for pixel-perfect output
        dpi = 100
        fig_size = self.resolution / dpi
        fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=dpi)
        fig.patch.set_facecolor('#1a1a2e')
        
        # Remove all margins for exact pixel alignment
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Draw map background with exact extent matching axes
        if self.map_image:
            ax.imshow(self.map_image, extent=[0, self.resolution, self.resolution, 0], 
                     zorder=1, aspect='equal')
        else:
            ax.set_facecolor('#16213e')
        
        # Draw smokes first (below players)
        for smoke in frame.smokes:
            self._draw_smoke(ax, smoke, frame.tick)
        
        # Draw grenades (HE and molotov)
        for grenade in frame.grenades:
            self._draw_grenade(ax, grenade, frame.tick)
        
        # Draw flashes (bright circle effect)
        for flash in frame.flashes:
            self._draw_flash(ax, flash, frame.tick)
        
        # Draw kills (skull markers)
        for kill in frame.kills:
            self._draw_kill(ax, kill, frame.tick)
        
        # Draw player trails (movement history)
        for player in frame.players:
            if player.steam_id in frame.trail_positions:
                self._draw_trail(ax, player, frame.trail_positions[player.steam_id])
        
        # Draw players
        for player in frame.players:
            self._draw_player(ax, player)
        
        # Draw bomb
        if frame.bomb_x is not None and frame.bomb_y is not None:
            bx, by = self._convert_coords(
                np.array([frame.bomb_x]),
                np.array([frame.bomb_y])
            )
            ax.scatter(bx, by, c=BOMB_COLOR, s=self.player_size * 8, 
                      marker='s', zorder=10, edgecolors='black', linewidth=1)
        
        # Set exact axes limits for alignment
        ax.set_xlim(0, self.resolution)
        ax.set_ylim(self.resolution, 0)  # Flip Y
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        
        # Add tick counter
        ax.text(
            0.02, 0.98, f"Tick: {frame.tick}",
            transform=ax.transAxes, color='white', fontsize=8,
            verticalalignment='top',
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=2)
        )
        
        # Add player count
        ct_alive = sum(1 for p in frame.players if p.team == 'CT' and p.alive)
        t_alive = sum(1 for p in frame.players if p.team == 'T' and p.alive)
        ax.text(
            0.98, 0.98, f"CT {ct_alive} - {t_alive} T",
            transform=ax.transAxes, color='white', fontsize=10,
            horizontalalignment='right', verticalalignment='top',
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=2)
        )
        
        # Save frame - NO bbox_inches to maintain exact pixel alignment
        frame_path = self.output_dir / f"frame_{frame_num:05d}.png"
        plt.savefig(frame_path, dpi=dpi, facecolor='#1a1a2e', 
                   pad_inches=0, bbox_inches=None)
        plt.close(fig)
        
        return str(frame_path)
    
    def _draw_player(self, ax, player: PlayerFrame):
        """Draw a single player on the map."""
        # Convert world coords to radar coords
        px, py = self._convert_coords(
            np.array([player.x]),
            np.array([player.y])
        )
        
        if len(px) == 0 or len(py) == 0:
            return
            
        px, py = px[0], py[0]
        
        # Skip if out of bounds
        if px < 0 or px > self.resolution or py < 0 or py > self.resolution:
            return
        
        # Color and alpha
        color = CT_COLOR if player.team == 'CT' else T_COLOR
        alpha = ALIVE_ALPHA if player.alive else DEAD_ALPHA
        
        # Draw player dot
        ax.scatter(
            px, py,
            c=color,
            s=self.player_size ** 2,
            alpha=alpha,
            zorder=5,
            edgecolors='white' if player.alive else 'gray',
            linewidth=1
        )
        
        # Draw X for dead players
        if not player.alive:
            ax.scatter(px, py, marker='x', c='white', s=self.player_size, alpha=0.5, zorder=6)
        
        # Draw name
        if self.show_names and player.alive:
            ax.text(
                px, py - 15,
                player.name[:10],
                color='white', fontsize=6,
                ha='center', va='bottom',
                alpha=0.8
            )
    
    def _draw_smoke(self, ax, smoke: SmokeFrame, current_tick: int):
        """Draw a smoke grenade circle on the map."""
        # Convert world coords to radar coords
        sx, sy = self._convert_coords(
            np.array([smoke.x]),
            np.array([smoke.y])
        )
        
        if len(sx) == 0 or len(sy) == 0:
            return
            
        sx, sy = sx[0], sy[0]
        
        # Skip if out of bounds
        if sx < 0 or sx > self.resolution or sy < 0 or sy > self.resolution:
            return
        
        # Calculate smoke age and fade
        age = current_tick - smoke.tick_start
        remaining = smoke.duration_ticks - age
        
        # Fade out in last 20% of duration
        fade_start = smoke.duration_ticks * 0.8
        if remaining < fade_start:
            alpha = max(0.1, 0.5 * (remaining / fade_start))
        else:
            alpha = 0.5
        
        # Draw smoke circle
        circle = Circle(
            (sx, sy), 
            SMOKE_RADIUS,
            facecolor=SMOKE_COLOR,
            edgecolor='#888888',
            alpha=alpha,
            linewidth=1,
            zorder=3
        )
        ax.add_patch(circle)
    
    def _draw_flash(self, ax, flash: FlashFrame, current_tick: int):
        """Draw a flash grenade effect (white circle)."""
        fx, fy = self._convert_coords(
            np.array([flash.x]),
            np.array([flash.y])
        )
        
        if len(fx) == 0 or len(fy) == 0:
            return
        fx, fy = fx[0], fy[0]
        
        if fx < 0 or fx > self.resolution or fy < 0 or fy > self.resolution:
            return
        
        # Fade out quickly
        age = current_tick - flash.tick
        alpha = max(0.1, 0.6 * (1 - age / flash.duration_ticks))
        
        # Draw flash circle
        circle = Circle(
            (fx, fy), 
            FLASH_RADIUS,
            facecolor=FLASH_COLOR,
            edgecolor='#FFFF00',
            alpha=alpha,
            linewidth=2,
            zorder=4
        )
        ax.add_patch(circle)
    
    def _draw_kill(self, ax, kill: KillFrame, current_tick: int):
        """Draw a kill marker (skull/X at death location)."""
        kx, ky = self._convert_coords(
            np.array([kill.x]),
            np.array([kill.y])
        )
        
        if len(kx) == 0 or len(ky) == 0:
            return
        kx, ky = kx[0], ky[0]
        
        if kx < 0 or kx > self.resolution or ky < 0 or ky > self.resolution:
            return
        
        # Fade out over duration
        age = current_tick - kill.tick
        alpha = max(0.2, 1.0 * (1 - age / kill.duration_ticks))
        
        # Color based on who got the kill (CT kill = blue X, T kill = red X)
        color = CT_COLOR if kill.attacker_team == 'CT' else T_COLOR
        
        # Draw skull marker (X with circle)
        ax.scatter(kx, ky, marker='x', c=color, s=150, alpha=alpha, linewidth=3, zorder=8)
        ax.scatter(kx, ky, marker='o', c='white', s=80, alpha=alpha * 0.3, zorder=7)
    
    def _draw_grenade(self, ax, grenade: GrenadeFrame, current_tick: int):
        """Draw an HE grenade or molotov."""
        gx, gy = self._convert_coords(
            np.array([grenade.x]),
            np.array([grenade.y])
        )
        
        if len(gx) == 0 or len(gy) == 0:
            return
        gx, gy = gx[0], gy[0]
        
        if gx < 0 or gx > self.resolution or gy < 0 or gy > self.resolution:
            return
        
        # Fade out
        age = current_tick - grenade.tick
        alpha = max(0.1, 0.7 * (1 - age / grenade.duration_ticks))
        
        # Color and radius based on type
        if grenade.grenade_type == 'he':
            color = HE_COLOR
            radius = HE_RADIUS
            edge = '#FFD700'  # Gold edge
        else:  # molotov
            color = MOLLY_COLOR
            radius = MOLLY_RADIUS
            edge = '#FF0000'  # Red edge
        
        circle = Circle(
            (gx, gy), 
            radius,
            facecolor=color,
            edgecolor=edge,
            alpha=alpha,
            linewidth=2,
            zorder=4
        )
        ax.add_patch(circle)
    
    def _draw_trail(self, ax, player: PlayerFrame, positions: list):
        """Draw player movement trail."""
        if len(positions) < 2:
            return
        
        # Convert all positions to radar coords
        radar_positions = []
        for wx, wy in positions:
            rx, ry = self._convert_coords(
                np.array([wx]),
                np.array([wy])
            )
            if len(rx) > 0 and len(ry) > 0:
                radar_positions.append((rx[0], ry[0]))
        
        if len(radar_positions) < 2:
            return
        
        # Color based on team
        color = CT_COLOR if player.team == 'CT' else T_COLOR
        
        # Draw trail as fading line
        for i in range(len(radar_positions) - 1):
            x1, y1 = radar_positions[i]
            x2, y2 = radar_positions[i + 1]
            
            # Fade older positions
            alpha = TRAIL_ALPHA * (i + 1) / len(radar_positions)
            
            ax.plot([x1, x2], [y1, y2], color=color, alpha=alpha, linewidth=2, zorder=2)
    
    def render_all(self, frames: List[TickFrame], progress_interval: int = 100) -> List[str]:
        """
        Render all frames.
        
        Returns:
            List of frame file paths
        """
        paths = []
        total = len(frames)
        
        for i, frame in enumerate(frames):
            path = self.render_frame(frame, i)
            paths.append(path)
            
            if (i + 1) % progress_interval == 0:
                print(f"    Rendered {i + 1}/{total} frames...")
        
        print(f"  ✅ Rendered {total} frames")
        return paths
    
    def cleanup(self):
        """Remove frame files after video encoding."""
        import shutil
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
