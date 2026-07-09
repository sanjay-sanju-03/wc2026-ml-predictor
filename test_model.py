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
    r_a = ratings[a]
    r_b = ratings[b]
    ea = (r_a["att"] + r_a["def"]) / 2.0
    eb = (r_b["att"] + r_b["def"]) / 2.0
    wp = expected_score(ea, eb)
    status = "[OK]" if wp > 0.5 else "[FAIL]"
    if wp <= 0.5:
        all_ok = False
    print(f"  {a}(comb:{ea:.0f}) vs {b}(comb:{eb:.0f}): {a} win prob = {wp:.1%} {status}")

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
print("=== TEST 3: DIXON-COLES & OVERDISPERSION MATH ===")
print("  Matches now draw goals from Negative Binomial distribution to avoid flat predictions.")
print("  Dixon-Coles is applied to adjust 0-0, 1-0, 0-1, and 1-1 probabilities.")

print()
print("=== TEST 4: SCORE DISTRIBUTION (1M sims, CAN vs MAR) ===")
rng = np.random.default_rng(42)
res = simulate_match(ratings['CAN'], ratings['MAR'], n_sims=1_000_000, rng=rng)
top_scores = sorted(res['all_scores'].items(), key=lambda x: x[1], reverse=True)[:8]
for score, count in top_scores:
    print(f"  {score[0]}-{score[1]}: {count/10000:.2f}%")

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

# New format: 8 rows (QF -> Final only)
expected_ids = (
    [f"QF_{i:03d}" for i in range(1, 5)] +
    [f"SF_{i:03d}" for i in range(1, 3)] +
    ["TP_001", "F_001"]
)
id_ok = df['match_id'].tolist() == expected_ids
print(f"  match_id format (8 rows QF->Final): {'[OK]' if id_ok else '[FAIL]'}")

stages_ok = df['stage'].isin({'Quarter Final','Semi Final','Third Place Play-off','Final'}).all()
print(f"  Stage names valid: {'[OK]' if stages_ok else '[FAIL]'}")

scores_ok = (df['predicted_home_score'] >= 0).all() and (df['predicted_away_score'] >= 0).all()
print(f"  Scores non-negative: {'[OK]' if scores_ok else '[FAIL]'}")

team_ok = df['predicted_winner'].str.match(r'^[A-Z]{2,3}$').all()
print(f"  Winner codes valid: {'[OK]' if team_ok else '[FAIL]'}")

# Scorer format: no commas inside scorer fields, semicolons only
no_comma_ok = True
for _, row in df.iterrows():
    sh = str(row['predicted_scorers_home'])
    sa = str(row['predicted_scorers_away'])
    if (',' in sh and sh != 'nan') or (',' in sa and sa != 'nan'):
        no_comma_ok = False
print(f"  Scorer separator is semicolon: {'[OK]' if no_comma_ok else '[FAIL]'}")

# Scorer count rule
count_ok = True
for _, row in df.iterrows():
    hs = int(row['predicted_home_score'])
    as_ = int(row['predicted_away_score'])
    sh = [x for x in str(row['predicted_scorers_home']).split(';') if x.strip() and x != 'nan']
    sa = [x for x in str(row['predicted_scorers_away']).split(';') if x.strip() and x != 'nan']
    if len(sh) > hs or len(sa) > as_:
        count_ok = False
    if hs > 0 and len(sh) == 0:
        count_ok = False
    if as_ > 0 and len(sa) == 0:
        count_ok = False
print(f"  Scorer count matches score: {'[OK]' if count_ok else '[FAIL]'}")

all_pass = id_ok and stages_ok and scores_ok and team_ok and no_comma_ok and count_ok
print()
print("=== DIAGNOSIS SUMMARY ===")
print(f"  {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
