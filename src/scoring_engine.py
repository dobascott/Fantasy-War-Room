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


# -------- Test the function --------

qb_rules = load_scoring_rules("QB")

print("Position:", qb_rules["position"])
print("Rules:", len(qb_rules["scoringRules"]))