#!/usr/bin/env python3

# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.
"""
CS2 AI Coach - Main Entry Point

A metrics-driven post-match coaching system for Counter-Strike 2.
Parses demo files, extracts features, classifies mistakes, and generates
explainable coaching feedback.

Usage:
    python main.py analyze --demo path/to/demo.dem [--ollama] [--output report.json]
    python main.py play path/to/demo.dem
"""

import argparse
import sys
from pathlib import Path

from config import OLLAMA_ENABLED
from src.parser import DemoParser, check_parser_availability
from src.features import FeatureExtractor
from src.classifier import MistakeClassifier
from src.nlp import OllamaPhrasing
from src.report import ReportGenerator
from src.visualization import HeatmapGenerator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CS2 AI Coach - Post-match coaching system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    analyze    Analyze demo and generate coaching report
    play       Play demo file in visual player (requires pygame)
    
Examples:
    python main.py analyze --demo match.dem
    python main.py analyze --demo match.dem --ollama --heatmap
    python main.py play match/acend-vs-washington-m1-dust2.dem
    
For more information, see README.md
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # =========================================================================
    # PLAY command
    # =========================================================================
    play_parser = subparsers.add_parser("play", help="Play demo file in visual player")
    play_parser.add_argument("demo", type=str, help="Path to CS2 demo file (.dem)")
    
    # =========================================================================
    # ANALYZE command
    # =========================================================================
    analyze_parser = subparsers.add_parser("analyze", help="Analyze demo and generate report")
    
    analyze_parser.add_argument(
        "--demo",
        type=str,
        required=True,
        help="Path to CS2 demo file (.dem)"
    )
    
    analyze_parser.add_argument(
        "--ollama",
        action="store_true",
        help="Enable Ollama for natural language feedback"
    )
    
    analyze_parser.add_argument(
        "--output",
        type=str,
        help="Output filename for JSON report"
    )
    
    analyze_parser.add_argument(
        "--markdown",
        action="store_true",
        help="Also generate Markdown report"
    )
    
    analyze_parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report (shareable)"
    )
    
    analyze_parser.add_argument(
        "--csv",
        action="store_true",
        help="Generate CSV export (for spreadsheets)"
    )
    
    analyze_parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Generate kill heatmap overlay on map"
    )
    
    analyze_parser.add_argument(
        "--radar",
        action="store_true",
        help="Generate MP4 radar replay video"
    )
    
    analyze_parser.add_argument(
        "--radar-fps",
        type=int,
        default=20,
        help="Radar video FPS (default: 20)"
    )
    analyze_parser.add_argument(
        "--gif",
        action="store_true",
        help="Generate GIF preview of radar"
    )
    analyze_parser.add_argument(
        "--fast-radar",
        action="store_true",
        help="Use fast PIL renderer (10x faster, simpler visuals)"
    )
    analyze_parser.add_argument(
        "--timeline",
        action="store_true",
        help="Generate per-round event timeline (JSON)"
    )
    
    analyze_parser.add_argument(
        "--player",
        type=str,
        help="Analyze specific player only (by Steam ID or name)"
    )
    
    analyze_parser.add_argument(
        "--parser",
        type=str,
        choices=["auto", "demoparser2", "awpy"],
        default="auto",
        help="Parser to use (default: auto)"
    )
    
    analyze_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    analyze_parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark (time, memory, throughput)"
    )
    
    # =========================================================================
    # CHECK-PARSERS command
    # =========================================================================
    check_parser = subparsers.add_parser("check-parsers", help="Check available demo parsers")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Route to command handler
    if args.command == "play":
        return run_play(args)
    elif args.command == "analyze":
        return run_analyze(args)
    elif args.command == "check-parsers":
        return print_parser_status()
    else:
        parser.print_help()
        return 0


def run_play(args) -> int:
    """Run the demo player."""
    demo_path = Path(args.demo)
    
    if not demo_path.exists():
        print(f"Error: Demo file not found: {args.demo}")
        return 1
    
    try:
        from src.player.renderer import run_player
        run_player(str(demo_path))
        return 0
    except ImportError as e:
        print(f"Error: {e}")
        print("Install pygame: pip install pygame")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_analyze(args) -> int:
    """Run demo analysis."""
    import time
    import tracemalloc
    import json as json_module
    
    # Validate demo file
    demo_path = Path(args.demo)
    if not demo_path.exists():
        print(f"Error: Demo file not found: {args.demo}")
        return 1
    
    if not demo_path.suffix.lower() == ".dem":
        print(f"Warning: File does not have .dem extension: {args.demo}")
    
    verbose = getattr(args, 'verbose', False)
    benchmark = getattr(args, 'benchmark', False)
    
    # Start benchmark tracking
    if benchmark:
        tracemalloc.start()
        total_start = time.perf_counter()
        parse_start = total_start
    
    if verbose:
        print(f"Analyzing demo: {demo_path}")
    
    try:
        # Step 1: Parse demo
        print("Parsing demo file...")
        demo_parser = DemoParser(str(demo_path), parser=args.parser)
        parsed_demo = demo_parser.parse()
        
        if benchmark:
            parse_time = time.perf_counter() - parse_start
            analyze_start = time.perf_counter()
        
        if verbose:
            print(f"  Parser used: {demo_parser.parser_type}")
            print(f"  Kills found: {len(parsed_demo.kills)}")
            print(f"  Damages found: {len(parsed_demo.damages)}")
        
        # Step 2: Extract features
        print("Extracting features...")
        extractor = FeatureExtractor(parsed_demo)
        player_features = extractor.extract_all()
        
        if verbose:
            print(f"  Players analyzed: {len(player_features)}")
        
        # Filter to specific player if requested
        if args.player:
            matching = {
                pid: features for pid, features in player_features.items()
                if args.player.lower() in pid.lower() or 
                   args.player.lower() in features.player_name.lower()
            }
            if matching:
                player_features = matching
            else:
                print(f"Warning: Player '{args.player}' not found. Analyzing all players.")
        
        # Step 3: Classify mistakes
        print("Classifying mistakes...")
        classifier = MistakeClassifier()
        classified_mistakes = {}
        
        for player_id, features in player_features.items():
            mistakes = classifier.classify(features)
            classified_mistakes[player_id] = mistakes
            
            if verbose:
                print(f"  {player_id}: {len(mistakes)} issues found")
        
        # Step 4: Optional NLP phrasing
        nlp_feedback = None
        if args.ollama or OLLAMA_ENABLED:
            print("Generating NLP feedback...")
            phrasing = OllamaPhrasing(enabled=True)
            
            if phrasing.is_available():
                nlp_feedback = {}
                for player_id, mistakes in classified_mistakes.items():
                    nlp_feedback[player_id] = phrasing.phrase_all_mistakes(mistakes)
                print("  Ollama feedback generated")
            else:
                print("  Warning: Ollama not available, using fallback messages")
                nlp_feedback = {}
                for player_id, mistakes in classified_mistakes.items():
                    nlp_feedback[player_id] = [
                        {
                            "category": m.category,
                            "subcategory": m.subcategory,
                            "feedback": classifier.get_fallback_message(m),
                            "severity": m.severity,
                            "confidence": m.confidence
                        }
                        for m in mistakes
                    ]
        
        # Step 5: Generate report
        print("Generating report...")
        generator = ReportGenerator()
        
        report = generator.generate(
            demo_path=str(demo_path),
            player_features=player_features,
            classified_mistakes=classified_mistakes,
            nlp_feedback=nlp_feedback,
            map_name=parsed_demo.map_name or "Unknown"
        )
        
        # Save reports
        json_path = generator.save_json(report, args.output)
        print(f"JSON report saved: {json_path}")
        
        if args.markdown:
            if args.output:
                base = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
                md_filename = f"{base}.md"
            else:
                md_filename = None
            md_path = generator.save_markdown(report, md_filename)
            print(f"Markdown report saved: {md_path}")
        
        if getattr(args, 'html', False):
            from src.report.html_reporter import HTMLReporter
            html_gen = HTMLReporter()
            if args.output:
                base = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
                html_filename = f"{base}.html"
            else:
                html_filename = None
            html_path = html_gen.save(report, html_filename)
            print(f"HTML report saved: {html_path}")
        
        if getattr(args, 'csv', False):
            import csv
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.output:
                base = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
                csv_filename = f"{base}.csv"
            else:
                csv_filename = f"reports/mistakes_{timestamp}.csv"
            
            with open(csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Player', 'Round', 'Time', 'Location', 'Type', 'Severity', 'Details', 'Fix'])
                for player_id, player_data in report['players'].items():
                    player_name = player_data.get('player_name') or player_id
                    for m in player_data.get('mistakes', []):
                        writer.writerow([
                            player_name,
                            m.get('round', ''),
                            m.get('time', ''),
                            m.get('location', ''),
                            m.get('type', ''),
                            m.get('severity', ''),
                            m.get('details', ''),
                            m.get('fix', '')
                        ])
            print(f"CSV report saved: {csv_filename}")
        
        # Heatmap generation
        if getattr(args, 'heatmap', False):
            from src.visualization.heatmap import HeatmapGenerator
            from datetime import datetime
            import base64
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            heatmap_dir = f"reports/heatmaps/{timestamp}"
            
            hm = HeatmapGenerator(parsed_demo, output_dir=heatmap_dir, overlay_enabled=True)
            heatmap_path = hm.generate_kills_heatmap()
            print(f"Heatmap saved: {heatmap_path}")
            
            # If HTML was also generated, create a combined version with heatmap
            if getattr(args, 'html', False) and heatmap_path:
                with open(heatmap_path, 'rb') as f:
                    heatmap_b64 = base64.b64encode(f.read()).decode()
                
                # Append heatmap to HTML report
                if html_path:
                    with open(html_path, 'r') as f:
                        html_content = f.read()
                    
                    heatmap_html = f'''
        <h2>Kill Heatmap</h2>
        <div style="text-align: center; margin: 2rem 0;">
            <img src="data:image/png;base64,{heatmap_b64}" alt="Kill Heatmap" style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"/>
            <p style="color: #888; margin-top: 1rem;">Kill locations density map for {parsed_demo.map_name}</p>
        </div>
'''
                    # Insert before closing </div></body>
                    html_content = html_content.replace('</div>\n</body>', heatmap_html + '</div>\n</body>')
                    
                    with open(html_path, 'w') as f:
                        f.write(html_content)
                    print(f"Heatmap embedded in HTML report")
        
        # Timeline generation (v3.3)
        if getattr(args, 'timeline', False):
            from src.timeline import TimelineBuilder, export_timeline_json, export_timeline_csv
            from datetime import datetime
            
            print("Generating event timeline...")
            builder = TimelineBuilder(parsed_demo)
            timelines = builder.build()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON export
            json_path = f"reports/timeline_{timestamp}.json"
            export_timeline_json(
                timelines,
                json_path,
                match_id=str(demo_path),
                map_name=parsed_demo.map_name
            )
            print(f"Timeline JSON: {json_path}")
            
            # CSV export
            csv_path = f"reports/timeline_{timestamp}.csv"
            export_timeline_csv(timelines, csv_path)
            print(f"Timeline CSV: {csv_path}")
        
        # Radar video generation
        if getattr(args, 'radar', False) or getattr(args, 'gif', False):
            from src.radar import extract_ticks, RadarRenderer, encode_video, encode_gif, check_ffmpeg
            from src.radar.fast_renderer import FastRadarRenderer
            from datetime import datetime
            import tempfile
            import base64
            
            if not check_ffmpeg():
                print("⚠️ ffmpeg not installed. Skipping radar video.")
                print("  Install with: brew install ffmpeg")
            else:
                use_fast = getattr(args, 'fast_radar', False)
                print(f"Generating radar replay {'(FAST mode)' if use_fast else ''}...")
                
                # Extract ticks: 64 tick demo / 16 interval = 4 frames per second of game
                # For 20 FPS output, 5 seconds of game = 1 second of video (5x speed)
                # Very smooth, detailed replay
                fps = getattr(args, 'radar_fps', 20)
                tick_interval = 16  # 4 samples per second of game time
                max_frames = 5000   # Limit to ~250 sec video at 20fps (covering ~20 mins of game)
                
                # Default limit for GIF only (preview mode)
                if getattr(args, 'gif', False) and not getattr(args, 'radar', False):
                    max_frames = 400  # ~20 seconds
                    
                frames = extract_ticks(parsed_demo, tick_interval=tick_interval, max_ticks=max_frames)
                
                if frames:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Create temp frames directory
                    frames_dir = f"reports/radar_frames_{timestamp}"
                    
                    # Choose renderer: Fast (PIL) or Standard (matplotlib)
                    if use_fast:
                        renderer = FastRadarRenderer(
                            map_name=parsed_demo.map_name,
                            output_dir=frames_dir
                        )
                    else:
                        renderer = RadarRenderer(
                            map_name=parsed_demo.map_name,
                            output_dir=frames_dir,
                            show_names=False
                        )
                    renderer.render_all(frames)
                    
                    # Encode to MP4
                    if getattr(args, 'radar', False):
                        video_path = f"reports/radar_{timestamp}.mp4"
                        encode_video(frames_dir, video_path, fps=getattr(args, 'radar_fps', 20))
                        print(f"Radar video saved: {video_path}")
                    
                    # Encode to GIF
                    if getattr(args, 'gif', False):
                        gif_path = f"reports/radar_{timestamp}.gif"
                        encode_gif(frames_dir, gif_path, fps=15, scale=480)
                        print(f"Radar GIF saved: {gif_path}")
                        # Use GIF for embedding if no MP4 (or override)
                        if not getattr(args, 'radar', False):
                            video_path = str(gif_path)
                    
                    # Cleanup frames
                    renderer.cleanup()
                    
                    print(f"Radar video saved: {video_path}")
                    
                    # Embed in HTML if also generating HTML
                    if getattr(args, 'html', False) and html_path:
                        with open(video_path, 'rb') as f:
                            video_b64 = base64.b64encode(f.read()).decode()
                        
                        with open(html_path, 'r') as f:
                            html_content = f.read()
                        
                        radar_html = f'''
        <h2>Radar Replay</h2>
        <div style="text-align: center; margin: 2rem 0;">
            <video id="radarVideo" controls style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            </video>
            <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 1rem; align-items: center;">
                <button onclick="document.getElementById('radarVideo').playbackRate = 0.5" style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #4ecdc4; background: transparent; color: #4ecdc4; cursor: pointer;">0.5x</button>
                <button onclick="document.getElementById('radarVideo').playbackRate = 1" style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #4ecdc4; background: #4ecdc4; color: #1a1a2e; cursor: pointer;">1x</button>
                <button onclick="document.getElementById('radarVideo').playbackRate = 2" style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #4ecdc4; background: transparent; color: #4ecdc4; cursor: pointer;">2x</button>
                <button onclick="document.getElementById('radarVideo').playbackRate = 4" style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #4ecdc4; background: transparent; color: #4ecdc4; cursor: pointer;">4x</button>
            </div>
            <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 1.5rem; font-size: 0.85rem; color: #888; flex-wrap: wrap;">
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #5C7AEA; border-radius: 50%; margin-right: 4px;"></span> CT</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #E94560; border-radius: 50%; margin-right: 4px;"></span> T</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #FFD93D; margin-right: 4px;"></span> Bomb</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #AAAAAA; border-radius: 50%; margin-right: 4px; opacity: 0.5;"></span> Smoke</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #FFFFFF; border-radius: 50%; margin-right: 4px; opacity: 0.6;"></span> Flash</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #FF8C00; border-radius: 50%; margin-right: 4px;"></span> HE</span>
                <span><span style="display: inline-block; width: 12px; height: 12px; background: #FF4500; border-radius: 50%; margin-right: 4px;"></span> Molly</span>
                <span style="color: #E94560;">✕ Kill</span>
                <span style="opacity: 0.5;">── Trail</span>
            </div>
            <p style="color: #888; margin-top: 0.5rem;">Player movement replay for {parsed_demo.map_name}</p>
        </div>
'''
                        html_content = html_content.replace('</div>\n</body>', radar_html + '</div>\n</body>')
                        
                        with open(html_path, 'w') as f:
                            f.write(html_content)
                        print("Radar video embedded in HTML report")
                else:
                    print("⚠️ No tick data available for radar")
        
        # Print summary
        generator.print_summary(report)
        
        # Benchmark results
        if benchmark:
            total_time = time.perf_counter() - total_start
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Count events
            events_count = len(parsed_demo.kills) + len(parsed_demo.damages)
            if hasattr(parsed_demo, 'rounds') and parsed_demo.rounds is not None:
                rounds_count = len(parsed_demo.rounds)
            else:
                rounds_count = 0
            
            benchmark_results = {
                "demo": str(demo_path),
                "map": parsed_demo.map_name,
                "parse_time_sec": round(parse_time, 3),
                "analyze_time_sec": round(total_time - parse_time, 3),
                "total_runtime_sec": round(total_time, 3),
                "peak_memory_mb": round(peak / 1024 / 1024, 2),
                "events_processed": events_count,
                "events_per_sec": round(events_count / total_time, 1) if total_time > 0 else 0,
                "rounds_count": rounds_count,
                "rounds_per_sec": round(rounds_count / total_time, 1) if total_time > 0 else 0,
                "status": "PASS" if total_time < 5 and peak / 1024 / 1024 < 500 else "FAIL"
            }
            
            # Print benchmark results
            print("\n" + "="*60)
            print("  BENCHMARK RESULTS")
            print("="*60)
            print(f"  Demo: {demo_path.name}")
            print(f"  Parse Time:    {benchmark_results['parse_time_sec']:.3f}s")
            print(f"  Analysis Time: {benchmark_results['analyze_time_sec']:.3f}s")
            print(f"  Total Runtime: {benchmark_results['total_runtime_sec']:.3f}s")
            print(f"  Peak Memory:   {benchmark_results['peak_memory_mb']:.1f} MB")
            print(f"  Events:        {events_count} ({benchmark_results['events_per_sec']:.0f}/sec)")
            print(f"  Rounds:        {rounds_count} ({benchmark_results['rounds_per_sec']:.1f}/sec)")
            print(f"  Status:        {benchmark_results['status']}")
            print("="*60)
            
            # Save benchmark JSON
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            benchmark_path = f"reports/benchmark_{timestamp}.json"
            with open(benchmark_path, 'w') as f:
                json_module.dump(benchmark_results, f, indent=2)
            print(f"Benchmark saved: {benchmark_path}")
        
        return 0
        
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Install required packages: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"Error analyzing demo: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def print_parser_status() -> int:
    """Print status of available parsers."""
    availability = check_parser_availability()
    
    print("CS2 Demo Parser Status")
    print("-" * 30)
    
    for parser_name, available in availability.items():
        status = "✓ Available" if available else "✗ Not installed"
        print(f"  {parser_name}: {status}")
    
    if not any(availability.values()):
        print("\nNo parsers available. Install one:")
        print("  pip install demoparser2  # Recommended")
        print("  pip install awpy         # Alternative")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
