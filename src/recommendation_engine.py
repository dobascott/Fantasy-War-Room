
import math


# ============================================================
# LEAGUE STARTER REQUIREMENTS
# ============================================================

STARTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR_TE": 3,
    "PK": 1,
    "DEF": 1,
}


# ============================================================
# SAFE NUMBER HANDLING
# ============================================================

def safe_number(value, default=0.0):
    try:
        number = float(value)

        if math.isnan(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


# ============================================================
# ROSTER COUNTS
# ============================================================

def get_roster_counts(roster):

    counts = {
        "QB": 0,
        "RB": 0,
        "WR": 0,
        "TE": 0,
        "WR_TE": 0,
        "PK": 0,
        "DEF": 0,
    }

    for _, player in roster.iterrows():

        position = player["position"]

        if position in counts:
            counts[position] += 1

        if position in ["WR", "TE"]:
            counts["WR_TE"] += 1

    return counts


# ============================================================
# BYE COUNTS
# ============================================================

def get_bye_week_counts(roster):

    bye_counts = {}

    for _, player in roster.iterrows():

        bye = safe_number(
            player.get("bye", 0),
            default=0
        )

        if bye <= 0:
            continue

        bye = int(bye)

        bye_counts[bye] = (
            bye_counts.get(bye, 0) + 1
        )

    return bye_counts


# ============================================================
# STARTER NEED
# ============================================================

def get_starter_need(position, counts):

    if position == "QB":
        return max(
            0,
            1 - counts["QB"]
        )

    if position == "RB":
        return max(
            0,
            2 - counts["RB"]
        )

    if position in ["WR", "TE"]:
        return max(
            0,
            3 - counts["WR_TE"]
        )

    if position == "PK":
        return max(
            0,
            1 - counts["PK"]
        )

    if position == "DEF":
        return max(
            0,
            1 - counts["DEF"]
        )

    return 0


# ============================================================
# LINEUP STATUS
# ============================================================

def core_lineup_complete(counts):

    return (
        counts["QB"] >= 1
        and counts["RB"] >= 2
        and counts["WR_TE"] >= 3
    )


def weekly_lineup_complete_except_defense(counts):

    return (
        counts["QB"] >= 1
        and counts["RB"] >= 2
        and counts["WR_TE"] >= 3
        and counts["PK"] >= 1
    )


# ============================================================
# ROUND 1 STARTER ELIGIBILITY
# ============================================================

def is_round_one_starter_eligible(position, counts):

    if position == "QB":
        return counts["QB"] < 1

    if position == "RB":
        return counts["RB"] < 2

    if position in ["WR", "TE"]:
        return counts["WR_TE"] < 3

    return False


# ============================================================
# FUTURE SCOTT PICKS
# ============================================================

def find_future_scott_picks(
    draft_order,
    current_sequence_index,
    number_of_future_picks=2
):

    future_scott_picks = []

    for future_index in range(
        current_sequence_index + 1,
        len(draft_order)
    ):

        future_pick = draft_order[future_index]

        if future_pick["owner"] == "Scott":

            future_scott_picks.append(
                {
                    "index": future_index,
                    "pick": future_pick,
                    "selections_away":
                        future_index
                        - current_sequence_index,
                }
            )

            if (
                len(future_scott_picks)
                >= number_of_future_picks
            ):
                break

    return future_scott_picks


# ============================================================
# POSITION POOL
# ============================================================

def get_position_pool(
    available_players,
    position
):

    return (
        available_players[
            available_players["position"]
            == position
        ]
        .sort_values("rank")
        .reset_index(drop=True)
    )


# ============================================================
# POSITION RUN RATE
# ============================================================

def get_position_run_rate(
    position,
    current_round
):

    if current_round <= 2:

        rates = {
            "QB": 0.16,
            "RB": 0.30,
            "WR": 0.34,
            "TE": 0.12,
            "PK": 0.03,
            "DEF": 0.00,
        }

    elif current_round <= 4:

        rates = {
            "QB": 0.15,
            "RB": 0.27,
            "WR": 0.31,
            "TE": 0.12,
            "PK": 0.08,
            "DEF": 0.00,
        }

    elif current_round <= 8:

        rates = {
            "QB": 0.12,
            "RB": 0.25,
            "WR": 0.29,
            "TE": 0.11,
            "PK": 0.08,
            "DEF": 0.05,
        }

    else:

        rates = {
            "QB": 0.10,
            "RB": 0.23,
            "WR": 0.27,
            "TE": 0.10,
            "PK": 0.08,
            "DEF": 0.12,
        }

    return rates.get(position, 0.20)


# ============================================================
# PROJECTED REPLACEMENT
# ============================================================

def get_projected_replacement(
    player,
    available_players,
    selections_away,
    current_round
):

    position = player["position"]

    position_pool = get_position_pool(
        available_players,
        position
    )

    if position_pool.empty:
        return None

    names = position_pool["player"].tolist()

    player_name = player["player"]

    if player_name not in names:
        return None

    current_position_index = (
        names.index(player_name)
    )

    run_rate = get_position_run_rate(
        position,
        current_round
    )

    estimated_position_picks = max(
        1,
        round(
            selections_away
            * run_rate
        )
    )

    replacement_index = min(
        current_position_index
        + estimated_position_picks,
        len(position_pool) - 1
    )

    return position_pool.iloc[
        replacement_index
    ]


# ============================================================
# PLAYER DROP
# ============================================================

def calculate_player_drop(
    current_player,
    replacement_player
):

    if replacement_player is None:
        return 0.0

    current_vor = safe_number(
        current_player["vor"],
        0
    )

    replacement_vor = safe_number(
        replacement_player["vor"],
        0
    )

    current_points = safe_number(
        current_player["projected_points"],
        0
    )

    replacement_points = safe_number(
        replacement_player["projected_points"],
        0
    )

    vor_loss = max(
        0,
        current_vor - replacement_vor
    )

    point_loss = max(
        0,
        current_points - replacement_points
    )

    return round(
        vor_loss
        + point_loss * 0.30,
        2
    )


# ============================================================
# PROJECTED AVAILABILITY
# ============================================================

def calculate_projected_availability(
    player,
    available_players,
    future_scott_picks,
    current_round
):

    next_pick_info = None
    two_pick_info = None

    if len(future_scott_picks) >= 1:

        next_scott = future_scott_picks[0]

        replacement = (
            get_projected_replacement(
                player,
                available_players,
                next_scott["selections_away"],
                current_round
            )
        )

        next_pick_info = {
            "selections_away":
                next_scott["selections_away"],

            "replacement":
                replacement["player"]
                if replacement is not None
                else None,

            "drop":
                calculate_player_drop(
                    player,
                    replacement
                ),
        }

    if len(future_scott_picks) >= 2:

        second_scott = (
            future_scott_picks[1]
        )

        replacement = (
            get_projected_replacement(
                player,
                available_players,
                second_scott["selections_away"],
                current_round
            )
        )

        two_pick_info = {
            "selections_away":
                second_scott["selections_away"],

            "replacement":
                replacement["player"]
                if replacement is not None
                else None,

            "drop":
                calculate_player_drop(
                    player,
                    replacement
                ),
        }

    next_drop = (
        next_pick_info["drop"]
        if next_pick_info
        else 0
    )

    two_drop = (
        two_pick_info["drop"]
        if two_pick_info
        else next_drop
    )

    if (
        next_drop >= 18
        or two_drop >= 30
    ):
        depth = "CLIFF"

    elif (
        next_drop >= 10
        or two_drop >= 18
    ):
        depth = "THIN"

    elif (
        next_drop <= 5
        and two_drop <= 10
    ):
        depth = "DEEP"

    else:
        depth = "NORMAL"

    return {
        "next_pick": next_pick_info,
        "two_picks": two_pick_info,
        "depth": depth,
    }


# ============================================================
# GEM VALUE
# ============================================================

def calculate_gem_value(player):

    rank = safe_number(
        player["rank"],
        500
    )

    adp = safe_number(
        player["average_adp"],
        rank
    )

    gap = adp - rank

    if gap >= 30:

        return {
            "score": 22,
            "label": "ELITE GEM",
            "gap": gap,
        }

    if gap >= 20:

        return {
            "score": 15,
            "label": "GEM",
            "gap": gap,
        }

    if gap >= 10:

        return {
            "score": 8,
            "label": "VALUE",
            "gap": gap,
        }

    return {
        "score": 0,
        "label": None,
        "gap": gap,
    }


# ============================================================
# BASE VALUE
# ============================================================

def calculate_base_value(player):

    rank = safe_number(
        player["rank"],
        500
    )

    vor = safe_number(
        player["vor"],
        0
    )

    adp = safe_number(
        player["average_adp"],
        rank
    )

    rank_score = max(
        0,
        135 - rank
    )

    vor_score = vor * 0.45

    market_value = max(
        -12,
        min(
            18,
            (adp - rank) * 0.15
        )
    )

    return (
        rank_score
        + vor_score
        + market_value
    )


# ============================================================
# BYE CONTEXT
# ============================================================

def calculate_bye_context(
    player,
    bye_counts,
    current_round
):

    bye = safe_number(
        player.get("bye", 0),
        0
    )

    if bye <= 0:

        return {
            "adjustment": 0,
            "bye_week": None,
            "current_count": 0,
            "label": None,
        }

    bye = int(bye)

    current_count = (
        bye_counts.get(bye, 0)
    )

    label = None

    if current_round >= 9:

        if current_count >= 4:
            label = "HEAVY BYE CONCENTRATION"

        elif current_count >= 2:
            label = "CONCENTRATED BYE"

        elif current_count == 0:
            label = "NEW BYE WEEK"

    # BYE concentration is informational.
    # It is not automatically treated as bad.

    return {
        "adjustment": 0,
        "bye_week": bye,
        "current_count": current_count,
        "label": label,
    }


# ============================================================
# PLAYER ROLE
# ============================================================

def get_player_role(
    position,
    counts,
    current_round
):

    starter_need = get_starter_need(
        position,
        counts
    )

    if starter_need > 0:
        return "STARTER"

    # Rounds 5-8:
    # Target RB/WR/TE players with potential
    # to become weekly starters.

    if (
        5 <= current_round <= 8
        and position in ["RB", "WR", "TE"]
    ):
        return "POTENTIAL_STARTER"

    # Rounds 9-12:
    # QB2 becomes a legitimate roster objective.

    if (
        9 <= current_round <= 12
        and position == "QB"
        and counts["QB"] == 1
    ):
        return "QB2"

    return "DEPTH"


# ============================================================
# SCOTT FIT
# ============================================================

def calculate_scott_fit(
    player,
    counts,
    current_round
):

    position = player["position"]

    starter_need = get_starter_need(
        position,
        counts
    )

    core_complete = (
        core_lineup_complete(counts)
    )

    role = get_player_role(
        position,
        counts,
        current_round
    )

    adjustment = 0
    reasons = []

    # ========================================================
    # ROUND 1 — BEST AVAILABLE STARTER
    # ========================================================

    if current_round == 1:

        if not is_round_one_starter_eligible(
            position,
            counts
        ):

            adjustment -= 500

            reasons.append(
                "Round 1 excludes bench-only selections"
            )

        else:

            adjustment += 20

            reasons.append(
                "Round 1 best-available starter candidate"
            )

    # ========================================================
    # ROUNDS 2-3 — BUILD STARTERS
    # ========================================================

    elif current_round <= 3:

        if starter_need > 0:

            adjustment += 34

            reasons.append(
                "starting-lineup construction priority"
            )

        else:

            adjustment -= 8

    # ========================================================
    # ROUND 4 — FINISH STARTING OFFENSE
    # ========================================================

    elif current_round == 4:

        if starter_need > 0:

            adjustment += 40

            reasons.append(
                "Round 4 final-starter priority"
            )

        else:

            adjustment -= 10

            reasons.append(
                "would initially be a bench selection"
            )

    # ========================================================
    # ROUNDS 5-8 — POTENTIAL STARTERS
    # ========================================================

    elif current_round <= 8:

        if position in ["RB", "WR", "TE"]:

            adjustment += 30

            reasons.append(
                "Rounds 5-8 potential-starter target"
            )

            if role == "POTENTIAL_STARTER":

                adjustment += 10

                reasons.append(
                    "RB/WR/TE depth with weekly-start upside"
                )

        elif position == "QB":

            if counts["QB"] >= 1:

                adjustment -= 45

                reasons.append(
                    "QB2 deferred while building potential-starter depth"
                )

        elif position == "PK":

            if counts["PK"] >= 1:
                adjustment -= 500

        elif position == "DEF":

            adjustment -= 500

    # ========================================================
    # ROUNDS 9-12 — COMPLETE ROSTER
    # ========================================================

    elif current_round <= 12:

        if position == "QB":

            if counts["QB"] == 1:

                adjustment += 28

                reasons.append(
                    "Rounds 9-12 QB2 roster need"
                )

            elif counts["QB"] >= 2:

                adjustment -= 500

        elif position in ["RB", "WR", "TE"]:

            adjustment += 10

            reasons.append(
                "Rounds 9-12 roster depth"
            )

        elif position == "PK":

            if counts["PK"] >= 1:
                adjustment -= 500

        elif position == "DEF":

            adjustment -= 500

    # ========================================================
    # ROUND 13 — DEF
    # ========================================================

    else:

        if position == "DEF":

            adjustment += 150

            reasons.append(
                "Round 13 defense target"
            )

        else:

            adjustment -= 100

    # ========================================================
    # QB MAXIMUM
    # ========================================================

    if position == "QB":

        if counts["QB"] >= 2:

            adjustment -= 500

            reasons.append(
                "Scott already has two QBs"
            )

    # ========================================================
    # PK
    # ========================================================

    if position == "PK":

        if counts["PK"] >= 1:

            adjustment -= 500

            reasons.append(
                "Scott only carries one kicker"
            )

        elif current_round == 1:

            adjustment -= 500

        elif current_round == 2:

            adjustment += 6

            reasons.append(
                "premium kicker may be considered in Round 2"
            )

        elif current_round <= 4:

            adjustment += 10

        if (
            str(player["player"])
            .strip()
            .lower()
            == "brandon aubrey"
            and counts["PK"] == 0
            and current_round >= 2
        ):

            adjustment += 8

            reasons.append(
                "Brandon Aubrey strategic target"
            )

    # ========================================================
    # DEF
    # ========================================================

    if position == "DEF":

        if counts["DEF"] >= 1:

            adjustment -= 500

            reasons.append(
                "Scott only carries one defense"
            )

        elif current_round < 13:

            adjustment -= 500

            reasons.append(
                "Scott intentionally waits until Round 13 for defense"
            )

    return {
        "adjustment": adjustment,
        "starter_need": starter_need,
        "core_complete": core_complete,
        "role": role,
        "reasons": reasons,
    }


# ============================================================
# ROSTER-AWARE AVAILABILITY BONUS
# ============================================================

def calculate_availability_bonus(
    availability,
    current_round,
    position,
    role
):

    next_drop = 0
    two_drop = 0

    if availability["next_pick"]:

        next_drop = (
            availability[
                "next_pick"
            ]["drop"]
        )

    if availability["two_picks"]:

        two_drop = (
            availability[
                "two_picks"
            ]["drop"]
        )

    # ========================================================
    # ROUND 1
    # ========================================================

    if current_round == 1:

        next_weight = 0.10
        two_weight = 0.03

    # ========================================================
    # ROUNDS 2-4
    # ========================================================

    elif current_round <= 4:

        if role == "STARTER":

            next_weight = 0.65
            two_weight = 0.25

        else:

            next_weight = 0.20
            two_weight = 0.08

    # ========================================================
    # ROUNDS 5-8
    # ========================================================

    elif current_round <= 8:

        if position in ["RB", "WR", "TE"]:

            next_weight = 0.90
            two_weight = 0.40

        elif position == "QB":

            # Scott already has his starting QB.
            # QB2 cliffs should not create false urgency.

            next_weight = 0.08
            two_weight = 0.03

        else:

            next_weight = 0.15
            two_weight = 0.05

    # ========================================================
    # ROUNDS 9-12
    # ========================================================

    elif current_round <= 12:

        if role == "QB2":

            next_weight = 0.55
            two_weight = 0.25

        elif position in ["RB", "WR", "TE"]:

            next_weight = 0.55
            two_weight = 0.25

        else:

            next_weight = 0.25
            two_weight = 0.10

    else:

        next_weight = 0.20
        two_weight = 0.05

    return (
        next_drop * next_weight
        + two_drop * two_weight
    )


# ============================================================
# GEM WEIGHT
# ============================================================

def get_gem_weight(
    current_round,
    position
):

    if current_round == 1:
        return 0.05

    if current_round <= 4:
        return 0.30

    if current_round <= 8:

        if position in ["RB", "WR", "TE"]:
            return 1.00

        if position == "QB":
            return 0.15

        return 0.25

    if current_round <= 12:
        return 0.55

    return 0.20


# ============================================================
# SCOTT RECOMMENDATIONS
# ============================================================

def recommend_scott_pick(
    available_players,
    my_team,
    current_round,
    current_sequence_index,
    draft_order,
    top_n=5
):

    counts = get_roster_counts(
        my_team
    )

    bye_counts = get_bye_week_counts(
        my_team
    )

    future_scott_picks = (
        find_future_scott_picks(
            draft_order,
            current_sequence_index,
            number_of_future_picks=2
        )
    )

    recommendations = []

    for _, player in (
        available_players.iterrows()
    ):

        position = player["position"]

        base_value = (
            calculate_base_value(
                player
            )
        )

        fit = (
            calculate_scott_fit(
                player,
                counts,
                current_round
            )
        )

        availability = (
            calculate_projected_availability(
                player,
                available_players,
                future_scott_picks,
                current_round
            )
        )

        availability_bonus = (
            calculate_availability_bonus(
                availability,
                current_round,
                position,
                fit["role"]
            )
        )

        gem = calculate_gem_value(
            player
        )

        gem_weight = get_gem_weight(
            current_round,
            position
        )

        bye_context = (
            calculate_bye_context(
                player,
                bye_counts,
                current_round
            )
        )

        final_score = (
            base_value
            + fit["adjustment"]
            + availability_bonus
            + gem["score"] * gem_weight
            + bye_context["adjustment"]
        )

        reasons = list(
            fit["reasons"]
        )

        depth = availability["depth"]

        if depth == "CLIFF":

            if (
                fit["role"]
                in [
                    "STARTER",
                    "POTENTIAL_STARTER",
                    "QB2",
                ]
            ):

                reasons.append(
                    "POSITION CLIFF — meaningful value may disappear"
                )

            else:

                reasons.append(
                    "position has a projected drop, but roster urgency is low"
                )

        elif depth == "THIN":

            if fit["role"] != "DEPTH":

                reasons.append(
                    "position depth is becoming thin"
                )

        elif depth == "DEEP":

            reasons.append(
                "comparable positional value may remain later"
            )

        if gem["label"]:

            reasons.append(
                f"{gem['label']} versus market ADP"
            )

        if (
            bye_context["label"]
            and current_round >= 9
        ):

            reasons.append(
                f"Bye Week "
                f"{bye_context['bye_week']}: "
                f"{bye_context['label']}"
            )

        rank = safe_number(
            player["rank"],
            999
        )

        if rank <= 10:

            reasons.append(
                "elite overall ranking"
            )

        elif rank <= 25:

            reasons.append(
                "high overall ranking"
            )

        next_replacement = None
        next_drop = 0

        if availability["next_pick"]:

            next_replacement = (
                availability[
                    "next_pick"
                ]["replacement"]
            )

            next_drop = (
                availability[
                    "next_pick"
                ]["drop"]
            )

        two_replacement = None
        two_drop = 0

        if availability["two_picks"]:

            two_replacement = (
                availability[
                    "two_picks"
                ]["replacement"]
            )

            two_drop = (
                availability[
                    "two_picks"
                ]["drop"]
            )

        effective_wait_drop = next_drop

        if (
            5 <= current_round <= 8
            and position == "QB"
            and counts["QB"] >= 1
        ):

            effective_wait_drop = (
                next_drop * 0.15
            )

        if effective_wait_drop >= 15:

            wait_label = "HIGH"

        elif effective_wait_drop >= 7:

            wait_label = "MEDIUM"

        else:

            wait_label = "LOW"

        recommendations.append(
            {
                "player":
                    player["player"],

                "position":
                    position,

                "team":
                    player["team"],

                "rank":
                    int(rank),

                "position_rank":
                    player["position_rank"],

                "average_adp":
                    safe_number(
                        player["average_adp"],
                        0
                    ),

                "vor":
                    safe_number(
                        player["vor"],
                        0
                    ),

                "projected_points":
                    safe_number(
                        player["projected_points"],
                        0
                    ),

                "bye":
                    bye_context["bye_week"],

                "bye_count_before_pick":
                    bye_context[
                        "current_count"
                    ],

                "bye_label":
                    bye_context["label"],

                "starter_need":
                    fit["starter_need"],

                "core_complete":
                    fit["core_complete"],

                "role":
                    fit["role"],

                "wait_cost":
                    round(
                        effective_wait_drop,
                        2
                    ),

                "wait_risk":
                    wait_label,

                "replacement_player":
                    next_replacement,

                "gem_label":
                    gem["label"],

                "next_pick_drop":
                    next_drop,

                "next_pick_replacement":
                    next_replacement,

                "two_pick_drop":
                    two_drop,

                "two_pick_replacement":
                    two_replacement,

                "position_depth":
                    depth,

                "recommendation_score":
                    round(
                        final_score,
                        2
                    ),

                "reasons":
                    reasons,
            }
        )

    # ========================================================
    # NORMAL ANALYTICAL SORT
    # ========================================================

    recommendations.sort(
        key=lambda item:
            item["recommendation_score"],
        reverse=True
    )

    # ========================================================
    # SCOTT ROUND 2 — BRANDON AUBREY LOCK
    # ========================================================
    #
    # Scott has made this decision in advance:
    #
    # If Brandon Aubrey is available at Scott's Round 2
    # selection, Aubrey MUST be Recommendation #1.
    #
    # This override happens AFTER all normal analytics.
    # Recommendations #2-#5 remain analytically ranked.
    #
    # If Aubrey has already been drafted, the override does
    # nothing and the normal recommendation order remains.
    # ========================================================

    if current_round == 2:

        aubrey_index = next(
            (
                index
                for index, recommendation
                in enumerate(recommendations)
                if (
                    recommendation["player"]
                    .strip()
                    .lower()
                    == "brandon aubrey"
                )
            ),
            None
        )

        if aubrey_index is not None:

            aubrey = recommendations.pop(
                aubrey_index
            )

            aubrey["reasons"].insert(
                0,
                "STRATEGIC TARGET — Scott Round 2 priority"
            )

            recommendations.insert(
                0,
                aubrey
            )

    return recommendations[:top_n]


# ============================================================
# GENERIC OPPONENT PICK
# ============================================================

def recommend_opponent_pick(
    available_players,
    owner_roster,
    current_round
):

    counts = get_roster_counts(
        owner_roster
    )

    candidates = []

    for _, player in (
        available_players.iterrows()
    ):

        position = player["position"]

        if current_round == 1:

            if not is_round_one_starter_eligible(
                position,
                counts
            ):
                continue

        if (
            position == "DEF"
            and current_round < 7
        ):
            continue

        if (
            position == "PK"
            and current_round < 3
        ):
            continue

        if (
            position == "PK"
            and counts["PK"] >= 1
        ):
            continue

        if (
            position == "DEF"
            and counts["DEF"] >= 1
        ):
            continue

        base_value = (
            calculate_base_value(
                player
            )
        )

        starter_need = (
            get_starter_need(
                position,
                counts
            )
        )

        adjustment = 0

        if current_round == 1:

            adjustment += 20

        elif current_round <= 4:

            if starter_need > 0:
                adjustment += 28

            else:
                adjustment -= 5

        else:

            if starter_need > 0:
                adjustment += 8

        final_score = (
            base_value
            + adjustment
        )

        candidates.append(
            {
                "player":
                    player["player"],

                "position":
                    position,

                "rank":
                    int(
                        safe_number(
                            player["rank"],
                            999
                        )
                    ),

                "score":
                    round(
                        final_score,
                        2
                    ),
            }
        )

    candidates.sort(
        key=lambda item:
            item["score"],
        reverse=True
    )

    if not candidates:
        return None

    return candidates[0]


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Recommendation Engine V5.1 loaded successfully."
    )

    print(
        "Potential-starter priority, roster-aware "
        "positional cliffs, deferred QB2, "
        "late-round roster completion, and "
        "Scott Round 2 Brandon Aubrey lock enabled."
    )