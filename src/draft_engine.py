def count_keepers_by_owner(owners, keepers):
    """
    Count how many keepers each owner has.
    """

    keeper_counts = {
        owner: 0
        for owner in owners
    }

    for keeper in keepers:

        owner = keeper.get("owner")

        if owner in keeper_counts:
            keeper_counts[owner] += 1

    return keeper_counts


def get_supplemental_rounds(keeper_count):
    """
    Determine which supplemental picks an owner receives.

    3 keepers -> none
    2 keepers -> S3
    1 keeper  -> S2, S3
    0 keepers -> S1, S2, S3
    """

    keeper_count = max(
        0,
        min(
            keeper_count,
            3
        )
    )

    supplemental_rounds = []

    for round_number in range(
        keeper_count + 1,
        4
    ):

        supplemental_rounds.append(
            round_number
        )

    return supplemental_rounds


def generate_draft_order(
    owners,
    rounds=13,
    keepers=None
):
    """
    Generate the rotating ladder draft order.

    Normal picks retain their regular overall numbers:
        1 through 130.

    Supplemental picks do NOT alter those numbers.

    Supplemental rules:

        3 keepers -> no supplemental picks
        2 keepers -> S3
        1 keeper  -> S2 and S3
        0 keepers -> S1, S2 and S3

    Supplemental picks occur at the END of the
    corresponding round.

    If multiple teams have a supplemental pick
    in the same round, their order follows their
    normal draft position in THAT round.
    """

    if keepers is None:
        keepers = []

    draft_order = []

    number_of_owners = len(
        owners
    )

    keeper_counts = (
        count_keepers_by_owner(
            owners,
            keepers
        )
    )

    overall_pick = 1
    sequence_number = 1


    for round_number in range(
        1,
        rounds + 1
    ):

        # ----------------------------------------------------
        # ROTATING LADDER ORDER
        # ----------------------------------------------------

        start_index = (
            round_number - 1
        ) % number_of_owners


        round_order = (
            owners[start_index:]
            + owners[:start_index]
        )


        # ----------------------------------------------------
        # NORMAL PICKS
        # ----------------------------------------------------

        for pick_in_round, owner in enumerate(
            round_order,
            start=1
        ):

            draft_order.append(
                {
                    "sequence_number":
                        sequence_number,

                    "pick_type":
                        "normal",

                    "pick_label":
                        str(
                            overall_pick
                        ),

                    "overall_pick":
                        overall_pick,

                    "round":
                        round_number,

                    "pick_in_round":
                        pick_in_round,

                    "owner":
                        owner,

                    "supplemental_round":
                        None
                }
            )

            overall_pick += 1
            sequence_number += 1


        # ----------------------------------------------------
        # SUPPLEMENTAL PICKS
        # ----------------------------------------------------

        if round_number <= 3:

            supplemental_owners = []

            for owner in round_order:

                keeper_count = (
                    keeper_counts[
                        owner
                    ]
                )

                supplemental_rounds = (
                    get_supplemental_rounds(
                        keeper_count
                    )
                )

                if (
                    round_number
                    in supplemental_rounds
                ):

                    supplemental_owners.append(
                        owner
                    )


            for supplemental_number, owner in enumerate(
                supplemental_owners,
                start=1
            ):

                draft_order.append(
                    {
                        "sequence_number":
                            sequence_number,

                        "pick_type":
                            "supplemental",

                        "pick_label":
                            f"S{round_number}",

                        "overall_pick":
                            None,

                        "round":
                            round_number,

                        "pick_in_round":
                            None,

                        "owner":
                            owner,

                        "supplemental_round":
                            round_number,

                        "supplemental_order":
                            supplemental_number
                    }
                )

                sequence_number += 1


    return draft_order


def get_keeper_summary(
    owners,
    keepers
):
    """
    Create a summary of keeper counts and
    supplemental picks for each owner.
    """

    keeper_counts = (
        count_keepers_by_owner(
            owners,
            keepers
        )
    )

    summary = []


    for owner in owners:

        keeper_count = (
            keeper_counts[
                owner
            ]
        )

        supplemental_rounds = (
            get_supplemental_rounds(
                keeper_count
            )
        )


        supplemental_labels = [
            f"S{round_number}"
            for round_number
            in supplemental_rounds
        ]


        summary.append(
            {
                "owner":
                    owner,

                "keeper_count":
                    keeper_count,

                "supplemental_picks":
                    supplemental_labels
            }
        )


    return summary


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

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


    # Example only:
    #
    # George keeps 2 -> S3
    # Cherie keeps 1 -> S2 + S3
    # Everyone else keeps 3.

    test_keepers = []


    keeper_counts_for_test = {
        "George": 2,
        "Jeff": 3,
        "Chris": 3,
        "Kevin": 3,
        "Paw": 3,
        "Blake": 3,
        "Cherie": 1,
        "Brian": 3,
        "Nate": 3,
        "Scott": 3
    }


    for owner, keeper_count in (
        keeper_counts_for_test.items()
    ):

        for keeper_number in range(
            keeper_count
        ):

            test_keepers.append(
                {
                    "owner":
                        owner,

                    "player":
                        (
                            f"{owner} "
                            f"Keeper "
                            f"{keeper_number + 1}"
                        )
                }
            )


    print()
    print("KEEPER / SUPPLEMENTAL SUMMARY")
    print("=" * 55)


    summary = get_keeper_summary(
        owners,
        test_keepers
    )


    for team in summary:

        supplemental = (
            ", ".join(
                team[
                    "supplemental_picks"
                ]
            )
        )

        if not supplemental:
            supplemental = "None"


        print(
            f"{team['owner']:8} | "
            f"Keepers: "
            f"{team['keeper_count']} | "
            f"Supplemental: "
            f"{supplemental}"
        )


    print()
    print("DRAFT ORDER")
    print("=" * 55)


    draft_order = generate_draft_order(
        owners=owners,
        rounds=13,
        keepers=test_keepers
    )


    for pick in draft_order:

        if (
            pick["pick_type"]
            == "normal"
        ):

            print(
                f"Overall "
                f"{pick['overall_pick']:3} | "
                f"Round "
                f"{pick['round']:2} | "
                f"Pick "
                f"{pick['pick_in_round']:2} | "
                f"{pick['owner']}"
            )

        else:

            print(
                f"{pick['pick_label']:>11} | "
                f"End Round "
                f"{pick['round']} | "
                f"SUPPLEMENTAL | "
                f"{pick['owner']}"
            )