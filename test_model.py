import sys
sys.path.insert(0, '.')
import numpy as np
from src.elo_model import get_current_ratings, expected_score
from src.simulator import compute_expected_goals, simulate_match
from scipy.stats import poisson

ratings = get_current_ratings()

print("=== TEST 1: ELO ORDERING ===")
pairs = [('FRA','PAR'), ('BRA','NOR'), ('ESP','ENG'), ('ARG','BEL'), ('FRA','CAN')]
all_ok = True
for a, b in pairs:
    ea, eb = ratings[a], ratings[b]
    wp = expected_score(ea, eb)
    status = "[OK]" if wp > 0.5 else "[FAIL]"
    if wp <= 0.5:
        all_ok = False
    print(f"  {a}({ea:.0f}) vs {b}({eb:.0f}): {a} win prob = {wp:.1%} {status}")

print()
print("=== TEST 2: EXPECTED GOALS ===")
match_pairs = [
    ('FRA', 'PAR', 'FRA dominates'),
    ('BRA', 'NOR', 'BRA clear favourite'),
    ('CAN', 'MAR', 'Near equal'),
    ('ESP', 'ENG', 'Close match'),
]
for a, b, label in match_pairs:
    la, lb = compute_expected_goals(ratings[a], ratings[b])
    print(f"  {a} vs {b} ({label}): lambda_{a}={la:.3f}, lambda_{b}={lb:.3f}")

print()
print("=== TEST 3: WHY MOST SCORES ARE 1-1 (Poisson Math) ===")
print("  The Poisson mode (most likely integer outcome) for typical WC knockout lambdas:")
for lam in [0.87, 0.91, 1.27, 1.35, 1.43, 1.83]:
    probs = [poisson.pmf(k, lam) for k in range(5)]
    mode = int(np.argmax(probs))
    bar = "=" * int(probs[mode] * 100)
    print(f"  lambda={lam:.2f} -> mode={mode}  P(mode)={probs[mode]:.3f}  {bar}")

print()
print("=== TEST 4: SCORE DISTRIBUTION (1M sims, CAN vs MAR) ===")
rng = np.random.default_rng(42)
res = simulate_match(ratings['CAN'], ratings['MAR'], n_sims=1_000_000, rng=rng)
top_scores = sorted(res['all_scores'].items(), key=lambda x: x[1], reverse=True)[:8]
for score, count in top_scores:
    print(f"  {score[0]}-{score[1]}: {count/10000:.1f}%")

print()
print("=== TEST 5: BRACKET PROPAGATION ===")
r16_winners = ['MAR','FRA','BRA','ESP','POR','ARG','MEX','COL']
qf_pairs = [(r16_winners[i], r16_winners[i+1]) for i in range(0,8,2)]
print(f"  R16 winners: {r16_winners}")
print(f"  QF pairings: {qf_pairs}")
qf_winners = ['FRA','ESP','ARG','COL']
sf_pairs = [(qf_winners[i], qf_winners[i+1]) for i in range(0,4,2)]
print(f"  QF winners:  {qf_winners}")
print(f"  SF pairings: {sf_pairs}")

print()
print("=== TEST 6: CSV FORMAT CHECK ===")
import pandas as pd
df = pd.read_csv('wc2026_predictions.csv')
print(f"  Columns: {list(df.columns)}")
print(f"  Row count: {len(df)}")
expected_ids = [f"R16_{i:03d}" for i in range(1,9)] + \
               [f"QF_{i:03d}" for i in range(1,5)] + \
               [f"SF_{i:03d}" for i in range(1,3)] + \
               ["TP_001","F_001"]
id_ok = df['match_id'].tolist() == expected_ids
print(f"  match_id format: {'[OK]' if id_ok else '[FAIL]'}")
stages_ok = df['stage'].isin({'Round of 16','Quarter Final','Semi Final','Third Place Play-off','Final'}).all()
print(f"  Stage names valid: {'[OK]' if stages_ok else '[FAIL]'}")
scores_ok = (df['predicted_home_score'] >= 0).all() and (df['predicted_away_score'] >= 0).all()
print(f"  Scores non-negative: {'[OK]' if scores_ok else '[FAIL]'}")
team_ok = df['predicted_winner'].str.match(r'^[A-Z]{2,3}$').all()
print(f"  Winner codes valid: {'[OK]' if team_ok else '[FAIL]'}")

print()
print("=== DIAGNOSIS SUMMARY ===")
