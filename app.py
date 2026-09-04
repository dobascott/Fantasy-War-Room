import streamlit as st

from src.player_loader import load_player_rankings
from src.scoring_engine import calculate_score
from src.draft_engine import (
    generate_draft_order,
    get_keeper_summary,
)
from src.draft_store import (
    load_draft_history,
    save_draft_history,
    reset_draft_history,
    load_keepers,
    save_keepers,
)
from src.recommendation_engine import (
    recommend_scott_pick,
)
from src.risk_engine import (
    load_player_risks,
    get_player_risk,
)


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Fantasy War Room",
    page_icon="🏈",
    layout="wide"
)


# ============================================================
# LEAGUE CONFIGURATION
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


# ============================================================
# LOAD PLAYER DATA
# ============================================================

players = load_player_rankings()

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

players = (
    players
    .sort_values("rank")
    .copy()
)

all_player_names = (
    players["player"]
    .tolist()
)


# ============================================================
# PLAYER RISK DATA
# ============================================================

player_risks = load_player_risks()


# ============================================================
# FLASH MESSAGE
# ============================================================

if "flash_message" not in st.session_state:

    st.session_state.flash_message = None


# ============================================================
# LOAD / CACHE KEEPERS
# ============================================================
#
# IMPORTANT:
#
# Google Sheets is read ONLY when this Streamlit
# session first starts.
#
# Every rerun after that uses the cached keeper list
# stored in st.session_state.
#
# This prevents rapid draft entry from exhausting
# the Google Sheets read-request quota.
# ============================================================

if "keepers" not in st.session_state:

    try:

        st.session_state.keepers = (
            load_keepers()
        )

        st.session_state.keeper_store_status = (
            "CONNECTED"
        )

        st.session_state.keeper_store_error = (
            None
        )

    except Exception as error:

        st.session_state.keepers = []

        st.session_state.keeper_store_status = (
            "ERROR"
        )

        st.session_state.keeper_store_error = (
            str(error)
        )


keepers = st.session_state.keepers


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
# GENERATE DRAFT ORDER
# ============================================================

draft_order = generate_draft_order(
    owners=owners,
    rounds=number_of_rounds,
    keepers=keepers
)


keeper_summary = get_keeper_summary(
    owners=owners,
    keepers=keepers
)


# ============================================================
# LOAD / CACHE DRAFT HISTORY
# ============================================================

if "draft_history" not in st.session_state:

    try:

        st.session_state.draft_history = (
            load_draft_history()
        )

        st.session_state.draft_store_status = (
            "CONNECTED"
        )

        st.session_state.draft_store_error = (
            None
        )

    except Exception as error:

        st.session_state.draft_history = []

        st.session_state.draft_store_status = (
            "ERROR"
        )

        st.session_state.draft_store_error = (
            str(error)
        )


draft_history = (
    st.session_state.draft_history
)


# ============================================================
# DRAFTED PLAYERS
# ============================================================

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

current_sequence_index = len(
    draft_history
)


draft_complete = (
    current_sequence_index
    >= len(draft_order)
)


if not draft_complete:

    current_pick = (
        draft_order[
            current_sequence_index
        ]
    )

    current_owner = (
        current_pick["owner"]
    )

    current_round = (
        current_pick["round"]
    )

else:

    current_pick = None
    current_owner = None
    current_round = None


# ============================================================
# AVAILABLE PLAYER POOL
# ============================================================

unavailable_names = set(
    keeper_names
    + drafted_names
)


available_players = players[
    ~players["player"].isin(
        unavailable_names
    )
].copy()


# ============================================================
# SCOTT TEAM
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

st.title(
    "🏈 Fantasy War Room"
)

st.subheader(
    "2026 Draft Decision Engine"
)

st.write(
    "Live draft tracking, keeper management, "
    "roster management, supplemental picks, "
    "recommendations, and persistent draft state."
)


# ============================================================
# STATUS
# ============================================================

status1, status2, status3, status4, status5 = (
    st.columns(5)
)


with status1:

    st.metric(
        "Scoring Engine",
        "ONLINE"
    )


with status2:

    st.metric(
        "Keepers Loaded",
        len(keeper_names)
    )


with status3:

    st.metric(
        "Draft Picks Recorded",
        len(draft_history)
    )


with status4:

    st.metric(
        "Players Remaining",
        len(available_players)
    )


with status5:

    st.metric(
        "Draft State",
        st.session_state.draft_store_status
    )


# ============================================================
# STORAGE ERRORS
# ============================================================

if (
    st.session_state.keeper_store_status
    == "ERROR"
):

    st.error(
        "Keeper storage error: "
        f"{st.session_state.keeper_store_error}"
    )


if (
    st.session_state.draft_store_status
    == "ERROR"
):

    st.error(
        "Draft storage error: "
        f"{st.session_state.draft_store_error}"
    )


# ============================================================
# FLASH MESSAGE
# ============================================================

if st.session_state.flash_message:

    st.success(
        st.session_state.flash_message
    )

    st.session_state.flash_message = (
        None
    )


st.divider()


# ============================================================
# LEAGUE KEEPERS
# ============================================================

with st.expander(
    "🔒 League Keepers — View / Edit",
    expanded=False
):

    st.write(
        "Each team may keep up to three players."
    )

    st.caption(
        "Unused keeper slots automatically create "
        "supplemental picks: S1, S2 and/or S3."
    )


    existing_by_owner = {
        owner: []
        for owner in owners
    }


    for keeper in keepers:

        owner = keeper["owner"]
        player = keeper["player"]

        if owner in existing_by_owner:

            existing_by_owner[
                owner
            ].append(
                player
            )


    keeper_selections = {}


    for owner in owners:

        st.markdown(
            f"### {owner}"
        )

        keeper_columns = (
            st.columns(3)
        )

        keeper_selections[
            owner
        ] = []


        current_owner_keepers = (
            existing_by_owner.get(
                owner,
                []
            )
        )


        for slot in range(3):

            current_player = ""


            if slot < len(
                current_owner_keepers
            ):

                current_player = (
                    current_owner_keepers[
                        slot
                    ]
                )


            options = (
                ["-- None --"]
                + all_player_names
            )


            if (
                current_player
                and current_player
                in options
            ):

                default_index = (
                    options.index(
                        current_player
                    )
                )

            else:

                default_index = 0


            with keeper_columns[slot]:

                selection = (
                    st.selectbox(
                        f"Keeper "
                        f"{slot + 1}",
                        options,
                        index=default_index,
                        key=(
                            f"keeper_"
                            f"{owner}_"
                            f"{slot}"
                        )
                    )
                )


            if (
                selection
                != "-- None --"
            ):

                keeper_selections[
                    owner
                ].append(
                    selection
                )


        keeper_count = len(
            keeper_selections[
                owner
            ]
        )


        if keeper_count == 3:

            st.caption(
                "Supplemental picks: None"
            )

        elif keeper_count == 2:

            st.caption(
                "Supplemental picks: S3"
            )

        elif keeper_count == 1:

            st.caption(
                "Supplemental picks: S2, S3"
            )

        else:

            st.caption(
                "Supplemental picks: S1, S2, S3"
            )


        st.divider()


    # --------------------------------------------------------
    # SAVE KEEPERS
    # --------------------------------------------------------

    if st.button(
        "Save League Keepers",
        type="primary"
    ):

        new_keeper_list = []

        player_owners = {}


        for owner in owners:

            for player_name in (
                keeper_selections[
                    owner
                ]
            ):

                new_keeper_list.append(
                    {
                        "owner":
                            owner,

                        "player":
                            player_name
                    }
                )


                if (
                    player_name
                    not in player_owners
                ):

                    player_owners[
                        player_name
                    ] = []


                player_owners[
                    player_name
                ].append(
                    owner
                )


        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        duplicate_details = []


        for (
            player_name,
            assigned_owners
        ) in player_owners.items():

            if (
                len(
                    assigned_owners
                ) > 1
            ):

                duplicate_details.append(
                    f"{player_name}: "
                    + ", ".join(
                        assigned_owners
                    )
                )


        selected_players = list(
            player_owners.keys()
        )


        # ----------------------------------------------------
        # KEEPER / DRAFT CONFLICT CHECK
        # ----------------------------------------------------

        keeper_drafted_conflicts = (
            sorted(
                set(
                    selected_players
                )
                & set(
                    drafted_names
                )
            )
        )


        if duplicate_details:

            st.error(
                "A player cannot be kept by "
                "more than one team. "
                "Duplicate assignment(s): "
                + " | ".join(
                    duplicate_details
                )
            )


        elif keeper_drafted_conflicts:

            st.error(
                "These players already appear "
                "in Draft History and cannot "
                "also be keepers: "
                + ", ".join(
                    keeper_drafted_conflicts
                )
            )


        else:

            try:

                save_keepers(
                    new_keeper_list
                )

                # IMPORTANT:
                #
                # Update our LOCAL SESSION CACHE immediately.
                # We do NOT reread Google Sheets.
                st.session_state.keepers = (
                    new_keeper_list
                )

                st.session_state.keeper_store_status = (
                    "CONNECTED"
                )

                st.session_state.keeper_store_error = (
                    None
                )

                st.session_state.flash_message = (
                    "League keepers saved. "
                    f"{len(new_keeper_list)} "
                    "keepers loaded."
                )

                st.rerun()


            except Exception as error:

                st.session_state.keeper_store_status = (
                    "ERROR"
                )

                st.session_state.keeper_store_error = (
                    str(error)
                )

                st.error(
                    "Keeper save failed."
                )

                st.exception(
                    error
                )


st.divider()


# ============================================================
# SUPPLEMENTAL PICK SUMMARY
# ============================================================

with st.expander(
    "➕ Supplemental Pick Summary",
    expanded=False
):

    for team in keeper_summary:

        supplemental = (
            team[
                "supplemental_picks"
            ]
        )


        if supplemental:

            supplemental_text = (
                ", ".join(
                    supplemental
                )
            )

        else:

            supplemental_text = (
                "None"
            )


        st.write(
            f"**{team['owner']}** — "
            f"{team['keeper_count']} keepers — "
            f"Supplemental: "
            f"{supplemental_text}"
        )


st.divider()


# ============================================================
# CURRENT PICK
# ============================================================

st.subheader(
    "🎯 Current Pick"
)


if not draft_complete:

    # --------------------------------------------------------
    # SUPPLEMENTAL PICK
    # --------------------------------------------------------

    if (
        current_pick["pick_type"]
        == "supplemental"
    ):

        st.warning(
            f"➕ SUPPLEMENTAL PICK "
            f"{current_pick['pick_label']} — "
            f"{current_owner} is on the clock"
        )

        st.caption(
            f"End of Round "
            f"{current_round}"
        )


    # --------------------------------------------------------
    # SCOTT NORMAL PICK
    # --------------------------------------------------------

    elif current_owner == "Scott":

        st.warning(
            f"🔥 SCOTT IS ON THE CLOCK — "
            f"Round "
            f"{current_round}, "
            f"Overall Pick "
            f"#{current_pick['overall_pick']}"
        )


    # --------------------------------------------------------
    # OTHER NORMAL PICK
    # --------------------------------------------------------

    else:

        st.info(
            f"Round "
            f"{current_round} — "
            f"Overall Pick "
            f"#{current_pick['overall_pick']}"
        )


    # --------------------------------------------------------
    # PICK METRICS
    # --------------------------------------------------------

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
            "Pick",
            current_pick[
                "pick_label"
            ]
        )


    # ========================================================
    # SCOTT RECOMMENDATIONS
    # ========================================================

    if current_owner == "Scott":

        recommendations = (
            recommend_scott_pick(
                available_players=(
                    available_players
                ),
                my_team=my_team,
                current_round=(
                    current_round
                ),
                current_sequence_index=(
                    current_sequence_index
                ),
                draft_order=(
                    draft_order
                ),
                top_n=5
            )
        )


        st.write(
            "### 🔥 Scott Recommendations"
        )


        for number, recommendation in enumerate(
            recommendations,
            start=1
        ):

            st.markdown(
    f"### {number}. "
    f"{recommendation['player']} "
    f"({recommendation['position']} — "
    f"{recommendation['team']})"
)


            player_risk = get_player_risk(
                recommendation["player"],
                player_risks
            )

            if player_risk:

                risk_level = player_risk.get(
                    "level",
                    "INFO"
                ).upper()

                risk_category = player_risk.get(
                    "category",
                    "STATUS"
                ).upper()

                risk_summary = player_risk.get(
                    "summary",
                    "Risk note available."
                )

                risk_source = player_risk.get(
                    "source",
                    ""
                )

                risk_updated = player_risk.get(
                    "updated",
                    ""
                )

                risk_message = (
                    f"{risk_category} — "
                    f"{risk_summary}"
                )

                if risk_level == "HIGH":
                    st.error(
                        f"🚨 HIGH RISK: {risk_message}"
                    )

                elif risk_level == "MEDIUM":
                    st.warning(
                        f"⚠️ MEDIUM RISK: {risk_message}"
                    )

                else:
                    st.info(
                        f"ℹ️ {risk_level} RISK: "
                        f"{risk_message}"
                    )

                source_parts = [
                    item
                    for item in [
                        risk_source,
                        risk_updated
                    ]
                    if item
                ]

                if source_parts:
                    st.caption(
                        "Risk source: "
                        + " | ".join(source_parts)
                    )


            st.write(
                f"Rank #{recommendation['rank']} | "
                f"{recommendation['position_rank']} | "
                f"ADP {recommendation['average_adp']} | "
                f"VOR {recommendation['vor']}"
            )

            st.write(
                f"Wait Risk: {recommendation['wait_risk']} | "
                f"Wait Cost: {recommendation['wait_cost']} | "
                f"Likely Replacement: "
                f"{recommendation['replacement_player']}"
            )

            if recommendation["gem_label"]:
                st.write(
                    f"💎 Market Value: "
                    f"{recommendation['gem_label']}"
                )

            st.write(
                f"Recommendation Score: "
                f"{recommendation['recommendation_score']}"
            )


            if recommendation[
                "reasons"
            ]:

                for reason in (
                    recommendation[
                        "reasons"
                    ]
                ):

                    st.caption(
                        f"• {reason}"
                    )


            st.divider()


    # ========================================================
    # DISTANCE UNTIL NEXT SCOTT PICK
    # ========================================================

    future_scott_pick = None
    future_scott_index = None


    for future_index in range(
        current_sequence_index,
        len(draft_order)
    ):

        future_pick = (
            draft_order[
                future_index
            ]
        )


        if (
            future_pick["owner"]
            == "Scott"
        ):

            future_scott_pick = (
                future_pick
            )

            future_scott_index = (
                future_index
            )

            break


    if (
        future_scott_pick
        and current_owner
        != "Scott"
    ):

        selections_until_scott = (
            future_scott_index
            - current_sequence_index
        )


        st.caption(
            f"Scott is "
            f"{selections_until_scott} "
            f"selection(s) away — "
            f"Pick "
            f"{future_scott_pick['pick_label']}."
        )


    # ========================================================
    # UP NEXT
    # ========================================================

    st.write(
        "### Up Next"
    )


    upcoming_picks = (
        draft_order[
            current_sequence_index + 1:
            current_sequence_index + 4
        ]
    )


    if upcoming_picks:

        upcoming_columns = (
            st.columns(
                len(
                    upcoming_picks
                )
            )
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
                    f"Pick "
                    f"{upcoming['pick_label']}"
                )


    # ========================================================
    # PLAYER SELECTION
    # ========================================================

    draft_player_options = (
        available_players
        .sort_values("rank")[
            "player"
        ]
        .tolist()
    )


    selected_draft_player = (
        st.selectbox(
            f"Player Drafted by "
            f"{current_owner}",
            draft_player_options
        )
    )


    button1, button2, spacer = (
        st.columns(
            [1, 1, 4]
        )
    )


    # ========================================================
    # RECORD PICK
    # ========================================================

    with button1:

        if st.button(
            "Record Pick",
            type="primary"
        ):

            new_pick = {
                "sequence_number":
                    current_pick[
                        "sequence_number"
                    ],

                "pick_type":
                    current_pick[
                        "pick_type"
                    ],

                "pick_label":
                    current_pick[
                        "pick_label"
                    ],

                "overall_pick":
                    current_pick[
                        "overall_pick"
                    ],

                "round":
                    current_pick[
                        "round"
                    ],

                "pick_in_round":
                    current_pick[
                        "pick_in_round"
                    ],

                "owner":
                    current_owner,

                "player":
                    selected_draft_player
            }


            st.session_state.draft_history.append(
                new_pick
            )


            try:

                save_draft_history(
                    st.session_state.draft_history
                )

                st.session_state.draft_store_status = (
                    "CONNECTED"
                )

                st.session_state.draft_store_error = (
                    None
                )

                st.session_state.flash_message = (
                    f"Pick "
                    f"{current_pick['pick_label']} "
                    f"saved: "
                    f"{current_owner} selected "
                    f"{selected_draft_player}."
                )

                st.rerun()


            except Exception as error:

                # Roll back local state if
                # persistence fails.
                st.session_state.draft_history.pop()

                st.session_state.draft_store_status = (
                    "ERROR"
                )

                st.session_state.draft_store_error = (
                    str(error)
                )

                st.error(
                    "Pick was NOT saved."
                )

                st.exception(
                    error
                )


    # ========================================================
    # UNDO LAST PICK
    # ========================================================

    with button2:

        if st.button(
            "Undo Last Pick"
        ):

            if (
                st.session_state
                .draft_history
            ):

                removed_pick = (
                    st.session_state
                    .draft_history
                    .pop()
                )


                try:

                    save_draft_history(
                        st.session_state
                        .draft_history
                    )

                    st.session_state.draft_store_status = (
                        "CONNECTED"
                    )

                    st.session_state.draft_store_error = (
                        None
                    )

                    st.session_state.flash_message = (
                        f"Undid Pick "
                        f"{removed_pick['pick_label']}: "
                        f"{removed_pick['owner']} — "
                        f"{removed_pick['player']}."
                    )

                    st.rerun()


                except Exception as error:

                    # Restore local state if the
                    # Google update fails.
                    st.session_state.draft_history.append(
                        removed_pick
                    )

                    st.session_state.draft_store_status = (
                        "ERROR"
                    )

                    st.session_state.draft_store_error = (
                        str(error)
                    )

                    st.error(
                        "Undo failed."
                    )

                    st.exception(
                        error
                    )


else:

    st.success(
        "🏆 Draft Complete."
    )


st.divider()


# ============================================================
# RESET DRAFT
# ============================================================

with st.expander(
    "🔄 Reset Draft",
    expanded=False
):

    st.warning(
        "Reset Draft removes ALL recorded "
        "draft selections but leaves every "
        "keeper unchanged."
    )

    st.write(
        "Use this after a practice draft "
        "to return Fantasy War Room to the "
        "keeper-only starting state."
    )


    confirm_reset = st.checkbox(
        "I understand that all recorded "
        "draft picks will be erased."
    )


    if st.button(
        "Reset Draft Now",
        disabled=(
            not confirm_reset
        )
    ):

        try:

            reset_draft_history()

            # Clear only draft picks.
            #
            # Keeper cache remains untouched.
            st.session_state.draft_history = []

            st.session_state.draft_store_status = (
                "CONNECTED"
            )

            st.session_state.draft_store_error = (
                None
            )

            st.session_state.flash_message = (
                "Draft reset successfully. "
                "All keepers remain loaded."
            )

            st.rerun()


        except Exception as error:

            st.session_state.draft_store_status = (
                "ERROR"
            )

            st.session_state.draft_store_error = (
                str(error)
            )

            st.error(
                "Draft reset failed."
            )

            st.exception(
                error
            )


st.divider()


# ============================================================
# MY TEAM
# ============================================================

st.subheader(
    "⭐ My Team"
)


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


    for _, player in (
        my_team.iterrows()
    ):

        keeper_marker = ""


        if (
            player["player"]
            in scott_keeper_names
        ):

            keeper_marker = (
                "⭐ Keeper"
            )


        st.write(
            f"**{player['position_rank']} — "
            f"{player['player']}** "
            f"({player['team']}) "
            f"{keeper_marker}"
        )


else:

    st.caption(
        "No players assigned."
    )


# ============================================================
# STARTING LINEUP NEEDS
# ============================================================

st.write(
    "### Starting Lineup Needs"
)


qb_count = len(
    my_team[
        my_team["position"]
        == "QB"
    ]
)


rb_count = len(
    my_team[
        my_team["position"]
        == "RB"
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
        my_team["position"]
        == "PK"
    ]
)


def_count = len(
    my_team[
        my_team["position"]
        == "DEF"
    ]
)


needs = {
    "QB":
        max(
            0,
            1 - qb_count
        ),

    "RB":
        max(
            0,
            2 - rb_count
        ),

    "WR/TE":
        max(
            0,
            3 - wr_te_count
        ),

    "PK":
        max(
            0,
            1 - pk_count
        ),

    "DEF":
        max(
            0,
            1 - def_count
        )
}


need_columns = (
    st.columns(5)
)


for column, (
    position,
    need
) in zip(
    need_columns,
    needs.items()
):

    with column:

        st.metric(
            f"{position} Needed",
            need
        )


st.divider()


# ============================================================
# TOP AVAILABLE PLAYERS
# ============================================================

st.subheader(
    "🏆 Top Available Players"
)


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
        f"— Rank "
        f"#{int(top_overall['rank'])}"
    )


position_list = [
    "QB",
    "RB",
    "WR",
    "TE",
    "PK",
    "DEF"
]


position_columns = (
    st.columns(
        len(position_list)
    )
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
                top_player[
                    "player"
                ]
            )

            st.caption(
                f"Rank "
                f"#{int(top_player['rank'])}"
            )


st.divider()


# ============================================================
# TEAM ROSTERS
# ============================================================

with st.expander(
    "👥 Team Rosters",
    expanded=False
):

    st.write(
        "Each roster contains that owner's "
        "keepers plus all recorded draft picks."
    )


    for owner in owners:

        owner_keeper_names = [
            keeper["player"]
            for keeper in keepers
            if keeper["owner"]
            == owner
        ]


        owner_drafted_names = [
            pick["player"]
            for pick in draft_history
            if pick["owner"]
            == owner
        ]


        roster_names = (
            owner_keeper_names
            + owner_drafted_names
        )


        st.markdown(
            f"### {owner}"
        )


        if roster_names:

            roster_players = players[
                players["player"].isin(
                    roster_names
                )
            ].copy()


            roster_players = (
                roster_players
                .sort_values(
                    [
                        "position",
                        "rank"
                    ]
                )
            )


            qb_total = len(
                roster_players[
                    roster_players["position"]
                    == "QB"
                ]
            )


            rb_total = len(
                roster_players[
                    roster_players["position"]
                    == "RB"
                ]
            )


            wr_te_total = len(
                roster_players[
                    roster_players["position"].isin(
                        [
                            "WR",
                            "TE"
                        ]
                    )
                ]
            )


            pk_total = len(
                roster_players[
                    roster_players["position"]
                    == "PK"
                ]
            )


            def_total = len(
                roster_players[
                    roster_players["position"]
                    == "DEF"
                ]
            )


            st.caption(
                f"Players: "
                f"{len(roster_players)} | "
                f"QB {qb_total} | "
                f"RB {rb_total} | "
                f"WR/TE {wr_te_total} | "
                f"PK {pk_total} | "
                f"DEF {def_total}"
            )


            for _, player in (
                roster_players.iterrows()
            ):

                keeper_label = ""


                if (
                    player["player"]
                    in owner_keeper_names
                ):

                    keeper_label = (
                        " ⭐ Keeper"
                    )


                st.write(
                    f"{player['position_rank']} — "
                    f"{player['player']} "
                    f"({player['team']})"
                    f"{keeper_label}"
                )


        else:

            st.caption(
                "No players assigned."
            )


        st.divider()


# ============================================================
# DRAFT HISTORY
# ============================================================

with st.expander(
    "📋 Draft History",
    expanded=False
):

    if draft_history:

        for pick in draft_history:

            st.write(
                f"**{pick['pick_label']}** | "
                f"Round "
                f"{pick['round']} | "
                f"{pick['owner']} — "
                f"{pick['player']}"
            )


    else:

        st.caption(
            "Draft history is empty."
        )


st.divider()


# ============================================================
# PLAYER BROWSER
# ============================================================

st.subheader(
    "Available Players"
)


search_text = st.text_input(
    "Search Player"
)


position_filter = st.selectbox(
    "Position",
    [
        "ALL",
        "QB",
        "RB",
        "WR",
        "TE",
        "PK",
        "DEF"
    ]
)


filtered_players = (
    available_players.copy()
)


if position_filter != "ALL":

    filtered_players = (
        filtered_players[
            filtered_players["position"]
            == position_filter
        ]
    )


if search_text:

    filtered_players = (
        filtered_players[
            filtered_players["player"]
            .str.contains(
                search_text,
                case=False,
                na=False
            )
        ]
    )


st.write(
    f"Players shown: "
    f"{len(filtered_players)}"
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
    filtered_players[
        display_columns
    ],
    width="stretch",
    hide_index=True
)


# ============================================================
# SCORING ENGINE CHECK
# ============================================================

with st.expander(
    "Scoring Engine Test"
):

    test_stats = {
        "length_of_passing_td":
            [
                12,
                38,
                62
            ],

        "passing_yards":
            345,

        "passing_interceptions_thrown":
            1,

        "passing_two_point_conversions":
            1,

        "number_of_rushing_tds":
            1,

        "rushing_yards":
            42
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
            "Unexpected scoring result."
        )