"""
Analysis Runner Service
Runs demo analysis in background thread with progress callbacks
"""

import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime


def run_analysis_thread(
    app,
    demo_path: Path,
    fast_radar: bool = True,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_complete: Optional[Callable[[Dict[str, Any], Optional[Path]], None]] = None,
    on_error: Optional[Callable[[str], None]] = None
):
    """
    Run analysis in a background thread.
    
    Args:
        app: The main application (for thread-safe UI updates)
        demo_path: Path to demo file
        fast_radar: Use fast PIL renderer
        on_progress: Callback(progress: 0-1, message: str)
        on_complete: Callback(result: dict, radar_dir: Path)
        on_error: Callback(error: str)
    """
    def _run():
        try:
            _run_analysis(
                app, demo_path, fast_radar,
                on_progress, on_complete, on_error
            )
        except Exception as e:
            if on_error:
                app.after(0, lambda: on_error(str(e)))
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def _run_analysis(
    app,
    demo_path: Path,
    fast_radar: bool,
    on_progress: Optional[Callable],
    on_complete: Optional[Callable],
    on_error: Optional[Callable]
):
    """Internal analysis runner."""
    
    def progress(value: float, msg: str):
        if on_progress:
            app.after(0, lambda: on_progress(value, msg))
    
    try:
        # Step 1: Parse demo (0-30%)
        progress(0.05, "Loading demo parser...")
        
        from src.parser import DemoParser
        
        progress(0.10, "Parsing demo file...")
        demo_parser = DemoParser(str(demo_path), parser="auto")
        parsed_demo = demo_parser.parse()
        
        progress(0.30, f"Parsed {len(parsed_demo.kills)} kills...")
        
        # Step 2: Extract features (30-50%)
        progress(0.35, "Extracting player features...")
        
        from src.features import FeatureExtractor
        
        extractor = FeatureExtractor(parsed_demo)
        player_features = extractor.extract_all()
        
        progress(0.50, f"Analyzed {len(player_features)} players...")
        
        # Step 3: Classify mistakes (50-65%)
        progress(0.55, "Classifying mistakes...")
        
        from src.classifier import MistakeClassifier
        
        classifier = MistakeClassifier()
        classified_mistakes = {}
        
        for player_id, features in player_features.items():
            mistakes = classifier.classify(features)
            classified_mistakes[player_id] = mistakes
        
        progress(0.65, "Generating report...")
        
        # Step 4: Generate report (65-75%)
        from src.report import ReportGenerator
        
        generator = ReportGenerator()
        report = generator.generate(
            demo_path=str(demo_path),
            player_features=player_features,
            classified_mistakes=classified_mistakes,
            nlp_feedback=None,
            map_name=parsed_demo.map_name or "Unknown"
        )
        
        progress(0.75, "Report generated...")
        
        # Step 5: Generate radar frames (75-95%)
        radar_dir = None
        
        progress(0.80, "Generating radar frames...")
        
        try:
            from src.radar import extract_ticks, check_ffmpeg
            from src.radar.fast_renderer import FastRadarRenderer
            from src.radar import RadarRenderer
            
            # Extract ticks
            tick_interval = 16
            max_frames = 1000  # Limit for UI preview
            
            frames = extract_ticks(parsed_demo, tick_interval=tick_interval, max_ticks=max_frames)
            
            if frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                radar_dir = Path(f"reports/radar_frames_{timestamp}")
                
                if fast_radar:
                    renderer = FastRadarRenderer(
                        map_name=parsed_demo.map_name,
                        output_dir=str(radar_dir)
                    )
                else:
                    renderer = RadarRenderer(
                        map_name=parsed_demo.map_name,
                        output_dir=str(radar_dir),
                        show_names=False
                    )
                
                # Render frames with progress updates
                total_frames = len(frames)
                for i, frame in enumerate(frames):
                    renderer.render_frame(frame, f"frame_{i:05d}.png")
                    if i % 50 == 0:
                        frame_progress = 0.80 + (i / total_frames) * 0.15
                        progress(frame_progress, f"Rendering frame {i}/{total_frames}...")
                
                progress(0.95, f"Rendered {total_frames} radar frames...")
                
        except Exception as e:
            # Radar is optional, continue without it
            progress(0.95, f"Radar skipped: {str(e)[:50]}")
        
        # Complete!
        progress(1.0, "Analysis complete!")
        
        if on_complete:
            app.after(0, lambda: on_complete(report, radar_dir))
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        if on_error:
            app.after(0, lambda: on_error(str(e)))
