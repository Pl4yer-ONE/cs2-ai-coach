"""
AI Advisor Service
Generates coaching advice using Ollama or fallback rules
"""

import threading
from typing import Dict, Any, Callable, Optional
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"  # or "mistral"


def get_coaching_advice(
    result: Dict[str, Any],
    on_complete: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None
):
    """
    Generate AI coaching advice from analysis results.
    
    Runs in background thread, calls on_complete with advice text.
    Falls back to rule-based advice if Ollama unavailable.
    """
    def _run():
        try:
            advice = _generate_advice(result)
            if on_complete:
                # Need to call in main thread for tkinter
                on_complete(advice)
        except Exception as e:
            if on_error:
                on_error(str(e))
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def _generate_advice(result: Dict[str, Any]) -> str:
    """Generate advice using Ollama or fallback."""
    
    # Try Ollama first
    try:
        advice = _ollama_advice(result)
        if advice:
            return advice
    except Exception:
        pass  # Fall through to rule-based
    
    # Fallback to rule-based
    return _rule_based_advice(result)


def _ollama_advice(result: Dict[str, Any]) -> Optional[str]:
    """Generate advice using local Ollama."""
    
    # Build context from results
    context = _build_context(result)
    
    prompt = f"""You are a professional CS2 coach analyzing a match. Based on the following analysis data, provide specific, actionable coaching advice. Be direct and practical.

MATCH DATA:
{context}

Provide 3-5 specific coaching tips based on the most critical issues found. Format each tip with an emoji and keep them concise. Focus on the most impactful improvements the players can make."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        
    except requests.exceptions.ConnectionError:
        return None  # Ollama not running
    except Exception:
        return None
    
    return None


def _build_context(result: Dict[str, Any]) -> str:
    """Build context string from analysis results."""
    lines = []
    
    map_name = result.get("map_name", "Unknown")
    lines.append(f"Map: {map_name}")
    lines.append("")
    
    # Player summaries
    for player_id, player_data in result.get("players", {}).items():
        name = player_data.get("player_name", player_id)
        stats = player_data.get("stats", {})
        role = player_data.get("role", {}).get("detected", "Unknown")
        rating = stats.get("rating", 1.0)
        
        lines.append(f"Player: {name} ({role})")
        lines.append(f"  Rating: {rating:.2f}")
        lines.append(f"  K/D: {stats.get('kills', 0)}/{stats.get('deaths', 0)}")
        
        mistakes = player_data.get("mistakes", [])
        if mistakes:
            lines.append(f"  Issues ({len(mistakes)}):")
            for m in mistakes[:3]:  # Top 3 only
                mtype = m.get("type", "").replace("_", " ")
                severity = m.get("severity", "")
                lines.append(f"    - {mtype} ({severity})")
        
        lines.append("")
    
    return "\n".join(lines)


def _rule_based_advice(result: Dict[str, Any]) -> str:
    """Generate rule-based advice without AI."""
    
    tips = []
    
    # Collect all mistakes
    all_mistakes = []
    for player_data in result.get("players", {}).values():
        all_mistakes.extend(player_data.get("mistakes", []))
    
    # Count by type
    type_counts = {}
    for m in all_mistakes:
        t = m.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Sort by count
    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
    
    # Comprehensive advice map for all mistake types
    advice_map = {
        "wide_peek_no_utility": (
            "🎯 **Dry Peeking Issue**\n"
            "You're peeking common angles without utility support. "
            "Pre-flash before peeking, or shoulder-peek to bait shots before committing."
        ),
        "isolated_death": (
            "👥 **Isolated Positioning**\n"
            "Too many deaths without trade potential. "
            "Stay within 600 units of a teammate so they can trade you if you die."
        ),
        "timing_error": (
            "⏱️ **Timing Desync**\n"
            "Your timing isn't synced with the team. "
            "Lurkers: time your push with the execute. Entry: don't go before utility lands."
        ),
        "utility_wasted": (
            "💨 **Utility Efficiency**\n"
            "Smokes and flashes being thrown without impact. "
            "Save utility for executes, retakes, or specific plays."
        ),
        "overexposure": (
            "👁️ **Multiple Angle Exposure**\n"
            "You're exposing yourself to multiple enemies at once. "
            "Clear angles one at a time, don't wide-swing into crossfires."
        ),
        "economy_mistake": (
            "💰 **Economy Management**\n"
            "Suboptimal buy decisions. "
            "Coordinate buys with team, don't force when team is saving."
        ),
        "crossfire_death": (
            "❌ **Crossfire Deaths**\n"
            "Getting caught in enemy crossfires. "
            "Use utility to isolate angles, or avoid common crossfire positions."
        ),
        "poor_positioning": (
            "📍 **Positioning Errors**\n"
            "Taking fights from disadvantaged positions. "
            "Always secure cover and off-angles before engaging."
        ),
        "no_trade_potential": (
            "🤝 **Trading Distance**\n"
            "Dying too far from teammates. "
            "Stay within 500-600 units to ensure trade potential."
        ),
        "entry_frag_bait": (
            "⚡ **Entry Support**\n"
            "Entry fraggers need support. "
            "Flash for your entry, be ready to trade immediately."
        ),
        "late_rotate": (
            "🔄 **Rotation Timing**\n"
            "Rotating too slowly to bomb site. "
            "Listen for audio cues and rotate earlier when info is clear."
        ),
        "peeking_without_info": (
            "🔍 **Info Gathering**\n"
            "Peeking without utility or info. "
            "Use utility, drones, or teammate comms before dry-peeking."
        ),
    }
    
    for mistake_type, count in sorted_types[:4]:
        if mistake_type in advice_map:
            tips.append(f"{advice_map[mistake_type]}\n*({count} instances found)*")
        else:
            # Generic advice for unknown types
            readable_type = mistake_type.replace("_", " ").title()
            tips.append(f"⚠️ **{readable_type}**\n*({count} instances found)*")
    
    if not tips:
        tips.append("✅ **Great Performance!**\nNo major recurring patterns found. Keep up the good work!")
    
    return "\n\n".join(tips)


def check_ollama_available() -> bool:
    """Check if Ollama is running and has the model."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(MODEL in m.get("name", "") for m in models)
    except Exception:
        pass
    return False
