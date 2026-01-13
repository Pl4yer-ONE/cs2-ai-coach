"""
Ollama NLP Phrasing
Optional module to convert classifier output to natural language feedback.

IMPORTANT: This module NEVER decides mistakes - it only phrases the output
from the deterministic classifier.
"""

import json
from typing import Dict, Any, Optional, List
import requests

from config import (
    OLLAMA_ENABLED,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    FALLBACK_MESSAGES,
    MistakeCategory
)
from src.classifier.mistake_classifier import ClassifiedMistake


class OllamaPhrasing:
    """
    Convert classified mistakes to natural language feedback using Ollama.
    
    This module only phrases the output from the deterministic classifier.
    NLP never decides what the mistakes are - only how to express them.
    """
    
    def __init__(
        self,
        enabled: bool = OLLAMA_ENABLED,
        host: str = OLLAMA_HOST,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT
    ):
        """
        Initialize Ollama phrasing.
        
        Args:
            enabled: Whether Ollama is enabled
            host: Ollama API host URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.enabled = enabled
        self.host = host
        self.model = model
        self.timeout = timeout
        self._available: Optional[bool] = None
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not self.enabled:
            return False
        
        if self._available is not None:
            return self._available
        
        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5
            )
            self._available = response.status_code == 200
        except requests.RequestException:
            self._available = False
        
        return self._available
    
    def phrase_mistake(
        self,
        mistake: ClassifiedMistake,
        player_name: str = "Player"
    ) -> str:
        """
        Convert a classified mistake to natural language feedback.
        
        Args:
            mistake: ClassifiedMistake object from classifier
            player_name: Player name for personalization
            
        Returns:
            Natural language feedback string
        """
        if not self.is_available():
            return self._get_fallback_message(mistake)
        
        prompt = self._build_prompt(mistake, player_name)
        
        try:
            response = self._call_ollama(prompt)
            if response:
                return response
        except Exception as e:
            print(f"Ollama error: {e}")
        
        return self._get_fallback_message(mistake)
    
    def phrase_all_mistakes(
        self,
        mistakes: List[ClassifiedMistake],
        player_name: str = "Player"
    ) -> List[Dict[str, str]]:
        """
        Convert all classified mistakes to natural language.
        
        Args:
            mistakes: List of ClassifiedMistake objects
            player_name: Player name for personalization
            
        Returns:
            List of dicts with type and feedback
        """
        results = []
        
        for mistake in mistakes:
            feedback = self.phrase_mistake(mistake, player_name)
            results.append({
                "type": mistake.mistake_type,
                "location": mistake.map_area,
                "round": mistake.round_num,
                "feedback": feedback,
                "severity": f"{int(mistake.severity * 100)}%"
            })
        
        return results
    
    def _build_prompt(
        self,
        mistake: ClassifiedMistake,
        player_name: str
    ) -> str:
        """Build the prompt for Ollama."""
        return f"""You are a CS2 coach. Convert this mistake into ONE concise coaching sentence.

MISTAKE:
- Type: {mistake.mistake_type}
- Details: {mistake.details}
- Location: {mistake.map_area}
- Round: {mistake.round_num}
- Severity: {int(mistake.severity * 100)}%
- Default Fix: {mistake.correction}

RULES:
1. Give ONE sentence of specific, actionable feedback
2. Be direct and constructive
3. Reference the specific map area when relevant
4. Player name is {player_name}

Respond with ONLY the coaching feedback sentence:"""
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API."""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 100
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
        except requests.RequestException as e:
            print(f"Ollama request failed: {e}")
        
        return None
    
    def _get_fallback_message(self, mistake: ClassifiedMistake) -> str:
        """Get fallback message when Ollama is unavailable."""
        # Use the correction from the classifier directly
        return mistake.correction
    
    def generate_summary(
        self,
        mistakes: List[ClassifiedMistake],
        player_name: str = "Player"
    ) -> str:
        """
        Generate a summary paragraph of all mistakes.
        
        Args:
            mistakes: List of ClassifiedMistake objects
            player_name: Player name for personalization
            
        Returns:
            Summary paragraph
        """
        if not mistakes:
            return f"{player_name} played well with no significant improvement areas identified."
        
        if not self.is_available():
            return self._generate_fallback_summary(mistakes, player_name)
        
        # Build summary prompt
        mistake_list = "\n".join([
            f"- {m.mistake_type} at {m.map_area}: {int(m.severity * 100)}% severity"
            for m in mistakes[:5]  # Limit to top 5
        ])
        
        prompt = f"""You are a CS2 coach. Write a brief 2-3 sentence summary of the player's main improvement areas.

PLAYER: {player_name}
IDENTIFIED MISTAKES:
{mistake_list}

Write a constructive summary focusing on the most impactful improvements:"""
        
        try:
            response = self._call_ollama(prompt)
            if response:
                return response
        except Exception:
            pass
        
        return self._generate_fallback_summary(mistakes, player_name)
    
    def _generate_fallback_summary(
        self,
        mistakes: List[ClassifiedMistake],
        player_name: str
    ) -> str:
        """Generate fallback summary without Ollama."""
        if not mistakes:
            return f"{player_name} played well with no significant improvement areas identified."
        
        # Group by mistake type
        types = {}
        for mistake in mistakes:
            if mistake.mistake_type not in types:
                types[mistake.mistake_type] = []
            types[mistake.mistake_type].append(mistake)
        
        # Build summary
        parts = [f"{player_name}'s main improvement areas:"]
        
        for mtype, type_mistakes in types.items():
            high_severity = [m for m in type_mistakes if m.severity >= 0.8]
            if high_severity:
                parts.append(f"- {mtype.replace('_', ' ')}: Critical (found {len(type_mistakes)}x)")
            elif type_mistakes:
                parts.append(f"- {mtype.replace('_', ' ')}: {len(type_mistakes)} instances")
        
        return " ".join(parts)
