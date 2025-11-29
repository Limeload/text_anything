"""
Utility functions for leaderboard ranking.
"""
import re
from typing import Any, List, Tuple
import pandas as pd
import numpy as np


def clean_value(value: Any) -> float:
    """
    Clean and normalize a value from the leaderboard.
    
    Converts 'D$Q', '–', NaN, None, empty strings to 0.0.
    
    Args:
        value: Value to clean (can be string, float, int, NaN, etc.)
        
    Returns:
        Cleaned float value
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    
    # Handle known invalid patterns
    if value_str.upper() in ['D$Q', '–', '-', '', 'NAN', 'NONE', 'NULL', 'N/A']:
        return 0.0
    
    # Try to extract numeric value (handles cases like "$100" or "100.5")
    # Remove currency symbols and other non-numeric characters except decimal point and minus
    cleaned = re.sub(r'[^\d\.\-]', '', value_str)
    
    if not cleaned or cleaned == '-' or cleaned == '.':
        return 0.0
    
    try:
        result = float(cleaned)
        return result if not np.isnan(result) else 0.0
    except (ValueError, TypeError):
        return 0.0


def extract_player_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only player rows from the dataframe.
    
    Assumes player rows are those that have a name/identifier column
    and contain numeric data in score columns.
    
    Args:
        df: Raw dataframe from Excel
        
    Returns:
        DataFrame with only player rows
    """
    # Try to identify the name column (usually first column or contains 'name', 'player', etc.)
    name_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['name', 'player', 'id', 'team']):
            name_col = col
            break
    
    if name_col is None:
        # Assume first column is the identifier
        name_col = df.columns[0]
    
    # Filter out rows where name is empty or NaN
    player_df = df[df[name_col].notna() & (df[name_col].astype(str).str.strip() != '')].copy()
    
    # Filter out header rows (rows that might be duplicates of column names)
    if len(player_df) > 0:
        # Remove rows where the name matches any column name
        column_names = [str(c).lower() for c in df.columns]
        player_df = player_df[
            ~player_df[name_col].astype(str).str.lower().isin(column_names)
        ]
    
    return player_df


def get_score_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that contain scores/points.
    
    Args:
        df: DataFrame
        
    Returns:
        List of column names that appear to be score columns
    """
    score_cols = []
    
    for col in df.columns:
        col_str = str(col).lower()
        # Skip name/identifier columns
        if any(keyword in col_str for keyword in ['name', 'player', 'id', 'team', 'total', 'spend']):
            continue
        
        # Check if column contains numeric data
        numeric_count = 0
        for val in df[col]:
            try:
                cleaned = clean_value(val)
                if cleaned != 0.0 or pd.notna(val):
                    numeric_count += 1
            except:
                pass
        
        # If at least some values are numeric, consider it a score column
        if numeric_count > 0:
            score_cols.append(col)
    
    return score_cols


def calculate_countback(scores: List[float]) -> Tuple[float, int, ...]:
    """
    Calculate countback tuple for tie-breaking.
    
    Countback is: (highest_score, frequency_of_highest, next_highest, frequency_of_next, ...)
    
    Args:
        scores: List of all event scores for a player
        
    Returns:
        Tuple for countback comparison (higher is better)
    """
    if not scores:
        return (0.0, 0)
    
    # Remove zeros (they don't contribute to countback)
    non_zero_scores = [s for s in scores if s > 0]
    
    if not non_zero_scores:
        return (0.0, 0)
    
    # Sort in descending order
    sorted_scores = sorted(non_zero_scores, reverse=True)
    
    # Build countback tuple: (score, frequency, next_score, frequency, ...)
    countback = []
    current_score = None
    current_count = 0
    
    for score in sorted_scores:
        if score == current_score:
            current_count += 1
        else:
            if current_score is not None:
                countback.extend([current_score, current_count])
            current_score = score
            current_count = 1
    
    # Add the last score
    if current_score is not None:
        countback.extend([current_score, current_count])
    
    # Pad with zeros to ensure consistent tuple length for comparison
    # Use a reasonable max length (e.g., 20 elements)
    max_length = 20
    while len(countback) < max_length:
        countback.append(0.0)
    
    return tuple(countback[:max_length])


def calculate_median_score(scores: List[float]) -> float:
    """
    Calculate median score as an additional tiebreaker.
    
    Args:
        scores: List of all event scores
        
    Returns:
        Median score (0.0 if no scores)
    """
    if not scores:
        return 0.0
    
    non_zero_scores = [s for s in scores if s > 0]
    if not non_zero_scores:
        return 0.0
    
    return float(np.median(non_zero_scores))

