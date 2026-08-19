import streamlit as st

from src.scoring_engine import calculate_score
from src.player_loader import load_player_rankings


st.set_page_config(
    page_title="Fantasy War Room",
    page_icon="🏈",
    layout="wide"
)


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


filtered_players = players.copy()


if selected_position != "ALL":
    filtered_players = filtered_players[
        filtered_players["position"] == selected_position
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
    filtered_players[display_columns],
    use_container_width=True,
    hide_index=True
)


st.divider()


# ------------------------------------------------------------
# SCORING ENGINE TEST
# ------------------------------------------------------------

with st.expander("Scoring Engine Test"):

    test_stats = {
        "length_of_passing_td": [12, 38, 62],
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