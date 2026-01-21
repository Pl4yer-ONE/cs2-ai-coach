"""
Radar Frame - Video playback for radar replay
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING
from PIL import Image, ImageTk
import os

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, BUTTON_SECONDARY

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class RadarFrame(ctk.CTkFrame):
    """Radar replay video player."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        
        self.frames_dir: Optional[Path] = None
        self.frame_files: List[Path] = []
        self.current_frame: int = 0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0
        self.after_id: Optional[str] = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the radar frame UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        
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
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        )
        self.frame_label.pack(side="right")
        
        # Main content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING["large"], pady=PADDING["medium"])
        
        # Radar display area
        self.radar_frame = ctk.CTkFrame(content, **FRAME)
        self.radar_frame.pack(fill="both", expand=True)
        
        # Canvas for radar image
        self.canvas = ctk.CTkCanvas(
            self.radar_frame,
            bg=COLORS["bg_medium"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.radar_frame,
            text="No radar frames available.\nRun analysis with radar option enabled.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Controls bar
        controls = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=60)
        controls.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        controls.pack_propagate(False)
        
        # Progress bar / scrubber
        self.progress_frame = ctk.CTkFrame(controls, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=PADDING["medium"], pady=5)
        
        self.scrubber = ctk.CTkSlider(
            self.progress_frame,
            from_=0,
            to=100,
            command=self._on_scrub,
            progress_color=COLORS["accent_cyan"],
            button_color=COLORS["accent_cyan"],
            button_hover_color="#3db8b0"
        )
        self.scrubber.pack(fill="x")
        self.scrubber.set(0)
        
        # Playback controls
        buttons_frame = ctk.CTkFrame(controls, fg_color="transparent")
        buttons_frame.pack(pady=5)
        
        # Step back
        self.back_btn = ctk.CTkButton(
            buttons_frame,
            text="◀◀",
            width=50,
            command=self._step_back,
            **BUTTON_SECONDARY
        )
        self.back_btn.pack(side="left", padx=2)
        
        # Previous frame
        self.prev_btn = ctk.CTkButton(
            buttons_frame,
            text="◀",
            width=50,
            command=self._prev_frame,
            **BUTTON_SECONDARY
        )
        self.prev_btn.pack(side="left", padx=2)
        
        # Play/Pause
        self.play_btn = ctk.CTkButton(
            buttons_frame,
            text="▶",
            width=80,
            command=self._toggle_play,
            fg_color=COLORS["accent_cyan"],
            hover_color="#3db8b0",
            text_color=COLORS["bg_dark"]
        )
        self.play_btn.pack(side="left", padx=5)
        
        # Next frame
        self.next_btn = ctk.CTkButton(
            buttons_frame,
            text="▶",
            width=50,
            command=self._next_frame,
            **BUTTON_SECONDARY
        )
        self.next_btn.pack(side="left", padx=2)
        
        # Step forward
        self.fwd_btn = ctk.CTkButton(
            buttons_frame,
            text="▶▶",
            width=50,
            command=self._step_forward,
            **BUTTON_SECONDARY
        )
        self.fwd_btn.pack(side="left", padx=2)
        
        # Speed controls
        speed_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        speed_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            speed_frame,
            text="Speed:",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=5)
        
        for speed, label in [(0.5, "0.5x"), (1.0, "1x"), (2.0, "2x"), (4.0, "4x")]:
            btn = ctk.CTkButton(
                speed_frame,
                text=label,
                width=50,
                command=lambda s=speed: self._set_speed(s),
                fg_color="transparent" if speed != 1.0 else COLORS["accent_cyan"],
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"] if speed != 1.0 else COLORS["bg_dark"]
            )
            btn.pack(side="left", padx=2)
            
            # Store reference for highlighting
            if not hasattr(self, 'speed_buttons'):
                self.speed_buttons = {}
            self.speed_buttons[speed] = btn
        
        # Current image reference (keep in memory)
        self._current_image = None
        self._current_photo = None
    
    def load_frames(self, frames_dir: Path):
        """Load radar frames from directory."""
        self.frames_dir = frames_dir
        
        if not frames_dir.exists():
            return
        
        # Get sorted frame files
        self.frame_files = sorted(
            [f for f in frames_dir.glob("*.png")],
            key=lambda x: int(x.stem.split("_")[-1]) if "_" in x.stem else 0
        )
        
        if not self.frame_files:
            return
        
        # Hide placeholder
        self.placeholder_label.place_forget()
        
        # Update scrubber
        self.scrubber.configure(to=len(self.frame_files) - 1)
        
        # Show first frame
        self.current_frame = 0
        self._display_frame(0)
    
    def _display_frame(self, index: int):
        """Display a specific frame."""
        if not self.frame_files or index < 0 or index >= len(self.frame_files):
            return
        
        self.current_frame = index
        frame_path = self.frame_files[index]
        
        # Update label
        self.frame_label.configure(text=f"Frame {index + 1} / {len(self.frame_files)}")
        
        # Update scrubber position
        self.scrubber.set(index)
        
        # Load and display image
        try:
            # Get canvas size
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            if canvas_w <= 1 or canvas_h <= 1:
                canvas_w, canvas_h = 800, 800
            
            # Load image
            img = Image.open(frame_path)
            
            # Calculate size to fit while maintaining aspect ratio
            img_ratio = img.width / img.height
            canvas_ratio = canvas_w / canvas_h
            
            if img_ratio > canvas_ratio:
                new_w = canvas_w
                new_h = int(canvas_w / img_ratio)
            else:
                new_h = canvas_h
                new_w = int(canvas_h * img_ratio)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self._current_image = img
            self._current_photo = ImageTk.PhotoImage(img)
            
            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_w // 2, canvas_h // 2,
                image=self._current_photo,
                anchor="center"
            )
            
        except Exception as e:
            print(f"Error loading frame: {e}")
    
    def _on_scrub(self, value):
        """Handle scrubber sliding."""
        if self.frame_files:
            index = int(value)
            self._display_frame(index)
    
    def _toggle_play(self):
        """Toggle playback."""
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """Start playback."""
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
        """Main playback loop."""
        if not self.is_playing:
            return
        
        # Advance frame
        if self.current_frame < len(self.frame_files) - 1:
            self._display_frame(self.current_frame + 1)
            
            # Schedule next frame (base 50ms = 20fps, adjusted by speed)
            delay = int(50 / self.playback_speed)
            self.after_id = self.after(delay, self._playback_loop)
        else:
            # End of video
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
    
    def _step_forward(self):
        """Step forward 10 frames."""
        new_frame = min(len(self.frame_files) - 1, self.current_frame + 10)
        self._display_frame(new_frame)
    
    def _set_speed(self, speed: float):
        """Set playback speed."""
        self.playback_speed = speed
        
        # Update button highlighting
        for s, btn in self.speed_buttons.items():
            if s == speed:
                btn.configure(fg_color=COLORS["accent_cyan"], text_color=COLORS["bg_dark"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_primary"])
