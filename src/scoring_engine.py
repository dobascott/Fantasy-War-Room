import json
from pathlib import Path


def load_scoring_rules(position):
    """Load scoring rules for the requested position."""

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "scoring"
        / f"{position.lower()}.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_score(position, stats, show_breakdown=False):
    """
    Calculate a fantasy score using the scoring rules for a position.

    Stats can contain:
      - Single numeric values, such as passing_yards = 345
      - Lists of values, such as length_of_passing_td = [12, 38, 62]
    """

    scoring_data = load_scoring_rules(position)
    rules = scoring_data["scoringRules"]

    total_score = 0
    breakdown = []

    for event, stat_value in stats.items():

        matching_rules = [
            rule
            for rule in rules
            if rule["event"] == event
        ]

        if not matching_rules:
            continue

        # Events where each occurrence can fall into a different range.
        # Example: touchdown lengths [12, 38, 62]
        if isinstance(stat_value, list):

            for occurrence in stat_value:

                for rule in matching_rules:
                    minimum = rule["range"]["min"]
                    maximum = rule["range"]["max"]

                    if minimum <= occurrence <= maximum:

                        if "points" in rule:
                            points = rule["points"]

                        elif "pointsPerOccurrence" in rule:
                            points = rule["pointsPerOccurrence"]

                        else:
                            points = 0

                        if points == 0:
                            break

                        total_score += points

                        breakdown.append(
                            f"{event}: {occurrence} = {points} points"
                        )

                        break

        # Normal numeric statistic.
        else:

            for rule in matching_rules:
                minimum = rule["range"]["min"]
                maximum = rule["range"]["max"]

                # Per-occurrence scoring.
                if "pointsPerOccurrence" in rule:
                    points_per_occurrence = rule["pointsPerOccurrence"]

                    if points_per_occurrence == 0:
                        break

                    points = stat_value * points_per_occurrence
                    total_score += points

                    breakdown.append(
                        f"{event}: {stat_value} x "
                        f"{points_per_occurrence} = {points} points"
                    )

                    break

                # Range-based scoring.
                if minimum <= stat_value <= maximum:
                    points = rule.get("points", 0)

                    if points == 0:
                        break

                    total_score += points

                    breakdown.append(
                        f"{event}: {stat_value} "
                        f"({minimum}-{maximum}) = {points} points"
                    )

                    break

    if show_breakdown:
        print("\nSCORING BREAKDOWN")
        print("=" * 60)

        for line in breakdown:
            print(line)

        print("-" * 60)
        print(f"TOTAL SCORE: {total_score}")

    return total_score


# ------------------------------------------------------------
# Temporary QB validation test
# ------------------------------------------------------------

if __name__ == "__main__":

    test_stats = {
        "number_of_passing_tds": 3,
        "length_of_passing_td": [12, 38, 62],
        "passing_yards": 345,
        "passing_interceptions_thrown": 1,
        "passing_two_point_conversions": 1,
        "number_of_rushing_tds": 1,
        "rushing_yards": 42,
        "rushing_two_point_conversions": 0,
        "number_of_receiving_tds": 0,
        "receiving_yards": 0,
        "receiving_two_point_conversions": 0
    }

    calculate_score(
        position="QB",
        stats=test_stats,
        show_breakdown=True
    )