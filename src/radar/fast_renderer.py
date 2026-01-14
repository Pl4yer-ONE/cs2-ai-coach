# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3.

"""
Fast Radar Renderer using PIL instead of matplotlib.
Target: <60s for full demo (vs 338s with matplotlib).
"""

from pathlib import Path
from typing import Union, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.radar.extractor import TickFrame, PlayerFrame, SmokeFrame, FlashFrame, GrenadeFrame, KillFrame
from src.radar.renderer import load_boltobserv_config, boltobserv_to_radar, load_map_registry, world_to_radar


# Colors (RGB tuples for PIL)
CT_COLOR = (74, 144, 217)      # #4A90D9
CT_COLOR_DEAD = (43, 82, 120)  # #2B5278
T_COLOR = (217, 164, 65)       # #D9A441
T_COLOR_DEAD = (120, 93, 43)   # #785D2B
SMOKE_COLOR = (180, 180, 180, 120)  # Gray with alpha
FLASH_COLOR = (255, 255, 200, 150)  # Yellow-white
MOLLY_COLOR = (255, 100, 0, 150)    # Orange fire
HE_COLOR = (255, 200, 0, 200)       # Yellow explosion
KILL_COLOR = (255, 0, 0)            # Red skull
BOMB_COLOR = (255, 165, 0)          # Orange bomb


class FastRadarRenderer:
    """
    High-speed radar renderer using PIL.
    10-20x faster than matplotlib version.
    """
    
    def __init__(
        self,
        map_name: str,
        output_dir: str = "tmp_frames",
        resolution: int = 1024,
        player_size: int = 18
    ):
        self.map_name = map_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resolution = resolution
        self.player_size = player_size
        
        # Check boltobserv availability
        boltobserv_config = load_boltobserv_config()
        self.use_boltobserv = map_name in boltobserv_config
        
        # Load map config
        self._registry = load_map_registry()
        self.map_config = self._registry.get(map_name)
        
        # Load and cache map background
        self.map_image = self._load_map_image()
        
        # Try to load font, fallback to default
        try:
            self._font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
            self._font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 9)
        except:
            self._font = ImageFont.load_default()
            self._font_small = self._font
    
    def _load_map_image(self) -> Image.Image:
        """Load radar map background."""
        boltobserv_dir = Path(__file__).parent / "boltobserv_maps"
        boltobserv_path = boltobserv_dir / f"{self.map_name}.png"
        
        if boltobserv_path.exists():
            img = Image.open(boltobserv_path).convert("RGBA")
            if img.size != (self.resolution, self.resolution):
                img = img.resize((self.resolution, self.resolution), Image.Resampling.LANCZOS)
            return img
        
        # Fallback to dark background
        return Image.new("RGBA", (self.resolution, self.resolution), (26, 26, 46, 255))
    
    def _convert_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coords to radar pixels."""
        if self.use_boltobserv:
            px, py = boltobserv_to_radar(
                np.array([x]), np.array([y]),
                self.map_name, self.resolution
            )
            return int(px[0]), int(py[0])
        else:
            px, py = world_to_radar(
                np.array([x]), np.array([y]),
                self.map_config, self.resolution
            )
            return int(px[0]), int(py[0])
    
    def render_frame(self, frame: TickFrame, frame_num: int) -> str:
        """Render a single frame using PIL (fast)."""
        # Start with map background copy
        img = self.map_image.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw smokes
        for smoke in frame.smokes:
            self._draw_smoke(draw, smoke, frame.tick)
        
        # Draw grenades
        for grenade in frame.grenades:
            self._draw_grenade(draw, grenade, frame.tick)
        
        # Draw flashes
        for flash in frame.flashes:
            self._draw_flash(draw, flash, frame.tick)
        
        # Draw kills
        for kill in frame.kills:
            self._draw_kill(draw, kill, frame.tick)
        
        # Draw players with numbers
        ct_players = [p for p in frame.players if p.team == 'CT']
        t_players = [p for p in frame.players if p.team == 'T']
        
        for i, player in enumerate(ct_players):
            self._draw_player(draw, player, i + 1)
        for i, player in enumerate(t_players):
            self._draw_player(draw, player, i + 6)
        
        # Draw bomb
        if frame.bomb_x is not None and frame.bomb_y is not None:
            bx, by = self._convert_coords(frame.bomb_x, frame.bomb_y)
            self._draw_bomb(draw, bx, by)
        
        # Draw HUD
        self._draw_hud(draw, frame)
        
        # Save frame
        frame_path = self.output_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG", optimize=False)
        
        return str(frame_path)
    
    def _draw_player(self, draw: ImageDraw.Draw, player: PlayerFrame, player_num: int):
        """Draw a player dot with number."""
        px, py = self._convert_coords(player.x, player.y)
        
        # Skip out of bounds
        if px < 0 or px > self.resolution or py < 0 or py > self.resolution:
            return
        
        # Choose color
        if player.team == 'CT':
            color = CT_COLOR if player.alive else CT_COLOR_DEAD
        else:
            color = T_COLOR if player.alive else T_COLOR_DEAD
        
        size = self.player_size if player.alive else 12
        
        # Draw circle
        bbox = [px - size//2, py - size//2, px + size//2, py + size//2]
        draw.ellipse(bbox, fill=color, outline=(255, 255, 255) if player.alive else (128, 128, 128), width=2)
        
        # Draw X for dead
        if not player.alive:
            draw.line([px - 5, py - 5, px + 5, py + 5], fill=(255, 255, 255), width=2)
            draw.line([px - 5, py + 5, px + 5, py - 5], fill=(255, 255, 255), width=2)
        
        # Draw number
        if player.alive and player_num > 0:
            text = str(player_num)
            # Center text
            try:
                text_bbox = draw.textbbox((0, 0), text, font=self._font_small)
                tw = text_bbox[2] - text_bbox[0]
                th = text_bbox[3] - text_bbox[1]
            except:
                tw, th = 6, 9
            draw.text((px - tw//2, py - th//2), text, fill=(255, 255, 255), font=self._font_small)
    
    def _draw_smoke(self, draw: ImageDraw.Draw, smoke: SmokeFrame, current_tick: int):
        """Draw smoke circle."""
        if current_tick < smoke.tick_start or current_tick > smoke.tick_start + smoke.duration_ticks:
            return
        
        px, py = self._convert_coords(smoke.x, smoke.y)
        radius = 30  # Smoke radius
        
        # Draw semi-transparent circle
        bbox = [px - radius, py - radius, px + radius, py + radius]
        draw.ellipse(bbox, fill=SMOKE_COLOR)
    
    def _draw_flash(self, draw: ImageDraw.Draw, flash: FlashFrame, current_tick: int):
        """Draw flash effect."""
        if current_tick < flash.tick or current_tick > flash.tick + flash.duration_ticks:
            return
        
        px, py = self._convert_coords(flash.x, flash.y)
        
        # Flash fades over time
        progress = (current_tick - flash.tick) / flash.duration_ticks
        alpha = int(200 * (1 - progress))
        radius = int(40 * (1 + progress * 0.5))
        
        color = (255, 255, 200, alpha)
        bbox = [px - radius, py - radius, px + radius, py + radius]
        draw.ellipse(bbox, fill=color)
    
    def _draw_grenade(self, draw: ImageDraw.Draw, grenade: GrenadeFrame, current_tick: int):
        """Draw HE or molotov."""
        if current_tick < grenade.tick or current_tick > grenade.tick + grenade.duration_ticks:
            return
        
        px, py = self._convert_coords(grenade.x, grenade.y)
        
        if grenade.grenade_type == 'molotov':
            radius = 25
            color = MOLLY_COLOR
        else:  # HE
            radius = 20
            color = HE_COLOR
        
        bbox = [px - radius, py - radius, px + radius, py + radius]
        draw.ellipse(bbox, fill=color)
    
    def _draw_kill(self, draw: ImageDraw.Draw, kill: KillFrame, current_tick: int):
        """Draw kill marker."""
        if current_tick < kill.tick or current_tick > kill.tick + kill.duration_ticks:
            return
        
        px, py = self._convert_coords(kill.x, kill.y)
        
        # Draw X marker
        size = 8
        draw.line([px - size, py - size, px + size, py + size], fill=KILL_COLOR, width=3)
        draw.line([px - size, py + size, px + size, py - size], fill=KILL_COLOR, width=3)
    
    def _draw_bomb(self, draw: ImageDraw.Draw, x: int, y: int):
        """Draw bomb marker."""
        size = 10
        bbox = [x - size, y - size, x + size, y + size]
        draw.rectangle(bbox, fill=BOMB_COLOR, outline=(0, 0, 0), width=2)
    
    def _draw_hud(self, draw: ImageDraw.Draw, frame: TickFrame):
        """Draw round info and player counts."""
        # Round number
        draw.text((10, 10), f"Round {frame.round_num}", fill=(255, 255, 255), font=self._font)
        
        # Player counts
        ct_alive = sum(1 for p in frame.players if p.team == 'CT' and p.alive)
        t_alive = sum(1 for p in frame.players if p.team == 'T' and p.alive)
        
        count_text = f"CT {ct_alive} - {t_alive} T"
        try:
            text_bbox = draw.textbbox((0, 0), count_text, font=self._font)
            tw = text_bbox[2] - text_bbox[0]
        except:
            tw = len(count_text) * 7
        
        draw.text((self.resolution - tw - 10, 10), count_text, fill=(255, 255, 255), font=self._font)
    
    def render_all(self, frames: list) -> None:
        """Render all frames with progress indicator."""
        from typing import List
        total = len(frames)
        print(f"  Rendering {total} frames (FAST mode)...")
        
        for i, frame in enumerate(frames):
            self.render_frame(frame, i)
            
            # Progress every 500 frames
            if (i + 1) % 500 == 0 or i == total - 1:
                pct = (i + 1) / total * 100
                print(f"    {pct:.0f}% ({i + 1}/{total})")

