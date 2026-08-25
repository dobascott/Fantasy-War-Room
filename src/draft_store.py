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

LOCAL_SECRETS_FOLDER = (
    PROJECT_ROOT
    / ".streamlit"
    / "secrets"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


def load_draft_config():
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_google_credentials():
    """
    Locally:
        Use the protected Google service-account JSON file.

    Streamlit Cloud:
        Use credentials stored in Streamlit Secrets.
    """

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


def get_draft_worksheet():
    config = load_draft_config()

    credentials = get_google_credentials()

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open_by_url(
        config["spreadsheet_url"]
    )

    worksheet = spreadsheet.worksheet(
        config["worksheet"]
    )

    return worksheet


def load_draft_history():
    """
    Read all saved draft picks from Google Sheets.
    """

    worksheet = get_draft_worksheet()

    records = worksheet.get_all_records()

    history = []

    for record in records:
        if not record.get("player"):
            continue

        history.append(
            {
                "overall_pick": int(
                    record["overall_pick"]
                ),
                "round": int(
                    record["round"]
                ),
                "pick_in_round": int(
                    record["pick_in_round"]
                ),
                "owner": str(
                    record["owner"]
                ),
                "player": str(
                    record["player"]
                )
            }
        )

    return history


def save_draft_history(history):
    """
    Replace the Google Sheet contents with the
    current authoritative draft history.
    """

    worksheet = get_draft_worksheet()

    headers = [
        "overall_pick",
        "round",
        "pick_in_round",
        "owner",
        "player"
    ]

    rows = [headers]

    for pick in history:
        rows.append(
            [
                pick["overall_pick"],
                pick["round"],
                pick["pick_in_round"],
                pick["owner"],
                pick["player"]
            ]
        )

    worksheet.clear()

    worksheet.update(
        values=rows,
        range_name="A1"
    )


if __name__ == "__main__":
    history = load_draft_history()

    print("Google Sheets connection successful.")
    print(f"Saved picks found: {len(history)}")