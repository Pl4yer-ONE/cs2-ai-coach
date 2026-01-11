"""
Unit tests for map coordinate transformation module.
"""

import pytest
import numpy as np
from pathlib import Path

from src.visualization.map_coords import (
    MapConfig,
    MapRegistry,
    load_map_registry,
    world_to_pixel,
    pixel_to_world,
    normalize_to_grid,
)


class TestMapConfig:
    """Tests for MapConfig dataclass."""
    
    def test_from_dict(self):
        """Test creating MapConfig from dictionary."""
        data = {
            "image": "de_test.png",
            "x_min": -1000,
            "x_max": 1000,
            "y_min": -500,
            "y_max": 500,
            "rotation": 45
        }
        cfg = MapConfig.from_dict("de_test", data)
        
        assert cfg.name == "de_test"
        assert cfg.image == "de_test.png"
        assert cfg.x_min == -1000
        assert cfg.x_max == 1000
        assert cfg.y_min == -500
        assert cfg.y_max == 500
        assert cfg.rotation == 45
    
    def test_width_height(self):
        """Test width and height properties."""
        cfg = MapConfig(
            name="test", image=None,
            x_min=-1000, x_max=1000,
            y_min=-500, y_max=500
        )
        assert cfg.width == 2000
        assert cfg.height == 1000
    
    def test_default(self):
        """Test default config for unknown maps."""
        cfg = MapConfig.default("unknown_map")
        assert cfg.name == "unknown_map"
        assert cfg.image is None
        assert cfg.x_min == -4000
        assert cfg.x_max == 4000


class TestMapRegistry:
    """Tests for MapRegistry singleton."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        MapRegistry.reset()
    
    def test_load_registry(self):
        """Test loading registry from JSON."""
        registry = load_map_registry()
        assert "de_dust2" in registry.available_maps
        assert "de_mirage" in registry.available_maps
    
    def test_get_known_map(self):
        """Test getting config for known map."""
        registry = load_map_registry()
        cfg = registry.get("de_dust2")
        
        assert cfg.name == "de_dust2"
        assert cfg.image == "de_dust2.png"
        assert cfg.x_min == -2476
    
    def test_get_unknown_map(self):
        """Test getting config for unknown map returns default."""
        registry = load_map_registry()
        cfg = registry.get("de_nonexistent")
        
        assert cfg.name == "de_nonexistent"
        assert cfg.x_min == -4000
        assert cfg.x_max == 4000
    
    def test_normalize_map_name(self):
        """Test that map names are normalized."""
        registry = load_map_registry()
        
        # Without de_ prefix
        cfg1 = registry.get("dust2")
        cfg2 = registry.get("de_dust2")
        
        assert cfg1.name == cfg2.name


class TestWorldToPixel:
    """Tests for coordinate transformation."""
    
    @pytest.fixture
    def simple_config(self):
        """Simple 1000x1000 unit config for easy math."""
        return MapConfig(
            name="test", image=None,
            x_min=0, x_max=1000,
            y_min=0, y_max=1000
        )
    
    def test_origin(self, simple_config):
        """Test world origin transforms correctly."""
        # World (0, 0) should be at pixel (0, img_h) due to Y inversion
        px, py = world_to_pixel(0, 0, simple_config, 1000, 1000)
        
        assert px == 0
        assert py == 1000  # Y inverted
    
    def test_max_corner(self, simple_config):
        """Test max world corner transforms correctly."""
        # World (1000, 1000) should be at pixel (1000, 0)
        px, py = world_to_pixel(1000, 1000, simple_config, 1000, 1000)
        
        assert px == 1000
        assert py == 0  # Y inverted
    
    def test_center(self, simple_config):
        """Test center point."""
        px, py = world_to_pixel(500, 500, simple_config, 1000, 1000)
        
        assert px == 500
        assert py == 500
    
    def test_y_inversion(self, simple_config):
        """Test Y axis is properly inverted."""
        # Higher world Y = lower pixel Y
        _, py1 = world_to_pixel(0, 100, simple_config, 1000, 1000)
        _, py2 = world_to_pixel(0, 900, simple_config, 1000, 1000)
        
        assert py1 > py2  # World Y=100 -> higher pixel Y than world Y=900
    
    def test_vectorized(self, simple_config):
        """Test vectorized input."""
        x = np.array([0, 500, 1000])
        y = np.array([0, 500, 1000])
        
        px, py = world_to_pixel(x, y, simple_config, 1000, 1000)
        
        np.testing.assert_array_equal(px, [0, 500, 1000])
        np.testing.assert_array_equal(py, [1000, 500, 0])
    
    def test_real_map_dust2(self):
        """Test with actual de_dust2 bounds."""
        MapRegistry.reset()
        registry = load_map_registry()
        cfg = registry.get("de_dust2")
        
        # Center of dust2 world
        center_x = (cfg.x_min + cfg.x_max) / 2
        center_y = (cfg.y_min + cfg.y_max) / 2
        
        px, py = world_to_pixel(center_x, center_y, cfg, 1024, 1024)
        
        # Should be approximately at image center
        assert abs(px - 512) < 1
        assert abs(py - 512) < 1


class TestPixelToWorld:
    """Tests for inverse transformation."""
    
    @pytest.fixture
    def simple_config(self):
        return MapConfig(
            name="test", image=None,
            x_min=0, x_max=1000,
            y_min=0, y_max=1000
        )
    
    def test_roundtrip(self, simple_config):
        """Test world->pixel->world roundtrip."""
        original_x, original_y = 300.0, 700.0
        
        px, py = world_to_pixel(original_x, original_y, simple_config, 1000, 1000)
        recovered_x, recovered_y = pixel_to_world(px, py, simple_config, 1000, 1000)
        
        assert abs(recovered_x - original_x) < 0.001
        assert abs(recovered_y - original_y) < 0.001


class TestNormalizeToGrid:
    """Tests for grid normalization."""
    
    def test_clipping(self):
        """Test out-of-bounds coordinates are clipped."""
        cfg = MapConfig(
            name="test", image=None,
            x_min=0, x_max=1000,
            y_min=0, y_max=1000
        )
        
        # Coordinates outside bounds
        x = np.array([-100, 500, 1500])
        y = np.array([-100, 500, 1500])
        
        gx, gy = normalize_to_grid(x, y, cfg, 100)
        
        # Should be clipped to [0, 99]
        assert gx.min() >= 0
        assert gx.max() <= 99
        assert gy.min() >= 0
        assert gy.max() <= 99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
