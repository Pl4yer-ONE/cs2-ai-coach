"""
Radar Frame - Optimized video playback for radar replay
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING
from PIL import Image
import os

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, BUTTON_SECONDARY

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class RadarFrame(ctk.CTkFrame):
    """Optimized radar replay video player with image caching."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        
        self.frames_dir: Optional[Path] = None
        self.frame_files: List[Path] = []
        self.current_frame: int = 0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0
        self.after_id: Optional[str] = None
        
        # Image cache for smooth playback
        self._image_cache: dict = {}
        self._cache_size = 50  # Cache ahead/behind frames
        self._current_photo = None
        self._canvas_size = (800, 600)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the radar frame UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=PADDING["large"], pady=(PADDING["medium"], 5))
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="🗺️ Radar Replay",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")
        
        self.frame_label = ctk.CTkLabel(
            header,
            text="",
            font=FONTS["mono"],
            text_color=COLORS["text_secondary"]
        )
        self.frame_label.pack(side="right")
        
        # Main content - centered radar
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING["medium"], pady=5)
        
        # Radar display area - fixed aspect ratio container
        self.radar_container = ctk.CTkFrame(content, fg_color=COLORS["bg_medium"], corner_radius=8)
        self.radar_container.pack(expand=True, fill="both")
        
        # Use a label for image display (simpler and faster than canvas)
        self.radar_label = ctk.CTkLabel(
            self.radar_container,
            text="",
            fg_color="transparent"
        )
        self.radar_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.radar_container,
            text="📡 No radar frames\n\nAnalyze a demo to generate radar replay",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Controls bar
        controls = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=80, corner_radius=8)
        controls.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        controls.pack_propagate(False)
        
        # Progress bar / scrubber
        scrubber_frame = ctk.CTkFrame(controls, fg_color="transparent")
        scrubber_frame.pack(fill="x", padx=PADDING["medium"], pady=(10, 5))
        
        self.scrubber = ctk.CTkSlider(
            scrubber_frame,
            from_=0,
            to=100,
            command=self._on_scrub,
            height=16,
            progress_color=COLORS["accent_green"],
            button_color=COLORS["accent_green"],
            button_hover_color="#4cc45a",
            fg_color=COLORS["bg_light"]
        )
        self.scrubber.pack(fill="x")
        self.scrubber.set(0)
        
        # Playback controls - centered
        buttons_frame = ctk.CTkFrame(controls, fg_color="transparent")
        buttons_frame.pack(pady=5)
        
        # Step back 10
        self.back_btn = ctk.CTkButton(
            buttons_frame, text="⏪", width=45, height=32,
            command=self._step_back, **BUTTON_SECONDARY
        )
        self.back_btn.pack(side="left", padx=2)
        
        # Previous frame
        self.prev_btn = ctk.CTkButton(
            buttons_frame, text="◀", width=45, height=32,
            command=self._prev_frame, **BUTTON_SECONDARY
        )
        self.prev_btn.pack(side="left", padx=2)
        
        # Play/Pause - bigger button
        self.play_btn = ctk.CTkButton(
            buttons_frame, text="▶", width=70, height=32,
            command=self._toggle_play,
            fg_color=COLORS["accent_green"],
            hover_color="#4cc45a",
            text_color="#ffffff",
            font=FONTS["body_bold"]
        )
        self.play_btn.pack(side="left", padx=8)
        
        # Next frame
        self.next_btn = ctk.CTkButton(
            buttons_frame, text="▶", width=45, height=32,
            command=self._next_frame, **BUTTON_SECONDARY
        )
        self.next_btn.pack(side="left", padx=2)
        
        # Step forward 10
        self.fwd_btn = ctk.CTkButton(
            buttons_frame, text="⏩", width=45, height=32,
            command=self._step_forward, **BUTTON_SECONDARY
        )
        self.fwd_btn.pack(side="left", padx=2)
        
        # Speed controls
        speed_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        speed_frame.pack(side="left", padx=20)
        
        self.speed_buttons = {}
        for speed, label in [(0.5, "½×"), (1.0, "1×"), (2.0, "2×"), (4.0, "4×")]:
            is_active = speed == 1.0
            btn = ctk.CTkButton(
                speed_frame, text=label, width=40, height=28,
                command=lambda s=speed: self._set_speed(s),
                fg_color=COLORS["accent_blue"] if is_active else "transparent",
                hover_color=COLORS["bg_hover"],
                text_color="#ffffff" if is_active else COLORS["text_secondary"],
                corner_radius=4
            )
            btn.pack(side="left", padx=1)
            self.speed_buttons[speed] = btn
    
    def load_frames(self, frames_dir: Path):
        """Load radar frames from directory."""
        self.frames_dir = Path(frames_dir) if frames_dir else None
        self._image_cache.clear()
        
        if not self.frames_dir or not self.frames_dir.exists():
            return
        
        # Get sorted frame files
        self.frame_files = sorted(
            [f for f in self.frames_dir.glob("*.png")],
            key=lambda x: int(x.stem.split("_")[-1]) if "_" in x.stem else 0
        )
        
        if not self.frame_files:
            return
        
        # Hide placeholder
        self.placeholder_label.place_forget()
        
        # Update scrubber
        self.scrubber.configure(to=len(self.frame_files) - 1)
        
        # Get container size for scaling
        self.radar_container.update_idletasks()
        self._canvas_size = (
            max(400, self.radar_container.winfo_width() - 20),
            max(400, self.radar_container.winfo_height() - 20)
        )
        
        # Show first frame
        self.current_frame = 0
        self._display_frame(0)
        
        # Pre-cache first few frames
        self._precache_frames(0)
    
    def _precache_frames(self, center: int):
        """Pre-cache frames around the current position."""
        start = max(0, center - self._cache_size // 2)
        end = min(len(self.frame_files), center + self._cache_size // 2)
        
        for i in range(start, end):
            if i not in self._image_cache:
                self._load_image(i)
    
    def _load_image(self, index: int) -> Optional[ctk.CTkImage]:
        """Load and cache an image."""
        if index in self._image_cache:
            return self._image_cache[index]
        
        if index < 0 or index >= len(self.frame_files):
            return None
        
        try:
            frame_path = self.frame_files[index]
            img = Image.open(frame_path)
            
            # Scale to fit container while maintaining aspect ratio
            canvas_w, canvas_h = self._canvas_size
            img_ratio = img.width / img.height
            canvas_ratio = canvas_w / canvas_h
            
            if img_ratio > canvas_ratio:
                new_w = canvas_w
                new_h = int(canvas_w / img_ratio)
            else:
                new_h = canvas_h
                new_w = int(canvas_h * img_ratio)
            
            # Use CTkImage for HiDPI support
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
            
            # Cache with size limit
            if len(self._image_cache) > self._cache_size * 2:
                # Remove oldest entries
                keys_to_remove = list(self._image_cache.keys())[:self._cache_size]
                for k in keys_to_remove:
                    del self._image_cache[k]
            
            self._image_cache[index] = ctk_image
            return ctk_image
            
        except Exception as e:
            print(f"Error loading frame {index}: {e}")
            return None
    
    def _display_frame(self, index: int):
        """Display a specific frame."""
        if not self.frame_files or index < 0 or index >= len(self.frame_files):
            return
        
        self.current_frame = index
        
        # Update label
        self.frame_label.configure(text=f"Frame {index + 1} / {len(self.frame_files)}")
        
        # Update scrubber position (without triggering callback)
        self.scrubber.set(index)
        
        # Load and display image
        photo = self._load_image(index)
        if photo:
            self._current_photo = photo  # Keep reference
            self.radar_label.configure(image=photo)
    
    def _on_scrub(self, value):
        """Handle scrubber sliding."""
        if self.frame_files:
            index = int(value)
            if index != self.current_frame:
                self._display_frame(index)
                self._precache_frames(index)
    
    def _toggle_play(self):
        """Toggle playback."""
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """Start playback."""
        if not self.frame_files:
            return
        self.is_playing = True
        self.play_btn.configure(text="⏸")
        self._playback_loop()
    
    def _pause(self):
        """Pause playback."""
        self.is_playing = False
        self.play_btn.configure(text="▶")
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def _playback_loop(self):
        """Main playback loop - optimized."""
        if not self.is_playing:
            return
        
        # Advance frame
        if self.current_frame < len(self.frame_files) - 1:
            self._display_frame(self.current_frame + 1)
            
            # Background cache next frames
            if self.current_frame % 10 == 0:
                self._precache_frames(self.current_frame)
            
            # Schedule next frame (20fps base, adjusted by speed)
            delay = max(10, int(50 / self.playback_speed))
            self.after_id = self.after(delay, self._playback_loop)
        else:
            # End of video - loop back
            self.current_frame = 0
            self._display_frame(0)
            self._pause()
    
    def _prev_frame(self):
        """Go to previous frame."""
        if self.current_frame > 0:
            self._display_frame(self.current_frame - 1)
    
    def _next_frame(self):
        """Go to next frame."""
        if self.current_frame < len(self.frame_files) - 1:
            self._display_frame(self.current_frame + 1)
    
    def _step_back(self):
        """Step back 10 frames."""
        new_frame = max(0, self.current_frame - 10)
        self._display_frame(new_frame)
        self._precache_frames(new_frame)
    
    def _step_forward(self):
        """Step forward 10 frames."""
        new_frame = min(len(self.frame_files) - 1, self.current_frame + 10)
        self._display_frame(new_frame)
        self._precache_frames(new_frame)
    
    def _set_speed(self, speed: float):
        """Set playback speed."""
        self.playback_speed = speed
        
        # Update button highlighting
        for s, btn in self.speed_buttons.items():
            if s == speed:
                btn.configure(fg_color=COLORS["accent_blue"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])
