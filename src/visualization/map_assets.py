"""
Map Assets Manager
Handles downloading and managing map radar images.
"""

import os
import requests
from pathlib import Path
from typing import Optional

class MapAssets:
    """
    Manages map assets (radar images).
    Auto-downloads missing maps from a public repository.
    """
    
    # reliable source for CS2 overviews
    BASE_URL = "https://raw.githubusercontent.com/untago/CS2-Map-Overviews/main/overviews"
    
    def __init__(self, assets_dir: str = "assets/maps"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
    def get_map_image(self, map_name: str) -> Optional[str]:
        """
        Get path to map image. Downloads if missing.
        Returns None if not found and download fails.
        """
        # Normalize name (de_dust2 -> de_dust2)
        if not map_name.startswith("de_") and map_name in ["dust2", "mirage", "inferno", "nuke", "overpass", "ancient", "anubis", "vertigo"]:
            map_name = f"de_{map_name}"
            
        filename = f"{map_name}_radar.png"
        path = self.assets_dir / filename
        
        if path.exists():
            return str(path)
            
        # Try to download
        print(f"  ⬇️ Downloading radar for {map_name}...")
        return self._download_map(map_name, path)
        
    def _download_map(self, map_name: str, target_path: Path) -> Optional[str]:
        """Download map from various sources."""
        # Try a few common naming conventions
        variants = [
            f"{self.BASE_URL}/{map_name}_radar.png",
            f"{self.BASE_URL}/{map_name}_lower_radar.png", # Nuke lower?
            f"https://raw.githubusercontent.com/JoaBroT/CS2-Map-Images/main/{map_name}.png" # Alternative
        ]
        
        for url in variants:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(response.content)
                    print(f"  ✅ Downloaded {map_name} radar to {target_path}")
                    return str(target_path)
            except Exception as e:
                pass
                
        print(f"  ⚠️ Could not download radar for {map_name}")
        return None
