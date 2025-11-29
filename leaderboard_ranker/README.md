# Leaderboard Points Ranking System

A Python script that sorts a leaderboard Excel sheet according to multiple ranking criteria including total points, spend, countback algorithm, and alphabetical fallback.

## Overview

This script processes `leaderboard.xlsx` from the project root, cleans invalid data, calculates ranking metrics, and outputs sorted results in multiple formats (CSV, XLSX, JSON).

## Ranking Rules

Players are sorted by the following priority (in order):

1. **Total Points** (descending) - Sum of all event scores
2. **Spend** (ascending) - Lower spend is better
3. **Countback** (descending) - Complex tie-breaking algorithm
4. **Alphabetical** (ascending) - By player name as final tiebreaker

## Data Cleaning

The script normalizes invalid data values to `0.0`:

- `D$Q` → 0.0
- `–` (en dash) → 0.0
- `-` (hyphen) → 0.0
- `NaN` / `None` → 0.0
- Empty strings → 0.0
- `N/A`, `NULL`, `NONE` → 0.0

The cleaning function also handles:
- Currency symbols (e.g., "$100" → 100.0)
- Whitespace trimming
- Type conversion errors

## Countback Algorithm

The countback algorithm is used to break ties when players have the same total points and spend. It works as follows:

### How Countback Works

1. **Extract all event scores** for a player (excluding zeros)
2. **Sort scores in descending order**
3. **Build a tuple** representing the countback:
   - Format: `(highest_score, frequency, next_highest, frequency, ...)`
   - Example: If scores are `[10, 10, 8, 5, 5, 5, 3]`, countback is `(10, 2, 8, 1, 5, 3, 3, 1)`
4. **Compare tuples lexicographically** (higher is better)

### Example Tie Resolution

Consider three players with the same total points (30) and spend (100):

**Player A scores:** `[10, 10, 5, 3, 2]`
- Countback: `(10, 2, 5, 1, 3, 1, 2, 1)`

**Player B scores:** `[12, 8, 6, 4, 0]`
- Countback: `(12, 1, 8, 1, 6, 1, 4, 1)`

**Player C scores:** `[9, 9, 9, 3, 0]`
- Countback: `(9, 3, 3, 1)`

**Ranking:**
1. Player B (highest single score: 12)
2. Player A (two scores of 10)
3. Player C (three scores of 9)

The countback prioritizes:
- Highest individual score
- Frequency of that score
- Next highest score
- And so on...

## Additional Tiebreaker: Median Score

As suggested in the requirements, the script also calculates **median score** as an additional tiebreaker metric. This is included in the output but not used in the primary sorting (as it wasn't specified in the main rules). It could be easily added as an additional sorting criterion if needed.

The median score:
- Excludes zero scores
- Provides a measure of consistent performance
- Could be used as a 5th tiebreaker if needed

## Usage

### Basic Execution

```bash
cd leaderboard_ranker
python rank.py
```

### Requirements

Install dependencies:
```bash
pip install pandas openpyxl numpy
```

Or create a `requirements.txt`:
```
pandas>=2.0.0
openpyxl>=3.1.0
numpy>=1.24.0
```

## Output Files

The script generates three output files in the project root:

1. **leaderboard_sorted.csv** - CSV format with ranking columns
2. **leaderboard_sorted.xlsx** - Excel format (same as CSV)
3. **leaderboard_sorted.json** - JSON format with full data including countback tuples and event scores

### Output Columns

- `rank` - Final ranking position
- `name` - Player name
- `total_points` - Sum of all event scores
- `spend` - Total spend
- `median_score` - Median of non-zero scores
- `num_events` - Number of events with non-zero scores
- `countback_summary` - Human-readable countback summary
- All original columns from the input Excel file

## Example Output

```
Top 10 Players:
--------------------------------------------------------------------------------
 1. Player A                    | Points:    150.0 | Spend:     50.0 | Countback: 25.0 (x2)
 2. Player B                    | Points:    150.0 | Spend:     50.0 | Countback: 24.0 (x1)
 3. Player C                    | Points:    145.0 | Spend:     45.0 | Countback: 30.0 (x1)
 ...
```

## Implementation Details

### Player Row Detection

The script automatically identifies player rows by:
1. Finding the name/identifier column (searches for keywords: 'name', 'player', 'id', 'team')
2. Filtering out rows with empty names
3. Removing header rows (rows where name matches column names)

### Score Column Detection

Score columns are identified by:
1. Excluding name/identifier columns
2. Excluding 'total' and 'spend' columns
3. Checking if columns contain numeric data

### Handling Edge Cases

- **Empty leaderboard**: Returns empty results with warning
- **No score columns**: Uses all numeric columns except name/total/spend
- **All zeros**: Countback is `(0.0, 0)`
- **Invalid Excel format**: Exits with error message

## Code Structure

- **rank.py** - Main script with CLI interface
- **utils.py** - Utility functions for cleaning, countback calculation, etc.

## Testing

To test the script:

1. Ensure `leaderboard.xlsx` exists in project root
2. Run: `python rank.py`
3. Check output files in project root
4. Verify rankings match expected sort order

## Future Improvements

If more time was available:

1. **Command-line arguments** for input/output paths
2. **Configurable ranking rules** via config file
3. **Support for different Excel formats** (multiple sheets, different structures)
4. **Visualization** of rankings and score distributions
5. **Historical tracking** of ranking changes over time
6. **Web interface** for interactive ranking
7. **Unit tests** for countback algorithm and data cleaning
8. **Performance optimization** for very large leaderboards
9. **Export to additional formats** (PDF report, HTML table)
10. **Validation** of input data structure before processing

