"""
Analysis Frame - Player stats and ratings display
"""

import customtkinter as ctk
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, CARD

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class AnalysisFrame(ctk.CTkFrame):
    """Analysis results with player stats table."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        self.result: Optional[Dict[str, Any]] = None
        self.selected_player: Optional[str] = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the analysis frame UI."""
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        
        title = ctk.CTkLabel(
            header,
            text="📊 Player Analysis",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")
        
        # Match info (right side of header)
        self.match_info = ctk.CTkLabel(
            header,
            text="",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        )
        self.match_info.pack(side="right")
        
        # Main content - split into two columns
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING["large"], pady=PADDING["medium"])
        
        # Left: Player table
        table_frame = ctk.CTkFrame(content, **FRAME)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, PADDING["medium"]))
        
        # Table header
        header_frame = ctk.CTkFrame(table_frame, fg_color=COLORS["bg_light"], height=40)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)
        
        columns = ["Player", "Team", "Role", "K/D/A", "ADR", "HS%", "Rating"]
        col_widths = [150, 60, 100, 100, 70, 70, 80]
        
        for i, (col, width) in enumerate(zip(columns, col_widths)):
            lbl = ctk.CTkLabel(
                header_frame,
                text=col,
                width=width,
                font=FONTS["body_bold"],
                text_color=COLORS["text_secondary"]
            )
            lbl.pack(side="left", padx=5, pady=8)
        
        # Scrollable player list
        self.player_scroll = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="transparent"
        )
        self.player_scroll.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Right: Selected player details
        self.detail_frame = ctk.CTkFrame(content, width=350, **FRAME)
        self.detail_frame.pack(side="right", fill="y")
        self.detail_frame.pack_propagate(False)
        
        self.detail_title = ctk.CTkLabel(
            self.detail_frame,
            text="Select a player",
            font=FONTS["subheading"],
            text_color=COLORS["text_secondary"]
        )
        self.detail_title.pack(pady=PADDING["large"])
        
        self.detail_content = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.detail_content.pack(fill="both", expand=True, padx=PADDING["medium"])
        
        # Placeholder message
        self.placeholder = ctk.CTkLabel(
            self,
            text="No analysis results yet.\nOpen a demo file and click Analyze.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
    
    def load_results(self, result: Dict[str, Any]):
        """Load analysis results into the view."""
        self.result = result
        self.placeholder.place_forget()
        
        # Update match info
        map_name = result.get("map_name", "Unknown")
        demo_name = result.get("demo", "Unknown")
        self.match_info.configure(text=f"Map: {map_name}")
        
        # Clear existing rows
        for widget in self.player_scroll.winfo_children():
            widget.destroy()
        
        # Get players and sort by rating
        players = result.get("players", {})
        sorted_players = sorted(
            players.items(),
            key=lambda x: x[1].get("stats", {}).get("rating", 0),
            reverse=True
        )
        
        # Create player rows
        for i, (player_id, player_data) in enumerate(sorted_players):
            self._create_player_row(player_id, player_data, i)
    
    def _create_player_row(self, player_id: str, data: Dict[str, Any], index: int):
        """Create a row in the player table."""
        stats = data.get("stats", {})
        
        # Alternating row colors
        bg_color = COLORS["bg_light"] if index % 2 == 0 else COLORS["bg_medium"]
        
        row = ctk.CTkFrame(
            self.player_scroll,
            fg_color=bg_color,
            height=45,
            corner_radius=4
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # Make row clickable
        row.bind("<Button-1>", lambda e, pid=player_id: self._select_player(pid))
        
        # Player name
        name = data.get("player_name", player_id)
        name_lbl = ctk.CTkLabel(
            row, text=name, width=150,
            font=FONTS["body_bold"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        name_lbl.pack(side="left", padx=5, pady=8)
        name_lbl.bind("<Button-1>", lambda e, pid=player_id: self._select_player(pid))
        
        # Team
        team = data.get("team", "?")
        team_color = COLORS["team_ct"] if team == "CT" else COLORS["team_t"]
        team_lbl = ctk.CTkLabel(
            row, text=team, width=60,
            font=FONTS["body_bold"],
            text_color=team_color
        )
        team_lbl.pack(side="left", padx=5)
        
        # Role
        role = data.get("role", {}).get("detected", "Unknown")
        role_short = role[:10] if len(role) > 10 else role
        role_lbl = ctk.CTkLabel(
            row, text=role_short, width=100,
            font=FONTS["body"],
            text_color=COLORS["text_secondary"]
        )
        role_lbl.pack(side="left", padx=5)
        
        # K/D/A
        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        assists = stats.get("assists", 0)
        kda_lbl = ctk.CTkLabel(
            row, text=f"{kills}/{deaths}/{assists}", width=100,
            font=FONTS["mono"],
            text_color=COLORS["text_primary"]
        )
        kda_lbl.pack(side="left", padx=5)
        
        # ADR
        adr = stats.get("adr", 0)
        adr_lbl = ctk.CTkLabel(
            row, text=f"{adr:.1f}", width=70,
            font=FONTS["mono"],
            text_color=COLORS["text_primary"]
        )
        adr_lbl.pack(side="left", padx=5)
        
        # HS%
        hs = stats.get("headshot_percentage", 0)
        hs_lbl = ctk.CTkLabel(
            row, text=f"{hs:.0f}%", width=70,
            font=FONTS["mono"],
            text_color=COLORS["text_primary"]
        )
        hs_lbl.pack(side="left", padx=5)
        
        # Rating with color
        rating = stats.get("rating", 1.0)
        if rating >= 1.1:
            rating_color = COLORS["rating_high"]
        elif rating <= 0.9:
            rating_color = COLORS["rating_low"]
        else:
            rating_color = COLORS["rating_mid"]
        
        rating_lbl = ctk.CTkLabel(
            row, text=f"{rating:.2f}", width=80,
            font=FONTS["body_bold"],
            text_color=rating_color
        )
        rating_lbl.pack(side="left", padx=5)
    
    def _select_player(self, player_id: str):
        """Select a player and show details."""
        self.selected_player = player_id
        
        if not self.result:
            return
        
        player_data = self.result.get("players", {}).get(player_id, {})
        
        # Clear detail content
        for widget in self.detail_content.winfo_children():
            widget.destroy()
        
        # Update title
        name = player_data.get("player_name", player_id)
        self.detail_title.configure(
            text=f"👤 {name}",
            text_color=COLORS["text_primary"]
        )
        
        # Stats section
        stats = player_data.get("stats", {})
        
        stat_rows = [
            ("Kills", stats.get("kills", 0)),
            ("Deaths", stats.get("deaths", 0)),
            ("Assists", stats.get("assists", 0)),
            ("ADR", f"{stats.get('adr', 0):.1f}"),
            ("KAST", f"{stats.get('kast', 0):.1f}%"),
            ("Headshot %", f"{stats.get('headshot_percentage', 0):.1f}%"),
            ("Rating", f"{stats.get('rating', 1.0):.2f}"),
        ]
        
        for label, value in stat_rows:
            row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row, text=label, font=FONTS["body"],
                text_color=COLORS["text_secondary"]
            ).pack(side="left")
            
            ctk.CTkLabel(
                row, text=str(value), font=FONTS["body_bold"],
                text_color=COLORS["text_primary"]
            ).pack(side="right")
        
        # Role section
        role_data = player_data.get("role", {})
        if role_data:
            ctk.CTkLabel(
                self.detail_content,
                text="\n🎯 Role",
                font=FONTS["subheading"],
                text_color=COLORS["text_primary"]
            ).pack(anchor="w", pady=(20, 5))
            
            ctk.CTkLabel(
                self.detail_content,
                text=role_data.get("detected", "Unknown"),
                font=FONTS["body_bold"],
                text_color=COLORS["accent_cyan"]
            ).pack(anchor="w")
            
            confidence = role_data.get("confidence", 0)
            ctk.CTkLabel(
                self.detail_content,
                text=f"Confidence: {confidence*100:.0f}%",
                font=FONTS["small"],
                text_color=COLORS["text_muted"]
            ).pack(anchor="w")
        
        # Mistakes count
        mistakes = player_data.get("mistakes", [])
        if mistakes:
            ctk.CTkLabel(
                self.detail_content,
                text=f"\n⚠️ {len(mistakes)} issues found",
                font=FONTS["subheading"],
                text_color=COLORS["accent_yellow"]
            ).pack(anchor="w", pady=(20, 5))
            
            # View mistakes button
            ctk.CTkButton(
                self.detail_content,
                text="View Mistakes →",
                command=lambda: self._view_mistakes(player_id),
                fg_color="transparent",
                text_color=COLORS["accent_cyan"],
                hover_color=COLORS["bg_hover"]
            ).pack(anchor="w")
    
    def _view_mistakes(self, player_id: str):
        """Switch to mistakes view filtered by player."""
        self.app.frames["mistakes"].filter_by_player(player_id)
        self.app.show_frame("mistakes")
