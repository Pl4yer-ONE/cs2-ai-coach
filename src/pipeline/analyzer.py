"""
Match Analyzer Pipeline
Encapsulates the full analysis logic for a single match.
"""

from pathlib import Path
import traceback
import time
from typing import Optional, Dict, Any

from src.parser.demo_parser import DemoParser
from src.features.extractor import FeatureExtractor
from src.classifier.mistake_classifier import MistakeClassifier
from src.visualization.heatmap import HeatmapGenerator
from src.report.json_reporter import JsonReporter

class MatchAnalyzer:
    """
    Orchestrates the analysis of a CS2 match demo.
    """
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_match(self, demo_path: Path, analyze_movement: bool = True) -> Dict[str, Any]:
        """
        Run full analysis on a single demo file.
        """
        start_time = time.time()
        result = {
            "demo_file": demo_path.name,
            "status": "failed",
            "report_path": "",
            "heatmaps": [],
            "error": ""
        }
        
        print(f"\n🚀 Starting analysis for {demo_path.name}...")
        
        try:
            # 1. Parse
            print("  Parsing demo file...")
            parser = DemoParser(str(demo_path))
            parsed_demo = parser.parse()
            print(f"  ✅ Parsed {len(parsed_demo.rounds)} rounds on {parsed_demo.map_name}")
            
            # 2. Features
            print("  Extracting features & Analyzing roles...")
            extractor = FeatureExtractor(parsed_demo)
            features = extractor.extract_all()
            print(f"  ✅ Extracted features for {len(features)} players")
            
            # 3. Mistakes
            print("  Running Smart Mistake Engine...")
            classifier = MistakeClassifier()
            all_mistakes = {}
            total_mistakes = 0
            for pid, player_features in features.items():
                mistakes = classifier.classify(player_features)
                all_mistakes[pid] = mistakes
                total_mistakes += len(mistakes)
            print(f"  ✅ Identified {total_mistakes} tactical mistakes")
            
            # 4. Visualization
            print("  Generating heatmaps...")
            # Create subfolder for this match
            match_id = demo_path.stem
            match_output_dir = self.output_dir / match_id
            heatmap_dir = match_output_dir / "heatmaps"
            heatmap_dir.mkdir(parents=True, exist_ok=True)
            
            heatmap_gen = HeatmapGenerator(parsed_demo, str(heatmap_dir), overlay_enabled=True)
            
            heatmaps = {
                "global": {},
                "personal": {}
            }
            # Global heatmaps
            heatmaps["global"]["kills"] = heatmap_gen.generate_kills_heatmap()
            
            # Per-player heatmaps
            for pid in features.keys():
                heatmaps["personal"][pid] = {}
                heatmaps["personal"][pid]["kills"] = heatmap_gen.generate_kills_heatmap(player_id=pid)
            
            print("  ✅ Heatmaps generated (Global + Personal)")
            
            # 5. Reporting
            print("  Generating final report...")
            report_dir = match_output_dir / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            reporter = JsonReporter(str(report_dir))
            report_path = reporter.generate_report(
                match_id=match_id,
                map_name=parsed_demo.map_name,
                players=features,
                mistakes=all_mistakes,
                heatmap_urls=heatmaps
            )
            
            result["status"] = "success"
            result["report_path"] = str(report_path)
            result["heatmaps"] = heatmaps
            result["duration"] = round(time.time() - start_time, 2)
            
            print(f"\n🎉 Analysis Complete! Report saved to:\n   {report_path}")
            
        except Exception as e:
            print(f"\n❌ Analysis Failed: {e}")
            traceback.print_exc()
            result["error"] = str(e)
            
        return result
