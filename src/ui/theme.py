"""
FragAudit Theme Configuration
Cyber-Cyberpunk Dark Theme - Inspired by Stitch Design
"""

# Color Palette - Cyber-Cyberpunk Neon Theme
COLORS = {
    # Base (Deep Dark)
    "bg_dark": "#0B0E11",          # Main window - deep charcoal
    "bg_medium": "#15191C",        # Card/component background - carbon grey
    "bg_light": "#1E2328",         # Elevated surfaces
    "bg_hover": "#252B32",         # Hover states
    "bg_active": "rgba(0, 209, 255, 0.1)",  # Active highlight with cyan glow
    
    # Neon Accents
    "accent_cyan": "#00D1FF",      # Primary action - electric cyan
    "accent_blue": "#00D1FF",      # Primary (same as cyan)
    "accent_green": "#00FF85",     # Success/Victory - neon green
    "accent_red": "#FF4B4B",       # Danger/Defeat - soft red/coral
    "accent_yellow": "#FFB800",    # Warning - electric yellow
    "accent_purple": "#9D4EDD",    # Special - neon purple
    "accent_orange": "#FF6B35",    # Attention - vibrant orange
    
    # Text
    "text_primary": "#FFFFFF",     # Primary text - pure white
    "text_secondary": "#94A3B8",   # Secondary/muted - slate grey
    "text_muted": "#64748B",       # Subtle text
    
    # Borders
    "border": "#2A3139",           # Default border - subtle
    "border_focus": "#00D1FF",     # Focus state - cyan glow
    
    # Rating colors (neon style)
    "rating_high": "#00FF85",      # > 1.1 (neon green)
    "rating_mid": "#FFB800",       # 0.9 - 1.1 (electric yellow)
    "rating_low": "#FF4B4B",       # < 0.9 (coral red)
    
    # Team colors (CS2 - vibrant)
    "team_ct": "#00D1FF",          # CT - Electric Cyan
    "team_t": "#FF6B35",           # T - Vibrant Orange
    
    # Glow effects (for box shadows in CSS/styling)
    "glow_cyan": "0 0 15px rgba(0, 209, 255, 0.5)",
    "glow_green": "0 0 15px rgba(0, 255, 133, 0.5)",
    "glow_red": "0 0 15px rgba(255, 75, 75, 0.5)",
}

# Fonts - Modern Sans-Serif with monospace accents
FONTS = {
    "heading_large": ("Inter", 28, "bold"),
    "heading": ("Inter", 20, "bold"),
    "subheading": ("Inter", 14, "bold"),
    "body": ("Inter", 12),
    "body_bold": ("Inter", 12, "bold"),
    "small": ("Inter", 10),
    "mono": ("JetBrains Mono", 12),
    "mono_small": ("JetBrains Mono", 10),
    "mono_large": ("JetBrains Mono", 16, "bold"),
}

# Widget Styling - Cyber-Cyberpunk with glow effects
BUTTON = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": "#00D1FF",         # Cyan primary
    "hover_color": "#00B8E6",      # Slightly darker cyan
    "text_color": "#0B0E11",       # Dark text on light button
    "border_color": "#00D1FF",
}

BUTTON_SECONDARY = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": "#15191C",
    "hover_color": "#252B32",
    "text_color": "#00D1FF",       # Cyan text
    "border_color": "#2A3139",
}

BUTTON_PRIMARY = {
    "corner_radius": 8,
    "border_width": 0,
    "fg_color": "#00FF85",         # Neon green
    "hover_color": "#00E676",
    "text_color": "#0B0E11",
}

BUTTON_DANGER = {
    "corner_radius": 8,
    "border_width": 0,
    "fg_color": "#FF4B4B",
    "hover_color": "#E63946",
    "text_color": "#FFFFFF",
}

ENTRY = {
    "corner_radius": 8,
    "border_width": 1,
    "fg_color": "#0B0E11",
    "border_color": "#2A3139",
    "text_color": "#FFFFFF",
    "placeholder_text_color": "#64748B",
}

FRAME = {
    "corner_radius": 10,
    "fg_color": "#15191C",
    "border_width": 1,
    "border_color": "#2A3139",
}

CARD = {
    "corner_radius": 12,
    "fg_color": "#15191C",
    "border_width": 1,
    "border_color": "#2A3139",
}

CARD_ELEVATED = {
    "corner_radius": 12,
    "fg_color": "#1E2328",
    "border_width": 1,
    "border_color": "#00D1FF",  # Cyan border for emphasis
}

# Severity colors for mistake cards
SEVERITY_COLORS = {
    "high": "#FF4B4B",     # Coral red
    "medium": "#FFB800",   # Electric yellow
    "low": "#00D1FF",      # Electric cyan
}

# Grade colors (tier-based like competitive games)
GRADE_COLORS = {
    "S": "#FFD700",        # Gold
    "A": "#00FF85",        # Neon green
    "B": "#00D1FF",        # Cyan
    "C": "#FFB800",        # Yellow
    "D": "#FF6B35",        # Orange
    "F": "#FF4B4B",        # Red
}

# Layout
PADDING = {
    "small": 6,
    "medium": 12,
    "large": 24,
    "xlarge": 36,
}

# Window
WINDOW = {
    "width": 1500,
    "height": 950,
    "min_width": 1280,
    "min_height": 720,
}

# Scrollbar Styling
SCROLLBAR = {
    "corner_radius": 4,
    "fg_color": "#2A3139",
    "button_color": "#00D1FF",
    "button_hover_color": "#00B8E6",
}

# Progress Bar
PROGRESS = {
    "corner_radius": 4,
    "fg_color": "#15191C",
    "progress_color": "#00D1FF",
    "border_width": 0,
}
