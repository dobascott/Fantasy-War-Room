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

        print(event)

        if "points" in rule:
            print("Fixed Points:", rule["points"])

        if "pointsPerOccurrence" in rule:
            print(
                "Points Per Occurrence:",
                rule["pointsPerOccurrence"]
            )

    return total_score

test_stats = {}

calculate_score("QB", test_stats)