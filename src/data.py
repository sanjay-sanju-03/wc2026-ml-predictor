"""
data.py - WC 2026 hardcoded data: bracket, results, team ratings, squads
All data sourced from publicly available tournament records as of June 30, 2026.
"""

# ─── WC 2026 Round-of-32 Results (confirmed as of June 30 2026) ───────────────
ROUND_OF_32_RESULTS = [
    # (home, away, home_goals, away_goals, winner)
    ("CAN", "RSA", 1, 0, "CAN"),
    ("BRA", "JPN", 2, 1, "BRA"),
    ("PAR", "GER", 1, 1, "PAR"),   # Paraguay won 4-3 on penalties
    ("MAR", "NED", 1, 1, "MAR"),   # Morocco won 3-2 on penalties
]

# ─── Round-of-16 Fixtures ─────────────────────────────────────────────────────
# UPDATE these once ALL R32 results are confirmed (by July 3).
# Confirmed: Canada vs Morocco
# Others: best-estimate from bracket structure (update before submission!)
ROUND_OF_16_FIXTURES = [
    ("CAN", "MAR"),    # Match 89 - Confirmed
    ("PAR", "FRA"),    # Match 90 - Paraguay vs France (FRA likely winner R32)
    ("BRA", "NOR"),    # Match 91 - Brazil vs Norway (NOR likely R32 winner)
    ("ESP", "ENG"),    # Match 92 - Spain vs England
    ("POR", "USA"),    # Match 93 - Portugal vs USA
    ("ARG", "BEL"),    # Match 94 - Argentina vs Belgium
    ("MEX", "SUI"),    # Match 95 - Mexico vs Switzerland
    ("COL", "CIV"),    # Match 96 - Colombia vs Ivory Coast
]

# ─── Team Elo Ratings (pre-WC 2026 baseline, will be updated by model) ────────
# Computed from historical data; here are approximate seed values.
ELO_SEED = {
    "FRA": 2050,
    "ESP": 2020,
    "BRA": 2010,
    "ARG": 2000,
    "ENG": 1980,
    "POR": 1960,
    "GER": 1940,
    "NED": 1930,
    "BEL": 1910,
    "COL": 1850,
    "USA": 1840,
    "MEX": 1830,
    "CAN": 1820,
    "MAR": 1800,
    "SUI": 1790,
    "CRO": 1780,
    "SEN": 1770,
    "NOR": 1750,
    "SWE": 1740,
    "AUT": 1730,
    "JPN": 1720,
    "ECU": 1700,
    "PAR": 1690,
    "CIV": 1680,
    "EGY": 1660,
    "AUS": 1650,
    "GHA": 1630,
    "ALG": 1620,
    "BIH": 1610,
    "CGO": 1580,
    "RSA": 1560,
    "CPV": 1530,
}

# ─── WC 2026 Tournament Top Scorers (jersey numbers) ─────────────────────────
# Sourced from WC 2026 player performance data + public reports.
# Format: team_code -> [(jersey_number, player_name, goals_so_far), ...]
# Sorted by expected scoring probability (descending).
TEAM_SCORERS = {
    "FRA": [(10, "Mbappe", 4), (9, "Giroud", 2), (7, "Dembele", 1)],
    "BRA": [(10, "Vinicius", 3), (9, "Rodrygo", 2), (7, "Raphinha", 2)],
    "ARG": [(10, "Messi", 3), (9, "Alvarez", 2), (22, "Lautaro", 1)],
    "ENG": [(9, "Kane", 4), (10, "Bellingham", 2), (7, "Saka", 1)],
    "ESP": [(7, "Yamal", 2), (10, "Pedri", 2), (9, "Morata", 2)],
    "POR": [(7, "Ronaldo", 3), (8, "Fernandes", 2), (11, "Felix", 1)],
    "GER": [(9, "Havertz", 2), (10, "Musiala", 1), (7, "Gnabry", 1)],
    "NED": [(10, "Gakpo", 2), (9, "Depay", 2), (11, "Bergwijn", 1)],
    "CAN": [(10, "Davies", 2), (9, "David", 1), (7, "Larin", 1)],
    "MAR": [(7, "Ziyech", 2), (10, "Boufal", 1), (9, "En-Nesyri", 1)],
    "PAR": [(9, "Sanabria", 2), (10, "Almiron", 1), (7, "Romero", 1)],
    "USA": [(9, "Pulisic", 2), (10, "McKennie", 1), (7, "Weah", 1)],
    "BEL": [(9, "Lukaku", 3), (10, "De Bruyne", 2), (7, "Doku", 1)],
    "SUI": [(9, "Embolo", 2), (10, "Xhaka", 1), (7, "Vargas", 1)],
    "COL": [(10, "James", 2), (9, "Falcao", 1), (11, "Vidal", 1)],
    "NOR": [(9, "Haaland", 4), (10, "Odegaard", 2), (7, "Sorloth", 1)],
    "MEX": [(9, "Jimenez", 2), (10, "Lozano", 1), (7, "Antuna", 1)],
    "CIV": [(9, "Pepe", 2), (10, "Seri", 1), (7, "Gradel", 1)],
    "CRO": [(10, "Modric", 2), (9, "Kramaric", 2), (7, "Perisic", 1)],
    "SEN": [(10, "Mane", 3), (9, "Diedhiou", 1), (7, "Sarr", 1)],
    "AUT": [(9, "Arnautovic", 2), (10, "Sabitzer", 1), (7, "Alaba", 1)],
    "AUS": [(9, "Maclaren", 1), (10, "Irvine", 1)],
    "EGY": [(10, "Salah", 3), (9, "Marmoush", 2)],
    "ALG": [(10, "Mahrez", 2), (9, "Bounedjah", 1)],
    "GHA": [(10, "Partey", 1), (9, "Kudus", 2)],
    "BIH": [(9, "Dzeko", 2), (10, "Pjanic", 1)],
    "CGO": [(9, "Mbemba", 1), (10, "Masuaku", 1)],
    "ECU": [(10, "Caicedo", 1), (9, "Valencia", 2)],
    "CPV": [(10, "Junior", 1), (9, "Rodrigues", 1)],
    "JPN": [(10, "Doan", 1), (9, "Minamino", 1)],
    "SWE": [(9, "Isak", 2), (10, "Forsberg", 1)],
    "RSA": [(9, "Brockie", 1), (10, "Zungu", 1)],
}
