from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RANKINGS_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "rankings"
)

OFFENSE_FILE = (
    RANKINGS_FOLDER
    / "rankings_2026.csv"
)

KICKER_FILE = (
    RANKINGS_FOLDER
    / "kickers_2026.csv"
)

DEFENSE_FILE = (
    RANKINGS_FOLDER
    / "defenses_2026.csv"
)


# ============================================================
# HELPERS
# ============================================================

def clean_numeric(series):
    """
    Convert a pandas Series to numeric values.
    Invalid / blank entries become NaN.
    """

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def calculate_position_vor(
    dataframe,
    replacement_index
):
    """
    Create a simple same-position VOR value.

    VOR = projected points above the chosen
    replacement-level player.

    Example:
        PK replacement_index = 10
        DEF replacement_index = 10

    This is intentionally positional rather
    than comparing kickers directly to RB/WR.
    """

    if dataframe.empty:
        return pd.Series(
            dtype=float
        )

    dataframe = dataframe.copy()

    dataframe = dataframe.sort_values(
        "projected_points",
        ascending=False
    ).reset_index(drop=True)


    replacement_index = min(
        replacement_index,
        len(dataframe) - 1
    )


    replacement_points = (
        dataframe.iloc[
            replacement_index
        ]["projected_points"]
    )


    return (
        dataframe["projected_points"]
        - replacement_points
    ).clip(
        lower=0
    )


# ============================================================
# OFFENSIVE PLAYERS
# ============================================================

def load_offense():
    """
    Load QB / RB / WR / TE rankings.
    """

    if not OFFENSE_FILE.exists():

        raise FileNotFoundError(
            f"Missing offensive rankings file: "
            f"{OFFENSE_FILE}"
        )


    df = pd.read_csv(
        OFFENSE_FILE
    )


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
        for column
        in required_columns
        if column not in df.columns
    ]


    if missing_columns:

        raise ValueError(
            "Offensive rankings file is missing "
            "required columns: "
            + ", ".join(
                missing_columns
            )
        )


    df = df[
        required_columns
    ].copy()


    df = df.rename(
        columns={
            "Rank":
                "rank",

            "Player":
                "player",

            "Team":
                "team",

            "BYE":
                "bye",

            "Position-Rank":
                "position_rank",

            "FF Pts":
                "projected_points",

            "VOR":
                "vor",

            "ADP ( Average )":
                "average_adp"
        }
    )


    df["position"] = (
        df["position_rank"]
        .astype(str)
        .str.split("-")
        .str[0]
        .str.upper()
    )


    df["rank"] = clean_numeric(
        df["rank"]
    )

    df["bye"] = clean_numeric(
        df["bye"]
    )

    df["projected_points"] = clean_numeric(
        df["projected_points"]
    )

    df["vor"] = clean_numeric(
        df["vor"]
    ).fillna(0)

    df["average_adp"] = clean_numeric(
        df["average_adp"]
    )


    df["source_rank"] = df[
        "rank"
    ]


    df["source_type"] = (
        "OFFENSE"
    )


    return df


# ============================================================
# KICKERS
# ============================================================

def load_kickers():
    """
    Load kicker rankings and normalize them
    to the same internal structure.
    """

    if not KICKER_FILE.exists():

        return pd.DataFrame()


    df = pd.read_csv(
        KICKER_FILE
    )


    required_columns = [
        "Rank",
        "Player",
        "Team",
        "BYE",
        "FF Pts",
        "ADP ( Average )"
    ]


    missing_columns = [
        column
        for column
        in required_columns
        if column not in df.columns
    ]


    if missing_columns:

        raise ValueError(
            "Kicker rankings file is missing "
            "required columns: "
            + ", ".join(
                missing_columns
            )
        )


    df = df[
        required_columns
    ].copy()


    df = df.rename(
        columns={
            "Rank":
                "source_rank",

            "Player":
                "player",

            "Team":
                "team",

            "BYE":
                "bye",

            "FF Pts":
                "projected_points",

            "ADP ( Average )":
                "average_adp"
        }
    )


    df["source_rank"] = clean_numeric(
        df["source_rank"]
    )

    df["bye"] = clean_numeric(
        df["bye"]
    )

    df["projected_points"] = clean_numeric(
        df["projected_points"]
    )

    df["average_adp"] = clean_numeric(
        df["average_adp"]
    )


    df["position"] = "PK"


    df["position_rank"] = (
        "PK-"
        + df["source_rank"]
        .fillna(99)
        .astype(int)
        .astype(str)
        .str.zfill(2)
    )


    # --------------------------------------------------------
    # KICKER VOR
    # --------------------------------------------------------
    #
    # 10-team league.
    # We compare each kicker to approximately
    # the 11th kicker in the pool.
    # --------------------------------------------------------

    sorted_kickers = (
        df.sort_values(
            "projected_points",
            ascending=False
        )
        .reset_index(drop=True)
    )


    kicker_vor = calculate_position_vor(
        sorted_kickers,
        replacement_index=10
    )


    sorted_kickers["vor"] = (
        kicker_vor
    )


    df = sorted_kickers


    # --------------------------------------------------------
    # SYNTHETIC OVERALL RANK
    # --------------------------------------------------------
    #
    # The kicker Rank column is PK rank, NOT an
    # overall fantasy ranking.
    #
    # We therefore give kickers a neutral synthetic
    # overall rank so they do not appear as #1
    # overall merely because Aubrey is PK1.
    #
    # Scott's recommendation engine will decide
    # whether a kicker is worth an early pick based
    # on points, VOR, fit and availability.
    # --------------------------------------------------------

    df["rank"] = (
        150
        + df["source_rank"]
    )


    df["source_type"] = (
        "KICKER"
    )


    return df


# ============================================================
# DEFENSES
# ============================================================

def load_defenses():
    """
    Load team-defense rankings and normalize them.
    """

    if not DEFENSE_FILE.exists():

        return pd.DataFrame()


    df = pd.read_csv(
        DEFENSE_FILE
    )


    required_columns = [
        "Rank",
        "Player",
        "Team",
        "BYE",
        "FF Pts",
        "ADP ( Average )"
    ]


    missing_columns = [
        column
        for column
        in required_columns
        if column not in df.columns
    ]


    if missing_columns:

        raise ValueError(
            "Defense rankings file is missing "
            "required columns: "
            + ", ".join(
                missing_columns
            )
        )


    df = df[
        required_columns
    ].copy()


    df = df.rename(
        columns={
            "Rank":
                "source_rank",

            "Player":
                "player",

            "Team":
                "team",

            "BYE":
                "bye",

            "FF Pts":
                "projected_points",

            "ADP ( Average )":
                "average_adp"
        }
    )


    df["source_rank"] = clean_numeric(
        df["source_rank"]
    )

    df["bye"] = clean_numeric(
        df["bye"]
    )

    df["projected_points"] = clean_numeric(
        df["projected_points"]
    )

    df["average_adp"] = clean_numeric(
        df["average_adp"]
    )


    df["position"] = "DEF"


    df["position_rank"] = (
        "DEF-"
        + df["source_rank"]
        .fillna(99)
        .astype(int)
        .astype(str)
        .str.zfill(2)
    )


    # --------------------------------------------------------
    # DEFENSE VOR
    # --------------------------------------------------------
    #
    # Compare against approximately DEF11
    # in a 10-team league.
    # --------------------------------------------------------

    sorted_defenses = (
        df.sort_values(
            "projected_points",
            ascending=False
        )
        .reset_index(drop=True)
    )


    defense_vor = calculate_position_vor(
        sorted_defenses,
        replacement_index=10
    )


    sorted_defenses["vor"] = (
        defense_vor
    )


    df = sorted_defenses


    # DEF source rank is also positional only.
    #
    # Give defenses a low synthetic overall rank.
    # Scott's strategy already strongly suppresses
    # DEF until the final rounds.
    df["rank"] = (
        250
        + df["source_rank"]
    )


    df["source_type"] = (
        "DEFENSE"
    )


    return df


# ============================================================
# MASTER PLAYER POOL
# ============================================================

def load_player_rankings():
    """
    Load and combine:

        QB / RB / WR / TE
        PK
        DEF

    All sources are normalized into the same schema.
    """

    offense = load_offense()

    kickers = load_kickers()

    defenses = load_defenses()


    frames = [
        frame
        for frame in [
            offense,
            kickers,
            defenses
        ]
        if not frame.empty
    ]


    players = pd.concat(
        frames,
        ignore_index=True
    )


    # --------------------------------------------------------
    # CLEAN FINAL DATA
    # --------------------------------------------------------

    players["player"] = (
        players["player"]
        .astype(str)
        .str.strip()
    )


    players["team"] = (
        players["team"]
        .astype(str)
        .str.strip()
    )


    players["position"] = (
        players["position"]
        .astype(str)
        .str.strip()
        .str.upper()
    )


    players["position_rank"] = (
        players["position_rank"]
        .astype(str)
        .str.strip()
    )


    # Remove accidental duplicate player rows.
    #
    # Keep the first source occurrence.
    players = (
        players
        .drop_duplicates(
            subset=[
                "player",
                "position"
            ],
            keep="first"
        )
    )


    players = (
        players
        .sort_values(
            [
                "rank",
                "position",
                "source_rank"
            ]
        )
        .reset_index(drop=True)
    )


    return players


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    players = load_player_rankings()


    print(
        "Unified player loader successful."
    )


    print(
        f"Total players loaded: "
        f"{len(players)}"
    )


    print()


    print(
        "Players by position:"
    )


    print(
        players[
            "position"
        ]
        .value_counts()
        .sort_index()
    )


    print()


    print(
        "Top kickers:"
    )


    print(
        players[
            players["position"]
            == "PK"
        ][
            [
                "position_rank",
                "player",
                "team",
                "projected_points",
                "vor"
            ]
        ]
        .head(5)
        .to_string(
            index=False
        )
    )


    print()


    print(
        "Top defenses:"
    )


    print(
        players[
            players["position"]
            == "DEF"
        ][
            [
                "position_rank",
                "player",
                "team",
                "projected_points",
                "vor"
            ]
        ]
        .head(5)
        .to_string(
            index=False
        )
    )