from __future__ import annotations

from .constants import RANK_ORDER
from .models import Card, ScoreEvent


def get_all_subsets(cards: list[Card]) -> list[list[Card]]:
    """Generate all subsets of cards (recursive)."""
    if not cards:
        return [[]]
    first = cards[0]
    rest_subsets = get_all_subsets(cards[1:])
    return rest_subsets + [subset + [first] for subset in rest_subsets]


def calculate_runs(combined: list[Card]) -> list[tuple[int, int]]:
    """
    Find runs of 3+ consecutive ranks.
    Returns list of (run_length, multiplicity).
    Multiplicity accounts for duplicate ranks (e.g., double run of 3 = 2 * 3).
    """
    frequency: dict[int, int] = {}
    for card in combined:
        order = RANK_ORDER[card.rank]
        frequency[order] = frequency.get(order, 0) + 1

    unique_values = sorted(frequency.keys())
    runs_found: list[tuple[int, int]] = []

    for length in [5, 4, 3]:
        for start_index in range(len(unique_values) - length + 1):
            slice_vals = unique_values[start_index : start_index + length]
            consecutive = all(
                slice_vals[i + 1] == slice_vals[i] + 1
                for i in range(len(slice_vals) - 1)
            )
            if consecutive:
                multiplicity = 1
                for val in slice_vals:
                    multiplicity *= frequency[val]
                runs_found.append((length, multiplicity))
                for val in slice_vals:
                    frequency[val] = 0

    return runs_found


def calculate_score(hand: list[Card], starter: Card) -> tuple[int, list[ScoreEvent]]:
    """
    Calculate the cribbage hand score.
    Returns (total_score, list of ScoreEvents).
    """
    total = 0
    events: list[ScoreEvent] = []
    combined = hand + [starter]

    # 15s
    fifteens_count = 0
    for combo in get_all_subsets(combined):
        if 2 <= len(combo) <= 5:
            if sum(c.value for c in combo) == 15:
                fifteens_count += 1
    if fifteens_count > 0:
        pts = fifteens_count * 2
        total += pts
        events.append(ScoreEvent(player="", points=pts, reason=f"{fifteens_count} fifteen(s) for {pts}"))

    # Pairs / triples / quads
    rank_counts: dict[str, int] = {}
    for c in combined:
        rank_counts[c.rank] = rank_counts.get(c.rank, 0) + 1
    for rank, count in rank_counts.items():
        if count == 2:
            total += 2
            events.append(ScoreEvent(player="", points=2, reason=f"Pair of {rank}s for 2"))
        elif count == 3:
            total += 6
            events.append(ScoreEvent(player="", points=6, reason=f"Three {rank}s for 6"))
        elif count == 4:
            total += 12
            events.append(ScoreEvent(player="", points=12, reason=f"Four {rank}s for 12"))

    # Runs
    runs = calculate_runs(combined)
    for run_length, multiplier in runs:
        pts = run_length * multiplier
        total += pts
        if multiplier > 1:
            events.append(ScoreEvent(player="", points=pts, reason=f"{multiplier}x run of {run_length} for {pts}"))
        else:
            events.append(ScoreEvent(player="", points=pts, reason=f"Run of {run_length} for {pts}"))

    # Flush
    if len(hand) >= 4:
        first_suit = hand[0].suit
        if all(c.suit == first_suit for c in hand):
            if starter.suit == first_suit:
                total += 5
                events.append(ScoreEvent(player="", points=5, reason="Flush for 5"))
            else:
                total += 4
                events.append(ScoreEvent(player="", points=4, reason="Flush for 4"))

    # Nobs: Jack in hand matching starter suit
    for c in hand:
        if c.rank == "J" and c.suit == starter.suit:
            total += 1
            events.append(ScoreEvent(player="", points=1, reason="Nobs for 1"))
            break

    return total, events


def calculate_play_score(play_pile: list[Card], running_total: int) -> list[ScoreEvent]:
    """
    Score the current play pile during the pegging phase.
    Called after a card is added. Checks for:
    - 15 (running total == 15) → 2 pts
    - 31 (running total == 31) → 2 pts
    - Pairs: last 2/3/4 cards same rank → 2/6/12 pts
    - Runs: last N cards (N≥3) form consecutive sequence → N pts
    """
    events: list[ScoreEvent] = []

    # 15 or 31
    if running_total == 15:
        events.append(ScoreEvent(player="", points=2, reason="Fifteen for 2"))
    elif running_total == 31:
        events.append(ScoreEvent(player="", points=2, reason="Thirty-one for 2"))

    # Pairs: check last 2, 3, 4 cards for matching ranks
    if len(play_pile) >= 2:
        last_rank = play_pile[-1].rank
        pair_count = 0
        for i in range(len(play_pile) - 2, -1, -1):
            if play_pile[i].rank == last_rank:
                pair_count += 1
            else:
                break
        if pair_count == 1:
            events.append(ScoreEvent(player="", points=2, reason="Pair for 2"))
        elif pair_count == 2:
            events.append(ScoreEvent(player="", points=6, reason="Three of a kind for 6"))
        elif pair_count >= 3:
            events.append(ScoreEvent(player="", points=12, reason="Four of a kind for 12"))

    # Runs: check if the last N cards (N = 3..len(pile)) form a run
    if len(play_pile) >= 3:
        best_run = 0
        for n in range(len(play_pile), 2, -1):
            last_n = play_pile[-n:]
            orders = sorted(RANK_ORDER[c.rank] for c in last_n)
            is_run = all(
                orders[i + 1] == orders[i] + 1 for i in range(len(orders) - 1)
            )
            if is_run:
                best_run = n
                break
        if best_run >= 3:
            events.append(ScoreEvent(player="", points=best_run, reason=f"Run of {best_run} for {best_run}"))

    return events
