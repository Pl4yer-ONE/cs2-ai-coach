"""
Home Frame - Welcome screen and demo selection
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, BUTTON, BUTTON_SECONDARY

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class HomeFrame(ctk.CTkFrame):
    """Home/welcome screen with demo selection."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        self.current_demo: Optional[Path] = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the home frame UI."""
        # Center container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")
        
        # Logo/Title
        title = ctk.CTkLabel(
            center,
            text="🎯 FragAudit",
            font=("Segoe UI", 48, "bold"),
            text_color=COLORS["accent_cyan"]
        )
        title.pack(pady=(0, 10))
        
        subtitle = ctk.CTkLabel(
            center,
            text="AI-Powered CS2 Demo Analyzer",
            font=FONTS["heading"],
            text_color=COLORS["text_secondary"]
        )
        subtitle.pack(pady=(0, 40))
        
        # Drop zone
        self.drop_zone = ctk.CTkFrame(
            center,
            width=500,
            height=200,
            **FRAME
        )
        self.drop_zone.pack(pady=20)
        self.drop_zone.pack_propagate(False)
        
        # Drop zone content
        drop_icon = ctk.CTkLabel(
            self.drop_zone,
            text="📂",
            font=("Segoe UI", 48)
        )
        drop_icon.pack(pady=(40, 10))
        
        self.drop_label = ctk.CTkLabel(
            self.drop_zone,
            text="Drop a .dem file here or click to browse",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        )
        self.drop_label.pack()
        
        browse_btn = ctk.CTkButton(
            self.drop_zone,
            text="Browse Files",
            command=self._browse_demo,
            width=150,
            **BUTTON_SECONDARY
        )
        browse_btn.pack(pady=20)
        
        # Selected demo info
        self.demo_info = ctk.CTkFrame(center, fg_color="transparent")
        self.demo_info.pack(pady=20)
        
        self.demo_label = ctk.CTkLabel(
            self.demo_info,
            text="",
            font=FONTS["body_bold"],
            text_color=COLORS["accent_green"]
        )
        self.demo_label.pack()
        
        # Quick start button
        self.start_btn = ctk.CTkButton(
            center,
            text="▶ Start Analysis",
            command=self._start_analysis,
            width=200,
            height=50,
            font=FONTS["heading"],
            state="disabled",
            **BUTTON
        )
        self.start_btn.pack(pady=20)
        
        # Features list
        features_frame = ctk.CTkFrame(center, fg_color="transparent")
        features_frame.pack(pady=30)
        
        features = [
            ("📊", "Player Stats & Ratings"),
            ("🗺️", "Radar Replay"),
            ("⚠️", "Mistake Detection"),
            ("🤖", "AI Coach Advice")
        ]
        
        for icon, text in features:
            feat = ctk.CTkLabel(
                features_frame,
                text=f"{icon} {text}",
                font=FONTS["body"],
                text_color=COLORS["text_secondary"]
            )
            feat.pack(side="left", padx=20)
    
    def _browse_demo(self):
        """Open file browser for demo selection."""
        self.app._open_demo()
    
    def _start_analysis(self):
        """Start analysis of selected demo."""
        self.app._run_analysis()
    
    def set_demo(self, path: Path):
        """Set the selected demo file."""
        self.current_demo = path
        self.demo_label.configure(text=f"✓ Selected: {path.name}")
        self.start_btn.configure(state="normal")
        
        # Update drop zone visual
        self.drop_label.configure(
            text=path.name,
            text_color=COLORS["accent_green"]
        )
