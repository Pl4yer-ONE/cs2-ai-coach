"""
FragAudit Desktop Application
Main application window and navigation
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict, Any

from src.ui.theme import COLORS, FONTS, WINDOW, PADDING, BUTTON, BUTTON_SECONDARY
from src.ui.frames.home import HomeFrame
from src.ui.frames.analysis import AnalysisFrame
from src.ui.frames.mistakes import MistakesFrame
from src.ui.frames.radar import RadarFrame


class FragAuditApp(ctk.CTk):
    """Main FragAudit desktop application."""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("🎯 FragAudit v3.9.0 - CS2 Demo Analyzer")
        self.geometry(f"{WINDOW['width']}x{WINDOW['height']}")
        self.minsize(WINDOW['min_width'], WINDOW['min_height'])
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # State
        self.current_demo: Optional[Path] = None
        self.analysis_result: Optional[Dict[str, Any]] = None
        self.radar_frames_dir: Optional[Path] = None
        
        # Build UI
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Show home by default
        self.show_frame("home")
    
    def _create_header(self):
        """Create top header with logo and main actions."""
        self.header = ctk.CTkFrame(self, height=60, fg_color=COLORS["bg_medium"], corner_radius=0)
        self.header.pack(fill="x", padx=0, pady=0)
        self.header.pack_propagate(False)
        
        # Logo
        self.logo_label = ctk.CTkLabel(
            self.header,
            text="🎯 FragAudit",
            font=FONTS["heading_large"],
            text_color=COLORS["accent_cyan"]
        )
        self.logo_label.pack(side="left", padx=PADDING["large"])
        
        # Action buttons frame
        actions_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        actions_frame.pack(side="left", padx=PADDING["large"])
        
        # Open Demo button
        self.open_btn = ctk.CTkButton(
            actions_frame,
            text="📂 Open Demo",
            command=self._open_demo,
            **BUTTON_SECONDARY
        )
        self.open_btn.pack(side="left", padx=5)
        
        # Analyze button
        self.analyze_btn = ctk.CTkButton(
            actions_frame,
            text="▶ Analyze",
            command=self._run_analysis,
            state="disabled",
            **BUTTON
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        # Fast mode toggle
        self.fast_mode = ctk.BooleanVar(value=True)
        self.fast_toggle = ctk.CTkSwitch(
            actions_frame,
            text="⚡ Fast Radar",
            variable=self.fast_mode,
            onvalue=True,
            offvalue=False,
            progress_color=COLORS["accent_cyan"]
        )
        self.fast_toggle.pack(side="left", padx=20)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            actions_frame,
            text="💾 Export",
            command=self._export_report,
            state="disabled",
            **BUTTON_SECONDARY
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Right side - nav tabs
        nav_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        nav_frame.pack(side="right", padx=PADDING["large"])
        
        self.nav_buttons = {}
        for name, label in [("home", "🏠 Home"), ("analysis", "📊 Stats"), 
                            ("mistakes", "⚠️ Mistakes"), ("radar", "🗺️ Radar")]:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                width=100,
                command=lambda n=name: self.show_frame(n),
                **BUTTON_SECONDARY
            )
            btn.pack(side="left", padx=2)
            self.nav_buttons[name] = btn
    
    def _create_main_content(self):
        """Create main content area with frames."""
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.content.pack(fill="both", expand=True, padx=PADDING["medium"], pady=PADDING["medium"])
        
        # Initialize frames
        self.frames: Dict[str, ctk.CTkFrame] = {}
        
        self.frames["home"] = HomeFrame(self.content, self)
        self.frames["analysis"] = AnalysisFrame(self.content, self)
        self.frames["mistakes"] = MistakesFrame(self.content, self)
        self.frames["radar"] = RadarFrame(self.content, self)
        
        for frame in self.frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    def _create_status_bar(self):
        """Create bottom status bar."""
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=COLORS["bg_medium"], corner_radius=0)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready - Select a demo file to begin",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="left", padx=PADDING["medium"])
        
        # Progress bar (hidden by default)
        self.progress = ctk.CTkProgressBar(
            self.status_bar,
            width=200,
            height=10,
            progress_color=COLORS["accent_cyan"]
        )
        self.progress.set(0)
    
    def show_frame(self, name: str):
        """Show a specific frame and update nav highlighting."""
        if name in self.frames:
            self.frames[name].tkraise()
            
            # Update nav button highlighting
            for btn_name, btn in self.nav_buttons.items():
                if btn_name == name:
                    btn.configure(fg_color=COLORS["accent_cyan"], text_color=COLORS["bg_dark"])
                else:
                    btn.configure(fg_color="transparent", text_color=COLORS["text_primary"])
    
    def set_status(self, message: str):
        """Update status bar message."""
        self.status_label.configure(text=message)
    
    def show_progress(self, show: bool = True):
        """Show or hide progress bar."""
        if show:
            self.progress.pack(side="right", padx=PADDING["medium"])
        else:
            self.progress.pack_forget()
    
    def set_progress(self, value: float):
        """Set progress bar value (0-1)."""
        self.progress.set(value)
    
    def _open_demo(self):
        """Open file dialog to select demo."""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            title="Select CS2 Demo File",
            filetypes=[("Demo files", "*.dem"), ("All files", "*.*")]
        )
        
        if filepath:
            self.current_demo = Path(filepath)
            self.set_status(f"Loaded: {self.current_demo.name}")
            self.analyze_btn.configure(state="normal")
            
            # Update home frame
            self.frames["home"].set_demo(self.current_demo)
    
    def _run_analysis(self):
        """Run analysis in background thread."""
        if not self.current_demo:
            return
        
        from src.ui.services.analyzer import run_analysis_thread
        
        self.analyze_btn.configure(state="disabled", text="⏳ Analyzing...")
        self.show_progress(True)
        self.set_status(f"Analyzing {self.current_demo.name}...")
        
        # Run in thread
        run_analysis_thread(
            self,
            self.current_demo,
            fast_radar=self.fast_mode.get(),
            on_progress=self._on_analysis_progress,
            on_complete=self._on_analysis_complete,
            on_error=self._on_analysis_error
        )
    
    def _on_analysis_progress(self, progress: float, message: str):
        """Handle analysis progress updates."""
        self.set_progress(progress)
        self.set_status(message)
    
    def _on_analysis_complete(self, result: Dict[str, Any], radar_dir: Optional[Path]):
        """Handle analysis completion."""
        self.analysis_result = result
        self.radar_frames_dir = radar_dir
        
        self.analyze_btn.configure(state="normal", text="▶ Analyze")
        self.export_btn.configure(state="normal")
        self.show_progress(False)
        self.set_status(f"✓ Analysis complete - {len(result.get('players', {}))} players analyzed")
        
        # Update frames with results
        self.frames["analysis"].load_results(result)
        self.frames["mistakes"].load_results(result)
        if radar_dir:
            self.frames["radar"].load_frames(radar_dir)
        
        # Switch to analysis view
        self.show_frame("analysis")
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.analyze_btn.configure(state="normal", text="▶ Analyze")
        self.show_progress(False)
        self.set_status(f"❌ Error: {error}")
    
    def _export_report(self):
        """Export analysis report."""
        if not self.analysis_result:
            return
        
        from tkinter import filedialog
        from src.report import ReportGenerator
        from src.report.html_reporter import HTMLReporter
        
        filepath = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".html",
            filetypes=[
                ("HTML Report", "*.html"),
                ("JSON Report", "*.json"),
                ("CSV Export", "*.csv")
            ]
        )
        
        if filepath:
            path = Path(filepath)
            
            if path.suffix == ".html":
                reporter = HTMLReporter()
                reporter.save(self.analysis_result, str(path))
            elif path.suffix == ".json":
                generator = ReportGenerator()
                generator.save_json(self.analysis_result, str(path))
            elif path.suffix == ".csv":
                self._export_csv(path)
            
            self.set_status(f"✓ Exported to {path.name}")
    
    def _export_csv(self, path: Path):
        """Export mistakes to CSV."""
        import csv
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Player', 'Round', 'Type', 'Severity', 'Location', 'Details'])
            
            for player_id, player_data in self.analysis_result.get('players', {}).items():
                player_name = player_data.get('player_name', player_id)
                for m in player_data.get('mistakes', []):
                    writer.writerow([
                        player_name,
                        m.get('round', ''),
                        m.get('type', ''),
                        m.get('severity', ''),
                        m.get('location', ''),
                        m.get('details', '')
                    ])
    
    def run(self):
        """Start the application."""
        self.mainloop()


if __name__ == "__main__":
    app = FragAuditApp()
    app.run()
