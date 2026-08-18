from pathlib import Path
import sys


# ------------------------------------------------------------
# Allow this test file to import modules from /src
# ------------------------------------------------------------

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from scoring_engine import calculate_score


def run_test(name, position, stats, expected):
    """
    Run one scoring test and compare the calculated result
    with the expected result.
    """

    actual = calculate_score(
        position=position,
        stats=stats,
        show_breakdown=False
    )

    if actual == expected:
        print(f"PASS: {name} = {actual}")
        return True

    print(
        f"FAIL: {name} | "
        f"Expected {expected}, got {actual}"
    )

    return False


tests_run = 0
tests_passed = 0


# ============================================================
# QB TEST
# ============================================================

qb_stats = {
    "length_of_passing_td": [12, 38, 62],
    "passing_yards": 345,
    "passing_interceptions_thrown": 1,
    "passing_two_point_conversions": 1,
    "number_of_rushing_tds": 1,
    "rushing_yards": 42
}

# 12-yard passing TD = 4
# 38-yard passing TD = 6
# 62-yard passing TD = 9
# 345 passing yards = 7
# 1 interception = -1
# 1 passing 2-point conversion = 2
# 1 rushing TD = 6
# 42 rushing yards = 0
#
# TOTAL = 33

tests_run += 1

if run_test(
    "QB scoring",
    "QB",
    qb_stats,
    33
):
    tests_passed += 1


# ============================================================
# RB TEST
# ============================================================

rb_stats = {
    "number_of_rushing_tds": 2,
    "rushing_yards": 118,
    "number_of_receiving_tds": 1,
    "receiving_yards": 67,
    "rushing_two_point_conversions": 1
}

# 2 rushing TDs = 12
# 118 rushing yards = 7
# 1 receiving TD = 6
# 67 receiving yards = 3
# 1 rushing 2-point conversion = 2
#
# TOTAL = 30

tests_run += 1

if run_test(
    "RB scoring",
    "RB",
    rb_stats,
    30
):
    tests_passed += 1


# ============================================================
# WR / TE TEST
# ============================================================

wr_te_stats = {
    "number_of_receiving_tds": 2,
    "receiving_yards": 162,
    "receiving_two_point_conversions": 1
}

# Based on our current WR/TE JSON:
#
# 2 receiving TDs = 18
# 162 receiving yards = 10
# 1 receiving 2-point conversion = 2
#
# TOTAL = 30

tests_run += 1

if run_test(
    "WR/TE scoring",
    "WR_TE",
    wr_te_stats,
    30
):
    tests_passed += 1


# ============================================================
# KICKER TEST
# ============================================================

pk_stats = {
    "length_of_field_goal_made": [38, 52, 57, 63],
    "extra_points_made": 3
}

# 38-yard FG = 3
# 52-yard FG = 4
# 57-yard FG = 6
# 63-yard FG = 9
# 3 extra points = 3
#
# TOTAL = 25

tests_run += 1

if run_test(
    "PK scoring",
    "PK",
    pk_stats,
    25
):
    tests_passed += 1


# ============================================================
# DEFENSE TEST
# ============================================================

def_stats = {
    "sacks": 4,
    "interceptions": 2,
    "fumble_recoveries": 1,
    "safeties": 1,
    "defensive_touchdowns": 1,
    "points_allowed": 0
}

# 4 sacks = 4
# 2 interceptions = 2
# 1 fumble recovery = 1
# 1 safety = 2
# 1 defensive TD = 6
# 0 points allowed = 7
#
# TOTAL = 22

tests_run += 1

if run_test(
    "DEF scoring",
    "DEF",
    def_stats,
    22
):
    tests_passed += 1


# ============================================================
# FINAL RESULTS
# ============================================================

print()
print("=" * 60)
print(f"TESTS PASSED: {tests_passed}/{tests_run}")
print("=" * 60)

if tests_passed == tests_run:
    print("SUCCESS: All scoring engine tests passed.")
else:
    print("WARNING: One or more scoring tests failed.")