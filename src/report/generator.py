# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.

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
        
        # Count mistakes by type
        type_counts = {}
        for mistakes in classified_mistakes.values():
            for mistake in mistakes:
                if mistake.mistake_type not in type_counts:
                    type_counts[mistake.mistake_type] = 0
                type_counts[mistake.mistake_type] += 1
        
        # Find most common issue
        most_common = max(type_counts.items(), key=lambda x: x[1]) if type_counts else (None, 0)
        
        return {
            "total_players_analyzed": len(player_features),
            "total_mistakes_found": total_mistakes,
            "mistakes_by_type": type_counts,
            "most_common_issue": most_common[0]
        }
    
    def _generate_player_report(
        self,
        features: PlayerFeatures,
        mistakes: List[ClassifiedMistake],
        feedback: List[Dict]
    ) -> Dict[str, Any]:
        """Generate per-player report with full competitive stats."""
        
        # Calculate rating if not already set
        adr = getattr(features, 'damage_per_round', 0)
        kast = getattr(features, 'kast_percentage', 0)
        kpr = features.kills / max(getattr(features, 'rounds_played', 1), 1)
        dpr = features.deaths / max(getattr(features, 'rounds_played', 1), 1)
        
        # Simple HLTV 2.0 inspired rating
        rating = (0.0073 * kast * 100) + (0.3591 * kpr) - (0.5329 * dpr) + (0.2372 * adr / 100) + 0.0032
        rating = max(0.0, min(3.0, rating))  # Clamp to reasonable range
        
        return {
            "player_name": features.player_name or "",
            "team": getattr(features, 'team_id', '') or "Unknown",
            "stats": {
                # Basic stats
                "kills": features.kills,
                "deaths": features.deaths,
                "assists": getattr(features, 'assists', 0),
                "kd_ratio": round(features.kills / max(features.deaths, 1), 2),
                "headshot_percentage": round(features.headshot_percentage * 100, 1),
                "adr": round(adr, 1),
                
                # Competitive stats (HLTV-style)
                "kast": round(kast * 100, 1),
                "rating": round(rating, 2),
                "rws": round(getattr(features, 'rws', 0), 1),  # FACEIT RWS
                
                # Opening duels / First Blood
                "entry_kills": getattr(features, 'entry_kills', 0),
                "entry_deaths": getattr(features, 'entry_deaths', 0),
                "first_blood_attempts": getattr(features, 'first_blood_attempts', 0),
                "first_blood_success": round(getattr(features, 'first_blood_success', 0) * 100, 1),
                
                # Clutches
                "clutches_1v1_won": getattr(features, 'clutches_1v1_won', 0),
                "clutches_1v1_attempted": getattr(features, 'clutches_1v1_attempted', 0),
                "clutches_1vN_won": getattr(features, 'clutches_1vN_won', 0),
                "clutches_1vN_attempted": getattr(features, 'clutches_1vN_attempted', 0),
                
                # Impact
                "total_wpa": round(getattr(features, 'total_wpa', 0), 2),
                "multikills": getattr(features, 'multikills', 0),
                "swing_kills": getattr(features, 'swing_kills', 0),
                
                # Trading (HLTV-style)
                "traded_deaths": getattr(features, 'tradeable_deaths', 0),
                "trades_given": getattr(features, 'trades_given', 0),
                "trades_received": getattr(features, 'trades_received', 0),
                "saved_teammates": getattr(features, 'saved_teammates', 0),
                "untradeable_death_ratio": round(getattr(features, 'untradeable_death_ratio', 0) * 100, 1),
                "trade_potential_score": getattr(features, 'trade_potential_score', 0),
                
                # Utility (HLTV-style)
                "flash_success_rate": round(features.flash_success_rate * 100, 1),
                "flashes_thrown": getattr(features, 'flashes_thrown', 0),
                "flash_assists": getattr(features, 'flash_assists', 0),
                "enemies_blinded": getattr(features, 'enemies_blinded', 0),
                "opp_flashed_time": round(getattr(features, 'opp_flashed_time', 0), 2),
                
                # Weapon breakdown
                "awp_kills": getattr(features, 'awp_kills', 0),
                "rifle_kills": getattr(features, 'rifle_kills', 0),
                "pistol_kills": getattr(features, 'pistol_kills', 0),
                "smg_kills": getattr(features, 'smg_kills', 0),
                
                # Economy context
                "adr_vs_eco": round(getattr(features, 'adr_vs_eco', 0), 1),
                "adr_vs_fullbuy": round(getattr(features, 'adr_vs_fullbuy', 0), 1),
            },
            "role": {
                "detected": getattr(features, 'detected_role', 'Support'),
                "confidence": 0.8,  # Placeholder, would be from classifier
            },
            "mistakes": [
                {
                    "round": m.round_num,
                    "time": f"{int(m.round_time_seconds // 60)}:{int(m.round_time_seconds % 60):02d}",
                    "location": m.map_area,
                    "type": m.mistake_type,
                    "details": m.details,
                    "fix": m.correction,
                    "severity": m.severity_label.lower()  # "high", "medium", "low"
                }
                for m in mistakes
            ],
            "feedback": feedback,
            "improvement_priority": [
                m.mistake_type for m in mistakes[:3]
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
                lines.append("### Mistakes")
                lines.append("")
                for mistake in player_data["mistakes"]:
                    sev = mistake["severity"]
                    severity_emoji = "🔴" if sev == "HIGH" else "🟡" if sev == "MED" else "🟢"
                    lines.append(f"#### {severity_emoji} [{sev}] Round {mistake['round']} | {mistake['time']} | {mistake['location']}")
                    lines.append("")
                    lines.append(f"**{mistake['type'].replace('_', ' ').title()}**")
                    lines.append(f"- {mistake['details']}")
                    lines.append(f"- **Fix:** {mistake['fix']}")
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
        """Print a styled summary to console with colors."""
        # ANSI color codes
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        DIM = "\033[2m"
        RESET = "\033[0m"
        
        summary = report["summary"]
        meta = report.get("meta", {})
        
        # Header
        print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
        print(f"{BOLD}{CYAN}  FRAGAUDIT ANALYSIS{RESET}")
        print(f"{CYAN}{'═' * 60}{RESET}")
        
        # Meta info
        print(f"\n{DIM}  Map: {meta.get('map', 'Unknown')}{RESET}")
        print(f"{DIM}  Demo: {meta.get('demo_file', 'Unknown')}{RESET}")
        
        # Stats row
        total_players = summary['total_players_analyzed']
        total_issues = summary['total_mistakes_found']
        issue_color = GREEN if total_issues < 5 else YELLOW if total_issues < 10 else RED
        
        print(f"\n  {BOLD}Players:{RESET} {total_players}    {BOLD}Issues:{RESET} {issue_color}{total_issues}{RESET}")
        
        # Issues breakdown
        if summary.get("mistakes_by_type"):
            print(f"\n  {DIM}Issue Types:{RESET}")
            for mtype, count in sorted(summary["mistakes_by_type"].items(), key=lambda x: -x[1]):
                bar = "█" * min(count, 10) + "░" * (10 - min(count, 10))
                print(f"    {mtype.replace('_', ' '):20} {bar} {count}")
        
        print(f"\n{CYAN}{'─' * 60}{RESET}")
        print(f"{BOLD}  PLAYER BREAKDOWN{RESET}")
        print(f"{CYAN}{'─' * 60}{RESET}")
        
        # Player cards
        for player_id, player_data in report["players"].items():
            stats = player_data["stats"]
            player_name = player_data.get("player_name") or player_id[:12]
            kd = stats['kd_ratio']
            hs = stats['headshot_percentage']
            role = stats.get('detected_role', '')
            mistakes = player_data.get("mistakes", [])
            
            # Color K/D
            kd_color = GREEN if kd >= 1.2 else YELLOW if kd >= 0.9 else RED
            
            # Trade score with color
            trade_score = stats.get('trade_potential_score', 0)
            trade_color = GREEN if trade_score >= 60 else YELLOW if trade_score >= 30 else RED
            
            print(f"\n  {BOLD}{player_name}{RESET}")
            print(f"    K/D: {kd_color}{kd}{RESET}  HS: {hs}%  Trade: {trade_color}{trade_score}%{RESET}  Role: {role}")
            
            if mistakes:
                for m in mistakes[:2]:  # Show top 2 mistakes
                    sev = m.get('severity', 'MED')
                    sev_icon = "🔴" if sev == "HIGH" else "🟡" if sev == "MED" else "🟢"
                    print(f"    {sev_icon} [{sev}] R{m.get('round', '?')} {m.get('time', '')} — {m.get('type', '').replace('_', ' ')}")
            else:
                print(f"    {GREEN}✓ No issues detected{RESET}")
        
        print(f"\n{CYAN}{'═' * 60}{RESET}\n")
