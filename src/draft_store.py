import json
from pathlib import Path

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "data"
    / "league"
    / "draft_state.json"
)

LOCAL_KEEPERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "league"
    / "keepers.json"
)

LOCAL_SECRETS_FOLDER = (
    PROJECT_ROOT
    / ".streamlit"
    / "secrets"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# ============================================================
# CONFIGURATION
# ============================================================

def load_draft_config():
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

def get_google_credentials():

    local_keys = list(
        LOCAL_SECRETS_FOLDER.glob("*.json")
    )

    if local_keys:

        return Credentials.from_service_account_file(
            local_keys[0],
            scopes=SCOPES
        )

    if "gcp_service_account" in st.secrets:

        service_account_info = dict(
            st.secrets["gcp_service_account"]
        )

        return Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )

    raise RuntimeError(
        "Google service-account credentials were not found."
    )


# ============================================================
# GOOGLE SHEET CONNECTION
# ============================================================

def get_spreadsheet():

    config = load_draft_config()

    credentials = get_google_credentials()

    client = gspread.authorize(
        credentials
    )

    return client.open_by_url(
        config["spreadsheet_url"]
    )


def get_draft_worksheet():

    config = load_draft_config()

    spreadsheet = get_spreadsheet()

    return spreadsheet.worksheet(
        config["draft_history_worksheet"]
    )


def get_keepers_worksheet():

    config = load_draft_config()

    spreadsheet = get_spreadsheet()

    return spreadsheet.worksheet(
        config["keepers_worksheet"]
    )


# ============================================================
# DRAFT HISTORY
# ============================================================

def load_draft_history():
    """
    Load saved picks.

    This is backward-compatible with the older
    five-column draft-history format.
    """

    worksheet = get_draft_worksheet()

    records = worksheet.get_all_records()

    history = []


    for sequence_number, record in enumerate(
        records,
        start=1
    ):

        player = str(
            record.get("player", "")
        ).strip()

        if not player:
            continue


        raw_overall = record.get(
            "overall_pick",
            ""
        )


        if (
            raw_overall == ""
            or raw_overall is None
        ):

            overall_pick = None

        else:

            try:
                overall_pick = int(
                    raw_overall
                )

            except (TypeError, ValueError):
                overall_pick = None


        pick_type = str(
            record.get(
                "pick_type",
                ""
            )
        ).strip()


        if not pick_type:

            if overall_pick is None:
                pick_type = "supplemental"

            else:
                pick_type = "normal"


        pick_label = str(
            record.get(
                "pick_label",
                ""
            )
        ).strip()


        round_number = int(
            record["round"]
        )


        if not pick_label:

            if pick_type == "normal":
                pick_label = str(
                    overall_pick
                )

            else:
                pick_label = (
                    f"S{round_number}"
                )


        raw_pick_in_round = record.get(
            "pick_in_round",
            ""
        )


        if (
            raw_pick_in_round == ""
            or raw_pick_in_round is None
        ):

            pick_in_round = None

        else:

            try:
                pick_in_round = int(
                    raw_pick_in_round
                )

            except (TypeError, ValueError):
                pick_in_round = None


        history.append(
            {
                "sequence_number":
                    int(
                        record.get(
                            "sequence_number",
                            sequence_number
                        )
                    ),

                "pick_type":
                    pick_type,

                "pick_label":
                    pick_label,

                "overall_pick":
                    overall_pick,

                "round":
                    round_number,

                "pick_in_round":
                    pick_in_round,

                "owner":
                    str(
                        record["owner"]
                    ),

                "player":
                    player
            }
        )


    return history


def save_draft_history(history):
    """
    Save the complete authoritative draft history.

    Normal picks retain overall pick numbers.
    Supplemental picks use S1 / S2 / S3 labels.
    """

    worksheet = get_draft_worksheet()


    headers = [
        "sequence_number",
        "pick_type",
        "pick_label",
        "overall_pick",
        "round",
        "pick_in_round",
        "owner",
        "player"
    ]


    rows = [
        headers
    ]


    for sequence_number, pick in enumerate(
        history,
        start=1
    ):

        rows.append(
            [
                sequence_number,
                pick["pick_type"],
                pick["pick_label"],
                (
                    pick["overall_pick"]
                    if pick["overall_pick"]
                    is not None
                    else ""
                ),
                pick["round"],
                (
                    pick["pick_in_round"]
                    if pick["pick_in_round"]
                    is not None
                    else ""
                ),
                pick["owner"],
                pick["player"]
            ]
        )


    worksheet.clear()

    worksheet.update(
        values=rows,
        range_name="A1"
    )


def reset_draft_history():
    """
    Remove all draft selections while leaving
    the keeper worksheet completely untouched.
    """

    save_draft_history([])


# ============================================================
# KEEPERS
# ============================================================

def load_local_keepers():

    if not LOCAL_KEEPERS_FILE.exists():
        return []

    with open(
        LOCAL_KEEPERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        keeper_data = json.load(file)

    return keeper_data.get(
        "keepers",
        []
    )


def load_keepers():

    worksheet = get_keepers_worksheet()

    records = worksheet.get_all_records()

    keepers = []


    for record in records:

        owner = str(
            record.get(
                "owner",
                ""
            )
        ).strip()

        player = str(
            record.get(
                "player",
                ""
            )
        ).strip()


        if not owner or not player:
            continue


        keepers.append(
            {
                "owner": owner,
                "player": player
            }
        )


    if keepers:
        return keepers


    return load_local_keepers()


def save_keepers(keepers):

    worksheet = get_keepers_worksheet()


    headers = [
        "owner",
        "player"
    ]


    rows = [
        headers
    ]


    for keeper in keepers:

        owner = str(
            keeper["owner"]
        ).strip()

        player = str(
            keeper["player"]
        ).strip()


        if not owner or not player:
            continue


        rows.append(
            [
                owner,
                player
            ]
        )


    worksheet.clear()

    worksheet.update(
        values=rows,
        range_name="A1"
    )


# ============================================================
# CONNECTION TEST
# ============================================================

if __name__ == "__main__":

    draft_history = load_draft_history()

    keepers = load_keepers()

    print(
        "Google Sheets connection successful."
    )

    print(
        f"Saved draft picks found: "
        f"{len(draft_history)}"
    )

    print(
        f"Keepers found: "
        f"{len(keepers)}"
    )