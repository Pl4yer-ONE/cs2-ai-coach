"""
HTML Report Generator
Creates shareable HTML reports with embedded CSS.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR


class HTMLReporter:
    """Generate HTML reports from analysis data."""
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, report: Dict[str, Any]) -> str:
        """Generate HTML report content."""
        meta = report.get("meta", {})
        summary = report.get("summary", {})
        players = report.get("players", {})
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FragAudit Report - {meta.get('map', 'Unknown')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #ff6b35; margin-bottom: 0.5rem; }}
        h2 {{ color: #4ecdc4; margin: 2rem 0 1rem; border-bottom: 2px solid #4ecdc4; padding-bottom: 0.5rem; }}
        h3 {{ color: #f7d354; margin: 1.5rem 0 0.5rem; }}
        .meta {{ color: #888; margin-bottom: 2rem; }}
        .summary {{
            background: #16213e;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }}
        .summary-item {{ text-align: center; }}
        .summary-value {{ font-size: 2rem; font-weight: bold; color: #ff6b35; }}
        .summary-label {{ color: #888; font-size: 0.9rem; }}
        .player-card {{
            background: #16213e;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .player-name {{ font-size: 1.4rem; color: #4ecdc4; margin-bottom: 1rem; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1rem; }}
        .stat {{ text-align: center; padding: 0.5rem; background: #1a1a2e; border-radius: 4px; }}
        .stat-value {{ font-size: 1.2rem; font-weight: bold; }}
        .stat-label {{ font-size: 0.8rem; color: #888; }}
        .mistake {{
            background: #1a1a2e;
            border-left: 4px solid #ff6b35;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 4px 4px 0;
        }}
        .mistake.high {{ border-color: #ff4444; }}
        .mistake.medium {{ border-color: #ffaa00; }}
        .mistake.low {{ border-color: #44ff44; }}
        .mistake-header {{ display: flex; justify-content: space-between; margin-bottom: 0.5rem; }}
        .mistake-context {{ color: #888; font-size: 0.9rem; }}
        .mistake-type {{ font-weight: bold; color: #ff6b35; }}
        .mistake-fix {{ color: #4ecdc4; margin-top: 0.5rem; }}
        .severity {{ 
            padding: 0.2rem 0.5rem; 
            border-radius: 4px; 
            font-size: 0.8rem;
            background: #333;
        }}
        footer {{ text-align: center; color: #666; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #333; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>FragAudit Report</h1>
        <p class="meta">
            Map: {meta.get('map', 'Unknown')} | 
            Demo: {meta.get('demo_file', 'Unknown')} |
            Generated: {meta.get('generated_at', datetime.now().isoformat())[:19]}
        </p>
        
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{summary.get('total_players_analyzed', 0)}</div>
                    <div class="summary-label">Players</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{summary.get('total_mistakes_found', 0)}</div>
                    <div class="summary-label">Mistakes</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{summary.get('most_common_issue', 'None') or 'None'}</div>
                    <div class="summary-label">Most Common</div>
                </div>
            </div>
        </div>
        
        <h2>Player Reports</h2>
"""
        
        for player_id, player_data in players.items():
            stats = player_data.get("stats", {})
            mistakes = player_data.get("mistakes", [])
            
            html += f"""
        <div class="player-card">
            <div class="player-name">{player_data.get('player_name', player_id)}</div>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-value">{stats.get('kd_ratio', 0)}</div>
                    <div class="stat-label">K/D</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats.get('headshot_percentage', 0)}%</div>
                    <div class="stat-label">HS%</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats.get('damage_per_round', 0)}</div>
                    <div class="stat-label">ADR</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats.get('detected_role', 'Unknown')}</div>
                    <div class="stat-label">Role</div>
                </div>
            </div>
"""
            
            if mistakes:
                html += "            <h3>Mistakes</h3>\n"
                for m in mistakes:
                    sev = m.get('severity', '50%')
                    sev_class = 'high' if '8' in sev or '9' in sev else 'medium' if '5' in sev or '6' in sev or '7' in sev else 'low'
                    html += f"""
            <div class="mistake {sev_class}">
                <div class="mistake-header">
                    <span class="mistake-context">Round {m.get('round', '?')} | {m.get('time', '?')} | {m.get('location', '?')}</span>
                    <span class="severity">{sev}</span>
                </div>
                <div class="mistake-type">{m.get('type', 'unknown').replace('_', ' ').title()}</div>
                <div>{m.get('details', '')}</div>
                <div class="mistake-fix">Fix: {m.get('fix', '')}</div>
            </div>
"""
            else:
                html += "            <p style='color: #4ecdc4;'>No mistakes detected</p>\n"
            
            html += "        </div>\n"
        
        html += """
        <footer>
            Generated by FragAudit — <a href="https://github.com/Pl4yer-ONE/FragAudit" style="color: #4ecdc4;">github.com/Pl4yer-ONE/FragAudit</a>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def save(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save HTML report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        html_content = self.generate(report)
        
        with open(filepath, "w") as f:
            f.write(html_content)
        
        return str(filepath)
