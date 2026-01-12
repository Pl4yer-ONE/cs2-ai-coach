"""
CS2 Demo Player - Pygame Renderer

Renders demo playback with radar background, player positions,
kill events, and HUD overlay.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import math

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Run: pip install pygame")

from src.player.demo_player import DemoPlayer, FrameData, PlayerState
from src.visualization.map_coords import MapRegistry, world_to_radar, load_map_registry


# Colors
COLOR_BG = (20, 20, 30)
COLOR_CT = (100, 150, 255)  # Blue
COLOR_CT_DEAD = (50, 75, 128)
COLOR_T = (255, 180, 80)   # Orange
COLOR_T_DEAD = (128, 90, 40)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_RED = (255, 80, 80)
COLOR_GREEN = (80, 255, 80)
COLOR_YELLOW = (255, 255, 80)
COLOR_HUD_BG = (0, 0, 0, 180)


class Renderer:
    """
    Pygame-based demo renderer.
    
    Renders radar background, player dots, kill events, and HUD.
    """
    
    # Window dimensions
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 900
    
    # Radar dimensions (left side)
    RADAR_SIZE = 800
    RADAR_OFFSET_X = 20
    RADAR_OFFSET_Y = 80
    
    # Player dot size
    PLAYER_RADIUS = 8
    DEAD_RADIUS = 5
    
    def __init__(self, player: DemoPlayer):
        """
        Initialize renderer with demo player.
        
        Args:
            player: DemoPlayer instance to render
        """
        if not PYGAME_AVAILABLE:
            raise RuntimeError("Pygame not installed. Run: pip install pygame")
        
        self.player = player
        self._registry = load_map_registry()
        self.map_config = self._registry.get(player.map_name)
        
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption(f"CS2 Demo Player - {player.demo_path.name}")
        
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Load radar image
        self.radar_surface = self._load_radar_image()
        
        # Kill feed history
        self.kill_feed: List[Dict[str, Any]] = []
        self.kill_feed_duration = 4.0  # seconds
        
        # Running state
        self.running = True
    
    def _load_radar_image(self) -> Optional[pygame.Surface]:
        """Load radar image for current map."""
        assets_dir = Path(__file__).parent.parent.parent / "assets" / "maps"
        
        # Try different naming conventions
        map_name = self.player.map_name
        possible_paths = [
            assets_dir / f"{map_name}_radar.png",
            assets_dir / f"{map_name}.png",
            assets_dir / f"{map_name.replace('de_', '')}_radar.png",
            assets_dir / f"{map_name.replace('de_', '')}.png",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    img = pygame.image.load(str(path))
                    return pygame.transform.scale(img, (self.RADAR_SIZE, self.RADAR_SIZE))
                except Exception as e:
                    print(f"Failed to load radar: {e}")
        
        # Create blank radar with grid
        return self._create_placeholder_radar()
    
    def _create_placeholder_radar(self) -> pygame.Surface:
        """Create a placeholder radar surface with grid."""
        surface = pygame.Surface((self.RADAR_SIZE, self.RADAR_SIZE))
        surface.fill((30, 30, 40))
        
        # Draw grid
        grid_color = (50, 50, 60)
        for i in range(0, self.RADAR_SIZE, 100):
            pygame.draw.line(surface, grid_color, (i, 0), (i, self.RADAR_SIZE))
            pygame.draw.line(surface, grid_color, (0, i), (self.RADAR_SIZE, i))
        
        # Border
        pygame.draw.rect(surface, COLOR_GRAY, (0, 0, self.RADAR_SIZE, self.RADAR_SIZE), 2)
        
        # Map name
        text = self.font_large.render(self.player.map_name.upper(), True, COLOR_GRAY)
        rect = text.get_rect(center=(self.RADAR_SIZE // 2, self.RADAR_SIZE // 2))
        surface.blit(text, rect)
        
        return surface
    
    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen pixels."""
        px, py = world_to_radar(x, y, self.map_config, self.RADAR_SIZE)
        
        # Clamp to radar bounds
        px = max(0, min(self.RADAR_SIZE - 1, px))
        py = max(0, min(self.RADAR_SIZE - 1, py))
        
        # Offset for radar position on screen
        return int(px + self.RADAR_OFFSET_X), int(py + self.RADAR_OFFSET_Y)
    
    def run(self) -> None:
        """Main render loop."""
        self.player.play()
        
        while self.running:
            # Handle events
            self._handle_events()
            
            # Update playback
            frame = self.player.update()
            
            # Render
            self._render(frame)
            
            # Cap framerate
            self.clock.tick(60)
        
        pygame.quit()
    
    def _handle_events(self) -> None:
        """Handle pygame events and keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
    
    def _handle_keydown(self, key: int) -> None:
        """Handle keyboard input."""
        if key == pygame.K_ESCAPE:
            self.running = False
        
        elif key == pygame.K_SPACE:
            self.player.toggle_play()
        
        elif key == pygame.K_LEFT:
            # Seek back 5 seconds
            self.player.seek_relative(-self.player.tickrate * 5)
        
        elif key == pygame.K_RIGHT:
            # Seek forward 5 seconds
            self.player.seek_relative(self.player.tickrate * 5)
        
        elif key == pygame.K_UP:
            # Previous round
            self.player.jump_to_round(max(1, self.player.current_round - 1))
        
        elif key == pygame.K_DOWN:
            # Next round
            self.player.jump_to_round(self.player.current_round + 1)
        
        elif key == pygame.K_EQUALS or key == pygame.K_PLUS:
            # Speed up
            self.player.set_speed(self.player.speed + 0.25)
        
        elif key == pygame.K_MINUS:
            # Slow down
            self.player.set_speed(self.player.speed - 0.25)
        
        elif key == pygame.K_r:
            # Reset to beginning
            self.player.seek(self.player.min_tick)
        
        # Number keys 1-9 for round jump
        elif pygame.K_1 <= key <= pygame.K_9:
            round_num = key - pygame.K_1 + 1
            self.player.jump_to_round(round_num)
    
    def _render(self, frame: FrameData) -> None:
        """Render a single frame."""
        # Clear screen
        self.screen.fill(COLOR_BG)
        
        # Draw radar background
        self.screen.blit(self.radar_surface, (self.RADAR_OFFSET_X, self.RADAR_OFFSET_Y))
        
        # Draw players
        self._draw_players(frame.players)
        
        # Draw events (kills, grenades)
        self._draw_events(frame.events)
        
        # Draw HUD
        self._draw_hud(frame)
        
        # Draw controls help
        self._draw_controls()
        
        # Update display
        pygame.display.flip()
    
    def _draw_players(self, players: List[PlayerState]) -> None:
        """Draw player dots on radar."""
        for p in players:
            sx, sy = self.world_to_screen(p.x, p.y)
            
            # Choose color based on team and alive status
            if p.team == "CT":
                color = COLOR_CT if p.is_alive else COLOR_CT_DEAD
            else:
                color = COLOR_T if p.is_alive else COLOR_T_DEAD
            
            radius = self.PLAYER_RADIUS if p.is_alive else self.DEAD_RADIUS
            
            # Draw player dot
            pygame.draw.circle(self.screen, color, (sx, sy), radius)
            
            # Draw view direction for alive players
            if p.is_alive:
                angle_rad = math.radians(-p.yaw)  # Negate for screen coords
                dx = math.cos(angle_rad) * (radius + 8)
                dy = math.sin(angle_rad) * (radius + 8)
                pygame.draw.line(self.screen, color, (sx, sy), (int(sx + dx), int(sy + dy)), 2)
            
            # Draw name (above player)
            if p.is_alive:
                name_text = self.font_small.render(p.name[:12], True, COLOR_WHITE)
                name_rect = name_text.get_rect(center=(sx, sy - radius - 10))
                self.screen.blit(name_text, name_rect)
    
    def _draw_events(self, events: List[Dict[str, Any]]) -> None:
        """Draw kill markers and update kill feed."""
        # Update kill feed
        for evt in events:
            if evt['type'] == 'kill' and evt.get('age', 0) == 0:
                self.kill_feed.insert(0, evt)
        
        # Trim old kills
        self.kill_feed = self.kill_feed[:6]  # Max 6 items
        
        # Draw death markers on radar
        for evt in events:
            if evt['type'] == 'kill':
                x, y = evt.get('x', 0), evt.get('y', 0)
                if x != 0 and y != 0:
                    sx, sy = self.world_to_screen(x, y)
                    # Draw X mark
                    age = evt.get('age', 0)
                    alpha = max(0, 255 - age * 2)
                    color = (255, 80, 80)
                    size = 6
                    pygame.draw.line(self.screen, color, (sx - size, sy - size), (sx + size, sy + size), 2)
                    pygame.draw.line(self.screen, color, (sx - size, sy + size), (sx + size, sy - size), 2)
    
    def _draw_hud(self, frame: FrameData) -> None:
        """Draw heads-up display."""
        # Header bar
        header_rect = pygame.Rect(0, 0, self.WINDOW_WIDTH, 60)
        pygame.draw.rect(self.screen, (30, 30, 40), header_rect)
        
        # Map name
        map_text = self.font_large.render(self.player.map_name.upper(), True, COLOR_WHITE)
        self.screen.blit(map_text, (20, 15))
        
        # Round info
        round_text = self.font_large.render(f"Round {frame.round_num}", True, COLOR_YELLOW)
        round_rect = round_text.get_rect(center=(self.WINDOW_WIDTH // 2, 30))
        self.screen.blit(round_text, round_rect)
        
        # Playback status
        status = "▶ PLAYING" if self.player.is_playing else "⏸ PAUSED"
        speed_text = f" ({self.player.speed}x)" if self.player.speed != 1.0 else ""
        status_text = self.font_medium.render(f"{status}{speed_text}", True, COLOR_GREEN if self.player.is_playing else COLOR_GRAY)
        self.screen.blit(status_text, (self.WINDOW_WIDTH - 200, 18))
        
        # Progress bar
        bar_y = self.WINDOW_HEIGHT - 40
        bar_width = self.WINDOW_WIDTH - 40
        bar_height = 10
        
        # Background
        pygame.draw.rect(self.screen, (50, 50, 60), (20, bar_y, bar_width, bar_height))
        
        # Progress
        progress_width = int(bar_width * self.player.progress)
        pygame.draw.rect(self.screen, COLOR_GREEN, (20, bar_y, progress_width, bar_height))
        
        # Tick info
        tick_text = self.font_small.render(
            f"Tick: {frame.tick} / {self.player.max_tick}", 
            True, COLOR_GRAY
        )
        self.screen.blit(tick_text, (20, bar_y - 20))
        
        # Kill feed (right side)
        self._draw_kill_feed()
    
    def _draw_kill_feed(self) -> None:
        """Draw kill feed on right side."""
        x = self.RADAR_OFFSET_X + self.RADAR_SIZE + 30
        y = self.RADAR_OFFSET_Y
        
        for i, kill in enumerate(self.kill_feed[:6]):
            attacker = kill.get('attacker', 'Unknown')[:12]
            victim = kill.get('victim', 'Unknown')[:12]
            weapon = kill.get('weapon', '?')[:10]
            hs = "☠" if kill.get('headshot') else ""
            
            text = f"{attacker} [{weapon}]{hs} {victim}"
            kill_text = self.font_small.render(text, True, COLOR_WHITE)
            self.screen.blit(kill_text, (x, y + i * 25))
    
    def _draw_controls(self) -> None:
        """Draw controls help text."""
        x = self.RADAR_OFFSET_X + self.RADAR_SIZE + 30
        y = self.RADAR_OFFSET_Y + 200
        
        controls = [
            "CONTROLS:",
            "Space - Play/Pause",
            "←/→ - Seek 5 sec",
            "↑/↓ - Prev/Next Round",
            "+/- - Speed",
            "1-9 - Jump to Round",
            "R - Restart",
            "ESC - Quit"
        ]
        
        for i, line in enumerate(controls):
            color = COLOR_YELLOW if i == 0 else COLOR_GRAY
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (x, y + i * 22))
        
        # Stats
        y += len(controls) * 22 + 30
        stats_text = self.font_small.render(f"Total Rounds: {len(self.player.rounds)}", True, COLOR_GRAY)
        self.screen.blit(stats_text, (x, y))


def run_player(demo_path: str) -> None:
    """
    Run the demo player.
    
    Args:
        demo_path: Path to .dem file
    """
    if not PYGAME_AVAILABLE:
        print("Error: pygame is required. Install with: pip install pygame")
        sys.exit(1)
    
    try:
        player = DemoPlayer(demo_path)
        renderer = Renderer(player)
        renderer.run()
    except Exception as e:
        print(f"Error: {e}")
        raise
