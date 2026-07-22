import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent

file_path = project_root / "data" / "scoring" / "qb.json"

with open(file_path, "r") as file:
    scoring_rules = json.load(file)

print("Scoring rules loaded successfully!")
print()

print(f"Position: {scoring_rules['position']}")
print(f"Number of Rules: {len(scoring_rules['scoringRules'])}")