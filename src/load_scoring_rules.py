import json
from pathlib import Path


# Find the project folder, regardless of where the script is launched from.
project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "scoring" / "qb.json"


# Load the QB scoring rules.
with open(file_path, "r", encoding="utf-8") as file:
    scoring_data = json.load(file)


def print_scoring_rules(data):
    """Display every scoring rule in a readable format."""

    print("\nQB SCORING RULES")
    print("=" * 50)

    for rule_number, rule in enumerate(data["scoringRules"], start=1):
        event = rule["event"]
        minimum = rule["range"]["min"]
        maximum = rule["range"]["max"]

        print(f"\nRule {rule_number}")
        print(f"  Event: {event}")
        print(f"  Range: {minimum} to {maximum}")

        if "pointsPerOccurrence" in rule:
            print(f"  Points per occurrence: {rule['pointsPerOccurrence']}")
        else:
            print(f"  Points: {rule['points']}")

    print("\n" + "=" * 50)


def find_range_points(event, value):
    """Find the points awarded for a value that falls within a rule's range."""

    for rule in scoring_data["scoringRules"]:
        if rule["event"] != event:
            continue

        minimum = rule["range"]["min"]
        maximum = rule["range"]["max"]

        if minimum <= value <= maximum:
            return rule.get("points", 0)

    return 0


def find_points_per_occurrence(event):
    """Find the point value for an event scored once per occurrence."""

    for rule in scoring_data["scoringRules"]:
        if rule["event"] == event:
            return rule.get("pointsPerOccurrence", 0)

    return 0


def run_hypothetical():
    """Ask for a hypothetical QB stat line and calculate its fantasy score."""

    print("\nHYPOTHETICAL QB SCORE")
    print("=" * 50)

    try:
        passing_yards = int(input("Enter passing yards: "))

        td_input = input(
            "Enter passing TD lengths separated by commas "
            "(example: 12, 38, 62), or press Enter for none: "
        ).strip()

        interceptions = int(input("Enter interceptions thrown: "))

        if td_input:
            touchdown_lengths = [
                int(length.strip())
                for length in td_input.split(",")
                if length.strip()
            ]
        else:
            touchdown_lengths = []

    except ValueError:
        print("\nInvalid entry. Please enter whole numbers only.")
        return

    total_score = 0

    print("\nSCORING BREAKDOWN")
    print("-" * 50)

    yardage_points = find_range_points("passing_yards", passing_yards)
    total_score += yardage_points
    print(f"Passing yards: {passing_yards} = {yardage_points} points")

    for touchdown_number, touchdown_length in enumerate(
        touchdown_lengths,
        start=1
    ):
        touchdown_points = find_range_points(
            "length_of_passing_td",
            touchdown_length
        )
        total_score += touchdown_points

        print(
            f"Passing TD {touchdown_number}: "
            f"{touchdown_length} yards = {touchdown_points} points"
        )

    interception_value = find_points_per_occurrence(
        "passing_interceptions_thrown"
    )
    interception_points = interceptions * interception_value
    total_score += interception_points

    print(
        f"Interceptions: {interceptions} "
        f"x {interception_value} = {interception_points} points"
    )

    print("-" * 50)
    print(f"TOTAL FANTASY SCORE: {total_score}")


print("Scoring rules loaded successfully!")
print(f"Position: {scoring_data['position']}")
print(f"Number of Rules: {len(scoring_data['scoringRules'])}")

print_scoring_rules(scoring_data)
run_hypothetical()