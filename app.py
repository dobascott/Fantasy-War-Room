import streamlit as st

from src.scoring_engine import calculate_score
from src.player_loader import load_player_rankings


st.set_page_config(
    page_title="Fantasy War Room",
    page_icon="🏈",
    layout="wide"
)


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🏈 Fantasy War Room")
st.subheader("2026 Draft Decision Engine")

st.write(
    "Fantasy War Room is online and connected to the scoring engine."
)


# ------------------------------------------------------------
# SYSTEM STATUS
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Scoring Engine",
        value="ONLINE"
    )

with col2:
    st.metric(
        label="Positions Tested",
        value="5 / 5"
    )

with col3:
    st.metric(
        label="Draft Status",
        value="BUILDING"
    )


st.divider()


# ------------------------------------------------------------
# LOAD PLAYER DATA
# ------------------------------------------------------------

players = load_player_rankings()


# ------------------------------------------------------------
# TOP AVAILABLE PLAYERS
# ------------------------------------------------------------

st.subheader("Top Available Players")


top_overall = (
    players
    .sort_values("rank")
    .iloc[0]
)


st.markdown(
    f"### ⭐ Top Overall: {top_overall['player']} "
    f"({top_overall['position']}) — Rank #{int(top_overall['rank'])}"
)

st.write(
    f"Team: {top_overall['team']} | "
    f"ADP: {top_overall['average_adp']} | "
    f"Projected Points: {top_overall['projected_points']}"
)


st.write("### Top Player by Position")


position_list = [
    "QB",
    "RB",
    "WR",
    "TE"
]


position_columns = st.columns(
    len(position_list)
)


for column, position in zip(
    position_columns,
    position_list
):

    position_players = (
        players[
            players["position"] == position
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
                f"Rank #{int(top_player['rank'])} | "
                f"{top_player['team']} | "
                f"ADP {top_player['average_adp']}"
            )


st.divider()


# ------------------------------------------------------------
# AVAILABLE PLAYER FILTERS
# ------------------------------------------------------------

st.subheader("Available Players")


search_text = st.text_input(
    "Search Player",
    placeholder="Josh Allen"
)


position_options = [
    "ALL",
    "QB",
    "RB",
    "WR",
    "TE"
]


selected_position = st.selectbox(
    "Position",
    position_options
)


filtered_players = (
    players.copy()
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
    f"Players shown: {len(filtered_players)}"
)


# ------------------------------------------------------------
# PLAYER DETAILS
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# PLAYER TABLE
# ------------------------------------------------------------

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
    use_container_width=True,
    hide_index=True
)


st.divider()


# ------------------------------------------------------------
# SCORING ENGINE TEST
# ------------------------------------------------------------

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
        label="Hypothetical QB Score",
        value=score
    )


    if score == 33:

        st.success(
            "Scoring engine connected successfully."
        )

    else:

        st.error(
            "Scoring engine returned an unexpected result."
        )