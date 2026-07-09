# WC 2026 ML Prediction Model
**µFifa '26 ML Challenge** — njr_sanju

---

## Champion Prediction

🏆 **France (FRA)**

---

## Predictions (Quarter Finals → Final)

| Match | Home | Away | Score | Winner |
|-------|------|------|-------|--------|
| QF 1 | FRA | MAR | 0–0 | **FRA** |
| QF 2 | NOR | ENG | 1–1 | **ENG** |
| QF 3 | ESP | BEL | 1–1 | **ESP** |
| QF 4 | ARG | SUI | 0–0 | **SUI** |
| SF 1 | FRA | ENG | 1–1 | **FRA** |
| SF 2 | ESP | SUI | 0–0 | **ESP** |
| 3rd Place | ENG | SUI | 1–1 | **ENG** |
| **Final** | **FRA** | **ESP** | **0–0** | **🏆 FRA** |

---

## Round of 16 Results (Actual)

| Home | Away | Score | Winner |
|------|------|-------|--------|
| PAR | FRA | 0–1 | FRA |
| CAN | MAR | 0–3 | MAR |
| BRA | NOR | 1–2 | NOR |
| MEX | ENG | 2–3 | ENG |
| POR | ESP | 0–1 | ESP |
| USA | BEL | 1–4 | BEL |
| ARG | EGY | 3–2 | ARG |
| SUI | COL | 0–0 (pens) | SUI |

---

## How to Run

```powershell
# Install dependencies
pip install -r requirements.txt

# Run prediction pipeline
python predict.py --data data/results.csv

# Run tests
python test_model.py
```

---

## Data Sources

- International Football Results (1872–present) — historical match data
- FIFA WC 2026 official top scorers list — player goal tallies
- Official FIFA squad lists — player jersey numbers

---

## Project Files

| File | Description |
|------|-------------|
| `predict.py` | Main pipeline |
| `src/data.py` | Team ratings and player data |
| `src/elo_model.py` | Team strength model |
| `src/simulator.py` | Match outcome simulator |
| `src/generate_csv.py` | CSV output |
| `wc2026_predictions.csv` | **Submission file** |
| `WC2026_Prediction_Model.ipynb` | Notebook |
| `test_model.py` | Tests |
