# CS2 Radar Map Images

## Overview

This folder stores community-sourced radar images for CS2 maps. These images are used as overlays for heatmap visualization.

## Required Files

Place PNG radar images here with the following naming convention:

| Map | Filename |
|-----|----------|
| Dust 2 | `de_dust2.png` |
| Mirage | `de_mirage.png` |
| Inferno | `de_inferno.png` |
| Nuke | `de_nuke.png` |
| Overpass | `de_overpass.png` |
| Ancient | `de_ancient.png` |
| Anubis | `de_anubis.png` |
| Vertigo | `de_vertigo.png` |

## Image Requirements

- **Format**: PNG (with transparency preferred)
- **Resolution**: Recommended 1024x1024 or similar square aspect
- **Orientation**: Standard radar orientation (spawn areas at bottom)

## Legal Notice

> **Important**: We do NOT bundle Valve game files. You must obtain radar images from community sources or create your own.

### Community Sources

- [CS2 Radar Images on GitHub](https://github.com/search?q=cs2+radar+images)
- [GameBanana CS2 Resources](https://gamebanana.com/games/20313)
- [Simple Radar](https://readtldr.gg/simpleradar)

## Configuration

Map bounds are defined in `map_registry.json`. If you add a custom map, update the JSON with:

```json
{
  "de_yourmap": {
    "image": "de_yourmap.png",
    "x_min": -3000,
    "x_max": 3000,
    "y_min": -3000,
    "y_max": 3000,
    "rotation": 0
  }
}
```

Bounds can be found using `getpos` command in CS2 console at map corners.
