# WC 2026 ML Prediction Model
### µFifa '26 ML Challenge — njr_sanju | sanjaykp@mulearn

---

## Overview

A Negative Binomial Monte Carlo tournament simulator with Dixon-Coles calibration that predicts the winner, regulation-time score, and goal scorers for all 16 knockout matches of the 2026 FIFA World Cup — from Round of 16 through the Final.

**Provisional champion prediction: ARG** *(will be regenerated after all Round of 32 fixtures are confirmed)*

---

## Pipeline

```
Step 1: Seed Elo Ratings
        Assign base Elo to all 32 teams from FIFA June 2026 rankings

Step 2: Update Team Strengths
        Replay confirmed WC 2026 Round of 32 results
        Elo shifts proportional to goal-based attack and defense ratings

Step 3: Simulate Match Scores (50,000 runs per match)
        Derive per-team expected goals (lambda) from Att/Def ratings
        Sample scorelines from Negative Binomial distributions (r=6.0)
        Apply Dixon-Coles calibration parameter (rho = -0.05)
        Pick the modal regulation-time scoreline as the prediction

Step 4: Resolve Advancement + Sample Scorers
        Draw outcomes resolved via Elo-weighted advancement proxy
        Scorer jersey numbers sampled from smoothed goal-share distribution

Step 5: Export CSV
        Write 16-row file in template format with fixed seed
```

---

## Assumptions

- `predicted_home_score` and `predicted_away_score` represent the **regulation-time score** (90 minutes only).
- `predicted_winner` stores the team expected to progress from the knockout match. A drawn regulation score is allowed, and this field is always populated for all 16 matches.
- For the Final, `predicted_winner` contains the team expected to win the tournament. Re-check final validator behavior before upload to confirm this field interpretation.
- Scorer jersey numbers correspond to the **set of players predicted to score** in that match. Exact set match is required for scorer points.
- The bracket is **provisional** and will be regenerated once all Round of 32 results are confirmed (by July 3).

---

## CSV Schema

Aligned with the template checked locally from `wcreflected.mulearn.org/submit`. Re-verify column names against the actual file before final upload — a single mismatch can fail validation.

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
| Key packages | `pandas`, `numpy`, `scipy`, `requests` |
| Random seed | `np.random.default_rng(42)` — fixed throughout |
| Simulations per match | 50,000 (configurable via `--sims`) |
| Output file | `wc2026_predictions.csv` (configurable via `--output`) |
| Tie-breaking | When outcomes have near-identical probability, the highest-frequency modal score is chosen; the fixed seed ensures a deterministic output. |

```powershell
# Standard run (uses the configured results dataset path)
$env:PYTHONIOENCODING="utf-8"; python predict.py --sims 50000

# Run diagnostic tests
$env:PYTHONIOENCODING="utf-8"; python test_model.py
```

---

## Model Details

### Attack/Defense Elo Rating System
- Separates attacking and defending strength for each team.
- K-factor: **24** for WC matches · **12** for non-WC matches.
- Home-ground advantage: $+80$ Elo rating points added to host team's attack strength.
- Updated dynamically using all confirmed WC 2026 results.

### Negative Binomial Goal Model
- Expected goals: `lambda_A = 1.35 * 10 ** ((att_A - def_B) / 400)`
- Goal counts sampled using Negative Binomial distribution ($r=6.0$) to support realistic variance.
- Dixon-Coles correlation parameter ($\rho = -0.05$) applied to calibrate low scores.
- **Known limitations:**
  - Final bracket predictions depend on the completed Round of 32 fixture state at the time of regeneration.
- **Score distribution note:** In this model, 1-1, 0-0, 0-1, and 1-0 are typical modal scorelines, matching the low-scoring structure of knockout football. Heavily mismatched pairs yield more descriptive scorelines (e.g. BRA vs NOR → 2-1).

### Scorer Prediction
- Scorers are sampled from a player-level probability distribution built from each player's **goal share** in WC 2026 matches.
- Smooth weights are applied (+0.25 Laplace smoothing) to reduce small-sample noise.
- Jersey numbers are deduplicated and stored in ascending order; empty string for 0-goal outcomes.

---

## Provisional Predictions

> **These are illustrative bracket outputs and will be regenerated after all Round of 32 results are finalized.**

| match_id | Stage | Home | Away | Score | Winner | Win Prob |
|----------|-------|------|------|-------|--------|----------|
| R16_001 | Round of 16 | CAN | MAR | 0–0 | MAR | 59.2% |
| R16_002 | Round of 16 | PAR | FRA | 0–1 | FRA | 74.2% |
| R16_003 | Round of 16 | BRA | NOR | 2–1 | BRA | 76.1% |
| R16_004 | Round of 16 | ESP | ENG | 0–0 | ENG | 50.4% |
| R16_005 | Round of 16 | POR | USA | 1–1 | POR | 72.7% |
| R16_006 | Round of 16 | ARG | BEL | 1–0 | ARG | 66.7% |
| R16_007 | Round of 16 | MEX | SUI | 0–0 | SUI | 58.0% |
| R16_008 | Round of 16 | COL | CIV | 0–0 | COL | 57.8% |
| QF_001 | Quarter Final | MAR | FRA | 0–1 | FRA | 67.6% |
| QF_002 | Quarter Final | BRA | ENG | 1–1 | BRA | 58.8% |
| QF_003 | Quarter Final | POR | ARG | 0–0 | ARG | 65.5% |
| QF_004 | Quarter Final | SUI | COL | 0–0 | SUI | 50.2% |
| SF_001 | Semi Final | FRA | BRA | 1–1 | FRA | 54.2% |
| SF_002 | Semi Final | ARG | SUI | 0–0 | ARG | 67.1% |
| TP_001 | Third Place Play-off | BRA | SUI | 1–1 | BRA | 63.6% |
| F_001 | Final | FRA | ARG | 0–0 | ARG | 52.2% |

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
| Negative Binomial & Dixon-Coles goal model | Passing locally |
| Score distribution from 1M sims (0-0 at 17.5%) | Passing locally |
| Bracket propagation R16 → QF → SF → Final | Passing locally |
| CSV schema matches current template | Passing locally |

Calibration metrics cannot be evaluated before the tournament results are known.

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
| `src/elo_model.py` | Elo rating logic |
| `src/simulator.py` | Poisson Monte Carlo simulator |
| `src/generate_csv.py` | CSV writer and validator |
| `wc2026_predictions.csv` | Predictions output file |
| `WC2026_Prediction_Model.ipynb` | Colab notebook template |
| `test_model.py` | Diagnostic tests |

---

## Submission Checklist

- [ ] **Re-verify CSV column names against the downloaded template before upload**
- [ ] **Update R16 fixtures in `src/data.py` once all R32 results are confirmed (by July 3)**
- [ ] Re-run: `$env:PYTHONIOENCODING="utf-8"; python predict.py --sims 50000`
- [ ] Upload `wc2026_predictions.csv` to the submission portal
- [ ] Add Google Colab link for `WC2026_Prediction_Model.ipynb`
- [ ] Post screenshot in Discord with `#mufifa2026-predict`
