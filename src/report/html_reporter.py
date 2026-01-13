"""
HTML Report Generator
Creates shareable HTML reports with modern styling.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR


class HTMLReporter:
    """Generate beautiful HTML reports from analysis data."""
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, report: Dict[str, Any]) -> str:
        """Generate HTML report content."""
        meta = report.get("meta", {})
        summary = report.get("summary", {})
        players = report.get("players", {})
        
        # Build issue bars HTML
        issues_html = ""
        if summary.get("mistakes_by_type"):
            max_count = max(summary["mistakes_by_type"].values()) if summary["mistakes_by_type"] else 1
            for mtype, count in sorted(summary["mistakes_by_type"].items(), key=lambda x: -x[1]):
                pct = (count / max_count) * 100
                issues_html += f'''
            <div class="issue-bar">
                <div class="issue-name">{mtype.replace('_', ' ')}</div>
                <div class="issue-visual"><div class="issue-fill" style="width: {pct}%"></div></div>
                <div class="issue-count">{count}</div>
            </div>'''
        
        # Build player cards HTML
        players_html = ""
        for player_id, player_data in players.items():
            stats = player_data.get("stats", {})
            mistakes = player_data.get("mistakes", [])
            player_name = player_data.get("player_name") or player_id[:16]
            
            kd = stats.get('kd_ratio', 0)
            kd_class = 'kd-good' if kd >= 1.2 else 'kd-mid' if kd >= 0.9 else 'kd-bad'
            
            mistakes_html = ""
            if mistakes:
                for m in mistakes:
                    sev = m.get('severity', 'MED')
                    sev_class = 'severity-high' if sev == 'HIGH' else 'severity-med' if sev == 'MED' else 'severity-low'
                    mistakes_html += f'''
                <div class="mistake">
                    <div class="mistake-header">
                        <span class="mistake-context">Round {m.get('round', '?')} • {m.get('time', '?')} • {m.get('location', 'Unknown')}</span>
                        <span class="severity {sev_class}">{sev}</span>
                    </div>
                    <div class="mistake-type">{m.get('type', 'unknown').replace('_', ' ').title()}</div>
                    <div>{m.get('details', '')}</div>
                    <div class="mistake-fix">Fix: {m.get('fix', '')}</div>
                </div>'''
            else:
                mistakes_html = '<div class="no-issues">✓ No issues detected</div>'
            
            # Trade score color class
            trade_score = stats.get('trade_potential_score', 0)
            trade_class = 'kd-good' if trade_score >= 60 else 'kd-mid' if trade_score >= 30 else 'kd-bad'
            
            players_html += f'''
            <div class="player-card">
                <div class="player-name">{player_name}</div>
                <div class="player-stats">
                    <span>K/D: <strong class="{kd_class}">{kd}</strong></span>
                    <span>HS: {stats.get('headshot_percentage', 0)}%</span>
                    <span>Trade: <strong class="{trade_class}">{trade_score}%</strong></span>
                    <span>Role: {stats.get('detected_role', 'Unknown')}</span>
                </div>
                {mistakes_html}
            </div>'''
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FragAudit Report - {meta.get('map', 'Unknown')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            line-height: 1.6;
            padding: 2rem;
            min-height: 100vh;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }}
        .logo {{ font-size: 2.5rem; font-weight: bold; color: #ff6b35; }}
        .subtitle {{ color: #888; margin-top: 0.5rem; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: rgba(78, 205, 196, 0.1);
            border: 1px solid rgba(78, 205, 196, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #4ecdc4; }}
        .stat-label {{ color: #888; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }}
        
        h2 {{
            color: #4ecdc4;
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(78, 205, 196, 0.3);
        }}
        
        .player-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #4ecdc4;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .player-card:hover {{
            transform: translateX(4px);
            box-shadow: 0 4px 20px rgba(78, 205, 196, 0.2);
        }}
        .player-name {{ font-size: 1.3rem; font-weight: bold; color: #fff; margin-bottom: 0.5rem; }}
        .player-stats {{ display: flex; gap: 2rem; color: #888; font-size: 0.9rem; margin-bottom: 1rem; flex-wrap: wrap; }}
        .player-stats span {{ display: flex; align-items: center; gap: 0.3rem; }}
        .kd-good {{ color: #4ecdc4; }}
        .kd-mid {{ color: #f7d354; }}
        .kd-bad {{ color: #ff6b6b; }}
        
        .mistake {{
            background: rgba(255, 107, 53, 0.1);
            border-left: 3px solid #ff6b35;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }}
        .mistake-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem; }}
        .mistake-context {{ color: #888; font-size: 0.85rem; }}
        .mistake-type {{ color: #ff6b35; font-weight: bold; }}
        .mistake-fix {{ color: #4ecdc4; margin-top: 0.5rem; font-size: 0.9rem; }}
        .severity {{ background: rgba(255, 107, 53, 0.2); padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }}
        .severity-high {{ background: rgba(255, 68, 68, 0.3); color: #ff4444; }}
        .severity-med {{ background: rgba(255, 170, 0, 0.3); color: #ffaa00; }}
        .severity-low {{ background: rgba(68, 255, 68, 0.3); color: #44ff44; }}
        
        .no-issues {{ color: #4ecdc4; padding: 0.5rem 0; }}
        
        .issue-bar {{ display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        .issue-name {{ width: 150px; color: #888; }}
        .issue-visual {{ flex: 1; height: 24px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }}
        .issue-fill {{ height: 100%; background: linear-gradient(90deg, #ff6b35, #f7d354); border-radius: 4px; }}
        .issue-count {{ width: 40px; text-align: right; font-weight: bold; }}
        
        footer {{ text-align: center; color: #666; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1); }}
        footer a {{ color: #4ecdc4; text-decoration: none; }}
        footer a:hover {{ text-decoration: underline; }}
        
        @media (max-width: 600px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .player-stats {{ flex-direction: column; gap: 0.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">FRAGAUDIT</div>
            <div class="subtitle">{meta.get('map', 'Unknown')} • {meta.get('demo_file', 'Unknown')}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary.get('total_players_analyzed', 0)}</div>
                <div class="stat-label">Players</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('total_mistakes_found', 0)}</div>
                <div class="stat-label">Issues</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{(summary.get('most_common_issue') or 'None').replace('_', ' ')}</div>
                <div class="stat-label">Most Common</div>
            </div>
        </div>
        
        <h2>Issue Distribution</h2>
        {issues_html if issues_html else '<div style="color: #4ecdc4; padding: 1rem;">No issues found</div>'}
        
        <h2>Player Reports</h2>
        {players_html}
        
        <footer>
            Generated by <a href="https://github.com/Pl4yer-ONE/FragAudit">FragAudit</a> — MIT Licensed
        </footer>
    </div>
</body>
</html>'''
        
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
