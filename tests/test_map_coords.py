"""
Unit tests for map coordinate transformation module.
Updated to match current API (pos_x, pos_y, scale based).
"""

import pytest
import numpy as np
from pathlib import Path

from src.visualization.map_coords import (
    MapConfig,
    MapRegistry,
    load_map_registry,
    world_to_radar,
    radar_to_world,
)


class TestMapConfig:
    """Tests for MapConfig dataclass."""
    
    def test_from_dict(self):
        """Test creating MapConfig from dictionary."""
        data = {
            "pos_x": -2476,
            "pos_y": 3239,
            "scale": 4.4,
        }
        cfg = MapConfig.from_dict("de_test", data)
        
        assert cfg.name == "de_test"
        assert cfg.pos_x == -2476
        assert cfg.pos_y == 3239
        assert cfg.scale == 4.4
    
    def test_default(self):
        """Test default config for unknown maps."""
        cfg = MapConfig.default("unknown_map")
        assert cfg.name == "unknown_map"
        assert cfg.pos_x == -3000
        assert cfg.pos_y == 2000
        assert cfg.scale == 5.0


class TestMapRegistry:
    """Tests for MapRegistry singleton."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        MapRegistry._instance = None
        MapRegistry._configs = {}
    
    def test_load_registry(self):
        """Test loading registry returns known maps."""
        registry = load_map_registry()
        cfg = registry.get("de_dust2")
        assert cfg is not None
        assert cfg.name == "de_dust2"
    
    def test_get_known_map(self):
        """Test getting config for known map."""
        registry = load_map_registry()
        cfg = registry.get("de_dust2")
        
        assert cfg.name == "de_dust2"
        assert cfg.pos_x == -2476
        assert cfg.scale == 4.4
    
    def test_get_unknown_map(self):
        """Test getting config for unknown map returns default."""
        registry = load_map_registry()
        cfg = registry.get("de_nonexistent")
        
        assert cfg.name == "de_nonexistent"
        assert cfg.pos_x == -3000  # Default
        assert cfg.scale == 5.0    # Default
    
    def test_normalize_map_name(self):
        """Test that map names are normalized."""
        registry = load_map_registry()
        
        # Without de_ prefix
        cfg1 = registry.get("dust2")
        cfg2 = registry.get("de_dust2")
        
        assert cfg1.name == cfg2.name


class TestWorldToRadar:
    """Tests for coordinate transformation."""
    
    @pytest.fixture
    def dust2_config(self):
        """Config for de_dust2."""
        return MapConfig(
            name="de_dust2", 
            pos_x=-2476, 
            pos_y=3239, 
            scale=4.4
        )
    
    def test_origin_transformation(self, dust2_config):
        """Test that pos_x, pos_y maps to pixel (0, 0)."""
        px, py = world_to_radar(
            dust2_config.pos_x, 
            dust2_config.pos_y, 
            dust2_config, 
            1024
        )
        
        assert abs(px) < 0.001
        assert abs(py) < 0.001
    
    def test_scale_applied(self, dust2_config):
        """Test that scale correctly converts distance."""
        # Move 440 units in world X (100 scale units)
        px, py = world_to_radar(
            dust2_config.pos_x + 440,  # 440 / 4.4 = 100 pixels
            dust2_config.pos_y,
            dust2_config,
            1024
        )
        
        assert abs(px - 100) < 0.001
        assert abs(py) < 0.001
    
    def test_y_inversion(self, dust2_config):
        """Test Y axis is properly inverted (world Y down = pixel Y up)."""
        # Moving down in world Y = moving up in pixel Y
        _, py1 = world_to_radar(0, dust2_config.pos_y - 100, dust2_config, 1024)
        _, py2 = world_to_radar(0, dust2_config.pos_y - 200, dust2_config, 1024)
        
        # Lower world Y = higher pixel Y
        assert py2 > py1
    
    def test_vectorized(self, dust2_config):
        """Test vectorized input."""
        x = np.array([dust2_config.pos_x, dust2_config.pos_x + 440])
        y = np.array([dust2_config.pos_y, dust2_config.pos_y])
        
        px, py = world_to_radar(x, y, dust2_config, 1024)
        
        np.testing.assert_array_almost_equal(px, [0, 100], decimal=3)
        np.testing.assert_array_almost_equal(py, [0, 0], decimal=3)


class TestRadarToWorld:
    """Tests for inverse transformation."""
    
    @pytest.fixture
    def dust2_config(self):
        return MapConfig(
            name="de_dust2", 
            pos_x=-2476, 
            pos_y=3239, 
            scale=4.4
        )
    
    def test_roundtrip(self, dust2_config):
        """Test world->radar->world roundtrip."""
        original_x, original_y = -1500.0, 2500.0
        
        px, py = world_to_radar(original_x, original_y, dust2_config, 1024)
        recovered_x, recovered_y = radar_to_world(px, py, dust2_config, 1024)
        
        assert abs(recovered_x - original_x) < 0.001
        assert abs(recovered_y - original_y) < 0.001
    
    def test_different_img_size(self, dust2_config):
        """Test roundtrip with non-standard image size."""
        original_x, original_y = -2000.0, 3000.0
        
        # Use 2048x2048 image
        px, py = world_to_radar(original_x, original_y, dust2_config, 2048)
        recovered_x, recovered_y = radar_to_world(px, py, dust2_config, 2048)
        
        assert abs(recovered_x - original_x) < 0.001
        assert abs(recovered_y - original_y) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
