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
            List of dicts with category and feedback
        """
        results = []
        
        for mistake in mistakes:
            feedback = self.phrase_mistake(mistake, player_name)
            results.append({
                "category": mistake.category,
                "subcategory": mistake.subcategory,
                "feedback": feedback,
                "severity": mistake.severity,
                "confidence": mistake.confidence
            })
        
        return results
    
    def _build_prompt(
        self,
        mistake: ClassifiedMistake,
        player_name: str
    ) -> str:
        """Build the prompt for Ollama."""
        return f"""You are a CS2 coach. Convert this classified mistake into ONE concise coaching sentence for the player.

MISTAKE DATA (this is determined by analysis, not for you to change):
- Category: {mistake.category}
- Subcategory: {mistake.subcategory}
- Severity: {mistake.severity}
- Current Value: {mistake.current_value}
- Target Value: {mistake.target_value}
- Evidence: {json.dumps(mistake.evidence_metrics)}

RULES:
1. Give ONE sentence of specific, actionable feedback
2. Do NOT question or change the classification
3. Be direct and constructive
4. Reference specific numbers when helpful
5. Player name is {player_name}

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
        category_messages = FALLBACK_MESSAGES.get(mistake.category, {})
        message = category_messages.get(
            mistake.feedback_key,
            f"Focus on improving your {mistake.subcategory.replace('_', ' ')}."
        )
        
        # Add current value context
        if mistake.current_value:
            message += f" (Current: {mistake.current_value}, Target: {mistake.target_value})"
        
        return message
    
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
            f"- {m.category}/{m.subcategory}: {m.severity} severity, {m.current_value} vs target {m.target_value}"
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
        
        # Group by category
        categories = {}
        for mistake in mistakes:
            if mistake.category not in categories:
                categories[mistake.category] = []
            categories[mistake.category].append(mistake)
        
        # Build summary
        parts = [f"{player_name}'s main improvement areas:"]
        
        for category, cat_mistakes in categories.items():
            high_severity = [m for m in cat_mistakes if m.severity == "high"]
            if high_severity:
                parts.append(f"- {category}: Focus on {high_severity[0].subcategory.replace('_', ' ')}")
            elif cat_mistakes:
                parts.append(f"- {category}: Minor improvements needed")
        
        return " ".join(parts)
