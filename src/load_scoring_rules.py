import json
file_path = "../data/scoring/qb.json"
with open(file_path, "r") as file:
        scoring_rules = json.load(file)
print("Scoring rules loaded successfully!")
print()

print(f"Position: {scoring_rules['position']}")
print(f"Number of Rules: {len(scoring_rules['scoringRules'])}")
