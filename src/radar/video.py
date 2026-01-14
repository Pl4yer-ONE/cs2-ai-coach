# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.

"""
Radar Video Encoder
Encodes PNG frames to MP4 video using ffmpeg.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


def encode_video(
    frames_dir: str,
    output_file: str,
    fps: int = 20,
    frame_pattern: str = "frame_%05d.png",
    quality: int = 23  # CRF: 0-51, lower = better quality, 23 is default
) -> Optional[str]:
    """
    Encode PNG frames to MP4 video.
    
    Args:
        frames_dir: Directory containing frame PNGs
        output_file: Output MP4 path
        fps: Frames per second
        frame_pattern: Frame filename pattern
        quality: Video quality (CRF value, lower = better)
        
    Returns:
        Path to output video, or None if failed
    """
    if not check_ffmpeg():
        print("  ⚠️ ffmpeg not found. Install with: brew install ffmpeg")
        return None
    
    frames_path = Path(frames_dir)
    if not frames_path.exists():
        print(f"  ⚠️ Frames directory not found: {frames_dir}")
        return None
    
    # Count frames
    frame_files = list(frames_path.glob("frame_*.png"))
    if not frame_files:
        print("  ⚠️ No frame files found")
        return None
    
    print(f"  Encoding {len(frame_files)} frames to video...")
    
    input_pattern = str(frames_path / frame_pattern)
    
    cmd = [
        "ffmpeg",
        "-y",                           # Overwrite output
        "-r", str(fps),                 # Input frame rate
        "-i", input_pattern,            # Input pattern
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # Ensure even dimensions
        "-c:v", "libx264",              # H.264 codec
        "-pix_fmt", "yuv420p",          # Pixel format for compatibility
        "-crf", str(quality),           # Quality
        "-preset", "fast",              # Encoding speed
        "-movflags", "+faststart",      # Web optimization
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        output_path = Path(output_file)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ Video saved: {output_file} ({size_mb:.1f} MB)")
            return str(output_path)
        else:
            print("  ⚠️ Video encoding failed - no output file")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️ ffmpeg error: {e.stderr}")
        return None
    except Exception as e:
        print(f"  ⚠️ Encoding error: {e}")
        return None


def encode_gif(
    frames_dir: str,
    output_file: str,
    fps: int = 10,
    frame_pattern: str = "frame_%05d.png",
    scale: int = 512  # Resize for smaller GIF
) -> Optional[str]:
    """
    Encode PNG frames to GIF.
    
    Args:
        frames_dir: Directory containing frame PNGs
        output_file: Output GIF path
        fps: Frames per second
        frame_pattern: Frame filename pattern
        scale: Output width (aspect ratio preserved)
        
    Returns:
        Path to output GIF, or None if failed
    """
    if not check_ffmpeg():
        print("  ⚠️ ffmpeg not found")
        return None
    
    frames_path = Path(frames_dir)
    input_pattern = str(frames_path / frame_pattern)
    
    # Two-pass for better quality GIF
    palette_file = "/tmp/palette.png"
    
    # Generate palette
    palette_cmd = [
        "ffmpeg",
        "-y",
        "-r", str(fps),
        "-i", input_pattern,
        "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,palettegen",
        palette_file
    ]
    
    # Generate GIF
    gif_cmd = [
        "ffmpeg",
        "-y",
        "-r", str(fps),
        "-i", input_pattern,
        "-i", palette_file,
        "-lavfi", f"fps={fps},scale={scale}:-1:flags=lanczos[x];[x][1:v]paletteuse",
        output_file
    ]
    
    try:
        subprocess.run(palette_cmd, capture_output=True, check=True)
        subprocess.run(gif_cmd, capture_output=True, check=True)
        
        output_path = Path(output_file)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ GIF saved: {output_file} ({size_mb:.1f} MB)")
            return str(output_path)
            
    except Exception as e:
        print(f"  ⚠️ GIF encoding error: {e}")
        return None
    
    return None
