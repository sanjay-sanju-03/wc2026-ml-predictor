# -*- coding: utf-8 -*-
"""
predict.py - Main entry point for the WC 2026 ML Prediction Pipeline.

Pipeline:
  1. Load historical match data (if available) -> compute Elo ratings
  2. Apply WC 2026 group stage + R32 updates to Elo
  3. Simulate all 16 knockout matches via Poisson model (50K iterations)
  4. Pick most likely bracket path: winner, score, scorer set
  5. Output final CSV for submission

Usage:
    python predict.py                         # Run with seed Elo only
    python predict.py --data results.csv      # Run with historical CSV data
    python predict.py --update-fixtures       # Print instructions to update fixtures
"""

import argparse
import os
import sys
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.elo_model import get_current_ratings, print_ratings
from src.simulator import simulate_bracket
from src.generate_csv import generate_submission_csv, validate_csv


def load_historical_data(filepath: str) -> pd.DataFrame:
    """Load and validate historical match results CSV."""
    print(f"\n[*] Loading historical data from: {filepath}")
    df = pd.read_csv(filepath)

    # Expected columns from Kaggle dataset
    required_cols = {"home_team", "away_team", "home_score", "away_score"}
    if not required_cols.issubset(df.columns):
        print(f"   [!] Missing columns. Found: {list(df.columns)}")
        print(f"   Expected at least: {required_cols}")
        print(f"   Proceeding with seed Elo ratings only...")
        return pd.DataFrame()

    # Filter to only matches with complete score data
    df = df.dropna(subset=["home_score", "away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    # Sort by date if available
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

    print(f"   [OK] Loaded {len(df)} historical matches")
    return df


def main():
    parser = argparse.ArgumentParser(description="WC 2026 ML Prediction Pipeline")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to historical results CSV (optional)")
    parser.add_argument("--output", type=str, default="wc2026_predictions.csv",
                        help="Output CSV path")
    parser.add_argument("--sims", type=int, default=50000,
                        help="Number of Monte Carlo simulations per match")
    parser.add_argument("--update-fixtures", action="store_true",
                        help="Print instructions for updating R16 fixtures")
    args = parser.parse_args()

    print("=" * 60)
    print("  WC 2026 ML PREDICTION PIPELINE")
    print("  Built for uFifa '26 Challenge")
    print("=" * 60)

    if args.update_fixtures:
        print("""
[!] TO UPDATE R16 FIXTURES:
    Edit src/data.py -> ROUND_OF_16_FIXTURES
    Replace 'TBD' teams with actual 3-letter codes once R32 is complete.
    
    Current known R16 fixtures:
    - Canada (CAN) vs Morocco (MAR) [OK] CONFIRMED
    - Others: update based on R32 results before July 3!
        """)
        return

    # Step 1: Load historical data
    historical_df = pd.DataFrame()
    if args.data:
        if os.path.exists(args.data):
            historical_df = load_historical_data(args.data)
        else:
            print(f"[!] Data file not found: {args.data}. Using seed ratings.")

    # Step 2: Compute Elo ratings
    print("\n[*] Computing team strength (Elo ratings)...")
    ratings = get_current_ratings(historical_df if not historical_df.empty else None)
    print_ratings(ratings, top_n=20)

    # Step 3: Simulate bracket
    print(f"\n[*] Running {args.sims:,} Monte Carlo simulations per match...")
    results = simulate_bracket(ratings, n_sims=args.sims)

    # Step 4: Generate CSV
    print(f"\n[*] Generating submission CSV...")
    df = generate_submission_csv(
        predictions=results["predictions"],
        champion=results["champion"],
        output_path=args.output
    )

    # Step 5: Validate
    validate_csv(df)

    print(f"\n[CHAMPION] Predicted Champion: {results['champion']}")
    print(f"[OUTPUT]   CSV saved to: {args.output}")
    print("\n[DONE] Upload the CSV at https://wcreflected.mulearn.org/submit")
    print("   Remember: You can re-upload before July 3, 2026 11:59 PM IST")


if __name__ == "__main__":
    main()
