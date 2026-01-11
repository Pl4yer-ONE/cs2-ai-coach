"""
CS2 Map Zones
Polygon-based callout definitions for accurate position labeling.

Uses ray-casting point-in-polygon algorithm for efficient lookups.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Zone:
    """A map zone defined by polygon vertices."""
    name: str
    display_name: str  # Human-readable
    polygon: List[Tuple[float, float]]  # (x, y) vertices
    priority: int = 0  # Higher priority zones win on overlap


def point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    """
    Ray-casting algorithm to detect if point is inside polygon.
    
    Args:
        x, y: Point coordinates
        polygon: List of (x, y) vertices defining the polygon
        
    Returns:
        True if point is inside polygon
    """
    n = len(polygon)
    inside = False
    
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside


# =============================================================================
# DUST2 ZONES - Comprehensive callouts
# Coordinates derived from CS2 world space
# =============================================================================
DUST2_ZONES = [
    # T Spawn Area
    Zone("t_spawn", "T Spawn", [(-600, -800), (400, -800), (400, 200), (-600, 200)]),
    
    # Mid
    Zone("mid_doors", "Mid Doors", [(-200, 600), (300, 600), (300, 1100), (-200, 1100)], priority=2),
    Zone("xbox", "Xbox", [(-100, 1100), (200, 1100), (200, 1400), (-100, 1400)], priority=3),
    Zone("mid", "Mid", [(-500, 400), (400, 400), (400, 1800), (-500, 1800)]),
    Zone("ct_mid", "CT Mid", [(300, 1600), (700, 1600), (700, 2100), (300, 2100)]),
    
    # A Site Area
    Zone("a_long", "A Long", [(500, 1500), (1400, 1500), (1400, 2700), (500, 2700)]),
    Zone("pit", "Pit", [(1200, 2500), (1600, 2500), (1600, 3000), (1200, 3000)], priority=2),
    Zone("a_long_corner", "Long Corner", [(400, 2400), (700, 2400), (700, 2800), (400, 2800)], priority=2),
    Zone("a_car", "A Car", [(1000, 2100), (1300, 2100), (1300, 2400), (1000, 2400)], priority=3),
    Zone("a_site", "A Site", [(900, 2200), (1500, 2200), (1500, 3100), (900, 3100)]),
    Zone("a_ramp", "A Ramp", [(700, 2800), (1000, 2800), (1000, 3200), (700, 3200)], priority=2),
    Zone("goose", "Goose", [(1300, 2900), (1600, 2900), (1600, 3200), (1300, 3200)], priority=3),
    
    # A Short/Cat
    Zone("a_short", "A Short", [(-100, 1800), (500, 1800), (500, 2500), (-100, 2500)]),
    Zone("cat", "Catwalk", [(200, 2200), (600, 2200), (600, 2800), (200, 2800)], priority=2),
    
    # B Site Area
    Zone("b_tunnels_upper", "Upper Tunnels", [(-1800, 400), (-800, 400), (-800, 1000), (-1800, 1000)]),
    Zone("b_tunnels_lower", "Lower Tunnels", [(-2100, -400), (-800, -400), (-800, 500), (-2100, 500)]),
    Zone("b_doors", "B Doors", [(-1400, 900), (-900, 900), (-900, 1300), (-1400, 1300)], priority=2),
    Zone("b_site", "B Site", [(-1700, 1200), (-700, 1200), (-700, 2500), (-1700, 2500)]),
    Zone("b_plat", "B Platform", [(-1600, 2000), (-1100, 2000), (-1100, 2400), (-1600, 2400)], priority=2),
    Zone("b_car", "B Car", [(-1200, 1500), (-900, 1500), (-900, 1800), (-1200, 1800)], priority=3),
    Zone("b_window", "B Window", [(-900, 1800), (-600, 1800), (-600, 2100), (-900, 2100)], priority=2),
    Zone("b_back", "Back of B", [(-1700, 2200), (-1200, 2200), (-1200, 2600), (-1700, 2600)], priority=2),
    
    # CT Spawn
    Zone("ct_spawn", "CT Spawn", [(700, 2900), (1400, 2900), (1400, 3400), (700, 3400)]),
]

# =============================================================================
# MIRAGE ZONES
# =============================================================================
MIRAGE_ZONES = [
    # T Spawn
    Zone("t_spawn", "T Spawn", [(-1400, 600), (-600, 600), (-600, 1400), (-1400, 1400)]),
    
    # A Site
    Zone("a_ramp", "A Ramp", [(-700, -1400), (0, -1400), (0, -800), (-700, -800)]),
    Zone("a_site", "A Site", [(-200, -1800), (700, -1800), (700, -1100), (-200, -1100)]),
    Zone("a_default", "A Default", [(200, -1600), (500, -1600), (500, -1300), (200, -1300)], priority=2),
    Zone("tetris", "Tetris", [(400, -1400), (700, -1400), (700, -1100), (400, -1100)], priority=3),
    Zone("stairs", "Stairs", [(-200, -1100), (100, -1100), (100, -800), (-200, -800)], priority=2),
    Zone("palace", "Palace", [(300, -1800), (1000, -1800), (1000, -1200), (300, -1200)]),
    
    # Mid
    Zone("mid", "Mid", [(-600, -400), (300, -400), (300, 400), (-600, 400)]),
    Zone("window", "Window Room", [(200, -200), (600, -200), (600, 200), (200, 200)], priority=2),
    Zone("connector", "Connector", [(300, 100), (700, 100), (700, 600), (300, 600)]),
    Zone("underpass", "Underpass", [(-300, 200), (200, 200), (200, 700), (-300, 700)]),
    
    # B Site
    Zone("b_apps", "B Apartments", [(-600, 400), (0, 400), (0, 1000), (-600, 1000)]),
    Zone("b_site", "B Site", [(-2000, -400), (-1200, -400), (-1200, 400), (-2000, 400)]),
    Zone("van", "Van", [(-1600, -200), (-1300, -200), (-1300, 100), (-1600, 100)], priority=2),
    Zone("bench", "Bench", [(-1900, 100), (-1600, 100), (-1600, 400), (-1900, 400)], priority=2),
    
    # CT
    Zone("ct_spawn", "CT Spawn", [(400, -1000), (1000, -1000), (1000, -400), (400, -400)]),
    Zone("jungle", "Jungle", [(100, -1000), (400, -1000), (400, -600), (100, -600)]),
    Zone("market", "Market", [(-1200, -800), (-800, -800), (-800, -400), (-1200, -400)]),
]

# =============================================================================
# INFERNO ZONES
# =============================================================================
INFERNO_ZONES = [
    Zone("t_spawn", "T Spawn", [(-800, -1600), (0, -1600), (0, -800), (-800, -800)]),
    Zone("mid", "Mid", [(200, -200), (900, -200), (900, 600), (200, 600)]),
    Zone("alt_mid", "Alt Mid", [(600, 400), (1100, 400), (1100, 1000), (600, 1000)]),
    
    # A Site
    Zone("a_long", "A Long", [(1300, -400), (2000, -400), (2000, 400), (1300, 400)]),
    Zone("a_short", "A Short", [(1100, 200), (1400, 200), (1400, 600), (1100, 600)]),
    Zone("a_site", "A Site", [(1800, 300), (2500, 300), (2500, 1100), (1800, 1100)]),
    Zone("pit", "Pit", [(2200, 0), (2600, 0), (2600, 400), (2200, 400)], priority=2),
    Zone("graveyard", "Graveyard", [(2000, 800), (2400, 800), (2400, 1200), (2000, 1200)], priority=2),
    Zone("apartments", "Apartments", [(1400, 1200), (2100, 1200), (2100, 2200), (1400, 2200)]),
    
    # Banana/B
    Zone("banana", "Banana", [(-200, 1200), (500, 1200), (500, 2000), (-200, 2000)]),
    Zone("car_banana", "Car (Banana)", [(100, 1600), (400, 1600), (400, 1900), (100, 1900)], priority=2),
    Zone("b_site", "B Site", [(-400, 2200), (500, 2200), (500, 3100), (-400, 3100)]),
    Zone("construction", "Construction", [(300, 2600), (700, 2600), (700, 3000), (300, 3000)], priority=2),
    Zone("ct_spawn", "CT Spawn", [(1400, 1800), (2000, 1800), (2000, 2400), (1400, 2400)]),
]

# =============================================================================
# NUKE ZONES
# =============================================================================
NUKE_ZONES = [
    Zone("t_spawn", "T Spawn", [(-400, -3600), (400, -3600), (400, -3000), (-400, -3000)]),
    Zone("outside", "Outside", [(-1800, -3200), (400, -3200), (400, -1800), (-1800, -1800)]),
    Zone("secret", "Secret", [(1800, -2600), (2600, -2600), (2600, -2000), (1800, -2000)]),
    Zone("ramp", "Ramp", [(600, -2600), (1400, -2600), (1400, -2000), (600, -2000)]),
    Zone("lobby", "Lobby", [(-400, -1600), (400, -1600), (400, -1000), (-400, -1000)]),
    Zone("a_site", "A Site", [(400, -1600), (1600, -1600), (1600, -800), (400, -800)]),
    Zone("hut", "Hut", [(1000, -1400), (1400, -1400), (1400, -1000), (1000, -1000)], priority=2),
    Zone("heaven", "Heaven", [(400, -1200), (800, -1200), (800, -800), (400, -800)], priority=2),
    Zone("b_site", "B Site", [(400, -1600), (1600, -1600), (1600, -800), (400, -800)]),  # Lower
    Zone("control", "Control Room", [(-200, -1000), (400, -1000), (400, -600), (-200, -600)]),
    Zone("ct_spawn", "CT Spawn", [(1400, -800), (2000, -800), (2000, -200), (1400, -200)]),
]

# =============================================================================
# TRAIN ZONES
# =============================================================================
TRAIN_ZONES = [
    Zone("t_spawn", "T Spawn", [(-1200, -1000), (-400, -1000), (-400, -400), (-1200, -400)]),
    Zone("t_con", "T Connector", [(-400, -800), (200, -800), (200, -200), (-400, -200)]),
    Zone("pop_dog", "Pop Dog", [(0, -400), (400, -400), (400, 0), (0, 0)], priority=2),
    Zone("a_site", "A Site", [(-600, 200), (400, 200), (400, 900), (-600, 900)]),
    Zone("ivy", "Ivy", [(-200, 800), (300, 800), (300, 1400), (-200, 1400)]),
    Zone("a_main", "A Main", [(-1000, 100), (-500, 100), (-500, 600), (-1000, 600)]),
    Zone("hell", "Hell", [(-800, 400), (-400, 400), (-400, 700), (-800, 700)], priority=2),
    Zone("heaven", "Heaven", [(200, 500), (600, 500), (600, 900), (200, 900)], priority=2),
    Zone("b_site", "B Site", [(800, -400), (1600, -400), (1600, 400), (800, 400)]),
    Zone("b_upper", "Upper B", [(1200, -200), (1600, -200), (1600, 200), (1200, 200)], priority=2),
    Zone("b_lower", "Lower B", [(900, 200), (1300, 200), (1300, 600), (900, 600)], priority=2),
    Zone("b_ramp", "B Ramp", [(400, -200), (800, -200), (800, 200), (400, 200)]),
    Zone("z_connector", "Z Connector", [(600, 600), (1000, 600), (1000, 1000), (600, 1000)]),
    Zone("ct_spawn", "CT Spawn", [(1000, 800), (1600, 800), (1600, 1400), (1000, 1400)]),
    Zone("old_bomb", "Old Bomb", [(-600, -600), (-200, -600), (-200, -200), (-600, -200)]),
    Zone("connector", "Connector", [(-200, 0), (400, 0), (400, 500), (-200, 500)]),
]

# =============================================================================
# OVERPASS ZONES
# =============================================================================
OVERPASS_ZONES = [
    Zone("t_spawn", "T Spawn", [(-2800, 400), (-2200, 400), (-2200, 1000), (-2800, 1000)]),
    Zone("a_long", "A Long", [(-2400, -400), (-1600, -400), (-1600, 400), (-2400, 400)]),
    Zone("toilets", "Toilets", [(-1800, -200), (-1400, -200), (-1400, 200), (-1800, 200)], priority=2),
    Zone("a_site", "A Site", [(-1400, -600), (-600, -600), (-600, 200), (-1400, 200)]),
    Zone("a_default", "A Default", [(-1100, -400), (-800, -400), (-800, -100), (-1100, -100)], priority=2),
    Zone("party", "Party", [(-600, -400), (-200, -400), (-200, 0), (-600, 0)], priority=2),
    Zone("bank", "Bank", [(-200, -600), (200, -600), (200, -200), (-200, -200)]),
    Zone("connector", "Connector", [(-400, 200), (200, 200), (200, 800), (-400, 800)]),
    Zone("monster", "Monster", [(200, 400), (700, 400), (700, 900), (200, 900)]),
    Zone("b_short", "B Short", [(600, 0), (1000, 0), (1000, 500), (600, 500)]),
    Zone("b_site", "B Site", [(800, -800), (1600, -800), (1600, 0), (800, 0)]),
    Zone("water", "Water", [(1000, -600), (1400, -600), (1400, -200), (1000, -200)], priority=2),
    Zone("graffiti", "Graffiti", [(1200, -400), (1500, -400), (1500, -100), (1200, -100)], priority=3),
    Zone("pillar", "Pillar", [(1400, -800), (1800, -800), (1800, -400), (1400, -400)], priority=2),
    Zone("heaven", "Heaven", [(1200, 0), (1600, 0), (1600, 400), (1200, 400)]),
    Zone("ct_spawn", "CT Spawn", [(1400, 600), (2000, 600), (2000, 1200), (1400, 1200)]),
]

# =============================================================================
# ANCIENT ZONES
# =============================================================================
ANCIENT_ZONES = [
    Zone("t_spawn", "T Spawn", [(-1600, -600), (-800, -600), (-800, 0), (-1600, 0)]),
    Zone("mid", "Mid", [(-800, -200), (0, -200), (0, 600), (-800, 600)]),
    Zone("a_main", "A Main", [(-400, 600), (400, 600), (400, 1200), (-400, 1200)]),
    Zone("a_site", "A Site", [(200, 1000), (1000, 1000), (1000, 1800), (200, 1800)]),
    Zone("a_default", "A Default Plant", [(400, 1200), (700, 1200), (700, 1500), (400, 1500)], priority=2),
    Zone("donut", "Donut", [(800, 1200), (1100, 1200), (1100, 1500), (800, 1500)], priority=2),
    Zone("elbow", "Elbow", [(100, 800), (400, 800), (400, 1100), (100, 1100)], priority=2),
    Zone("b_ramp", "B Ramp", [(-1200, 0), (-600, 0), (-600, 600), (-1200, 600)]),
    Zone("b_main", "B Main", [(-1800, 400), (-1200, 400), (-1200, 1000), (-1800, 1000)]),
    Zone("b_site", "B Site", [(-2000, 1000), (-1200, 1000), (-1200, 1800), (-2000, 1800)]),
    Zone("cave", "Cave", [(-1600, 1400), (-1200, 1400), (-1200, 1700), (-1600, 1700)], priority=2),
    Zone("ct_spawn", "CT Spawn", [(600, 1600), (1200, 1600), (1200, 2200), (600, 2200)]),
    Zone("ct_mid", "CT Mid", [(0, 200), (400, 200), (400, 600), (0, 600)]),
]

# =============================================================================
# MAP REGISTRY
# =============================================================================
MAP_ZONES: Dict[str, List[Zone]] = {
    "de_dust2": DUST2_ZONES,
    "de_mirage": MIRAGE_ZONES,
    "de_inferno": INFERNO_ZONES,
    "de_nuke": NUKE_ZONES,
    "de_train": TRAIN_ZONES,
    "de_overpass": OVERPASS_ZONES,
    "de_ancient": ANCIENT_ZONES,
}


class ZoneDetector:
    """
    Detects which zone a coordinate belongs to.
    Uses polygon-based detection with priority resolution.
    """
    
    def __init__(self, map_name: str):
        """Initialize detector for a specific map."""
        self.map_name = map_name.lower()
        self.zones = MAP_ZONES.get(self.map_name, [])
        
        # Sort by priority (highest first) for overlap resolution
        self.zones = sorted(self.zones, key=lambda z: z.priority, reverse=True)
        
        # Pre-compute zone centroids for nearest-zone fallback
        self._centroids = {}
        for zone in self.zones:
            if zone.polygon:
                cx = sum(p[0] for p in zone.polygon) / len(zone.polygon)
                cy = sum(p[1] for p in zone.polygon) / len(zone.polygon)
                self._centroids[zone.name] = (cx, cy)
    
    def get_zone(self, x: float, y: float) -> Optional[Zone]:
        """
        Get the zone for a given coordinate.
        
        Returns highest-priority matching zone, or None if no match.
        """
        for zone in self.zones:
            if point_in_polygon(x, y, zone.polygon):
                return zone
        return None
    
    def get_nearest_zone(self, x: float, y: float) -> Optional[Zone]:
        """
        Get the nearest zone by centroid distance.
        
        Used as fallback when point is outside all polygons.
        NEVER returns None if zones exist.
        """
        if not self.zones:
            return None
        
        min_dist = float('inf')
        nearest = None
        
        for zone in self.zones:
            if zone.name in self._centroids:
                cx, cy = self._centroids[zone.name]
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    nearest = zone
        
        return nearest if nearest else self.zones[0]
    
    def get_callout(self, x: float, y: float) -> str:
        """
        Get the callout name for a coordinate.
        
        NEVER returns 'unknown' - always finds nearest zone.
        """
        # Try exact polygon match first
        zone = self.get_zone(x, y)
        if zone:
            return zone.display_name
        
        # Fallback to nearest zone
        nearest = self.get_nearest_zone(x, y)
        if nearest:
            return nearest.display_name
        
        # Last resort for maps with no zones defined
        return "Mid"  # Default to mid if no zones
    
    def get_callout_key(self, x: float, y: float) -> str:
        """Get the zone key (for grouping/aggregation)."""
        zone = self.get_zone(x, y)
        if zone:
            return zone.name
        
        nearest = self.get_nearest_zone(x, y)
        if nearest:
            return nearest.name
        
        return "mid"


def get_zone_detector(map_name: str) -> ZoneDetector:
    """Factory function to get a zone detector for a map."""
    return ZoneDetector(map_name)
