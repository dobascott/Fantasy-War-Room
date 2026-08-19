from pathlib import Path
import pandas as pd


def load_player_rankings():
    """
    Load and normalize the primary 2026 player rankings CSV.
    """

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "rankings"
        / "rankings_2026.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Ranking file not found: {file_path}"
        )

    # Let pandas detect the delimiter automatically.
    df = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    # Clean any accidental spaces/BOM characters from headers.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    required_columns = [
        "Rank",
        "Player",
        "Team",
        "BYE",
        "Position-Rank",
        "FF Pts",
        "VOR",
        "ADP ( Average )"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("\nERROR: Required columns were not found.")
        print("Missing:")
        for column in missing_columns:
            print(f"  - {column}")

        print("\nColumns actually found in the CSV:")
        for column in df.columns:
            print(f"  - {column}")

        raise ValueError(
            "The rankings CSV does not match the expected 4for4 format."
        )

    df = df[required_columns].copy()

    df = df.rename(
        columns={
            "Rank": "rank",
            "Player": "player",
            "Team": "team",
            "BYE": "bye",
            "Position-Rank": "position_rank",
            "FF Pts": "projected_points",
            "VOR": "vor",
            "ADP ( Average )": "average_adp"
        }
    )

    df["position"] = (
        df["position_rank"]
        .astype(str)
        .str.extract(r"([A-Za-z]+)", expand=False)
        .str.upper()
    )

    return df


if __name__ == "__main__":
    players = load_player_rankings()

    print()
    print(players.head(10).to_string(index=False))
    print()
    print(f"Players loaded: {len(players)}")