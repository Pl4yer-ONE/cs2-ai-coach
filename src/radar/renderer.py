"""
Radar Frame Renderer
Renders player positions on map radar as PNG frames.
"""

import os
from pathlib import Path
from typing import List, Optional
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from PIL import Image


from src.radar.extractor import TickFrame, PlayerFrame, SmokeFrame, FlashFrame, KillFrame
from src.visualization.map_coords import world_to_radar, load_map_registry


# Colors
CT_COLOR = '#5C7AEA'      # Blue
T_COLOR = '#E94560'       # Red  
BOMB_COLOR = '#FFD93D'    # Yellow
SMOKE_COLOR = '#AAAAAA'   # Gray
FLASH_COLOR = '#FFFFFF'   # White flash
KILL_COLOR = '#FF0000'    # Red for kill marker
DEAD_ALPHA = 0.25
ALIVE_ALPHA = 0.9
SMOKE_RADIUS = 30         # Radar pixels (~144 units in-game)
FLASH_RADIUS = 40         # Flash effect radius


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
        
        # Load map config
        self._registry = load_map_registry()
        self.map_config = self._registry.get(map_name)
        
        # Load map image
        self.map_image = self._load_map_image()
        
    def _load_map_image(self) -> Optional[Image.Image]:
        """Load radar map image."""
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
        fig, ax = plt.subplots(figsize=(10.24, 10.24), dpi=100)
        fig.patch.set_facecolor('#1a1a2e')
        
        # Draw map background
        if self.map_image:
            ax.imshow(self.map_image, extent=[0, self.resolution, self.resolution, 0], zorder=1)
        else:
            ax.set_facecolor('#16213e')
        
        # Draw smokes first (below players)
        for smoke in frame.smokes:
            self._draw_smoke(ax, smoke, frame.tick)
        
        # Draw flashes (bright circle effect)
        for flash in frame.flashes:
            self._draw_flash(ax, flash, frame.tick)
        
        # Draw kills (skull markers)
        for kill in frame.kills:
            self._draw_kill(ax, kill, frame.tick)
        
        # Draw players
        for player in frame.players:
            self._draw_player(ax, player)
        
        # Draw bomb
        if frame.bomb_x is not None and frame.bomb_y is not None:
            bx, by = world_to_radar(
                np.array([frame.bomb_x]),
                np.array([frame.bomb_y]),
                self.map_config,
                self.resolution
            )
            ax.scatter(bx, by, c=BOMB_COLOR, s=self.player_size * 8, 
                      marker='s', zorder=10, edgecolors='black', linewidth=1)
        
        # Clean up axes
        ax.set_xlim(0, self.resolution)
        ax.set_ylim(self.resolution, 0)  # Flip Y
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
        
        # Save frame
        frame_path = self.output_dir / f"frame_{frame_num:05d}.png"
        plt.savefig(frame_path, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='#1a1a2e')
        plt.close(fig)
        
        return str(frame_path)
    
    def _draw_player(self, ax, player: PlayerFrame):
        """Draw a single player on the map."""
        # Convert world coords to radar coords
        px, py = world_to_radar(
            np.array([player.x]),
            np.array([player.y]),
            self.map_config,
            self.resolution
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
        sx, sy = world_to_radar(
            np.array([smoke.x]),
            np.array([smoke.y]),
            self.map_config,
            self.resolution
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
        fx, fy = world_to_radar(
            np.array([flash.x]),
            np.array([flash.y]),
            self.map_config,
            self.resolution
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
        kx, ky = world_to_radar(
            np.array([kill.x]),
            np.array([kill.y]),
            self.map_config,
            self.resolution
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
