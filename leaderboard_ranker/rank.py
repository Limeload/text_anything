#!/usr/bin/env python3
"""
Leaderboard Points Ranking System

Sorts a leaderboard Excel sheet according to:
- Total points (descending)
- Spend (ascending)
- Countback (highest score, frequency, next highest, etc.)
- Alphabetical fallback
"""
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from utils import clean_value, extract_player_rows, get_score_columns, calculate_countback, calculate_median_score


def load_leaderboard(excel_path: str) -> pd.DataFrame:
    """
    Load leaderboard from Excel file.
    
    Args:
        excel_path: Path to leaderboard.xlsx
        
    Returns:
        DataFrame with leaderboard data
    """
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        sys.exit(1)


def process_leaderboard(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process leaderboard and calculate rankings.
    
    Args:
        df: Raw dataframe from Excel
        
    Returns:
        List of player dictionaries with calculated fields
    """
    # Extract player rows
    player_df = extract_player_rows(df)
    
    if len(player_df) == 0:
        print("No player rows found in leaderboard")
        return []
    
    # Identify columns
    name_col = None
    for col in player_df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['name', 'player', 'id', 'team']):
            name_col = col
            break
    
    if name_col is None:
        name_col = player_df.columns[0]
    
    # Get score columns (exclude name, total, spend columns)
    all_cols = [c for c in player_df.columns if c != name_col]
    score_cols = get_score_columns(player_df)
    
    # Identify total and spend columns if they exist
    total_col = None
    spend_col = None
    
    for col in player_df.columns:
        col_lower = str(col).lower()
        if 'total' in col_lower and 'point' in col_lower:
            total_col = col
        elif 'spend' in col_lower:
            spend_col = col
    
    # Process each player
    players = []
    
    for idx, row in player_df.iterrows():
        player_name = str(row[name_col]).strip()
        
        # Extract all event scores
        event_scores = []
        for col in score_cols:
            score = clean_value(row[col])
            event_scores.append(score)
        
        # Calculate total points (sum of all event scores)
        total_points = sum(event_scores)
        
        # Get spend (from column if exists, otherwise 0)
        if spend_col and spend_col in row:
            spend = clean_value(row[spend_col])
        else:
            spend = 0.0
        
        # Calculate countback
        countback_tuple = calculate_countback(event_scores)
        
        # Calculate median score (for additional tiebreaker)
        median_score = calculate_median_score(event_scores)
        
        player_data = {
            'name': player_name,
            'total_points': total_points,
            'spend': spend,
            'countback': countback_tuple,
            'median_score': median_score,
            'event_scores': event_scores,
            'num_events': len([s for s in event_scores if s > 0])
        }
        
        # Preserve original row data
        for col in player_df.columns:
            if col not in player_data:
                player_data[col] = row[col]
        
        players.append(player_data)
    
    return players


def sort_players(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort players according to ranking rules:
    1. Total points (descending)
    2. Spend (ascending)
    3. Countback (tuple comparison)
    4. Alphabetical by name
    
    Args:
        players: List of player dictionaries
        
    Returns:
        Sorted list of players
    """
    def sort_key(player: Dict[str, Any]) -> tuple:
        # For countback, we want descending order (higher is better)
        # Since tuple comparison is lexicographic, we negate each element
        countback_tuple = player['countback']
        negated_countback = tuple(-x if isinstance(x, (int, float)) else x for x in countback_tuple)
        
        return (
            -player['total_points'],  # Negative for descending
            player['spend'],          # Ascending
            negated_countback,        # Negated for descending (higher countback is better)
            player['name'].lower()    # Alphabetical
        )
    
    return sorted(players, key=sort_key)


def save_results(players: List[Dict[str, Any]], output_dir: Path):
    """
    Save sorted results to CSV, XLSX, and JSON.
    
    Args:
        players: Sorted list of player dictionaries
        output_dir: Directory to save output files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare dataframe for CSV/XLSX (exclude complex types)
    df_data = []
    for player in players:
        row = {
            'rank': players.index(player) + 1,
            'name': player['name'],
            'total_points': player['total_points'],
            'spend': player['spend'],
            'median_score': player['median_score'],
            'num_events': player['num_events'],
            'countback_summary': f"{player['countback'][0]} (x{player['countback'][1]})" if len(player['countback']) >= 2 else "0"
        }
        # Add original columns (excluding name, total_points, spend if they were in original)
        for key, value in player.items():
            if key not in ['name', 'total_points', 'spend', 'countback', 'median_score', 'event_scores', 'num_events']:
                # Convert complex types to strings
                if isinstance(value, (list, tuple, dict)):
                    row[key] = str(value)
                else:
                    row[key] = value
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Save CSV
    csv_path = output_dir / 'leaderboard_sorted.csv'
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")
    
    # Save XLSX
    xlsx_path = output_dir / 'leaderboard_sorted.xlsx'
    df.to_excel(xlsx_path, index=False, engine='openpyxl')
    print(f"Saved XLSX to {xlsx_path}")
    
    # Save JSON (include full data)
    json_path = output_dir / 'leaderboard_sorted.json'
    # Convert countback tuple to list for JSON serialization
    json_data = []
    for player in players:
        json_player = player.copy()
        json_player['countback'] = list(json_player['countback'])
        json_player['rank'] = players.index(player) + 1
        json_data.append(json_player)
    
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"Saved JSON to {json_path}")


def main():
    """Main execution function."""
    # Determine paths
    script_dir = Path(__file__).parent
    # Option 2: expect leaderboard.xlsx to live alongside rank.py
    project_root = script_dir.parent
    excel_path = script_dir / 'leaderboard.xlsx'
    # Still write outputs to project root so they land one level up
    output_dir = project_root
    
    if not excel_path.exists():
        print(f"Error: leaderboard.xlsx not found at {excel_path}")
        sys.exit(1)
    
    print(f"Loading leaderboard from {excel_path}")
    
    # Load and process
    df = load_leaderboard(str(excel_path))
    print(f"Loaded {len(df)} rows from Excel")
    
    players = process_leaderboard(df)
    print(f"Processed {len(players)} players")
    
    # Sort
    sorted_players = sort_players(players)
    print(f"Sorted {len(sorted_players)} players")
    
    # Display top 10
    print("\nTop 10 Players:")
    print("-" * 80)
    for i, player in enumerate(sorted_players[:10], 1):
        print(f"{i:2d}. {player['name']:30s} | Points: {player['total_points']:8.1f} | "
              f"Spend: {player['spend']:8.1f} | Countback: {player['countback'][0]:.1f} (x{player['countback'][1]})")
    
    # Save results
    save_results(sorted_players, output_dir)
    
    print("\nRanking complete!")


if __name__ == "__main__":
    main()

