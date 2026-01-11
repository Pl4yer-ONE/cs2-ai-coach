
from src.parser.demo_parser import DemoParser
import pandas as pd

def debug():
    path = "/Users/batman/Downloads/match/gamerlegion-vs-venom-m2-dust2.dem"
    print(f"Parsing {path}...")
    parser = DemoParser(path)
    data = parser.parse()
    
    print("\n--- Ticks DF ---")
    if data.player_positions is not None and not data.player_positions.empty:
        df = data.player_positions
        print("Columns:", df.columns.tolist())
        print("Head:")
        print(df.head())
        
        if 'vel_X' in df.columns:
            print("\nVelocity Stats:")
            print(df['vel_X'].describe())
            print("Non-zero velocities:", (df['vel_X'] != 0).sum())
        else:
            print("\n❌ vel_X column MISSING!")
            
        if 'steamid' in df.columns:
            print("\nUnique SteamIDs:", df['steamid'].unique()[:5])
        else:
             print("\n❌ steamid column MISSING!")
    else:
        print("❌ tick data empty")

if __name__ == "__main__":
    debug()
