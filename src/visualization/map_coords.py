"""
Map Coordinate Transformation Module

Provides coordinate conversion from CS2 world space to radar pixel space.
Uses official Valve map overview data (pos_x, pos_y, scale).

Math:
    Source Engine World -> Radar Image:
    pixel_x = (world_x - pos_x) / scale
    pixel_y = (pos_y - world_y) / scale  # Y is inverted (World Up vs Image Down)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any
import json
import numpy as np


# Official Map Data (Backup if JSON missing)
# pos_x, pos_y: Top-left corner of the radar in world coordinates
# scale: Map units per pixel (usually 1024x1024 radar)
# Source: CS2 resource files
KNOWN_MAPS = {
    "de_dust2": {"pos_x": -2476, "pos_y": 3239, "scale": 4.4},
    "de_mirage": {"pos_x": -3230, "pos_y": 1713, "scale": 5.0},
    "de_inferno": {"pos_x": -2087, "pos_y": 3870, "scale": 4.9},
    "de_nuke": {"pos_x": -3453, "pos_y": 2887, "scale": 7.0},
    "de_overpass": {"pos_x": -4831, "pos_y": 1781, "scale": 5.2},
    "de_ancient": {"pos_x": -2953, "pos_y": 2164, "scale": 5.0},
    "de_anubis": {"pos_x": -2796, "pos_y": 3328, "scale": 5.22},
    "de_vertigo": {"pos_x": -3168, "pos_y": 1762, "scale": 4.0},
}

# Default registry path
DEFAULT_REGISTRY_PATH = Path(__file__).parent.parent.parent / "assets" / "maps" / "map_registry.json"


@dataclass
class MapConfig:
    """Configuration for a single map."""
    name: str
    pos_x: float
    pos_y: float
    scale: float
    rotate: bool = False  # Some maps might need rotation (rare in CS2 radars)
    zoom: float = 1.0     # Optional zoom factor
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "MapConfig":
        """Create MapConfig from dictionary."""
        return cls(
            name=name,
            pos_x=float(data.get("pos_x", 0)),
            pos_y=float(data.get("pos_y", 0)),
            scale=float(data.get("scale", 1.0)),
            rotate=bool(data.get("rotate", False)),
            zoom=float(data.get("zoom", 1.0))
        )
    
    @classmethod
    def default(cls, name: str = "unknown") -> "MapConfig":
        """Create default config for unknown maps."""
        # Generic decent guess for 1024x1024
        return cls(
            name=name,
            pos_x=-3000,
            pos_y=2000,
            scale=5.0
        )


class MapRegistry:
    """
    Registry of map configurations.
    """
    
    _instance: Optional["MapRegistry"] = None
    _configs: Dict[str, MapConfig] = {}
    
    def __new__(cls, registry_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(registry_path or DEFAULT_REGISTRY_PATH)
        return cls._instance
    
    def _load(self, path: Path) -> None:
        """Load registry from JSON file or fall back to KNOWN_MAPS."""
        self._configs = {}
        
        # Load hardcoded defaults first
        for name, data in KNOWN_MAPS.items():
            self._configs[name] = MapConfig.from_dict(name, data)
            
        # Override with JSON if available
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                
                for map_name, config in data.items():
                    norm_name = self._normalize_name(map_name)
                    # Merge with existing or create new
                    if norm_name in self._configs:
                        # Update existing
                        base = self._configs[norm_name]
                        if "pos_x" in config: base.pos_x = float(config["pos_x"])
                        if "pos_y" in config: base.pos_y = float(config["pos_y"])
                        if "scale" in config: base.scale = float(config["scale"])
                    else:
                        self._configs[norm_name] = MapConfig.from_dict(norm_name, config)
            except Exception as e:
                print(f"  Warning: Failed to load map registry JSON: {e}")
    
    def _normalize_name(self, name: str) -> str:
        """Normalize map name (e.g. 'dust2' -> 'de_dust2')."""
        name = name.lower().strip()
        if "/" in name:
            name = name.split("/")[-1]
        
        # Add prefix if missing and it's a known map base
        known_bases = ["dust2", "mirage", "inferno", "nuke", "overpass", "ancient", "anubis", "vertigo"]
        if not name.startswith("de_") and name in known_bases:
            return f"de_{name}"
            
        return name
    
    def get(self, map_name: str) -> MapConfig:
        """Get config for a map."""
        norm_name = self._normalize_name(map_name)
        return self._configs.get(norm_name, MapConfig.default(norm_name))


def load_map_registry(path: Optional[Path] = None) -> MapRegistry:
    """Load map registry singleton."""
    if path and MapRegistry._instance:
        MapRegistry._instance = None
    return MapRegistry(path)


def world_to_radar(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    map_cfg: MapConfig,
    img_size: int = 1024
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert CS2 world coordinates to radar pixel coordinates.
    
    Formula:
    px = (world_x - pos_x) / scale
    py = (pos_y - world_y) / scale
    
    If img_size is not 1024 (standard), we scale the result.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    
    # Standard transformation (for 1024x1024)
    pixel_x = (x - map_cfg.pos_x) / map_cfg.scale
    pixel_y = (map_cfg.pos_y - y) / map_cfg.scale
    
    # Scale if image size is different from standard 1024
    if img_size != 1024:
        factor = img_size / 1024.0
        pixel_x *= factor
        pixel_y *= factor
        
    return pixel_x, pixel_y


def radar_to_world(
    px: Union[float, np.ndarray],
    py: Union[float, np.ndarray],
    map_cfg: MapConfig,
    img_size: int = 1024
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert radar pixel coordinates back to CS2 world coordinates.
    """
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    
    # Unscale if image size is different
    if img_size != 1024:
        factor = 1024.0 / img_size
        px *= factor
        py *= factor
        
    world_x = (px * map_cfg.scale) + map_cfg.pos_x
    world_y = map_cfg.pos_y - (py * map_cfg.scale)
    
    return world_x, world_y

