"""
Analysis Frame - Player stats and ratings display with team sorting
"""

import customtkinter as ctk
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from src.ui.theme import COLORS, FONTS, PADDING, FRAME, CARD

if TYPE_CHECKING:
    from src.ui.app import FragAuditApp


class AnalysisFrame(ctk.CTkFrame):
    """Analysis results with player stats table and team tabs."""
    
    def __init__(self, parent, app: "FragAuditApp"):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.app = app
        self.result: Optional[Dict[str, Any]] = None
        self.selected_player: Optional[str] = None
        self.current_team_filter: str = "all"  # "all", "CT", "T"
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the analysis frame UI."""
        # Header with team tabs
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=PADDING["large"], pady=PADDING["medium"])
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="📊 Player Analysis",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")
        
        # Team filter tabs
        self.team_tabs = ctk.CTkFrame(header, fg_color="transparent")
        self.team_tabs.pack(side="left", padx=30)
        
        self.tab_buttons = {}
        for team, label, color in [
            ("all", "All Players", COLORS["text_primary"]),
            ("CT", "CT Team", COLORS["team_ct"]),
            ("T", "T Team", COLORS["team_t"])
        ]:
            btn = ctk.CTkButton(
                self.team_tabs,
                text=label,
                width=90,
                height=28,
                corner_radius=4,
                command=lambda t=team: self._filter_team(t),
                fg_color=COLORS["accent_blue"] if team == "all" else "transparent",
                hover_color=COLORS["bg_hover"],
                text_color="#ffffff" if team == "all" else COLORS["text_secondary"]
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[team] = btn
        
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
        
        # Rank column added
        columns = ["#", "Player", "Team", "Role", "K/D/A", "ADR", "HS%", "Rating"]
        col_widths = [35, 140, 55, 90, 90, 60, 60, 70]
        
        for i, (col, width) in enumerate(zip(columns, col_widths)):
            lbl = ctk.CTkLabel(
                header_frame,
                text=col,
                width=width,
                font=FONTS["body_bold"],
                text_color=COLORS["text_secondary"]
            )
            lbl.pack(side="left", padx=3, pady=8)
        
        # Scrollable player list
        self.player_scroll = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="transparent"
        )
        self.player_scroll.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Right: Selected player details
        self.detail_frame = ctk.CTkFrame(content, width=320, **FRAME)
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
    
    def _filter_team(self, team: str):
        """Filter players by team."""
        self.current_team_filter = team
        
        # Update tab highlighting
        for t, btn in self.tab_buttons.items():
            if t == team:
                btn.configure(fg_color=COLORS["accent_blue"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])
        
        # Reload results with filter
        if self.result:
            self._display_players()
    
    def load_results(self, result: Dict[str, Any]):
        """Load analysis results into the view."""
        self.result = result
        self.placeholder.place_forget()
        
        # Update match info
        map_name = result.get("map_name", "Unknown")
        self.match_info.configure(text=f"🗺️ {map_name}")
        
        # Display players
        self._display_players()
    
    def _display_players(self):
        """Display players with current filter."""
        # Clear existing rows
        for widget in self.player_scroll.winfo_children():
            widget.destroy()
        
        if not self.result:
            return
        
        players = self.result.get("players", {})
        
        # Filter by team
        if self.current_team_filter != "all":
            players = {k: v for k, v in players.items() 
                      if v.get("team") == self.current_team_filter}
        
        # Sort by rating
        sorted_players = sorted(
            players.items(),
            key=lambda x: x[1].get("stats", {}).get("rating", 0),
            reverse=True
        )
        
        # Create player rows with rank
        for rank, (player_id, player_data) in enumerate(sorted_players, 1):
            self._create_player_row(player_id, player_data, rank)
    
    def _create_player_row(self, player_id: str, data: Dict[str, Any], rank: int):
        """Create a row in the player table with rank."""
        stats = data.get("stats", {})
        team = data.get("team", "?")
        
        # Row background based on team
        if team == "CT":
            bg_color = "#1a2a4a" if rank % 2 == 1 else "#152035"
        else:
            bg_color = "#3a2a1a" if rank % 2 == 1 else "#2f2015"
        
        row = ctk.CTkFrame(
            self.player_scroll,
            fg_color=bg_color,
            height=42,
            corner_radius=4
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # Make row clickable
        row.bind("<Button-1>", lambda e, pid=player_id: self._select_player(pid))
        
        # Rank (medal for top 3)
        rank_text = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else str(rank)
        rank_lbl = ctk.CTkLabel(
            row, text=rank_text, width=35,
            font=FONTS["body_bold"] if rank <= 3 else FONTS["body"],
            text_color=COLORS["text_primary"]
        )
        rank_lbl.pack(side="left", padx=3, pady=6)
        
        # Player name
        name = data.get("player_name", player_id)
        name_short = name[:12] if len(name) > 12 else name
        name_lbl = ctk.CTkLabel(
            row, text=name_short, width=140,
            font=FONTS["body_bold"],
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        name_lbl.pack(side="left", padx=3)
        name_lbl.bind("<Button-1>", lambda e, pid=player_id: self._select_player(pid))
        
        # Team badge
        team_color = COLORS["team_ct"] if team == "CT" else COLORS["team_t"]
        team_lbl = ctk.CTkLabel(
            row, text=team, width=55,
            font=FONTS["body_bold"],
            text_color=team_color
        )
        team_lbl.pack(side="left", padx=3)
        
        # Role
        role = data.get("role", {}).get("detected", "?")
        role_short = role[:8] if len(role) > 8 else role
        role_lbl = ctk.CTkLabel(
            row, text=role_short, width=90,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"]
        )
        role_lbl.pack(side="left", padx=3)
        
        # K/D/A
        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        assists = stats.get("assists", 0)
        kda_lbl = ctk.CTkLabel(
            row, text=f"{kills}/{deaths}/{assists}", width=90,
            font=FONTS["mono"],
            text_color=COLORS["text_primary"]
        )
        kda_lbl.pack(side="left", padx=3)
        
        # ADR
        adr = stats.get("adr", 0)
        adr_color = COLORS["accent_green"] if adr >= 80 else COLORS["text_primary"]
        adr_lbl = ctk.CTkLabel(
            row, text=f"{adr:.0f}", width=60,
            font=FONTS["mono"],
            text_color=adr_color
        )
        adr_lbl.pack(side="left", padx=3)
        
        # HS%
        hs = stats.get("headshot_percentage", 0)
        hs_lbl = ctk.CTkLabel(
            row, text=f"{hs:.0f}%", width=60,
            font=FONTS["mono"],
            text_color=COLORS["text_primary"]
        )
        hs_lbl.pack(side="left", padx=3)
        
        # Rating with color and styling
        rating = stats.get("rating", 1.0)
        if rating >= 1.2:
            rating_color = COLORS["accent_green"]
            rating_bg = "#1a3a1a"
        elif rating >= 1.0:
            rating_color = COLORS["rating_mid"]
            rating_bg = None
        else:
            rating_color = COLORS["rating_low"]
            rating_bg = "#3a1a1a"
        
        rating_frame = ctk.CTkFrame(row, fg_color=rating_bg or "transparent", corner_radius=4)
        rating_frame.pack(side="left", padx=3)
        
        rating_lbl = ctk.CTkLabel(
            rating_frame, text=f"{rating:.2f}", width=60,
            font=FONTS["body_bold"],
            text_color=rating_color
        )
        rating_lbl.pack(padx=4, pady=2)
    
    def _select_player(self, player_id: str):
        """Select a player and show details."""
        self.selected_player = player_id
        
        if not self.result:
            return
        
        player_data = self.result.get("players", {}).get(player_id, {})
        
        # Clear detail content
        for widget in self.detail_content.winfo_children():
            widget.destroy()
        
        # Update title with team color
        name = player_data.get("player_name", player_id)
        team = player_data.get("team", "?")
        team_color = COLORS["team_ct"] if team == "CT" else COLORS["team_t"]
        
        self.detail_title.configure(
            text=f"👤 {name}",
            text_color=team_color
        )
        
        # Stats section
        stats = player_data.get("stats", {})
        rating = stats.get("rating", 1.0)
        
        # Grade based on rating
        if rating >= 1.3:
            grade = "S"
            grade_color = "#FFD700"
        elif rating >= 1.1:
            grade = "A"
            grade_color = COLORS["accent_green"]
        elif rating >= 0.9:
            grade = "B"
            grade_color = COLORS["rating_mid"]
        elif rating >= 0.7:
            grade = "C"
            grade_color = COLORS["accent_orange"]
        else:
            grade = "D"
            grade_color = COLORS["rating_low"]
        
        # Grade display
        grade_frame = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        grade_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            grade_frame,
            text=grade,
            font=("Segoe UI", 36, "bold"),
            text_color=grade_color
        ).pack(side="left")
        
        ctk.CTkLabel(
            grade_frame,
            text=f"  {rating:.2f} Rating",
            font=FONTS["heading"],
            text_color=COLORS["text_primary"]
        ).pack(side="left", pady=(12, 0))
        
        # Stats grid
        stat_rows = [
            ("Kills", stats.get("kills", 0)),
            ("Deaths", stats.get("deaths", 0)),
            ("Assists", stats.get("assists", 0)),
            ("ADR", f"{stats.get('adr', 0):.1f}"),
            ("KAST", f"{stats.get('kast', 0):.1f}%"),
            ("Headshot %", f"{stats.get('headshot_percentage', 0):.1f}%"),
        ]
        
        for label, value in stat_rows:
            row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
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
            ).pack(anchor="w", pady=(15, 5))
            
            ctk.CTkLabel(
                self.detail_content,
                text=role_data.get("detected", "Unknown"),
                font=FONTS["body_bold"],
                text_color=COLORS["accent_blue"]
            ).pack(anchor="w")
        
        # Mistakes count
        mistakes = player_data.get("mistakes", [])
        if mistakes:
            ctk.CTkLabel(
                self.detail_content,
                text=f"\n⚠️ {len(mistakes)} issues found",
                font=FONTS["subheading"],
                text_color=COLORS["accent_yellow"]
            ).pack(anchor="w", pady=(15, 5))
            
            # View mistakes button
            ctk.CTkButton(
                self.detail_content,
                text="View Mistakes →",
                command=lambda: self._view_mistakes(player_id),
                fg_color="transparent",
                text_color=COLORS["accent_blue"],
                hover_color=COLORS["bg_hover"]
            ).pack(anchor="w")
    
    def _view_mistakes(self, player_id: str):
        """Switch to mistakes view filtered by player."""
        self.app.frames["mistakes"].filter_by_player(player_id)
        self.app.show_frame("mistakes")
