"""
JSON Reporter
Generates the final structured JSON output for the frontend/user.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.features.extractor import PlayerFeatures
from src.classifier.mistake_classifier import ClassifiedMistake
from src.metrics.scoring import ScoreEngine
from src.report.drills import get_drills_for_mistake

class JsonReporter:
    """
    Generates JSON reports from analyzed data.
    """
    
    def __init__(self, output_dir: str = "outputs/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _to_relative_paths(heatmaps: Dict, base_marker: str = "outputs/") -> Dict:
        """
        Convert absolute heatmap paths to relative paths for portability.
        Strips everything before 'outputs/' to make paths deployment-friendly.
        """
        if not heatmaps:
            return {}
        
        def relativize(path: str) -> str:
            if not path or not isinstance(path, str):
                return path
            # Find the base marker and keep everything after it
            if base_marker in path:
                idx = path.find(base_marker)
                return path[idx:]
            # Fallback: just return the filename
            return Path(path).name
        
        result = {}
        for key, value in heatmaps.items():
            if isinstance(value, dict):
                result[key] = JsonReporter._to_relative_paths(value, base_marker)
            elif isinstance(value, str):
                result[key] = relativize(value)
            else:
                result[key] = value
        return result
        
    def generate_report(
        self, 
        match_id: str, 
        map_name: str, 
        players: Dict[str, PlayerFeatures], 
        mistakes: Dict[str, List[ClassifiedMistake]],
        heatmap_urls: Dict[str, str] = None
    ) -> str:
        """
        Create and save the full match report.
        """
        report = {
            "meta": {
                "match_id": match_id,
                "map": map_name,
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0"
            },
            "players": {},
            "team_summary": self._generate_team_summary(players)
        }
        
        for pid, features in players.items():
            player_mistakes = mistakes.get(pid, [])
            report["players"][pid] = self._generate_player_report(features, player_mistakes, heatmap_urls)
            
        # Save to file
        filename = f"match_report_{match_id}.json"
        out_path = self.output_dir / filename
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
            
        return str(out_path)

    def _generate_player_report(
        self, 
        p: PlayerFeatures, 
        mistakes: List[ClassifiedMistake],
        heatmaps: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Generate individual player section."""
        
        # Calculate scores
        # Calculate scores
        # Prepare inputs
        kpr = p.kills / max(1, p.rounds_played)
        kdr = p.kills / max(1, p.deaths)
        untradeable_deaths = p.deaths - p.tradeable_deaths
        survival_rate = (p.rounds_played - p.deaths) / max(1, p.rounds_played)
        
        # Aim returns (raw, effective) tuple for honesty
        raw_aim, effective_aim = ScoreEngine.compute_aim_score(
            p.headshot_percentage, 
            kpr, 
            p.damage_per_round,
            p.counter_strafing_score_avg
        )
        
        scores = {
            "raw_aim": raw_aim,
            "aim": effective_aim,  # The penalized/effective value used for rating
            "positioning": ScoreEngine.compute_positioning_score(
                p.untradeable_death_ratio,
                0.0, # Trade success default
                survival_rate
            ),
            "utility": ScoreEngine.compute_utility_score(
                p.enemies_blinded, 
                p.grenade_damage, 
                p.flashes_thrown
            ),
            "impact": ScoreEngine.compute_impact_score(
                p.entry_kills,
                p.entry_deaths,
                p.multikills, 
                p.clutches_1v1_won,
                p.clutches_1vN_won,
                untradeable_deaths,
                p.tradeable_deaths,
                p.damage_per_round,
                p.kills,
                p.deaths
            )
        }
        
        # Handle hidden utility score
        if scores["utility"] == -1:
            scores["utility"] = None # Will be null in JSON
            
        overall_rating = ScoreEngine.compute_final_rating(
            scores, 
            p.detected_role, 
            kdr, 
            untradeable_deaths,
            survival_rate,
            p.entry_kills  # Opening kills
        )
        
        # Process mistakes with severity weighting
        processed_mistakes = []
        for m in mistakes:
            processed_mistakes.append({
                "tick": m.tick,
                "round": m.round_num,
                "type": m.mistake_type,
                "description": m.details,
                "advice": m.correction,
                "severity": m.severity,
                "drills": get_drills_for_mistake(m.mistake_type)
            })
            
        # Top 3 mistakes
        mistake_counts = {}
        for m in mistakes:
            mistake_counts[m.mistake_type] = mistake_counts.get(m.mistake_type, 0) + 1
        top_mistakes = sorted(mistake_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
        # Link heatmaps - convert to relative paths for portability
        player_heatmaps = {}
        if heatmaps:
            if "personal" in heatmaps and p.player_id in heatmaps["personal"]:
                player_heatmaps = self._to_relative_paths(heatmaps["personal"][p.player_id])
            elif "global" in heatmaps:
                player_heatmaps = self._to_relative_paths(heatmaps["global"])
            elif isinstance(heatmaps, dict):
                player_heatmaps = self._to_relative_paths(heatmaps)

        return {
            "name": p.player_name,
            "role": p.detected_role,
            "rating": overall_rating,
            "scores": scores,
            "stats": {
                "kills": p.kills,
                "deaths": p.deaths,
                "kdr": round(p.kills/max(1, p.deaths), 2),
                "adr": round(p.damage_per_round, 1),
                "hs_percent": round(p.headshot_percentage * 100, 1),
                "untradeable_deaths": p.deaths - p.tradeable_deaths,
                "tradeable_deaths": p.tradeable_deaths,
                "entry_kills": p.entry_kills,
                "entry_deaths": p.entry_deaths,
                "multikills": p.multikills,
                "enemies_blinded": p.enemies_blinded,
                "utility_damage": p.grenade_damage,
                "clutches_1v1_won": p.clutches_1v1_won,
                "clutches_1vN_won": p.clutches_1vN_won
            },
            "mechanics": {
                "avg_counter_strafing": round(p.counter_strafing_score_avg, 1),
                "peek_stats": p.peek_types
            },
            "top_issues": [k for k,v in top_mistakes],
            "mistakes": processed_mistakes,
            "heatmaps": player_heatmaps
        }

    def _generate_team_summary(self, players: Dict[str, PlayerFeatures]) -> Dict[str, Any]:
        """Generate team-wide stats."""
        total_kills = sum(p.kills for p in players.values())
        total_deaths = sum(p.deaths for p in players.values())
        
        # Aggregate stats
        return {
            "total_kills": total_kills,
            "total_deaths": total_deaths,
            "kd_ratio": round(total_kills / max(1, total_deaths), 2),
            "players_analyzed": len(players)
        }
