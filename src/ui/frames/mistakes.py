"""
Mistakes Frame - Mistake cards and AI advice
"""

import customtkinter as ctk
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, CARD, SEVERITY_COLORS

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class MistakesFrame(ctk.CTkFrame):
    """Mistakes display with AI coach advice."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        self.result: Optional[Dict[str, Any]] = None
        self.current_filter: Optional[str] = None  # Player filter
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the mistakes frame UI."""
        # Header with filter
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        
        title = ctk.CTkLabel(
            header,
            text="⚠️ Mistakes & Recommendations",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")
        
        # Filter dropdown
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="right")
        
        ctk.CTkLabel(
            filter_frame,
            text="Filter by:",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 10))
        
        self.player_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=["All Players"],
            command=self._on_filter_change,
            fg_color=COLORS["bg_light"],
            button_color=COLORS["bg_hover"],
            button_hover_color=COLORS["accent_cyan"],
            dropdown_fg_color=COLORS["bg_medium"]
        )
        self.player_filter.pack(side="left")
        
        # Main content - two columns with proper weights
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING["large"], pady=PADDING["medium"])
        
        # Configure grid for proper column sizing
        content.grid_columnconfigure(0, weight=3)  # Mistakes list gets more space
        content.grid_columnconfigure(1, weight=1)  # AI coach fixed width
        content.grid_rowconfigure(0, weight=1)
        
        # Left: Mistakes list
        left_frame = ctk.CTkFrame(content, **FRAME)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING["medium"]))
        
        left_header = ctk.CTkLabel(
            left_frame,
            text="📋 Issues Found",
            font=FONTS["subheading"],
            text_color=COLORS["text_primary"]
        )
        left_header.pack(anchor="w", padx=PADDING["medium"], pady=PADDING["medium"])
        
        self.mistakes_scroll = ctk.CTkScrollableFrame(
            left_frame,
            fg_color="transparent"
        )
        self.mistakes_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right: AI advice (fixed width sidebar)
        right_frame = ctk.CTkFrame(content, width=380, **FRAME)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_propagate(False)
        
        # AI Header
        ai_header = ctk.CTkFrame(right_frame, fg_color="transparent", height=40)
        ai_header.pack(fill="x", padx=PADDING["medium"], pady=PADDING["medium"])
        ai_header.pack_propagate(False)
        
        ctk.CTkLabel(
            ai_header,
            text="🤖 AI Coach",
            font=FONTS["heading"],
            text_color=COLORS["accent_cyan"]
        ).pack(side="left", anchor="w")
        
        self.ai_status = ctk.CTkLabel(
            ai_header,
            text="",
            font=FONTS["small"],
            text_color=COLORS["text_muted"]
        )
        self.ai_status.pack(side="right", anchor="e")
        
        # AI advice content - scrollable
        self.ai_content = ctk.CTkScrollableFrame(
            right_frame,
            fg_color=COLORS["bg_light"],
            corner_radius=10
        )
        self.ai_content.pack(fill="both", expand=True, padx=PADDING["medium"], pady=(0, PADDING["small"]))
        
        self.ai_text = ctk.CTkLabel(
            self.ai_content,
            text="Run analysis to get AI coaching advice.",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            wraplength=340,
            justify="left",
            anchor="nw"
        )
        self.ai_text.pack(anchor="nw", padx=PADDING["medium"], pady=PADDING["medium"], fill="x")
        
        # Refresh advice button - at bottom
        self.refresh_btn = ctk.CTkButton(
            right_frame,
            text="🔄 Get Fresh Advice",
            command=self._refresh_advice,
            state="disabled",
            height=36,
            corner_radius=8,
            fg_color=COLORS["accent_cyan"],
            hover_color="#00B8E6",
            text_color=COLORS["bg_dark"],
            font=FONTS["body_bold"]
        )
        self.refresh_btn.pack(fill="x", padx=PADDING["medium"], pady=PADDING["medium"])
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self,
            text="No mistakes to display.\nRun analysis on a demo file first.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
    
    def load_results(self, result: Dict[str, Any]):
        """Load analysis results."""
        self.result = result
        self.placeholder.place_forget()
        
        # Update player filter options
        players = list(result.get("players", {}).keys())
        player_names = ["All Players"] + [
            result["players"][p].get("player_name", p) for p in players
        ]
        self.player_filter.configure(values=player_names)
        self.player_filter.set("All Players")
        
        # Display all mistakes
        self._display_mistakes()
        
        # Enable AI advice
        self.refresh_btn.configure(state="normal")
        self._generate_ai_advice()
    
    def _display_mistakes(self, filter_player: Optional[str] = None):
        """Display mistake cards, optionally filtered by player."""
        # Clear existing
        for widget in self.mistakes_scroll.winfo_children():
            widget.destroy()
        
        if not self.result:
            return
        
        players = self.result.get("players", {})
        all_mistakes = []
        
        for player_id, player_data in players.items():
            player_name = player_data.get("player_name", player_id)
            
            # Apply filter
            if filter_player and filter_player != "All Players":
                if player_name != filter_player:
                    continue
            
            for mistake in player_data.get("mistakes", []):
                all_mistakes.append({
                    "player": player_name,
                    **mistake
                })
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_mistakes.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))
        
        if not all_mistakes:
            no_mistakes = ctk.CTkLabel(
                self.mistakes_scroll,
                text="No mistakes found! Great performance.",
                font=FONTS["body"],
                text_color=COLORS["accent_green"]
            )
            no_mistakes.pack(pady=20)
            return
        
        # Create cards
        for mistake in all_mistakes:
            self._create_mistake_card(mistake)
    
    def _create_mistake_card(self, mistake: Dict[str, Any]):
        """Create a mistake card widget."""
        severity = mistake.get("severity", "low")
        color = SEVERITY_COLORS.get(severity, COLORS["accent_blue"])
        
        card = ctk.CTkFrame(
            self.mistakes_scroll,
            fg_color=COLORS["bg_light"],
            corner_radius=8
        )
        card.pack(fill="x", pady=5, padx=5)
        
        # Severity indicator bar
        indicator = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=2)
        indicator.pack(side="left", fill="y", padx=(0, 10))
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 10))
        
        # Header row
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        
        # Type
        type_text = mistake.get("type", "Unknown").replace("_", " ").title()
        ctk.CTkLabel(
            header,
            text=type_text,
            font=FONTS["body_bold"],
            text_color=COLORS["text_primary"]
        ).pack(side="left")
        
        # Severity badge
        badge_color = color
        ctk.CTkLabel(
            header,
            text=severity.upper(),
            font=FONTS["small"],
            text_color=badge_color
        ).pack(side="right")
        
        # Details
        details = ctk.CTkFrame(content, fg_color="transparent")
        details.pack(fill="x", pady=(5, 0))
        
        # Player and round info
        player = mistake.get("player", "Unknown")
        round_num = mistake.get("round", "?")
        location = mistake.get("location", "")
        
        info_text = f"👤 {player}  •  Round {round_num}"
        if location:
            info_text += f"  •  📍 {location}"
        
        ctk.CTkLabel(
            details,
            text=info_text,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Description/fix
        fix = mistake.get("fix", mistake.get("details", ""))
        if fix:
            ctk.CTkLabel(
                content,
                text=f"💡 {fix}",
                font=FONTS["body"],
                text_color=COLORS["accent_cyan"],
                wraplength=500,
                justify="left"
            ).pack(anchor="w", pady=(8, 0))
    
    def _on_filter_change(self, value: str):
        """Handle filter dropdown change."""
        self._display_mistakes(value if value != "All Players" else None)
    
    def filter_by_player(self, player_id: str):
        """Filter to show only mistakes from a specific player."""
        if not self.result:
            return
        
        player_name = self.result["players"].get(player_id, {}).get("player_name", player_id)
        self.player_filter.set(player_name)
        self._display_mistakes(player_name)
    
    def _generate_ai_advice(self):
        """Generate AI coaching advice."""
        from src.ui.services.ai_advisor import get_coaching_advice
        
        self.ai_status.configure(text="Generating...")
        
        def on_complete(advice: str):
            self.ai_text.configure(text=advice, text_color=COLORS["text_primary"])
            self.ai_status.configure(text="✓ Ollama" if "ollama" in advice.lower() or len(advice) > 100 else "⚡ Quick Tips")
        
        def on_error(error: str):
            self.ai_text.configure(
                text=f"Could not generate AI advice: {error}\n\nUsing rule-based tips instead.",
                text_color=COLORS["text_secondary"]
            )
            self.ai_status.configure(text="Offline")
            self._show_fallback_tips()
        
        # Run in thread
        get_coaching_advice(
            self.result,
            on_complete=on_complete,
            on_error=on_error
        )
    
    def _show_fallback_tips(self):
        """Show rule-based tips when AI is unavailable."""
        if not self.result:
            return
        
        tips = []
        
        # Analyze common mistakes
        all_mistakes = []
        for player_data in self.result.get("players", {}).values():
            all_mistakes.extend(player_data.get("mistakes", []))
        
        # Count by type
        type_counts = {}
        for m in all_mistakes:
            t = m.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Generate tips for top issues
        if type_counts.get("wide_peek_no_utility", 0) > 0:
            tips.append("💡 Wide Peeks: Pre-flash or shoulder-peek before dry-peeking common angles.")
        
        if type_counts.get("isolated_death", 0) > 0:
            tips.append("💡 Isolated Deaths: Stay within trading distance (~600 units) of teammates.")
        
        if type_counts.get("timing_error", 0) > 0:
            tips.append("💡 Timing: Sync your pushes with team executes. Don't lurk too early or late.")
        
        if type_counts.get("utility_wasted", 0) > 0:
            tips.append("💡 Utility: Don't throw smokes randomly. Save them for executes or retakes.")
        
        if not tips:
            tips = ["✓ No major patterns found. Keep up the good work!"]
        
        self.ai_text.configure(
            text="\n\n".join(tips),
            text_color=COLORS["text_primary"]
        )
    
    def _refresh_advice(self):
        """Refresh AI advice."""
        if self.result:
            self._generate_ai_advice()
