#!/usr/bin/env python3
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
        help="Verbose output"
    )
    
    analyze_parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Generate kill/death/movement heatmaps"
    )
    
    analyze_parser.add_argument(
        "--heatmap-phase",
        type=str,
        choices=["early", "mid", "late"],
        default=None,
        help="Filter heatmaps by round phase"
    )
    
    analyze_parser.add_argument(
        "--overlay-map",
        action="store_true",
        help="Overlay heatmaps on radar map images"
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
    # Validate demo file
    demo_path = Path(args.demo)
    if not demo_path.exists():
        print(f"Error: Demo file not found: {args.demo}")
        return 1
    
    if not demo_path.suffix.lower() == ".dem":
        print(f"Warning: File does not have .dem extension: {args.demo}")
    
    verbose = getattr(args, 'verbose', False)
    
    if verbose:
        print(f"Analyzing demo: {demo_path}")
    
    try:
        # Step 1: Parse demo
        print("Parsing demo file...")
        demo_parser = DemoParser(str(demo_path), parser=args.parser)
        parsed_demo = demo_parser.parse()
        
        if verbose:
            print(f"  Parser used: {demo_parser.parser_type}")
            print(f"  Kills found: {len(parsed_demo.kills)}")
            print(f"  Damages found: {len(parsed_demo.damages)}")
        
        # Step 1b: Generate heatmaps if requested
        if args.heatmap:
            overlay = getattr(args, 'overlay_map', False)
            heatmap_gen = HeatmapGenerator(
                parsed_demo,
                phase=getattr(args, 'heatmap_phase', None),
                overlay_enabled=overlay
            )
            heatmap_paths = heatmap_gen.generate_all()
        
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
        
        # Print summary
        generator.print_summary(report)
        
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
