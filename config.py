"""
CS2 AI Coach - Configuration
Thresholds and constants for coaching analysis.
"""

# =============================================================================
# OLLAMA CONFIGURATION
# =============================================================================
OLLAMA_ENABLED = False  # Set to True to enable NLP phrasing
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Or "mistral", "phi3", etc.
OLLAMA_TIMEOUT = 30  # seconds

# =============================================================================
# METRIC THRESHOLDS - Aim
# =============================================================================
AIM_THRESHOLDS = {
    "headshot_percentage": {
        "poor": 0.20,       # Below 20% = needs improvement
        "average": 0.30,    # 20-30% = average
        "good": 0.45,       # 30-45% = good
        # Above 45% = excellent
    },
    "spray_control": {
        "poor": 0.15,       # Damage per bullet ratio threshold
        "average": 0.25,
        "good": 0.35,
    }
}

# =============================================================================
# METRIC THRESHOLDS - Positioning
# =============================================================================
POSITIONING_THRESHOLDS = {
    "exposed_death_ratio": {
        "poor": 0.50,       # >50% deaths while exposed = problem
        "average": 0.35,
        "good": 0.20,
    },
    "trade_distance": 800,  # Units - teammate must be within this to trade
    "cover_distance": 200,  # Units - distance to nearest cover
}

# =============================================================================
# METRIC THRESHOLDS - Utility
# =============================================================================
UTILITY_THRESHOLDS = {
    "flash_success_rate": {
        "poor": 0.10,       # <10% flashes lead to kills
        "average": 0.20,
        "good": 0.35,
    },
    "nade_damage_per_round": {
        "poor": 10,         # Average nade damage per round
        "average": 25,
        "good": 40,
    }
}

# =============================================================================
# METRIC THRESHOLDS - Economy
# =============================================================================
ECONOMY_THRESHOLDS = {
    "force_buy_death_ratio": {
        "poor": 0.70,       # Dying on >70% of force buys = bad
        "average": 0.50,
        "good": 0.35,
    }
}

# =============================================================================
# CLASSIFIER SETTINGS
# =============================================================================
CONFIDENCE_WEIGHTS = {
    "sample_size": 0.3,     # More events = higher confidence
    "consistency": 0.4,     # Consistent mistakes = higher confidence
    "severity": 0.3,        # Impact of the mistake
}

# Minimum events required to classify a mistake
MIN_EVENTS_FOR_CLASSIFICATION = {
    "aim": 5,           # At least 5 kills/deaths
    "positioning": 3,   # At least 3 death events
    "utility": 3,       # At least 3 utility uses
    "economy": 4,       # At least 4 buy rounds
}

# =============================================================================
# MISTAKE CATEGORIES
# =============================================================================
class MistakeCategory:
    AIM = "AIM"
    POSITIONING = "POSITIONING"
    UTILITY = "UTILITY"
    ECONOMY = "ECONOMY"
    GAMESENSE = "GAMESENSE"

# =============================================================================
# FALLBACK COACHING MESSAGES
# Used when Ollama is unavailable
# =============================================================================
FALLBACK_MESSAGES = {
    MistakeCategory.AIM: {
        "headshot_low": "Your headshot percentage is below average. Focus on crosshair placement and aim at head level when holding angles.",
        "spray_poor": "Your spray control needs work. Practice spray patterns in workshop maps and burst fire at longer ranges.",
    },
    MistakeCategory.POSITIONING: {
        "exposed_deaths": "You're dying in exposed positions too often. Use cover more effectively and avoid over-peeking.",
        "untradeable": "Your deaths are often untradeable. Stay closer to teammates and play for trades.",
    },
    MistakeCategory.UTILITY: {
        "flash_ineffective": "Your flashes aren't creating opportunities. Learn pop-flash lineups and coordinate with team pushes.",
        "low_nade_damage": "You're not utilizing damage grenades effectively. Use HE and molotovs to clear common positions.",
    },
    MistakeCategory.ECONOMY: {
        "force_buy_deaths": "You're dying too often on force buy rounds. Play more conservatively when at an equipment disadvantage.",
    },
    MistakeCategory.GAMESENSE: {
        "general": "Review your decision-making. Watch pro demos to understand timing and rotations better.",
    }
}

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
REPORT_FORMAT = "json"  # "json" or "markdown"
OUTPUT_DIR = "reports"
