"""
Enhanced Heatmap Generation Module
Professional-quality heatmaps with map overlays, round phases, and high-res output.

Features:
- Map overlay support (radar images from assets)
- Round-phase separation (early/mid/late)
- Side separation (CT/T)
- Professional color schemes (hot/reds)
- 1024x1024 radar-aligned output
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal
import numpy as np
import matplotlib
matplotlib.use('Agg') # Force non-interactive backend for thread safety
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.image import imread
import pandas as pd
from scipy.ndimage import gaussian_filter

from src.parser.demo_parser import ParsedDemo
from src.visualization.map_coords import (
    MapRegistry,
    MapConfig,
    world_to_radar,
    load_map_registry,
)
from src.visualization.map_assets import MapAssets


# Round phase boundaries (by round number, not time)
ROUND_PHASES = {
    "early": (1, 5),      # Rounds 1-5
    "mid": (6, 20),       # Rounds 6-20
    "late": (21, 999),    # Rounds 21+
}


class HeatmapGenerator:
    """
    Generate professional-quality heatmaps from CS2 demo data.
    """
    
    def __init__(
        self,
        parsed_demo: ParsedDemo,
        output_dir: str = "outputs/heatmaps",
        resolution: int = 1024,  # Standard radar size
        sigma_kills: float = 8.0,
        sigma_movement: float = 4.0,
        phase: Optional[str] = None,
        side: Optional[Literal["CT", "T"]] = None,
        overlay_enabled: bool = True
    ):
        """Initialize heatmap generator."""
        self.demo = parsed_demo
        self.resolution = resolution
        self.sigma_kills = sigma_kills
        self.sigma_movement = sigma_movement
        self.phase = phase
        self.side = side
        self.overlay_enabled = overlay_enabled
        
        # Load map registry
        self._registry = load_map_registry()
        
        # Detect map
        self.map_name = self._detect_map_name(parsed_demo)
        self.map_config = self._registry.get(self.map_name)
        
        # Output directory (per-map)
        map_folder = self.map_name.replace("de_", "") if self.map_name.startswith("de_") else self.map_name
        self.output_dir = Path(output_dir) / map_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Map image path
        self.assets_dir = Path(__file__).parent.parent.parent / "assets" / "maps"
        
        # Try specific image from config, then standard name
        self.map_image_path = self.assets_dir / f"{self.map_name}_radar.png"
        if not self.map_image_path.exists():
             self.map_image_path = self.assets_dir / f"{self.map_name}.png"
        
        self.has_map_image = self.overlay_enabled and self.map_image_path.exists()
        
        if self.overlay_enabled and not self.has_map_image:
            print(f"  Note: No radar image found at {self.map_image_path}")
            print(f"        Heatmaps will render without overlay.")
        
        # Create professional colormaps
        self.cmap_hot = self._create_hot_colormap()
        self.cmap_cool = self._create_cool_colormap()
    
    def _detect_map_name(self, parsed_demo: ParsedDemo) -> str:
        """Detect map name from parser or filename."""
        known_maps = ["dust2", "mirage", "inferno", "nuke", "overpass", "ancient", "anubis", "vertigo"]
        
        # Try parser first
        if parsed_demo.map_name and parsed_demo.map_name != "Unknown":
            name = parsed_demo.map_name.lower().strip()
            if "/" in name:
                name = name.split("/")[-1]
            if not name.startswith("de_"):
                for km in known_maps:
                    if km in name:
                        return f"de_{km}"
            return name
        
        # Fallback: extract from filename
        if parsed_demo.demo_path:
            filename = Path(parsed_demo.demo_path).stem.lower()
            for km in known_maps:
                if km in filename:
                    return f"de_{km}"
        
        return "unknown"
    
    def _create_hot_colormap(self) -> LinearSegmentedColormap:
        """Create professional hot colormap for kills/deaths."""
        colors = [
            (0.0, 0.0, 0.0, 0.0),       # Transparent
            (0.1, 0.0, 0.0, 0.3),       # Very dark red
            (0.3, 0.0, 0.0, 0.5),       # Dark red
            (0.6, 0.1, 0.0, 0.7),       # Red
            (0.9, 0.3, 0.0, 0.85),      # Orange-red
            (1.0, 0.6, 0.0, 0.95),      # Orange
            (1.0, 1.0, 0.2, 1.0),       # Yellow (hot spots)
        ]
        return LinearSegmentedColormap.from_list("heatmap_hot", colors, N=256)
    
    def _create_cool_colormap(self) -> LinearSegmentedColormap:
        """Create cool colormap for movement density."""
        colors = [
            (0.0, 0.0, 0.0, 0.0),       # Transparent
            (0.0, 0.1, 0.2, 0.3),       # Dark blue
            (0.0, 0.3, 0.5, 0.5),       # Blue
            (0.0, 0.5, 0.7, 0.7),       # Cyan-blue
            (0.2, 0.8, 0.8, 0.85),      # Cyan
            (0.5, 1.0, 0.8, 0.95),      # Light cyan
            (1.0, 1.0, 1.0, 1.0),       # White (hot spots)
        ]
        return LinearSegmentedColormap.from_list("heatmap_cool", colors, N=256)
    
    def _is_empty(self, df: pd.DataFrame) -> bool:
        """Helper to check if DataFrame is None or empty."""
        return df is None or df.empty

    def _extract_coordinates(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        team_col: Optional[str] = None,
        steamid_col: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self._is_empty(df):
             return np.array([]), np.array([]), np.array([])
             
        # Find actual columns
        cols_map = {c.lower(): c for c in df.columns}
        
        actual_x = cols_map.get(x_col.lower()) or cols_map.get("x")
        actual_y = cols_map.get(y_col.lower()) or cols_map.get("y")
        
        if not actual_x or not actual_y:
            return np.array([]), np.array([]), np.array([])

        # Filter by Player ID if provided
        if player_id:
             if not steamid_col:
                 # Try to guess
                 if "attacker_steamid" in df.columns: steamid_col = "attacker_steamid"
                 elif "steamid" in df.columns: steamid_col = "steamid"
                 elif "user_steamid" in df.columns: steamid_col = "user_steamid"
                 else: return np.array([]), np.array([]), np.array([])
             
             df = df[df[steamid_col].astype(str) == str(player_id)]

        # Filter by Side
        mask = np.ones(len(df), dtype=bool)
        if self.side and team_col:
            actual_team = cols_map.get(team_col.lower()) or cols_map.get("team_name")
            if actual_team:
                # Assuming team names are "CT" and "TERRORIST" or similar
                # Normalize widely used team names
                target = self.side.upper()
                if target == "T": target_aliases = ["T", "TERRORIST", "Tea", "Opfor"]
                else: target_aliases = ["CT", "CTs", "COUNTER-TERRORIST", "Counter-Terrorist"]
                
                # Create mask
                team_vals = df[actual_team].astype(str).str.upper()
                mask = team_vals.isin([t.upper() for t in target_aliases])
        
        filtered_df = df[mask]
        
        if filtered_df.empty:
            return np.array([]), np.array([]), np.array([])
            
        x = filtered_df[actual_x].to_numpy(dtype=np.float64)
        y = filtered_df[actual_y].to_numpy(dtype=np.float64)
        
        return x, y, filtered_df.index.to_numpy()
    
    def _filter_by_phase(self, df: pd.DataFrame, indices: np.ndarray) -> np.ndarray:
        """Filter indices by round phase."""
        if self.phase is None or len(indices) == 0:
            return indices
            
        if self.phase not in ROUND_PHASES:
            return indices
            
        start_round, end_round = ROUND_PHASES[self.phase]
        
        # Try to find round column
        round_col = None
        for col in ['total_rounds_played', 'round', 'round_num', 'Round']:
            if col in df.columns:
                round_col = col
                break
                
        if not round_col:
            return indices
            
        rounds = df.loc[indices, round_col].to_numpy()
        mask = (rounds >= start_round) & (rounds <= end_round)
        return indices[mask]

    def _create_density_grid(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Create 2D density grid from world coords."""
        if len(x) == 0:
            return np.zeros((self.resolution, self.resolution))
            
        # Convert to radar pixels
        px, py = world_to_radar(x, y, self.map_config, self.resolution)
        
        # Filter out-of-bounds
        mask = (px >= 0) & (px < self.resolution) & (py >= 0) & (py < self.resolution)
        px, py = px[mask], py[mask]
        
        if len(px) == 0:
            return np.zeros((self.resolution, self.resolution))
            
        # Histogram
        grid, _, _ = np.histogram2d(
            py, px, # numpy uses (row, col) = (y, x)
            bins=self.resolution,
            range=[[0, self.resolution], [0, self.resolution]]
        )
        
        return grid

    def _render_heatmap(
        self,
        grid: np.ndarray,
        title: str,
        output_path: Path,
        cmap: LinearSegmentedColormap,
        sigma: float
    ) -> str:
        """Render high-quality heatmap to PNG with legend."""
        raw_event_count = int(grid.sum())
        
        # Apply Gaussian smoothing
        if sigma > 0 and raw_event_count > 0:
            grid = gaussian_filter(grid, sigma=sigma)
        
        # Normalize
        max_density = grid.max()
        if max_density > 0:
            grid_norm = grid / max_density
        else:
            grid_norm = np.zeros_like(grid)
            
        # Create figure with space for colorbar
        fig = plt.figure(figsize=(11.5, 10.24), dpi=100)
        ax = fig.add_axes([0.02, 0.05, 0.85, 0.88])  # Main plot
        cbar_ax = fig.add_axes([0.89, 0.15, 0.03, 0.6])  # Colorbar
        
        # Background color
        fig.patch.set_facecolor('#1a1a2e')
        
        # 1. Overlay on Map (if available)
        if self.map_image_path and os.path.exists(self.map_image_path):
            try:
                from PIL import Image
                map_img = Image.open(self.map_image_path).convert("RGBA")
                if map_img.size != (self.resolution, self.resolution):
                    map_img = map_img.resize((self.resolution, self.resolution), Image.Resampling.LANCZOS)
                ax.imshow(map_img, extent=[0, self.resolution, self.resolution, 0], zorder=1)
            except Exception as e:
                print(f"    ⚠️ Failed to load map image: {e}")
                ax.set_facecolor('#16213e')
        else:
            ax.set_facecolor('#16213e')
        
        # 2. Overlay Heatmap
        im = None
        if raw_event_count > 0:
            im = ax.imshow(
                grid_norm,
                cmap=cmap,
                origin='upper',
                extent=[0, self.resolution, self.resolution, 0],
                alpha=0.8,
                zorder=2,
                vmin=0,
                vmax=1
            )
        
        # 3. Add Colorbar Legend
        if im is not None:
            cbar = fig.colorbar(im, cax=cbar_ax)
            cbar.set_label('Kill Density', color='white', fontsize=10)
            cbar.ax.yaxis.set_tick_params(color='white')
            cbar.outline.set_edgecolor('white')
            cbar.ax.tick_params(labelsize=8, colors='white')
            # Add labels
            cbar.ax.set_yticklabels(['Low', '', '', '', 'Med', '', '', '', '', 'High'])
        
        # Title & Annotations
        side_text = f" ({self.side})" if self.side else ""
        phase_text = f" [{self.phase.upper()}]" if self.phase else ""
        full_title = f"{title}{side_text}{phase_text}"
        
        ax.set_title(full_title, color='white', fontsize=14, fontweight='bold', loc='left', pad=10)
        ax.text(0.5, 1.02, self.map_name.upper(), transform=ax.transAxes, 
                color='#4ecdc4', fontsize=12, ha='center', fontweight='bold')
        ax.axis('off')
        
        # Stats Box
        stats_text = f"Events: {raw_event_count}"
        if max_density > 0:
            # Find hotspot location (highest density pixel)
            hotspot_idx = np.unravel_index(np.argmax(grid), grid.shape)
            stats_text += f"\nHotspot: ({hotspot_idx[1]}, {hotspot_idx[0]})"
        
        ax.text(
            0.02, 0.02, stats_text,
            transform=ax.transAxes, color='white', fontsize=9,
            bbox=dict(facecolor='black', alpha=0.7, edgecolor='#4ecdc4', boxstyle='round,pad=0.5'),
            verticalalignment='bottom'
        )
        
        # Map name at bottom
        ax.text(
            0.98, 0.02, self.map_name,
            transform=ax.transAxes, color='#666', fontsize=10,
            ha='right', verticalalignment='bottom'
        )
        
        # Save
        plt.savefig(output_path, dpi=100, bbox_inches='tight', pad_inches=0.1, facecolor='#1a1a2e')
        plt.close(fig)
        
        return str(output_path)

    def generate_kills_heatmap(self, player_id: Optional[str] = None) -> str:
        source = self.demo.kills
        x, y, indices = self._extract_coordinates(source, "attacker_X", "attacker_Y", "attacker_team_name", "attacker_steamid", player_id)
        
        # Filter by phase
        if self.phase:
            final_indices = self._filter_by_phase(source, indices)
            mask = np.isin(indices, final_indices)
            x, y = x[mask], y[mask]
            
        grid = self._create_density_grid(x, y)
        
        suffix = f"{'_' + self.phase if self.phase else ''}{'_' + self.side if self.side else ''}"
        if player_id:
            suffix += f"_{player_id}"
        path = self.output_dir / f"kills{suffix}.png"
        return self._render_heatmap(grid, "KILL LOCATIONS", path, self.cmap_hot, self.sigma_kills)

        
        if self.phase:
            final_indices = self._filter_by_phase(source, indices)
            mask = np.isin(indices, final_indices)
            x, y = x[mask], y[mask]
            
        grid = self._create_density_grid(x, y)
        suffix = f"{'_' + self.phase if self.phase else ''}{'_' + self.side if self.side else ''}"
        path = self.output_dir / f"deaths{suffix}.png"
        return self._render_heatmap(grid, "DEATH LOCATIONS", path, self.cmap_hot, self.sigma_kills)
    
    def generate_movement_heatmap(self) -> str:
        source = self.demo.player_positions
        x, y, indices = self._extract_coordinates(source, "X", "Y", "team_name")
        
        # Movement data is huge, filtering by phase is tricky without round column in positions
        # Assuming positions has 'round' or similar if enriched, else skip phase filter for movement
        # (Current parser often doesn't propagate round num to every tick)
        
        grid = self._create_density_grid(x, y)
        suffix = f"{'_' + self.phase if self.phase else ''}{'_' + self.side if self.side else ''}"
        path = self.output_dir / f"movement{suffix}.png"
        return self._render_heatmap(grid, "MOVEMENT DENSITY", path, self.cmap_cool, self.sigma_movement)

    def generate_all(self) -> Dict[str, str]:
        """Generate all types."""
        results = {}
        try: results["kills"] = self.generate_kills_heatmap()
        except Exception as e: print(f"Kills heatmap failed: {e}")
        
        try: results["deaths"] = self.generate_deaths_heatmap()
        except Exception as e: print(f"Deaths heatmap failed: {e}")
        
        try: results["movement"] = self.generate_movement_heatmap()
        except Exception as e: print(f"Movement heatmap failed: {e}")
        
        return results


def generate_heatmaps(
    parsed_demo: ParsedDemo,
    output_dir: str = "outputs/heatmaps",
    resolution: int = 1024,
    phase: Optional[str] = None,
    side: Optional[str] = None,
    overlay_enabled: bool = True
) -> Dict[str, str]:
    generator = HeatmapGenerator(parsed_demo, output_dir, resolution, 8.0, 4.0, phase, side, overlay_enabled)
    return generator.generate_all()
