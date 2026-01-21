"""
FragAudit Theme Configuration
Gaming-inspired dark theme with CS2 colors
"""

# Color Palette - CS2 Inspired
COLORS = {
    # Base
    "bg_dark": "#0d1117",
    "bg_medium": "#161b22", 
    "bg_light": "#21262d",
    "bg_hover": "#30363d",
    
    # Accent
    "accent_blue": "#4A90D9",      # CT Blue
    "accent_orange": "#D9A441",    # T Orange
    "accent_green": "#3fb950",     # Success
    "accent_red": "#f85149",       # Error/High severity
    "accent_yellow": "#d29922",    # Warning/Medium severity
    "accent_cyan": "#4ecdc4",      # Primary action
    
    # Text
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    
    # Borders
    "border": "#30363d",
    "border_focus": "#4A90D9",
    
    # Rating colors
    "rating_high": "#3fb950",      # > 1.1
    "rating_mid": "#d29922",       # 0.9 - 1.1
    "rating_low": "#f85149",       # < 0.9
    
    # Team colors
    "team_ct": "#4A90D9",
    "team_t": "#D9A441",
}

# Fonts
FONTS = {
    "heading_large": ("Segoe UI", 24, "bold"),
    "heading": ("Segoe UI", 18, "bold"),
    "subheading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 10),
    "mono": ("Consolas", 11),
    "mono_small": ("Consolas", 10),
}

# Widget Styling
BUTTON = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": COLORS["accent_cyan"],
    "hover_color": "#3db8b0",
    "text_color": COLORS["bg_dark"],
    "border_color": COLORS["accent_cyan"],
}

BUTTON_SECONDARY = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": "transparent",
    "hover_color": COLORS["bg_hover"],
    "text_color": COLORS["text_primary"],
    "border_color": COLORS["border"],
}

ENTRY = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": COLORS["bg_light"],
    "border_color": COLORS["border"],
    "text_color": COLORS["text_primary"],
    "placeholder_text_color": COLORS["text_muted"],
}

FRAME = {
    "corner_radius": 12,
    "fg_color": COLORS["bg_medium"],
    "border_width": 1,
    "border_color": COLORS["border"],
}

CARD = {
    "corner_radius": 10,
    "fg_color": COLORS["bg_light"],
    "border_width": 0,
}

# Severity colors for mistake cards
SEVERITY_COLORS = {
    "high": COLORS["accent_red"],
    "medium": COLORS["accent_yellow"],
    "low": COLORS["accent_blue"],
}

# Layout
PADDING = {
    "small": 5,
    "medium": 10,
    "large": 20,
    "xlarge": 30,
}

# Window
WINDOW = {
    "width": 1400,
    "height": 900,
    "min_width": 1200,
    "min_height": 700,
}
