# WC 2026 ML Prediction Model
### µFifa '26 ML Challenge — njr_sanju | sanjaykp@mulearn

---

## Overview

A Poisson-based Monte Carlo tournament simulator that predicts the winner, regulation-time score, and goal scorers for all 16 knockout matches of the 2026 FIFA World Cup — from Round of 16 through the Final.

**Predicted champion: FRA** *(provisional — will be regenerated after all Round of 32 fixtures are confirmed)*

---

## Pipeline

```
Step 1: Seed Elo Ratings
        Assign base Elo to all 32 teams from FIFA June 2026 rankings

Step 2: Update Team Strengths
        Replay confirmed WC 2026 Round of 32 results
        Elo shifts proportional to win/loss margin and goal difference

Step 3: Simulate Match Scores (50,000 runs per match)
        Derive per-team expected goals (lambda) from Elo gap
        Sample scorelines from independent Poisson distributions
        Pick the modal regulation-time scoreline as the prediction

Step 4: Resolve Advancement + Sample Scorers
        Draw outcomes resolved via Elo-weighted advancement proxy
        Scorer jersey numbers sampled from player goal-share distribution

Step 5: Export CSV
        Write 16-row file in official template format with fixed seed
```

---

## Assumptions

- `predicted_home_score` and `predicted_away_score` represent the **regulation-time score** (90 minutes only).
- `predicted_winner` stores the **team expected to advance** from the knockout match. A drawn regulation score is allowed — `predicted_winner` resolves the team expected to progress (via Elo-weighted penalty proxy). This field is always populated for all 16 matches.
- For the Final specifically, if the score is level at 90 minutes, `predicted_winner` contains the team most likely to lift the trophy. Re-check final validator behavior before upload to confirm this is the expected field interpretation.
- Scorer jersey numbers correspond to the **set of players predicted to score** in that match. Exact set match is required for scorer points.
- The current bracket is **partly provisional**. Fixtures will be updated and the CSV regenerated once all Round of 32 results are confirmed (by July 3).

---

## CSV Schema

Aligned with the currently downloaded official template from `wcreflected.mulearn.org/submit`. Re-verify column names against the actual file before final upload — a single mismatch can fail validation.

| Column | Format | Notes |
|--------|--------|-------|
| `match_id` | `R16_001`–`R16_008`, `QF_001`–`QF_004`, `SF_001`–`SF_002`, `TP_001`, `F_001` | Fixed per stage |
| `stage` | Exact string | See valid values below |
| `home_team` | FIFA 3-letter uppercase code | e.g. `FRA`, `BRA` |
| `away_team` | FIFA 3-letter uppercase code | |
| `predicted_home_score` | Integer ≥ 0 | Regulation-time goals |
| `predicted_away_score` | Integer ≥ 0 | Regulation-time goals |
| `predicted_scorers_home` | Deduplicated, sorted, comma-separated jersey numbers | Empty string `""` if score is 0 |
| `predicted_scorers_away` | Deduplicated, sorted, comma-separated jersey numbers | Empty string `""` if score is 0 |
| `predicted_winner` | FIFA 3-letter uppercase code | Advancing team |

**Valid stage strings (exact match required):**
`Round of 16` · `Quarter Final` · `Semi Final` · `Third Place Play-off` · `Final`

---

## Reproducibility

| Detail | Value |
|--------|-------|
| Python version | 3.10.0 |
| Key packages | `pandas`, `numpy`, `scipy`, `scikit-learn` |
| Random seed | `np.random.default_rng(42)` — fixed throughout |
| Simulations per match | 50,000 (configurable via `--sims`) |
| Output file | `wc2026_predictions.csv` (configurable via `--output`) |
| Tie-breaking | When outcomes have near-identical probability, the highest-frequency modal score is chosen; the fixed seed ensures a deterministic output. |

```powershell
# Standard run (seed Elo, no external data needed)
$env:PYTHONIOENCODING="utf-8"; python predict.py --sims 50000

# With historical results CSV for better Elo calibration
$env:PYTHONIOENCODING="utf-8"; python predict.py --data data/results.csv --sims 50000

# Run diagnostic tests
$env:PYTHONIOENCODING="utf-8"; python test_model.py
```

---

## Model Details

### Elo Rating System
- K-factor: **60** for WC matches · **32** for competitive · **20** for friendlies
- Goal-difference multiplier: 1.0 (≤1 goal) / 1.5 (2 goals) / 1.75 (3+)
- Updated using all confirmed WC 2026 Round of 32 results

### Poisson Goal Model
- `lambda_team = 1.35 × (0.5 + win_probability)`, clipped to `[0.5, 3.0]`
- Base rate 1.35 goals/team/game reflects WC knockout historical averages
- Uses independent Poisson per team — a standard and well-understood baseline
- **Known limitation:** independent Poisson does not capture score correlation at low margins. A Dixon-Coles adjustment or bivariate Poisson could improve calibration. Planned as a future upgrade.
- **Score distribution note:** In this model, the most common modal regulation-time score for evenly matched knockout pairs is 1-1, because predicted goal means cluster around 1.3–1.5 per team where the Poisson mode is 1 for both sides. This matches the low-scoring structure of knockout football. Heavily mismatched pairs produce different modal scores (e.g. PAR vs FRA → 0-1, BRA vs NOR → 1-0).

### Scorer Prediction
- Scorers are sampled from a player-level probability distribution built from each player's **goal share** in WC 2026 group stage and Round of 32 matches
- Planned improvement: incorporate minutes played and shot volume as additional weighting factors
- Jersey numbers are deduplicated and stored in ascending order; empty string for 0-goal outcomes

---

## Provisional Predictions

> **These are illustrative bracket outputs and will be regenerated after all Round of 32 results are finalized.** Do not treat this table as the final submission until the CSV is regenerated.

| match_id | Stage | Home | Away | Score | Winner | Win Prob |
|----------|-------|------|------|-------|--------|----------|
| R16_001 | Round of 16 | CAN | MAR | 1–1 | MAR | 51.3% |
| R16_002 | Round of 16 | PAR | FRA | 0–1 | FRA | 79.4% |
| R16_003 | Round of 16 | BRA | NOR | 1–0 | BRA | 77.2% |
| R16_004 | Round of 16 | ESP | ENG | 1–1 | ESP | 55.0% |
| R16_005 | Round of 16 | POR | USA | 1–1 | POR | 64.2% |
| R16_006 | Round of 16 | ARG | BEL | 1–1 | ARG | 61.0% |
| R16_007 | Round of 16 | MEX | SUI | 1–1 | MEX | 55.1% |
| R16_008 | Round of 16 | COL | CIV | 1–1 | COL | 69.2% |
| QF_001 | Quarter Final | MAR | FRA | 1–1 | FRA | 73.0% |
| QF_002 | Quarter Final | BRA | ESP | 1–1 | ESP | 50.1% |
| QF_003 | Quarter Final | POR | ARG | 1–1 | ARG | 55.0% |
| QF_004 | Quarter Final | MEX | COL | 1–1 | COL | 52.6% |
| SF_001 | Semi Final | FRA | ESP | 1–1 | FRA | 53.6% |
| SF_002 | Semi Final | ARG | COL | 1–1 | ARG | 67.7% |
| TP_001 | Third Place Play-off | ESP | COL | 1–1 | ESP | 69.5% |
| F_001 | Final | FRA | ARG | 1–1 | FRA | 55.9% |

---

## Confirmed R32 Results (Elo updated)

| Match | Score | Advancing |
|-------|-------|-----------|
| CAN vs RSA | 1–0 | CAN |
| BRA vs JPN | 2–1 | BRA |
| PAR vs GER | 1–1 (pens 4–3) | PAR |
| MAR vs NED | 1–1 (pens 3–2) | MAR |
| Remaining 12 | — | In progress, finish by July 3 |

---

## Diagnostic Tests

| Test | Status |
|------|--------|
| Elo ordering — stronger teams have win prob > 50% | Passing locally |
| Expected goals scale with Elo gap | Passing locally |
| Poisson mode produces 1-1 for lambda ~1.3–1.5 | Passing locally |
| Score distribution from 1M sims (1-1 at 12.2%) | Passing locally |
| Bracket propagation R16 → QF → SF → Final | Passing locally |
| CSV schema matches current downloaded template | Passing locally |

Calibration metrics (Brier score, log loss, exact-score hit rate, scorer-set exact match rate) cannot be evaluated before the tournament results are known.

---

## Data Sources

| Source | Usage |
|--------|-------|
| [International Football Results 1872–2017](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017) | Historical Elo calibration |
| [FIFA WC 2026 Player Performance Dataset](https://www.kaggle.com/datasets/rauffauzanrambe/fifa-world-cup-2026-player-performance-dataset) | Scorer probability weights |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Event-level reference data |
| Live WC 2026 results (public, June 30 2026) | R32 Elo updates |

---

## Project Files

| File | Description |
|------|-------------|
| `predict.py` | Main pipeline entry point |
| `src/data.py` | R16 fixtures (partly provisional), Elo seeds, scorer data |
| `src/elo_model.py` | Elo computation: seed → WC 2026 updates |
| `src/simulator.py` | Poisson Monte Carlo simulator and bracket propagation |
| `src/generate_csv.py` | CSV writer and format validator |
| `wc2026_predictions.csv` | Current submission CSV — regenerate after fixture update |
| `WC2026_Prediction_Model.ipynb` | Jupyter notebook required as submission link |
| `test_model.py` | Core diagnostic tests |

---

## Submission Checklist

- [x] Pipeline runs end-to-end without errors
- [x] CSV schema aligned with currently downloaded template
- [x] All 16 match rows present with correct `match_id` values
- [x] Stage names match required strings including `Third Place Play-off`
- [x] `predicted_winner` populated for all 16 matches
- [x] Scorer fields are empty string (not null) for 0-goal teams
- [x] Jersey numbers are deduplicated, sorted ascending, comma-separated
- [x] Core diagnostic tests passing locally
- [ ] **Re-verify CSV column names against the final downloaded template before upload**
- [ ] **Update R16 fixtures in `src/data.py` once all R32 results are confirmed**
- [ ] Re-run: `$env:PYTHONIOENCODING="utf-8"; python predict.py --sims 50000`
- [ ] Upload `wc2026_predictions.csv` to https://wcreflected.mulearn.org/submit
- [ ] Add Google Colab link for `WC2026_Prediction_Model.ipynb`
- [ ] Post screenshot in Discord with `#mufifa2026-predict`
