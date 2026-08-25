def generate_draft_order(owners, rounds=13):
    """
    Generate the rotating ladder draft order.

    Round 1 starts with owner position 1.
    Round 2 starts with owner position 2.
    Round 3 starts with owner position 3.
    Etc.

    After position 10, the order wraps back to position 1.
    """

    draft_order = []
    number_of_owners = len(owners)
    overall_pick = 1

    for round_number in range(1, rounds + 1):

        # Round 1 starts at index 0.
        # Round 2 starts at index 1.
        # Round 3 starts at index 2.
        start_index = (round_number - 1) % number_of_owners

        round_order = (
            owners[start_index:]
            + owners[:start_index]
        )

        for pick_in_round, owner in enumerate(
            round_order,
            start=1
        ):

            draft_order.append(
                {
                    "overall_pick": overall_pick,
                    "round": round_number,
                    "pick_in_round": pick_in_round,
                    "owner": owner
                }
            )

            overall_pick += 1

    return draft_order


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

    draft_order = generate_draft_order(
        owners=owners,
        rounds=13
    )

    for pick in draft_order:
        print(
            f"Overall {pick['overall_pick']:3} | "
            f"Round {pick['round']:2} | "
            f"Pick {pick['pick_in_round']:2} | "
            f"{pick['owner']}"
        )