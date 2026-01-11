"""
Report Generator
Generates coaching reports in JSON and Markdown formats.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from config import OUTPUT_DIR
from src.features.extractor import PlayerFeatures
from src.classifier.mistake_classifier import ClassifiedMistake


class ReportGenerator:
    """
    Generate coaching reports from analysis results.
    """
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        demo_path: str,
        player_features: Dict[str, PlayerFeatures],
        classified_mistakes: Dict[str, List[ClassifiedMistake]],
        nlp_feedback: Optional[Dict[str, List[Dict]]] = None,
        map_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Generate a complete coaching report.
        
        Args:
            demo_path: Path to analyzed demo
            player_features: Dict mapping player_id to PlayerFeatures
            classified_mistakes: Dict mapping player_id to list of ClassifiedMistake
            nlp_feedback: Optional NLP-phrased feedback per player
            map_name: Map name from demo
            
        Returns:
            Report dictionary
        """
        timestamp = datetime.now().isoformat()
        
        report = {
            "meta": {
                "generated_at": timestamp,
                "demo_file": demo_path,
                "map": map_name,
                "analysis_version": "1.0.0"
            },
            "summary": self._generate_summary(player_features, classified_mistakes),
            "players": {}
        }
        
        # Generate per-player reports
        for player_id, features in player_features.items():
            mistakes = classified_mistakes.get(player_id, [])
            feedback = nlp_feedback.get(player_id, []) if nlp_feedback else []
            
            report["players"][player_id] = self._generate_player_report(
                features=features,
                mistakes=mistakes,
                feedback=feedback
            )
        
        return report
    
    def _generate_summary(
        self,
        player_features: Dict[str, PlayerFeatures],
        classified_mistakes: Dict[str, List[ClassifiedMistake]]
    ) -> Dict[str, Any]:
        """Generate match summary."""
        total_mistakes = sum(len(m) for m in classified_mistakes.values())
        
        # Count mistakes by category
        category_counts = {}
        for mistakes in classified_mistakes.values():
            for mistake in mistakes:
                if mistake.category not in category_counts:
                    category_counts[mistake.category] = 0
                category_counts[mistake.category] += 1
        
        # Find most common issue
        most_common = max(category_counts.items(), key=lambda x: x[1]) if category_counts else (None, 0)
        
        return {
            "total_players_analyzed": len(player_features),
            "total_mistakes_found": total_mistakes,
            "mistakes_by_category": category_counts,
            "most_common_issue": most_common[0]
        }
    
    def _generate_player_report(
        self,
        features: PlayerFeatures,
        mistakes: List[ClassifiedMistake],
        feedback: List[Dict]
    ) -> Dict[str, Any]:
        """Generate per-player report."""
        return {
            "player_name": features.player_name or "",
            "stats": {
                "kills": features.kills,
                "deaths": features.deaths,
                "kd_ratio": round(features.kills / max(features.deaths, 1), 2),
                "headshot_percentage": round(features.headshot_percentage * 100, 1),
                "damage_per_round": round(features.damage_per_round, 1),
                "flash_success_rate": round(features.flash_success_rate * 100, 1),
                # Trade detection stats
                "entry_deaths": getattr(features, 'entry_deaths', 0),
                "traded_deaths": getattr(features, 'tradeable_deaths', 0),
                "untradeable_death_ratio": round(getattr(features, 'untradeable_death_ratio', 0) * 100, 1),
                # Role detection
                "detected_role": getattr(features, 'detected_role', 'support'),
                "entry_death_ratio": round(getattr(features, 'entry_death_ratio', 0) * 100, 1),
                "primary_death_area": getattr(features, 'primary_death_area', ''),
                # Round phase deaths
                "early_round_deaths": getattr(features, 'early_round_deaths', 0),
                "mid_round_deaths": getattr(features, 'mid_round_deaths', 0),
                "late_round_deaths": getattr(features, 'late_round_deaths', 0),
            },
            "mistakes": [
                {
                    "category": m.category,
                    "subcategory": m.subcategory,
                    "severity": m.severity,
                    "confidence": round(m.confidence, 2),
                    "current_value": m.current_value,
                    "target_value": m.target_value,
                    "tactical_feedback": getattr(m, 'tactical_feedback', ''),
                    "evidence": m.evidence_metrics
                }
                for m in mistakes
            ],
            "feedback": feedback,
            "improvement_priority": [
                m.subcategory for m in mistakes[:3]  # Top 3 priorities
            ]
        }
    
    def save_json(self, report: Dict[str, Any], filename: str = None) -> str:
        """
        Save report as JSON.
        
        Args:
            report: Report dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coaching_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(filepath)
    
    def save_markdown(self, report: Dict[str, Any], filename: str = None) -> str:
        """
        Save report as Markdown.
        
        Args:
            report: Report dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coaching_report_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        md_content = self._generate_markdown(report)
        
        with open(filepath, "w") as f:
            f.write(md_content)
        
        return str(filepath)
    
    def _generate_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to Markdown format."""
        lines = []
        
        # Header
        lines.append("# CS2 Coaching Report")
        lines.append("")
        lines.append(f"**Generated:** {report['meta']['generated_at']}")
        lines.append(f"**Demo:** {report['meta']['demo_file']}")
        lines.append(f"**Map:** {report['meta']['map']}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        summary = report["summary"]
        lines.append(f"- **Players Analyzed:** {summary['total_players_analyzed']}")
        lines.append(f"- **Total Issues Found:** {summary['total_mistakes_found']}")
        if summary["most_common_issue"]:
            lines.append(f"- **Most Common Issue:** {summary['most_common_issue']}")
        lines.append("")
        
        # Per-player sections
        for player_id, player_data in report["players"].items():
            player_name = player_data.get("player_name", "") or player_id
            lines.append(f"## Player: {player_name}")
            lines.append("")
            
            # Stats table
            lines.append("### Stats")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            stats = player_data["stats"]
            lines.append(f"| K/D | {stats['kd_ratio']} ({stats['kills']}/{stats['deaths']}) |")
            lines.append(f"| Headshot % | {stats['headshot_percentage']}% |")
            lines.append(f"| ADR | {stats['damage_per_round']} |")
            lines.append(f"| Flash Success | {stats['flash_success_rate']}% |")
            lines.append("")
            
            # Mistakes
            if player_data["mistakes"]:
                lines.append("### Improvement Areas")
                lines.append("")
                for mistake in player_data["mistakes"]:
                    severity_emoji = "🔴" if mistake["severity"] == "high" else "🟡" if mistake["severity"] == "medium" else "🟢"
                    lines.append(f"#### {severity_emoji} {mistake['category']}: {mistake['subcategory'].replace('_', ' ').title()}")
                    lines.append("")
                    lines.append(f"- **Current:** {mistake['current_value']}")
                    lines.append(f"- **Target:** {mistake['target_value']}")
                    lines.append(f"- **Confidence:** {mistake['confidence'] * 100:.0f}%")
                    lines.append("")
            
            # Feedback
            if player_data["feedback"]:
                lines.append("### Coaching Feedback")
                lines.append("")
                for fb in player_data["feedback"]:
                    lines.append(f"- {fb['feedback']}")
                lines.append("")
            
            # Priority
            if player_data["improvement_priority"]:
                lines.append("### Priority Focus")
                lines.append("")
                for i, priority in enumerate(player_data["improvement_priority"], 1):
                    lines.append(f"{i}. {priority.replace('_', ' ').title()}")
                lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("*Generated by CS2 AI Coach - Metrics-driven, explainable feedback*")
        
        return "\n".join(lines)
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a quick summary to console."""
        print("\n" + "=" * 50)
        print("CS2 COACHING REPORT SUMMARY")
        print("=" * 50)
        
        summary = report["summary"]
        print(f"Players analyzed: {summary['total_players_analyzed']}")
        print(f"Issues found: {summary['total_mistakes_found']}")
        
        if summary["mistakes_by_category"]:
            print("\nIssues by category:")
            for category, count in summary["mistakes_by_category"].items():
                print(f"  - {category}: {count}")
        
        print("\n" + "-" * 50)
        
        for player_id, player_data in report["players"].items():
            stats = player_data["stats"]
            player_name = player_data.get("player_name", "") or player_id
            print(f"\nPlayer: {player_name}")
            print(f"  K/D: {stats['kd_ratio']} | HS%: {stats['headshot_percentage']}%")
            
            if player_data["improvement_priority"]:
                print(f"  Focus: {', '.join(player_data['improvement_priority'][:2])}")
        
        print("\n" + "=" * 50)
