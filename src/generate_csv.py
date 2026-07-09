"""
generate_csv.py - Generate the final prediction CSV from simulation results.
Matches the EXACT official template format from wcreflected.mulearn.org/submit

Official columns (from the downloaded template):
  match_id, stage, home_team, away_team,
  predicted_home_score, predicted_away_score,
  predicted_scorers_home, predicted_scorers_away,
  predicted_winner
"""

import pandas as pd
import os


MATCH_ID_PREFIXES = {
    "Round of 16":           "R16",
    "Quarter Final":         "QF",
    "Semi Final":            "SF",
    "Third Place Play-off":  "TP",
    "Final":                 "F",
}

STAGE_ORDER = {
    "Round of 16": 1,
    "Quarter Final": 2,
    "Semi Final": 3,
    "Third Place Play-off": 4,
    "Final": 5,
}


def format_scorers(jersey_numbers: list) -> str:
    """Format jersey numbers as a comma-separated string."""
    if not jersey_numbers:
        return ""
    return ";".join(str(j) for j in sorted(jersey_numbers))


def generate_submission_csv(predictions: list, champion: str,
                             output_path: str = "wc2026_predictions.csv"):
    """
    Generate the final submission CSV matching the official template.
    """
    rows = []

    # Sort predictions by stage order
    predictions_sorted = sorted(
        predictions,
        key=lambda p: STAGE_ORDER.get(p["stage"], 99)
    )

    # Per-stage counters for match_id numbering
    stage_counters = {}

    for pred in predictions_sorted:
        stage = pred["stage"]
        prefix = MATCH_ID_PREFIXES.get(stage, "XX")
        stage_counters[stage] = stage_counters.get(stage, 0) + 1
        match_id = f"{prefix}_{stage_counters[stage]:03d}"

        row = {
            "match_id":               match_id,
            "stage":                  stage,
            "home_team":              pred["team_home"],
            "away_team":              pred["team_away"],
            "predicted_home_score":   pred["score_home"],
            "predicted_away_score":   pred["score_away"],
            "predicted_scorers_home": format_scorers(pred["scorers_home"]),
            "predicted_scorers_away": format_scorers(pred["scorers_away"]),
            "predicted_winner":       pred["winner"],
        }
        rows.append(row)

    df = pd.DataFrame(rows, columns=[
        "match_id", "stage", "home_team", "away_team",
        "predicted_home_score", "predicted_away_score",
        "predicted_scorers_home", "predicted_scorers_away",
        "predicted_winner"
    ])

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"\n[OK] Predictions CSV written to: {output_path}")
    print(f"   Total matches: {len(df)}")
    print(f"   Champion: {champion}  (predicted_winner of F_001)")
    print("\n[PREVIEW]:")
    print(df.to_string(index=False))

    return df


def validate_csv(df: pd.DataFrame) -> bool:
    """
    Validate the CSV against the official template requirements.
    Returns True if valid.
    """
    errors = []

    # Check row count (8 R16 + 4 QF + 2 SF + 1 TP + 1 F = 16)
    if len(df) != 16:
        errors.append(f"Expected 16 rows, got {len(df)}")

    # Check required columns
    required_cols = [
        "match_id", "stage", "home_team", "away_team",
        "predicted_home_score", "predicted_away_score",
        "predicted_scorers_home", "predicted_scorers_away",
        "predicted_winner"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        if errors:
            print("\n[FAIL] Validation Errors:")
            for e in errors:
                print(f"   - {e}")
            return False

    # Check match_ids match the exact expected pattern
    expected_ids = (
        [f"R16_{i:03d}" for i in range(1, 9)] +
        [f"QF_{i:03d}"  for i in range(1, 5)] +
        [f"SF_{i:03d}"  for i in range(1, 3)] +
        ["TP_001", "F_001"]
    )
    actual_ids = df["match_id"].tolist()
    if actual_ids != expected_ids:
        errors.append(f"match_id mismatch.\n  Expected: {expected_ids}\n  Got:      {actual_ids}")

    # Check stage values
    valid_stages = {
        "Round of 16", "Quarter Final", "Semi Final",
        "Third Place Play-off", "Final"
    }
    invalid_stages = df[~df["stage"].isin(valid_stages)]["stage"].tolist()
    if invalid_stages:
        errors.append(f"Invalid stage values: {invalid_stages}")

    # Check team codes are 2-3 uppercase letters
    for col in ["home_team", "away_team", "predicted_winner"]:
        invalid = df[~df[col].str.match(r"^[A-Z]{2,3}$", na=False)]
        if not invalid.empty:
            errors.append(f"Invalid team codes in {col}: {invalid[col].tolist()}")

    # Check scores are non-negative
    for col in ["predicted_home_score", "predicted_away_score"]:
        if not df[col].apply(lambda x: isinstance(x, (int, float)) and x >= 0).all():
            errors.append(f"Invalid scores in {col}")

    if errors:
        print("\n[FAIL] Validation Errors:")
        for e in errors:
            print(f"   - {e}")
        return False

    print("\n[OK] CSV validation passed! Matches official template. Ready to upload.")
    return True
