"""
elo_model.py - Compute and update Elo ratings from historical match data.
Elo K-factor is higher for World Cup matches.
"""

import pandas as pd
import numpy as np
from src.data import ELO_SEED, ROUND_OF_32_RESULTS


def expected_score(rating_a: float, rating_b: float) -> float:
    """Expected score (win probability) for team A against team B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(rating_a: float, rating_b: float, result: float,
               k: float = 40) -> tuple:
    """
    Update Elo ratings after a match.
    result: 1.0 = A wins, 0.5 = draw, 0.0 = B wins
    Returns (new_rating_a, new_rating_b)
    """
    ea = expected_score(rating_a, rating_b)
    new_a = rating_a + k * (result - ea)
    new_b = rating_b + k * ((1 - result) - (1 - ea))
    return new_a, new_b


COUNTRY_TO_CODE = {
    "France": "FRA",
    "Spain": "ESP",
    "Brazil": "BRA",
    "Argentina": "ARG",
    "England": "ENG",
    "Portugal": "POR",
    "Germany": "GER",
    "Netherlands": "NED",
    "Belgium": "BEL",
    "Colombia": "COL",
    "United States": "USA",
    "USA": "USA",
    "Mexico": "MEX",
    "Canada": "CAN",
    "Morocco": "MAR",
    "Switzerland": "SUI",
    "Croatia": "CRO",
    "Senegal": "SEN",
    "Norway": "NOR",
    "Sweden": "SWE",
    "Austria": "AUT",
    "Japan": "JPN",
    "Ecuador": "ECU",
    "Paraguay": "PAR",
    "Ivory Coast": "CIV",
    "Egypt": "EGY",
    "Australia": "AUS",
    "Ghana": "GHA",
    "Algeria": "ALG",
    "Bosnia and Herzegovina": "BIH",
    "DR Congo": "CGO",
    "South Africa": "RSA",
    "Cabo Verde": "CPV",
    "Cape Verde": "CPV",
}


def build_elo_from_history(matches_df: pd.DataFrame,
                           base_k: float = 32,
                           wc_k: float = 60) -> dict:
    """
    Build Elo ratings by replaying historical matches.
    matches_df columns: date, home_team, away_team, home_score, away_score, tournament
    Returns dict of team -> Elo rating.
    """
    ratings = {}

    # Start from FIFA seed ratings
    ratings.update(ELO_SEED)

    # Replay historical matches chronologically
    for _, row in matches_df.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        home_goals = row["home_score"]
        away_goals = row["away_score"]

        # Map full names to three-letter codes for WC teams
        home = COUNTRY_TO_CODE.get(home, home)
        away = COUNTRY_TO_CODE.get(away, away)

        # Initialize unknown teams
        if home not in ratings:
            ratings[home] = 1500
        if away not in ratings:
            ratings[away] = 1500

        # Determine K-factor (higher for World Cup)
        is_wc = "World Cup" in str(row.get("tournament", ""))
        k = wc_k if is_wc else base_k

        # Result from home perspective
        if home_goals > away_goals:
            result = 1.0
        elif home_goals == away_goals:
            result = 0.5
        else:
            result = 0.0

        # Goal-difference multiplier (optional: heavier updates for big wins)
        goal_diff = abs(home_goals - away_goals)
        if goal_diff == 0 or goal_diff == 1:
            gd_mult = 1.0
        elif goal_diff == 2:
            gd_mult = 1.5
        else:
            gd_mult = 1.75

        ratings[home], ratings[away] = update_elo(
            ratings[home], ratings[away], result, k=k * gd_mult
        )

    return ratings


def apply_wc2026_updates(ratings: dict) -> dict:
    """
    Apply WC 2026 group stage + Round-of-32 results to update Elo ratings.
    Uses confirmed results from ROUND_OF_32_RESULTS.
    """
    ratings = ratings.copy()
    wc_k = 60

    for home, away, hg, ag, winner in ROUND_OF_32_RESULTS:
        if hg is None:
            continue  # Skip TBD matches

        if home not in ratings:
            ratings[home] = 1500
        if away not in ratings:
            ratings[away] = 1500

        if winner == home:
            result = 1.0
        elif winner == away:
            result = 0.0
        else:
            result = 0.5  # Draw (but there are no draws in knockout; treat as 0.5

        goal_diff = abs(hg - ag)
        gd_mult = 1.0 if goal_diff <= 1 else (1.5 if goal_diff == 2 else 1.75)

        ratings[home], ratings[away] = update_elo(
            ratings[home], ratings[away], result, k=wc_k * gd_mult
        )

    return ratings


def get_current_ratings(historical_df: pd.DataFrame = None) -> dict:
    """
    Get current Elo ratings. If historical data is provided, compute from scratch.
    Otherwise, use seed ratings + WC 2026 updates.
    """
    if historical_df is not None and not historical_df.empty:
        print(f"Building Elo from {len(historical_df)} historical matches...")
        ratings = build_elo_from_history(historical_df)
    else:
        print("Using seed Elo ratings (no historical data provided)...")
        ratings = dict(ELO_SEED)

    # Apply WC 2026 confirmed results
    ratings = apply_wc2026_updates(ratings)
    print(f"Elo ratings computed for {len(ratings)} teams.")
    return ratings


def print_ratings(ratings: dict, top_n: int = 20):
    """Print top N teams by Elo rating."""
    sorted_teams = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{'Rank':<5} {'Team':<10} {'Elo Rating':<12}")
    print("-" * 30)
    for i, (team, elo) in enumerate(sorted_teams[:top_n], 1):
        print(f"{i:<5} {team:<10} {elo:.0f}")
