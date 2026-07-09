"""
elo_model.py - Goal-based Attack & Defense rating model.
Tracks team attacking and defending strengths separately using historical goal counts.
Includes time-decay weighting (recent matches matter more) and separate K-factors
for regular matches vs. WC knockout stage matches.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.data import ELO_SEED, ROUND_OF_32_RESULTS, ROUND_OF_16_RESULTS

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


def compute_expected_goals(att_rating: float, def_rating: float, home_advantage: float = 0.0) -> float:
    """Expected goals based on attack strength vs opponent defense strength."""
    # Base expected rate is 1.35 goals
    base_rate = 1.35
    diff = (att_rating - def_rating + home_advantage) / 400.0
    return np.clip(base_rate * (10 ** diff), 0.2, 4.5)


def update_attack_defense(att_h: float, def_h: float, att_a: float, def_a: float,
                           goals_h: float, goals_a: float, k: float, home_adv: float = 0.0) -> tuple:
    """
    Update Attacking and Defending Elo ratings after a match.
    Returns (new_att_h, new_def_h, new_att_a, new_def_a)
    """
    expected_h = compute_expected_goals(att_h, def_a, home_adv)
    expected_a = compute_expected_goals(att_a, def_h, 0.0)

    # Attack update: did they score more/less than expected?
    new_att_h = att_h + k * (goals_h - expected_h)
    new_att_a = att_a + k * (goals_a - expected_a)

    # Defense update: did they concede more/less than expected?
    # Note: if opponent scored more than expected, defense rating decreases
    new_def_h = def_h - k * (goals_a - expected_a)
    new_def_a = def_a - k * (goals_h - expected_h)

    return new_att_h, new_def_h, new_att_a, new_def_a


def build_elo_from_history(matches_df: pd.DataFrame,
                           base_k: float = 12.0,
                           wc_k: float = 24.0) -> dict:
    """
    Build Attack and Defense Elo ratings by replaying historical matches.
    Applies time-decay: matches in the last 2 years receive up to 2x the K-factor.
    WC matches receive a higher K-factor to reflect their predictive value.
    """
    # Each team has an att and def rating initialized to seed
    ratings = {}
    for team, seed in ELO_SEED.items():
        ratings[team] = {"att": seed, "def": seed}

    # Reference date for time-decay (WC 2026 start)
    reference_date = datetime(2026, 6, 11)

    # Replay historical matches chronologically
    for _, row in matches_df.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        home_goals = row["home_score"]
        away_goals = row["away_score"]

        home = COUNTRY_TO_CODE.get(home, home)
        away = COUNTRY_TO_CODE.get(away, away)

        # Initialize unknown teams
        if home not in ratings:
            ratings[home] = {"att": 1500.0, "def": 1500.0}
        if away not in ratings:
            ratings[away] = {"att": 1500.0, "def": 1500.0}

        # K-factor: WC matches carry more weight
        is_wc = "World Cup" in str(row.get("tournament", ""))
        k_base = wc_k if is_wc else base_k

        # Time-decay: exponential decay, half-life ~4 years
        # Matches within last 2 years: multiplier up to 2.0
        # Matches older than 8 years: multiplier ~0.5
        match_date = row.get("date", None)
        decay_multiplier = 1.0
        if match_date is not None:
            try:
                if isinstance(match_date, str):
                    match_date = datetime.strptime(str(match_date)[:10], "%Y-%m-%d")
                elif hasattr(match_date, 'to_pydatetime'):
                    match_date = match_date.to_pydatetime()
                years_ago = (reference_date - match_date).days / 365.25
                # Decay: multiply K by exp(-0.1 * years_ago), capped [0.5, 2.0]
                decay_multiplier = np.clip(np.exp(-0.1 * max(years_ago - 1.0, 0.0)), 0.5, 2.0)
            except Exception:
                decay_multiplier = 1.0

        k = k_base * decay_multiplier

        # Home ground advantage (approx 80 rating points boost if not neutral)
        is_neutral = row.get("neutral", True)
        home_adv_rating = 80.0 if not is_neutral else 0.0

        att_h, def_h = ratings[home]["att"], ratings[home]["def"]
        att_a, def_a = ratings[away]["att"], ratings[away]["def"]

        # Run update
        new_att_h, new_def_h, new_att_a, new_def_a = update_attack_defense(
            att_h, def_h, att_a, def_a, home_goals, away_goals, k, home_adv_rating
        )

        ratings[home]["att"] = new_att_h
        ratings[home]["def"] = new_def_h
        ratings[away]["att"] = new_att_a
        ratings[away]["def"] = new_def_a

    return ratings


def apply_wc2026_updates(ratings: dict) -> dict:
    """
    Apply WC 2026 Round-of-32 and Round-of-16 results to update Elo ratings.
    Uses higher K=32 for R16 knockout matches (higher stake = stronger signal).
    """
    ratings = {k: v.copy() for k, v in ratings.items()}
    r32_k = 24.0  # Group/R32 K-factor
    r16_k = 32.0  # R16 knockout: elevated K-factor — confirmed results carry more weight

    # 1. Round of 32 updates
    for home, away, hg, ag, winner in ROUND_OF_32_RESULTS:
        if hg is None:
            continue

        if home not in ratings:
            ratings[home] = {"att": 1500.0, "def": 1500.0}
        if away not in ratings:
            ratings[away] = {"att": 1500.0, "def": 1500.0}

        att_h, def_h = ratings[home]["att"], ratings[home]["def"]
        att_a, def_a = ratings[away]["att"], ratings[away]["def"]

        # Knockouts are neutral venue
        new_att_h, new_def_h, new_att_a, new_def_a = update_attack_defense(
            att_h, def_h, att_a, def_a, hg, ag, r32_k, 0.0
        )

        ratings[home]["att"] = new_att_h
        ratings[home]["def"] = new_def_h
        ratings[away]["att"] = new_att_a
        ratings[away]["def"] = new_def_a

    # 2. Round of 16 updates — elevated K-factor
    for home, away, hg, ag, winner in ROUND_OF_16_RESULTS:
        if hg is None:
            continue

        if home not in ratings:
            ratings[home] = {"att": 1500.0, "def": 1500.0}
        if away not in ratings:
            ratings[away] = {"att": 1500.0, "def": 1500.0}

        att_h, def_h = ratings[home]["att"], ratings[home]["def"]
        att_a, def_a = ratings[away]["att"], ratings[away]["def"]

        new_att_h, new_def_h, new_att_a, new_def_a = update_attack_defense(
            att_h, def_h, att_a, def_a, hg, ag, r16_k, 0.0
        )

        ratings[home]["att"] = new_att_h
        ratings[home]["def"] = new_def_h
        ratings[away]["att"] = new_att_a
        ratings[away]["def"] = new_def_a

    return ratings


def get_current_ratings(historical_df: pd.DataFrame = None) -> dict:
    """
    Get current Att/Def ratings. If historical data is provided, compute.
    """
    if historical_df is not None and not historical_df.empty:
        print(f"Building Att/Def Elo from {len(historical_df)} historical matches...")
        ratings = build_elo_from_history(historical_df)
    else:
        print("Using seed Att/Def Elo ratings (no history)...")
        ratings = {}
        for team, seed in ELO_SEED.items():
            ratings[team] = {"att": seed, "def": seed}

    ratings = apply_wc2026_updates(ratings)
    print(f"Att/Def Elo ratings computed for {len(ratings)} teams.")
    return ratings


def print_ratings(ratings: dict, top_n: int = 20):
    """Print top N teams by combined Attack + Defense Elo rating."""
    # We rank by the average of (Attack - Defending_cost), where higher defense is better
    # In our model, a higher def rating means better defense (concedes fewer goals).
    # So combined strength = Att - (1500 - Def) or simply (Att + Def) / 2
    combined = {}
    for team, info in ratings.items():
        combined[team] = (info["att"] + info["def"]) / 2.0

    sorted_teams = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{'Rank':<5} {'Team':<10} {'Attack':<10} {'Defense':<10} {'Combined':<12}")
    print("-" * 52)
    for i, (team, score) in enumerate(sorted_teams[:top_n], 1):
        att = ratings[team]["att"]
        deff = ratings[team]["def"]
        print(f"{i:<5} {team:<10} {att:<10.0f} {deff:<10.0f} {score:<12.0f}")


def expected_score(rating_a, rating_b) -> float:
    """Proxy expected score for tournament bracket compatibility (expected win %)."""
    if isinstance(rating_a, dict):
        rating_a = (rating_a.get("att", 1500.0) + rating_a.get("def", 1500.0)) / 2.0
    if isinstance(rating_b, dict):
        rating_b = (rating_b.get("att", 1500.0) + rating_b.get("def", 1500.0)) / 2.0
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
