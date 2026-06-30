"""
simulator.py - Match outcome simulator using Poisson + Elo-based goal models.
Runs 50,000 Monte Carlo simulations per match to determine:
  - Most likely result (win/draw/lose)
  - Most likely exact score
  - Bracket progression through QF, SF, 3rd place, Final
"""

import numpy as np
from scipy.stats import poisson
from src.elo_model import expected_score
from src.data import ROUND_OF_16_FIXTURES, TEAM_SCORERS


# ─── Goal Rate Constants ──────────────────────────────────────────────────────
BASE_GOALS_PER_GAME = 1.35  # Average goals per team per WC knockout game
ELO_GOALS_SCALE = 0.0015    # How much Elo diff translates to extra goals


def compute_expected_goals(elo_a: float, elo_b: float,
                            base_rate: float = BASE_GOALS_PER_GAME) -> tuple:
    """
    Compute expected goals for both teams based on Elo difference.
    Returns (lambda_a, lambda_b) — Poisson parameters.
    """
    win_prob_a = expected_score(elo_a, elo_b)
    # Scale expected goals based on relative strength
    # Stronger team scores more, weaker team scores less
    lambda_a = base_rate * (0.5 + win_prob_a)
    lambda_b = base_rate * (0.5 + (1 - win_prob_a))
    # Clip to reasonable range
    lambda_a = np.clip(lambda_a, 0.5, 3.0)
    lambda_b = np.clip(lambda_b, 0.5, 3.0)
    return lambda_a, lambda_b


def simulate_match(elo_a: float, elo_b: float,
                   n_sims: int = 50000, rng: np.random.Generator = None) -> dict:
    """
    Simulate a single match n_sims times.
    Returns a dict with:
      - result: 'home' | 'away' (no draws in knockout — extra time/pens)
      - score: (home_goals, away_goals) most likely scoreline
      - win_prob_home: float
      - all_scores: {(h, a): count} for all simulated scorelines
    """
    if rng is None:
        rng = np.random.default_rng(42)

    lambda_a, lambda_b = compute_expected_goals(elo_a, elo_b)

    # Sample scorelines from independent Poisson distributions
    goals_a = rng.poisson(lambda_a, n_sims)
    goals_b = rng.poisson(lambda_b, n_sims)

    # In knockout matches, draws go to extra time / penalties
    # For draws, we use Elo win probability to determine who wins on pens
    win_prob_a = expected_score(elo_a, elo_b)

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
            # Draw -> penalties (use Elo prob)
            if rng.random() < win_prob_a:
                wins_a += 1
                score_key = (ga, gb)  # Score stays the same in extra time
            else:
                wins_b += 1
                score_key = (ga, gb)

        score_counts[score_key] = score_counts.get(score_key, 0) + 1

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
    Pick the most likely jersey numbers for `n_goals` goals scored by `team`.
    Returns a list of jersey numbers (may repeat if same player scores twice).
    """
    if team not in TEAM_SCORERS or n_goals == 0:
        return []

    scorers_data = TEAM_SCORERS[team]
    # Build probability weights based on goals scored so far
    names = [s[0] for s in scorers_data]  # jersey numbers
    weights = np.array([s[2] for s in scorers_data], dtype=float)
    weights = weights / weights.sum()

    # Sample n_goals scorers (with replacement - a player can score multiple)
    selected = rng.choice(names, size=n_goals, replace=True, p=weights)
    # Return unique set (as the platform wants the set of scorers)
    return sorted(set(selected.tolist()))


def simulate_bracket(ratings: dict, n_sims: int = 50000) -> dict:
    """
    Simulate the entire knockout bracket from R16 to Final.
    Returns predictions for all 16 matches (R16, QF, SF, 3rd place, Final).
    """
    rng = np.random.default_rng(42)
    predictions = []

    # ─── Round of 16 ─────────────────────────────────────────────────────────
    r16_fixtures = ROUND_OF_16_FIXTURES
    r16_winners = []
    r16_losers = []

    print("\n=== ROUND OF 16 ===")
    for team_a, team_b in r16_fixtures:
        elo_a = ratings.get(team_a, 1500)
        elo_b = ratings.get(team_b, 1500)
        result = simulate_match(elo_a, elo_b, n_sims=n_sims, rng=rng)

        home_goals, away_goals = result["score"]
        winner = team_a if result["result"] == "home" else team_b
        loser = team_b if winner == team_a else team_a
        r16_winners.append(winner)
        r16_losers.append(loser)

        # Scorer prediction
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

    # ─── Quarter Finals (4 matches) ───────────────────────────────────────────
    # Bracket: R16 winners pair up: (0 vs 1), (2 vs 3), (4 vs 5), (6 vs 7)
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
        elo_a = ratings.get(team_a, 1500)
        elo_b = ratings.get(team_b, 1500)
        result = simulate_match(elo_a, elo_b, n_sims=n_sims, rng=rng)

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

    # ─── Semi Finals (2 matches) ──────────────────────────────────────────────
    sf_fixtures = [
        (qf_winners[0], qf_winners[1]),
        (qf_winners[2], qf_winners[3]),
    ]
    sf_winners = []
    sf_losers = []

    print("\n=== SEMI FINALS ===")
    for team_a, team_b in sf_fixtures:
        elo_a = ratings.get(team_a, 1500)
        elo_b = ratings.get(team_b, 1500)
        result = simulate_match(elo_a, elo_b, n_sims=n_sims, rng=rng)

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

    # ─── Third Place (1 match) ────────────────────────────────────────────────
    third_a, third_b = sf_losers[0], sf_losers[1]
    elo_a = ratings.get(third_a, 1500)
    elo_b = ratings.get(third_b, 1500)
    result = simulate_match(elo_a, elo_b, n_sims=n_sims, rng=rng)
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

    # ─── Final (1 match) ──────────────────────────────────────────────────────
    final_a, final_b = sf_winners[0], sf_winners[1]
    elo_a = ratings.get(final_a, 1500)
    elo_b = ratings.get(final_b, 1500)
    result = simulate_match(elo_a, elo_b, n_sims=n_sims, rng=rng)
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
