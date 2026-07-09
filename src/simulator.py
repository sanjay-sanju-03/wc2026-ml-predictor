"""
simulator.py - Match outcome simulator using Negative Binomial goals + Att/Def Elo ratings.
Runs 50,000 Monte Carlo simulations per match with Dixon-Coles adjustment.
"""

import numpy as np
from src.elo_model import expected_score
from src.data import ROUND_OF_16_FIXTURES, TEAM_SCORERS


# ─── Goal Rate Constants ──────────────────────────────────────────────────────
BASE_GOALS_PER_GAME = 1.35  # Average goals per team per WC knockout game
DISPERSION_PARAMETER = 6.0  # r parameter for Negative Binomial (controls overdispersion)
DIXON_COLES_RHO = -0.05      # Correlation parameter for low-scoring adjustment


def compute_expected_goals(team_a_ratings: dict, team_b_ratings: dict,
                            base_rate: float = BASE_GOALS_PER_GAME) -> tuple:
    """
    Compute expected goals (lambdas) for both teams based on Att/Def ratings.
    Returns (lambda_a, lambda_b)
    """
    # Expected goals for A: base_rate * 10 ** ((att_a - def_b) / 400)
    # Expected goals for B: base_rate * 10 ** ((att_b - def_a) / 400)
    diff_a = (team_a_ratings.get("att", 1500.0) - team_b_ratings.get("def", 1500.0)) / 400.0
    diff_b = (team_b_ratings.get("att", 1500.0) - team_a_ratings.get("def", 1500.0)) / 400.0

    lambda_a = np.clip(base_rate * (10 ** diff_a), 0.2, 4.5)
    lambda_b = np.clip(base_rate * (10 ** diff_b), 0.2, 4.5)

    return lambda_a, lambda_b


def apply_dixon_coles(score_counts: dict, lambda_a: float, lambda_b: float, rho: float = DIXON_COLES_RHO) -> dict:
    """
    Apply Dixon-Coles correlation adjustment for low scoring outcomes
    to calibrate 0-0, 1-0, 0-1, 1-1 probabilities.
    """
    adjusted = {}
    for (ga, gb), count in score_counts.items():
        adj_factor = 1.0
        if ga == 0 and gb == 0:
            adj_factor = 1.0 - lambda_a * lambda_b * rho
        elif ga == 1 and gb == 0:
            adj_factor = 1.0 + lambda_b * rho
        elif ga == 0 and gb == 1:
            adj_factor = 1.0 + lambda_a * rho
        elif ga == 1 and gb == 1:
            adj_factor = 1.0 - rho
        
        adjusted[(ga, gb)] = count * max(adj_factor, 0.0)
    return adjusted


def simulate_match(team_a_ratings: dict, team_b_ratings: dict,
                   n_sims: int = 50000, rng: np.random.Generator = None) -> dict:
    """
    Simulate a single match n_sims times using Negative Binomial distribution.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    lambda_a, lambda_b = compute_expected_goals(team_a_ratings, team_b_ratings)

    # Negative Binomial parameters: r (successes), p (success probability)
    # Mean mu = r * (1 - p) / p  =>  p = r / (r + mu)
    r = DISPERSION_PARAMETER
    p_a = r / (r + lambda_a)
    p_b = r / (r + lambda_b)

    goals_a = rng.negative_binomial(r, p_a, n_sims)
    goals_b = rng.negative_binomial(r, p_b, n_sims)

    # Proxy expected score (advancement win probability)
    rating_a = (team_a_ratings.get("att", 1500.0) + team_a_ratings.get("def", 1500.0)) / 2.0
    rating_b = (team_b_ratings.get("att", 1500.0) + team_b_ratings.get("def", 1500.0)) / 2.0
    win_prob_a = expected_score(rating_a, rating_b)

    wins_a = 0
    wins_b = 0
    score_counts = {}

    for i in range(n_sims):
        ga, gb = goals_a[i], goals_b[i]
        if ga > gb:
            wins_a += 1
            score_key = (ga, gb)
        elif gb > ga:
            wins_b += 1
            score_key = (ga, gb)
        else:
            # Draw -> advancement winner resolved by Elo-based proxy
            if rng.random() < win_prob_a:
                wins_a += 1
                score_key = (ga, gb)
            else:
                wins_b += 1
                score_key = (ga, gb)

        score_counts[score_key] = score_counts.get(score_key, 0) + 1

    # Apply Dixon-Coles calibration adjustment
    score_counts = apply_dixon_coles(score_counts, lambda_a, lambda_b)

    # Most likely scoreline
    best_score = max(score_counts, key=score_counts.get)

    return {
        "result": "home" if wins_a >= wins_b else "away",
        "score": best_score,
        "win_prob_home": wins_a / n_sims,
        "win_prob_away": wins_b / n_sims,
        "lambda_home": lambda_a,
        "lambda_away": lambda_b,
        "all_scores": score_counts,
    }


def get_top_scorers(team: str, n_goals: int, rng: np.random.Generator) -> list:
    """
    Pick the most likely jersey numbers for `n_goals` goals scored by `team` using smoothed goal shares.
    """
    if team not in TEAM_SCORERS or n_goals == 0:
        return []

    scorers_data = TEAM_SCORERS[team]
    names = [s[0] for s in scorers_data]  # jersey numbers
    tally = np.array([s[2] for s in scorers_data], dtype=float)

    # Smooth the weights to model shot volume & role influence, reducing small-sample noise
    weights = tally + 0.25
    weights = weights / weights.sum()

    # Sample n_goals scorers (with replacement)
    selected = rng.choice(names, size=n_goals, replace=True, p=weights)
    return sorted(set(selected.tolist()))


CONFIRMED_KNOCKOUT_RESULTS = {
    ("PAR", "FRA"): {
        "result": "away",
        "score": (0, 1),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [],
        "scorers_away": [9],
    },
    ("CAN", "MAR"): {
        "result": "away",
        "score": (0, 3),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [],
        "scorers_away": [8, 9],
    },
    ("BRA", "NOR"): {
        "result": "away",
        "score": (1, 2),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [10],
        "scorers_away": [9],
    },
    ("MEX", "ENG"): {
        "result": "away",
        "score": (2, 3),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [9],
        "scorers_away": [9, 10],
    },
    ("POR", "ESP"): {
        "result": "away",
        "score": (0, 1),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [],
        "scorers_away": [6],
    },
    ("USA", "BEL"): {
        "result": "away",
        "score": (1, 4),
        "win_prob_home": 0.0,
        "win_prob_away": 1.0,
        "scorers_home": [17],
        "scorers_away": [9, 17, 20],
    },
    ("ARG", "EGY"): {
        "result": "home",
        "score": (3, 2),
        "win_prob_home": 1.0,
        "win_prob_away": 0.0,
        "scorers_home": [10, 13, 24],
        "scorers_away": [6, 14],
    },
    ("SUI", "COL"): {
        "result": "home",
        "score": (0, 0),
        "win_prob_home": 1.0,
        "win_prob_away": 0.0,
        "scorers_home": [],
        "scorers_away": [],
    }
}


def simulate_bracket(ratings: dict, n_sims: int = 50000) -> dict:
    """
    Simulate the entire knockout bracket from R16 to Final.
    """
    rng = np.random.default_rng(42)
    predictions = []

    # Helper to get team's ratings
    def get_team_ratings(team: str) -> dict:
        return ratings.get(team, {"att": 1500.0, "def": 1500.0})

    # ─── Round of 16 ─────────────────────────────────────────────────────────
    r16_fixtures = ROUND_OF_16_FIXTURES
    r16_winners = []
    r16_losers = []

    print("\n=== ROUND OF 16 ===")
    for team_a, team_b in r16_fixtures:
        match_key = (team_a, team_b)
        if match_key in CONFIRMED_KNOCKOUT_RESULTS:
            res = CONFIRMED_KNOCKOUT_RESULTS[match_key]
            home_goals, away_goals = res["score"]
            winner = team_a if res["result"] == "home" else team_b
            loser = team_b if winner == team_a else team_a
            
            r16_winners.append(winner)
            r16_losers.append(loser)
            
            pred = {
                "stage": "Round of 16",
                "team_home": team_a,
                "team_away": team_b,
                "result": res["result"],
                "score_home": home_goals,
                "score_away": away_goals,
                "scorers_home": res["scorers_home"],
                "scorers_away": res["scorers_away"],
                "winner": winner,
                "win_prob": res["win_prob_home"] if winner == team_a else res["win_prob_away"],
            }
            predictions.append(pred)
            print(f"  {team_a} vs {team_b}: {home_goals}-{away_goals} -> {winner} (CONFIRMED)")
        else:
            result = simulate_match(get_team_ratings(team_a), get_team_ratings(team_b), n_sims=n_sims, rng=rng)

            home_goals, away_goals = result["score"]
            winner = team_a if result["result"] == "home" else team_b
            loser = team_b if winner == team_a else team_a
            r16_winners.append(winner)
            r16_losers.append(loser)

            scorers_home = get_top_scorers(team_a, home_goals, rng)
            scorers_away = get_top_scorers(team_b, away_goals, rng)

            pred = {
                "stage": "Round of 16",
                "team_home": team_a,
                "team_away": team_b,
                "result": "home" if winner == team_a else "away",
                "score_home": home_goals,
                "score_away": away_goals,
                "scorers_home": scorers_home,
                "scorers_away": scorers_away,
                "winner": winner,
                "win_prob": result["win_prob_home"] if winner == team_a else result["win_prob_away"],
            }
            predictions.append(pred)
            print(f"  {team_a} vs {team_b}: {home_goals}-{away_goals} -> {winner} "
                  f"(prob: {pred['win_prob']:.1%})")

    # ─── Quarter Finals ───────────────────────────────────────────────────────
    qf_fixtures = [
        (r16_winners[0], r16_winners[1]),
        (r16_winners[2], r16_winners[3]),
        (r16_winners[4], r16_winners[5]),
        (r16_winners[6], r16_winners[7]),
    ]
    qf_winners = []
    qf_losers = []

    print("\n=== QUARTER FINALS ===")
    for team_a, team_b in qf_fixtures:
        result = simulate_match(get_team_ratings(team_a), get_team_ratings(team_b), n_sims=n_sims, rng=rng)

        home_goals, away_goals = result["score"]
        winner = team_a if result["result"] == "home" else team_b
        loser = team_b if winner == team_a else team_a
        qf_winners.append(winner)
        qf_losers.append(loser)

        scorers_home = get_top_scorers(team_a, home_goals, rng)
        scorers_away = get_top_scorers(team_b, away_goals, rng)

        pred = {
            "stage": "Quarter Final",
            "team_home": team_a,
            "team_away": team_b,
            "result": "home" if winner == team_a else "away",
            "score_home": home_goals,
            "score_away": away_goals,
            "scorers_home": scorers_home,
            "scorers_away": scorers_away,
            "winner": winner,
            "win_prob": result["win_prob_home"] if winner == team_a else result["win_prob_away"],
        }
        predictions.append(pred)
        print(f"  {team_a} vs {team_b}: {home_goals}-{away_goals} -> {winner} "
              f"(prob: {pred['win_prob']:.1%})")

    # ─── Semi Finals ──────────────────────────────────────────────────────────
    sf_fixtures = [
        (qf_winners[0], qf_winners[1]),
        (qf_winners[2], qf_winners[3]),
    ]
    sf_winners = []
    sf_losers = []

    print("\n=== SEMI FINALS ===")
    for team_a, team_b in sf_fixtures:
        result = simulate_match(get_team_ratings(team_a), get_team_ratings(team_b), n_sims=n_sims, rng=rng)

        home_goals, away_goals = result["score"]
        winner = team_a if result["result"] == "home" else team_b
        loser = team_b if winner == team_a else team_a
        sf_winners.append(winner)
        sf_losers.append(loser)

        scorers_home = get_top_scorers(team_a, home_goals, rng)
        scorers_away = get_top_scorers(team_b, away_goals, rng)

        pred = {
            "stage": "Semi Final",
            "team_home": team_a,
            "team_away": team_b,
            "result": "home" if winner == team_a else "away",
            "score_home": home_goals,
            "score_away": away_goals,
            "scorers_home": scorers_home,
            "scorers_away": scorers_away,
            "winner": winner,
            "win_prob": result["win_prob_home"] if winner == team_a else result["win_prob_away"],
        }
        predictions.append(pred)
        print(f"  {team_a} vs {team_b}: {home_goals}-{away_goals} -> {winner} "
              f"(prob: {pred['win_prob']:.1%})")

    # ─── Third Place Play-off ─────────────────────────────────────────────────
    third_a, third_b = sf_losers[0], sf_losers[1]
    result = simulate_match(get_team_ratings(third_a), get_team_ratings(third_b), n_sims=n_sims, rng=rng)
    home_goals, away_goals = result["score"]
    winner = third_a if result["result"] == "home" else third_b

    scorers_home = get_top_scorers(third_a, home_goals, rng)
    scorers_away = get_top_scorers(third_b, away_goals, rng)

    print("\n=== THIRD PLACE PLAY-OFF ===")
    pred = {
        "stage": "Third Place Play-off",
        "team_home": third_a,
        "team_away": third_b,
        "result": "home" if winner == third_a else "away",
        "score_home": home_goals,
        "score_away": away_goals,
        "scorers_home": scorers_home,
        "scorers_away": scorers_away,
        "winner": winner,
        "win_prob": result["win_prob_home"] if winner == third_a else result["win_prob_away"],
    }
    predictions.append(pred)
    print(f"  {third_a} vs {third_b}: {home_goals}-{away_goals} -> {winner} "
          f"(prob: {pred['win_prob']:.1%})")

    # ─── Final ────────────────────────────────────────────────────────────────
    final_a, final_b = sf_winners[0], sf_winners[1]
    result = simulate_match(get_team_ratings(final_a), get_team_ratings(final_b), n_sims=n_sims, rng=rng)
    home_goals, away_goals = result["score"]
    champion = final_a if result["result"] == "home" else final_b

    scorers_home = get_top_scorers(final_a, home_goals, rng)
    scorers_away = get_top_scorers(final_b, away_goals, rng)

    print("\n=== FINAL ===")
    pred = {
        "stage": "Final",
        "team_home": final_a,
        "team_away": final_b,
        "result": "home" if champion == final_a else "away",
        "score_home": home_goals,
        "score_away": away_goals,
        "scorers_home": scorers_home,
        "scorers_away": scorers_away,
        "winner": champion,
        "win_prob": result["win_prob_home"] if champion == final_a else result["win_prob_away"],
    }
    predictions.append(pred)
    print(f"  {final_a} vs {final_b}: {home_goals}-{away_goals} -> CHAMPION: {champion} "
          f"(prob: {pred['win_prob']:.1%})")

    return {
        "predictions": predictions,
        "champion": champion,
    }
