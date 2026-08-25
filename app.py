import json
from pathlib import Path

import streamlit as st

from src.player_loader import load_player_rankings
from src.scoring_engine import calculate_score
from src.draft_engine import generate_draft_order


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Fantasy War Room",
    page_icon="🏈",
    layout="wide"
)


# ============================================================
# PATHS
# ============================================================

project_root = Path(__file__).resolve().parent

keepers_file = (
    project_root
    / "data"
    / "league"
    / "keepers.json"
)


# ============================================================
# LEAGUE / DRAFT CONFIGURATION
# ============================================================

owners = [
    "George",
    "Jeff",
    "Chris",
    "Kevin",
    "Paw",
    "Blake",
    "Cherie",
    "Brian",
    "Nate",
    "Scott"
]

number_of_rounds = 13

draft_order = generate_draft_order(
    owners=owners,
    rounds=number_of_rounds
)


# ============================================================
# LOAD PLAYER DATA
# ============================================================

players = load_player_rankings()


# Normalize position names from ranking sources.
players["position"] = (
    players["position"]
    .replace(
        {
            "K": "PK",
            "DST": "DEF",
            "D": "DEF"
        }
    )
)


# ============================================================
# LOAD KEEPERS
# ============================================================

with open(
    keepers_file,
    "r",
    encoding="utf-8"
) as file:

    keeper_data = json.load(file)


keepers = keeper_data["keepers"]


keeper_names = [
    keeper["player"]
    for keeper in keepers
]


scott_keeper_names = [
    keeper["player"]
    for keeper in keepers
    if keeper["owner"] == "Scott"
]


# ============================================================
# SESSION STATE
# ============================================================

if "draft_history" not in st.session_state:
    st.session_state.draft_history = []


draft_history = st.session_state.draft_history


drafted_names = [
    pick["player"]
    for pick in draft_history
]


scott_drafted_names = [
    pick["player"]
    for pick in draft_history
    if pick["owner"] == "Scott"
]


# ============================================================
# CURRENT DRAFT POSITION
# ============================================================

current_pick_index = len(draft_history)

draft_complete = (
    current_pick_index >= len(draft_order)
)


if not draft_complete:

    current_pick = draft_order[
        current_pick_index
    ]

    current_owner = current_pick["owner"]

    current_round = current_pick["round"]

    current_overall_pick = (
        current_pick["overall_pick"]
    )

    current_pick_in_round = (
        current_pick["pick_in_round"]
    )

else:

    current_pick = None
    current_owner = None


# ============================================================
# AVAILABLE PLAYER POOL
# ============================================================

unavailable_names = set(
    keeper_names + drafted_names
)


available_players = players[
    ~players["player"].isin(
        unavailable_names
    )
].copy()


# ============================================================
# SCOTT'S TEAM
# ============================================================

scott_team_names = (
    scott_keeper_names
    + scott_drafted_names
)


my_team = players[
    players["player"].isin(
        scott_team_names
    )
].copy()


# ============================================================
# HEADER
# ============================================================

st.title("🏈 Fantasy War Room")
st.subheader("2026 Draft Decision Engine")

st.write(
    "Live draft tracking, roster management, "
    "and player availability."
)


# ============================================================
# STATUS
# ============================================================

status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)


with status_col1:

    st.metric(
        "Scoring Engine",
        "ONLINE"
    )


with status_col2:

    st.metric(
        "Keepers Loaded",
        len(keeper_names)
    )


with status_col3:

    st.metric(
        "Draft Picks Recorded",
        len(draft_history)
    )


with status_col4:

    st.metric(
        "Players Remaining",
        len(available_players)
    )


st.divider()


# ============================================================
# CURRENT PICK
# ============================================================

st.subheader("🎯 Current Pick")


if not draft_complete:

    if current_owner == "Scott":

        st.warning(
            f"🔥 SCOTT IS ON THE CLOCK — "
            f"Round {current_round}, "
            f"Overall Pick #{current_overall_pick}"
        )

    else:

        st.info(
            f"Round {current_round} — "
            f"Overall Pick #{current_overall_pick}"
        )


    pick_col1, pick_col2, pick_col3 = (
        st.columns(3)
    )


    with pick_col1:

        st.metric(
            "On The Clock",
            current_owner
        )


    with pick_col2:

        st.metric(
            "Round",
            current_round
        )


    with pick_col3:

        st.metric(
            "Pick In Round",
            current_pick_in_round
        )


    # --------------------------------------------------------
    # HOW MANY PICKS UNTIL SCOTT?
    # --------------------------------------------------------

    future_scott_pick = None

    for future_pick in draft_order[
        current_pick_index:
    ]:

        if future_pick["owner"] == "Scott":
            future_scott_pick = future_pick
            break


    if future_scott_pick:

        picks_until_scott = (
            future_scott_pick[
                "overall_pick"
            ]
            - current_overall_pick
        )


        if current_owner != "Scott":

            st.caption(
                f"Scott is {picks_until_scott} "
                f"selection(s) away — "
                f"Overall Pick "
                f"#{future_scott_pick['overall_pick']}."
            )


    # --------------------------------------------------------
    # UPCOMING OWNERS
    # --------------------------------------------------------

    st.write("### Up Next")


    upcoming_picks = draft_order[
        current_pick_index + 1:
        current_pick_index + 4
    ]


    if upcoming_picks:

        upcoming_columns = st.columns(
            len(upcoming_picks)
        )


        for column, upcoming in zip(
            upcoming_columns,
            upcoming_picks
        ):

            with column:

                st.markdown(
                    f"**{upcoming['owner']}**"
                )

                st.caption(
                    f"Overall "
                    f"#{upcoming['overall_pick']}"
                )


    # --------------------------------------------------------
    # PLAYER SELECTION
    # --------------------------------------------------------

    draft_player_options = (
        available_players
        .sort_values("rank")["player"]
        .tolist()
    )


    selected_draft_player = st.selectbox(
        f"Player Drafted by {current_owner}",
        draft_player_options
    )


    button_col1, button_col2, button_col3 = (
        st.columns([1, 1, 4])
    )


    with button_col1:

        if st.button(
            "Record Pick",
            type="primary"
        ):

            st.session_state.draft_history.append(
                {
                    "overall_pick":
                        current_overall_pick,

                    "round":
                        current_round,

                    "pick_in_round":
                        current_pick_in_round,

                    "owner":
                        current_owner,

                    "player":
                        selected_draft_player
                }
            )

            st.rerun()


    with button_col2:

        if st.button(
            "Undo Last Pick"
        ):

            if st.session_state.draft_history:

                st.session_state.draft_history.pop()

                st.rerun()


else:

    st.success(
        "🏆 Draft Complete — "
        "all 130 selections have been recorded."
    )


# ============================================================
# LAST PICK
# ============================================================

if draft_history:

    last_pick = draft_history[-1]

    st.success(
        f"Last Pick: "
        f"#{last_pick['overall_pick']} — "
        f"{last_pick['owner']} selected "
        f"{last_pick['player']}"
    )


st.divider()


# ============================================================
# MY TEAM
# ============================================================

st.subheader("⭐ My Team")


if not my_team.empty:

    my_team = (
        my_team
        .sort_values(
            [
                "position",
                "rank"
            ]
        )
    )


    team_columns = st.columns(
        min(
            len(my_team),
            4
        )
    )


    for index, (_, player) in enumerate(
        my_team.iterrows()
    ):

        column = team_columns[
            index % len(team_columns)
        ]


        with column:

            if (
                player["player"]
                in scott_keeper_names
            ):

                keeper_marker = "⭐ "

            else:

                keeper_marker = ""


            st.markdown(
                f"### {keeper_marker}"
                f"{player['player']}"
            )


            st.write(
                f"{player['position_rank']} | "
                f"{player['team']}"
            )


            st.caption(
                f"Overall Rank "
                f"#{int(player['rank'])} | "
                f"Bye {int(player['bye'])}"
            )


else:

    st.warning(
        "Scott currently has no players."
    )


# ============================================================
# STARTING LINEUP NEEDS
# ============================================================

st.write("### Starting Lineup Needs")


roster_requirements = {
    "QB": 1,
    "RB": 2,
    "WR_TE": 3,
    "PK": 1,
    "DEF": 1
}


qb_count = len(
    my_team[
        my_team["position"] == "QB"
    ]
)


rb_count = len(
    my_team[
        my_team["position"] == "RB"
    ]
)


wr_te_count = len(
    my_team[
        my_team["position"].isin(
            [
                "WR",
                "TE"
            ]
        )
    ]
)


pk_count = len(
    my_team[
        my_team["position"] == "PK"
    ]
)


def_count = len(
    my_team[
        my_team["position"] == "DEF"
    ]
)


qb_needed = max(
    0,
    roster_requirements["QB"]
    - qb_count
)


rb_needed = max(
    0,
    roster_requirements["RB"]
    - rb_count
)


wr_te_needed = max(
    0,
    roster_requirements["WR_TE"]
    - wr_te_count
)


pk_needed = max(
    0,
    roster_requirements["PK"]
    - pk_count
)


def_needed = max(
    0,
    roster_requirements["DEF"]
    - def_count
)


need_col1, need_col2, need_col3, need_col4, need_col5 = (
    st.columns(5)
)


with need_col1:

    st.metric(
        "QB Needed",
        qb_needed
    )


with need_col2:

    st.metric(
        "RB Needed",
        rb_needed
    )


with need_col3:

    st.metric(
        "WR/TE Needed",
        wr_te_needed
    )


with need_col4:

    st.metric(
        "PK Needed",
        pk_needed
    )


with need_col5:

    st.metric(
        "DEF Needed",
        def_needed
    )


st.divider()


# ============================================================
# TOP AVAILABLE PLAYERS
# ============================================================

st.subheader("🏆 Top Available Players")


if not available_players.empty:

    top_overall = (
        available_players
        .sort_values("rank")
        .iloc[0]
    )


    st.markdown(
        f"### ⭐ Top Overall: "
        f"{top_overall['player']} "
        f"({top_overall['position']}) "
        f"— Rank #{int(top_overall['rank'])}"
    )


    st.write(
        f"Team: {top_overall['team']} | "
        f"ADP: {top_overall['average_adp']} | "
        f"Projected Points: "
        f"{top_overall['projected_points']}"
    )


st.write("### Top Player by Position")


position_list = [
    "QB",
    "RB",
    "WR",
    "TE",
    "PK",
    "DEF"
]


position_columns = st.columns(
    len(position_list)
)


for column, position in zip(
    position_columns,
    position_list
):

    position_players = (
        available_players[
            available_players["position"]
            == position
        ]
        .sort_values("rank")
    )


    if not position_players.empty:

        top_player = (
            position_players
            .iloc[0]
        )


        with column:

            st.markdown(
                f"**{position}**"
            )


            st.write(
                top_player["player"]
            )


            st.caption(
                f"Rank "
                f"#{int(top_player['rank'])} | "
                f"{top_player['team']} | "
                f"ADP "
                f"{top_player['average_adp']}"
            )


st.divider()


# ============================================================
# DRAFT HISTORY
# ============================================================

st.subheader("📋 Draft History")


if draft_history:

    for pick in draft_history:

        st.write(
            f"#{pick['overall_pick']} | "
            f"Round {pick['round']} | "
            f"{pick['owner']} — "
            f"{pick['player']}"
        )


else:

    st.caption(
        "Draft history is empty."
    )


st.divider()


# ============================================================
# AVAILABLE PLAYER FILTERS
# ============================================================

st.subheader("Available Players")


search_text = st.text_input(
    "Search Player",
    placeholder="Search available players"
)


position_options = [
    "ALL",
    "QB",
    "RB",
    "WR",
    "TE",
    "PK",
    "DEF"
]


selected_position = st.selectbox(
    "Position",
    position_options
)


filtered_players = (
    available_players.copy()
)


if selected_position != "ALL":

    filtered_players = filtered_players[
        filtered_players["position"]
        == selected_position
    ]


if search_text:

    filtered_players = filtered_players[
        filtered_players["player"]
        .str.contains(
            search_text,
            case=False,
            na=False
        )
    ]


st.write(
    f"Players shown: "
    f"{len(filtered_players)}"
)


# ============================================================
# PLAYER DETAILS
# ============================================================

st.subheader("Player Details")


player_options = (
    filtered_players["player"]
    .tolist()
)


if player_options:

    selected_player_name = st.selectbox(
        "Select Player",
        player_options
    )


    selected_player = (
        filtered_players[
            filtered_players["player"]
            == selected_player_name
        ]
        .iloc[0]
    )


    detail_col1, detail_col2, detail_col3, detail_col4 = (
        st.columns(4)
    )


    with detail_col1:

        st.metric(
            "Overall Rank",
            int(
                selected_player["rank"]
            )
        )

        st.metric(
            "Team",
            selected_player["team"]
        )


    with detail_col2:

        st.metric(
            "Position",
            selected_player[
                "position_rank"
            ]
        )

        st.metric(
            "Bye Week",
            int(
                selected_player["bye"]
            )
        )


    with detail_col3:

        st.metric(
            "Projected Points",
            selected_player[
                "projected_points"
            ]
        )

        st.metric(
            "Average ADP",
            selected_player[
                "average_adp"
            ]
        )


    with detail_col4:

        st.metric(
            "VOR",
            selected_player["vor"]
        )


else:

    st.warning(
        "No players match the current filters."
    )


st.divider()


# ============================================================
# PLAYER TABLE
# ============================================================

display_columns = [
    "rank",
    "player",
    "team",
    "position",
    "position_rank",
    "bye",
    "projected_points",
    "average_adp",
    "vor"
]


st.dataframe(
    filtered_players[
        display_columns
    ],
    width="stretch",
    hide_index=True
)


st.divider()


# ============================================================
# SCORING ENGINE TEST
# ============================================================

with st.expander(
    "Scoring Engine Test"
):

    test_stats = {
        "length_of_passing_td": [
            12,
            38,
            62
        ],
        "passing_yards": 345,
        "passing_interceptions_thrown": 1,
        "passing_two_point_conversions": 1,
        "number_of_rushing_tds": 1,
        "rushing_yards": 42
    }


    score = calculate_score(
        position="QB",
        stats=test_stats,
        show_breakdown=False
    )


    st.metric(
        "Hypothetical QB Score",
        score
    )


    if score == 33:

        st.success(
            "Scoring engine connected successfully."
        )

    else:

        st.error(
            "Scoring engine returned an unexpected result."
        )