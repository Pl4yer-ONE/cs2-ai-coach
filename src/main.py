import argparse
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.pipeline.analyzer import MatchAnalyzer

def main():
    parser = argparse.ArgumentParser(description="CS2 AI Coach - Production Analytics Engine")
    parser.add_argument("input_path", type=str, help="Path to .dem file or directory containing .dem files")
    parser.add_argument("--output", type=str, default="outputs", help="Output directory")
    parser.add_argument("--analyze-movement", action="store_true", help="Enable computationally expensive movement analysis")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers for batch processing")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Input path '{input_path}' does not exist.")
        sys.exit(1)

    analyzer = MatchAnalyzer(output_dir=args.output)
    
    demos_to_process = []
    if input_path.is_file():
        if input_path.suffix == ".dem":
            demos_to_process.append(input_path)
        else:
            print("Error: Input file must be a .dem file")
            sys.exit(1)
    elif input_path.is_dir():
        print(f"Scanning directory: {input_path}")
        demos_to_process = list(input_path.glob("*.dem"))
        print(f"Found {len(demos_to_process)} demo files.")

    if not demos_to_process:
        print("No demo files found to process.")
        sys.exit(0)

    # Process
    print(f"Starting batch analysis of {len(demos_to_process)} demos with {args.workers} workers...")
    
    successful = 0
    failed = 0
    
    # Use ThreadPoolExecutor for batch processing (CPU bound mostly, but I/O heavy parser)
    # ProcessPool might be better but serialization is tricky with pandas objects.
    # Sequential for safety first, or ThreadPool.
    
    if args.workers > 1 and len(demos_to_process) > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(analyzer.analyze_match, demo, args.analyze_movement): demo for demo in demos_to_process}
            for future in futures:
                res = future.result()
                if res["status"] == "success":
                    successful += 1
                else:
                    failed += 1
    else:
        for demo in demos_to_process:
            res = analyzer.analyze_match(demo, args.analyze_movement)
            if res["status"] == "success":
                successful += 1
            else:
                failed += 1
                
    print(f"\n Batch Complete. Success: {successful}, Failed: {failed}")

if __name__ == "__main__":
    main()
