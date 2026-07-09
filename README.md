# WC 2026 ML Prediction Model
### µFifa '26 ML Challenge — njr_sanju | sanjaykp@mulearn

---

## Overview

A Negative Binomial Monte Carlo tournament simulator with Dixon-Coles calibration, time-decay Elo ratings, and real WC 2026 player performance data. Predicts the winner, regulation-time score, and goal scorers for all knockout matches from the Quarter Finals through the Final.

**Current champion prediction: 🏆 FRA** *(v2 — upgraded July 10, 2026 with real WC 2026 tournament data)*

---

## Pipeline

```
Step 1: Build Attack / Defense Elo from 49,501 historical matches
        Apply time-decay weighting (recent matches weighted up to 2× more)
        WC matches get higher K-factor than friendlies

Step 2: Recalibrated Seed Ratings (WC 2026 form-adjusted)
        NOR: 1920 (+170), ARG: 2055 (+55), BEL: 1960 (+50), MAR: 1880 (+80)
        Based on actual tournament performances and top scorers list

Step 3: Apply Confirmed WC 2026 Results
        R32: K=24  (all 16 matches replayed)
        R16: K=32  (elevated — knockout results carry stronger signal)
        Inject actual confirmed scorers for all 8 R16 matches

Step 4: Simulate Match Scores (100,000 runs per match)
        Expected goals: lambda = 1.42 × 10^((att - def) / 400)
        Sample from Negative Binomial distribution (r=6.0)
        Apply Dixon-Coles calibration (rho = -0.05) for 0-0, 1-0, 0-1, 1-1
        Pick modal regulation-time scoreline as prediction

Step 5: Resolve Advancement + Sample Scorers
        Draws resolved via Elo-based win probability
        Scorer jersey numbers weighted by REAL WC 2026 tournament goals

Step 6: Export 8-row CSV (QF → Final)
        Format: semicolons between jersey numbers (official template)
        Scorer count ≤ predicted goals (all rows validated)
```

---

## Model Upgrades (v2 — July 10, 2026)

| Component | v1 | v2 (Current) |
|---|---|---|
| Elo seeds | Generic pre-tournament | **Recalibrated to WC 2026 form** |
| NOR seed | 1750 | **1920** — Haaland 7g, beat BRA |
| ARG seed | 2000 | **2055** — Messi #1 scorer (8 goals) |
| BEL seed | 1910 | **1960** — Dominated USA 4-1 |
| MAR seed | 1800 | **1880** — 3-0 vs CAN, 2nd QF |
| Elo time-decay | ❌ None | ✅ Exponential (recent = up to 2× weight) |
| R16 K-factor | 24 | **32** (knockout results = stronger signal) |
| TEAM_SCORERS | Old estimates | **Real WC 2026 tournament goals** |
| Goal rate | 1.35 per team | **1.42** (actual WC 2026: 2.84 goals/game) |
| Simulations | 50,000 | **100,000** (tighter estimates) |
| Training data | Seed Elo only | **49,501 historical matches** |
| Scorer separator | `,` (incorrect) | **`;`** (official template format) |

---

## Predictions & Bracket Status (July 10, 2026)

> R32 and R16 results are confirmed and locked in. QF onward are model predictions.

### ✅ Completed — Round of 32 & Round of 16 (Actual Results)

| match_id | Stage | Home | Away | Score | Winner |
|----------|-------|------|------|-------|--------|
| R16_001 | Round of 16 | PAR | FRA | 0–1 | FRA ✅ Actual |
| R16_002 | Round of 16 | CAN | MAR | 0–3 | MAR ✅ Actual |
| R16_003 | Round of 16 | BRA | NOR | 1–2 | NOR ✅ Actual |
| R16_004 | Round of 16 | MEX | ENG | 2–3 | ENG ✅ Actual |
| R16_005 | Round of 16 | POR | ESP | 0–1 | ESP ✅ Actual |
| R16_006 | Round of 16 | USA | BEL | 1–4 | BEL ✅ Actual |
| R16_007 | Round of 16 | ARG | EGY | 3–2 | ARG ✅ Actual |
| R16_008 | Round of 16 | SUI | COL | 0–0 (pens) | SUI ✅ Actual |

### 🔮 Predictions — Quarter Finals → Final

| match_id | Stage | Home | Away | Score | Scorers Home | Scorers Away | Winner | Win Prob |
|----------|-------|------|------|-------|---|---|--------|----------|
| QF_001 | Quarter Final | FRA | MAR | 0–0 | — | — | **FRA** (pens) | 52.6% |
| QF_002 | Quarter Final | NOR | ENG | 1–1 | #10 | #9 | **ENG** (pens) | 50.8% |
| QF_003 | Quarter Final | ESP | BEL | 1–1 | #19 | #9 | **ESP** (pens) | 59.2% |
| QF_004 | Quarter Final | ARG | SUI | 0–0 | — | — | **SUI** (pens) | 53.3% |
| SF_001 | Semi Final | FRA | ENG | 1–1 | #10 | #9 | **FRA** (pens) | 59.9% |
| SF_002 | Semi Final | ESP | SUI | 0–0 | — | — | **ESP** (pens) | 61.8% |
| TP_001 | Third Place Play-off | ENG | SUI | 1–1 | #10 | #9 | **ENG** (pens) | 56.1% |
| F_001 | Final | FRA | ESP | 0–0 | — | — | **🏆 FRA** (pens) | 50.1% |

> **Insight:** SUI edges ARG in QF (53.3%) — Switzerland's historically elite defense (Elo 1867) vs Argentina's attack in 49K+ historical matches. NOR vs ENG is essentially a coin flip (50.8%).

---

## WC 2026 Top Scorers Used in Model

| Rank | Player | Team | Jersey | Goals (Tournament) |
|------|--------|------|--------|-------------------|
| 1 | Lionel Messi | ARG | #10 | 8 |
| 2 | Kylian Mbappé | FRA | #10 | 7 |
| 3 | Erling Haaland | NOR | #9 | 7 |
| 4 | Harry Kane | ENG | #9 | 6 |
| 5 | Ousmane Dembélé | FRA | #7 | 4 |
| 5 | Mikel Oyarzabal | ESP | #21 | 4 |
| 5 | Jude Bellingham | ENG | #10 | 4 |

*Source: FIFA official top scorers as of July 9, 2026*

---

## Assumptions

- `predicted_home_score` / `predicted_away_score`: **regulation time only** (no penalty goals).
- `predicted_winner`: always the team expected to **advance**, including via penalty shootout.
- Scorer jersey numbers separated by **semicolon (`;`)** per official template.
- Scorer count always ≤ predicted score for that team.
- Bracket is fully propagated from real R16 results — no simulated R16 teams.

---

## CSV Schema

| Column | Format | Notes |
|--------|--------|-------|
| `match_id` | `QF_001`–`QF_004`, `SF_001`–`SF_002`, `TP_001`, `F_001` | 8 rows only |
| `stage` | Exact string | See valid values below |
| `home_team` | FIFA 3-letter uppercase code | e.g. `FRA`, `ESP` |
| `away_team` | FIFA 3-letter uppercase code | |
| `predicted_home_score` | Integer ≥ 0 | Regulation-time goals only |
| `predicted_away_score` | Integer ≥ 0 | Regulation-time goals only |
| `predicted_scorers_home` | Semicolon-separated jersey numbers | Empty if score = 0 |
| `predicted_scorers_away` | Semicolon-separated jersey numbers | Empty if score = 0 |
| `predicted_winner` | FIFA 3-letter uppercase code | Advancing team |

**Valid stage strings:** `Quarter Final` · `Semi Final` · `Third Place Play-off` · `Final`

---

## Reproducibility

| Detail | Value |
|--------|-------|
| Python version | 3.10+ |
| Key packages | `pandas`, `numpy`, `scipy`, `requests` |
| Random seed | `np.random.default_rng(42)` — fixed throughout |
| Simulations per match | **100,000** (configurable via `--sims`) |
| Goal base rate | **1.42** goals/team/game (WC 2026 calibrated) |
| Output file | `wc2026_predictions.csv` |
| Tie-breaking | Highest-frequency modal score; deterministic via fixed seed |

```powershell
# Full run with historical data (recommended)
$env:PYTHONIOENCODING="utf-8"; python predict.py --data data/results.csv --sims 100000

# Seed-only run (fast)
$env:PYTHONIOENCODING="utf-8"; python predict.py

# Run diagnostic tests
$env:PYTHONIOENCODING="utf-8"; python test_model.py
```

---

## Model Details

### Attack / Defense Elo with Time-Decay
- **Separate** attacking and defending Elo per team.
- **Time-decay:** exponential decay with `multiplier = exp(-0.1 × max(years_ago - 1, 0))`, capped at [0.5, 2.0]. Matches from the last 12 months get up to 2× weight.
- **K-factors:**
  - Historical non-WC: K=12
  - Historical WC: K=24
  - WC 2026 R32: K=24
  - **WC 2026 R16: K=32** (elevated for confirmed knockout results)
- Home-ground advantage: +80 Elo rating points (neutralized for all WC 2026 matches).

### Negative Binomial Goal Model
- Expected goals: `lambda = 1.42 × 10^((att - def) / 400)`
- Goal counts sampled via **Negative Binomial** ($r=6.0$) for realistic variance.
- **Dixon-Coles** ($\rho = -0.05$) corrects 0-0, 1-0, 0-1, 1-1 probabilities.
- 100,000 Monte Carlo simulations per match for tight probability estimates.

### Scorer Prediction
- Weights built from **real WC 2026 tournament goals** per player.
- Laplace smoothing (+0.25) applied to reduce small-sample noise.
- Jersey numbers deduplicated, stored ascending, separated by `;`.

---

## Data Sources

| Source | Usage |
|--------|-------|
| [International Football Results 1872–present](https://raw.githubusercontent.com/martj42/international_results/master/results.csv) | 49,501 matches for Elo calibration with time-decay |
| FIFA WC 2026 Official Top Scorers (live) | Real goal tallies per player for scorer model |
| Official FIFA Squad Lists (June 2, 2026) | Verified jersey numbers for all QF teams |
| WC 2026 Confirmed Match Results (public) | R32 & R16 Elo updates and bracket propagation |

---

## Project Files

| File | Description |
|------|-------------|
| `predict.py` | Main pipeline entry point |
| `src/data.py` | Elo seeds (WC 2026 calibrated), real scorer data, R16 results |
| `src/elo_model.py` | Att/Def Elo with time-decay and elevated R16 K-factor |
| `src/simulator.py` | Neg Binomial + Dixon-Coles simulator (100K sims) |
| `src/generate_csv.py` | CSV writer / validator (semicolon scorer format) |
| `wc2026_predictions.csv` | **Final submission file** (8 rows: QF → Final) |
| `WC2026_Prediction_Model.ipynb` | Colab notebook |
| `test_model.py` | Diagnostic tests |

---

## Diagnostic Tests

| Test | Status |
|------|--------|
| Elo ordering — stronger teams win prob > 50% | ✅ Passing |
| Expected goals scale with Elo gap | ✅ Passing |
| Negative Binomial + Dixon-Coles model | ✅ Passing |
| Score distribution from 1M sims | ✅ Passing |
| Bracket propagation R16 → QF → SF → Final | ✅ Passing |
| CSV schema matches official template | ✅ Passing |
| Scorer count ≤ predicted score (all rows) | ✅ Passing |
| Semicolon separator in scorer fields | ✅ Passing |

---

## Submission Checklist

- [x] R32 results confirmed and Elo updated
- [x] R16 results confirmed — actual scores locked in CSV
- [x] QF teams populated from real R16 outcomes
- [x] Scorer data updated with real WC 2026 tournament goals
- [x] CSV format matches official template (8 rows, semicolons)
- [x] All validation rules pass (scorer count ≤ score, no commas in scorer fields)
- [ ] Upload `wc2026_predictions.csv` to [wcreflected.mulearn.org/submit](https://wcreflected.mulearn.org/submit)
- [ ] Post screenshot in Discord `#mufifa2026-predict`
