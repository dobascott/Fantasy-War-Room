import json
from pathlib import Path


def load_scoring_rules(position):

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root /
        "data" /
        "scoring" /
        f"{position.lower()}.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_score(position, stats):
    rules = load_scoring_rules(position)
    total_score = 0

    for rule in rules["scoringRules"]:
        event = rule["event"]

        if event == "passing_yards":
            player_yards = stats[event]

            minimum = rule["range"]["min"]
            maximum = rule["range"]["max"]

            if minimum <= player_yards <= maximum:
                total_score += rule["points"]

                print(
                    f"{player_yards} yards "
                    f"matches {minimum}-{maximum}"
                )

                print(
                    "Award:",
                    rule["points"],
                    "points"
                )

                print(
                    "Running Total:",
                    total_score
                )

    return total_score


test_stats = {
    "passing_yards": 345,
    "number_of_passing_tds": 3,
    "passing_interceptions_thrown": 1,
    "number_of_rushing_tds": 1,
    "rushing_yards": 42
}

calculate_score("QB", test_stats)