import random # random is used to shuffle the deck and for the computer picking random cards

# As I started, I found it tedious to play when the suit was merely spelled out so I mapped the suit to emojis 😄
SUIT_EMOJIS = {
    "Hearts": "♥️",
    "Diamonds": "♦️",
    "Clubs": "♣️",
    "Spades": "♠️"
}

# This maps card ranks to values, which is helpful for detecting runs
# Ace is low (1), cards 2-10 are rank number, jack is 11, queen 12, king 13
RANK_ORDER = {
    "Ace": 1, "2": 2, "3": 3, "4":4, "5":5,
    "6":6, "7":7, "8":8, "9":9, "10":10,
    "Jack":11, "Queen":12, "King":13
}

"""
Each card has:
  suit: string (e.g. "Hearts")
  rank: string (e.g. "5")
  value: an integer used for scoring 15s (Ace=1, J/Q/K=10, others their face value)
"""
def create_card(suit, rank):
    if rank in ["Jack", "Queen", "King"]:
        value = 10
    elif rank == "Ace":
        value = 1
    else:
        value = int(rank)

    return {
        "suit": suit,
        "rank": rank,
        "value": value
    }

def create_deck():
    # Standard 52-card deck
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
    deck = []
    for suit in suits:
        for rank in ranks:
            deck.append(create_card(suit, rank))
    return deck

def shuffle_deck(deck):
    random.shuffle(deck)

def deal_cards(deck, number_of_cards):
    dealt = deck[:number_of_cards] # Deal cards from top of deck
    del deck[:number_of_cards] # Remove them from deck
    return dealt

# Return a string representation of the card, e.g, "5 ♥️"
def print_card(card):
    return f"{card['rank']} {SUIT_EMOJIS[card['suit']]}"

def create_player(name):
    return {
        "name": name,
        "hand": [],
        "score": 0, # Scoring starts at 0 and ends at 120 and is most commonly tracked on a board.
        "crib": [] # A crib is a second hand the dealer gets. It is comprised of 4 cards, 2 from each player.
    }

# The crib needs to reset after every hand
def reset_crib(player):
    player["crib"] = []

def player_add_score(player, points):
    player["score"] += points

def player_play_card(player, card_index):
    return player["hand"].pop(card_index) # Used when a player chooses a card to play during the play phase


"""
This is used to find combos of 2-5 cards for scoring 15.
We need to consider all subsets because any combo of cards could make 15.
Recurison was helpful for cleaning up messy nested loops.
"""
def get_all_subsets(cards):
    if not cards:
        return [[]]
    first = cards[0]
    rest = cards[1:]
    subsets_without_first = get_all_subsets(rest)
    subsets_with_first = []
    for subset in subsets_without_first:
        new_subset = subset + [first]
        subsets_with_first.append(new_subset)
    return subsets_without_first + subsets_with_first

def calculate_runs(combined_hand):
    """
    A run is a sequence of 3 or more consecutive ranks.
    Points for runs: length of run times the multiplicities of duplicates.
    For example, if you have two '2's and a '3' and a '4', you can form the run (2,3,4) twice because there are two 2s.
    """
    # Count how many of each rank (by RANK_ORDER) we have
    frequency = {}
    for card in combined_hand:
        card_value_for_run = RANK_ORDER[card["rank"]]
        frequency[card_value_for_run] = frequency.get(card_value_for_run, 0) + 1

    unique_values = sorted(frequency.keys())
    runs_found = []

    # Check for runs of length 5, then 4, then 3. Starting with the longest allowed me to avoid double counting a run of 4 as 3 and then 4
    for length in [5,4,3]:
        # Try every consecutive slice of unique values of this length
        for start_index in range(len(unique_values) - length + 1):
            slice_vals = unique_values[start_index:start_index+length]
            # Make sure they're consecutive
            consecutive = True
            for i in range(len(slice_vals)-1):
                if slice_vals[i+1] != slice_vals[i] + 1:
                    consecutive = False
                    break
            if consecutive: # There's a run
                # Now look for frequency of each rank in the run (double,triple,quadruple)
                multiplicity = 1
                for val in slice_vals:
                    multiplicity *= frequency[val]
                runs_found.append((length, multiplicity))
                # We need to mark these values as used so we don't get an instance where we're double counting a smaller run
                for val in slice_vals:
                    frequency[val] = 0
    return runs_found


def calculate_score(hand, starter):
    """
    Calculate the cribbage hand score for hand including the 'starter'
    Note: Starter in actual play is a card that is flipped after the non-dealer cuts the deck.

    Scoring:
    - 15s: Any combination of 2-5 cards that sum to 15 is worth 2 points
    - Pairs/Triples/Quads: 2 cards of same rank=2pts, 3=6pts, 4=12pts
    - Runs: Consecutive sequences of 3 or more cards. Points = length * multiplicities (usually called double run, triple run or quadruple runs of _)
    - Flush: 4 cards in same suit in hand=4pts, 5 with starter=5pts
    - His Nobs: Jack in hand of same suit as starter=1pt
    """
    total_score = 0
    breakdown = []
    combined = hand + [starter]

    # Looking for 15s
    all_subs = get_all_subsets(combined)
    for combo in all_subs:
        if 2 <= len(combo) <= 5:
            sum_val = sum(card["value"] for card in combo)
            if sum_val == 15:
                total_score += 2
                breakdown.append("15 for 2") # In future iteration, I'd add 15s together to align with lingo "Fifteen Six"

    # Counting the ranks to find pairs/triples/quads
    rank_counts = {}
    for c in combined:
        rank_counts[c["rank"]] = rank_counts.get(c["rank"], 0) + 1
    for rank, count in rank_counts.items():
        if count == 2:
            total_score += 2
            breakdown.append(f"Pair of {rank}s for 2")
        elif count == 3:
            total_score += 6
            breakdown.append(f"Triple of {rank}s for 6")
        elif count == 4:
            total_score += 12
            breakdown.append(f"Quadruple of {rank}s for 12")

    # Runs
    runs = calculate_runs(combined)
    for run_length, multiplier in runs:
        points = run_length * multiplier
        total_score += points
        if multiplier > 1:
            breakdown.append(f"{multiplier}x Run of {run_length} for {points}") # In a future version I'd have this say double, triple, quadruple run of _
        else:
            breakdown.append(f"Run of {run_length} for {points}")

    # Flush
    if len(hand) >= 4:
        first_suit = hand[0]["suit"]
        all_same_suit = all(c["suit"] == first_suit for c in hand)
        if all_same_suit:
            # 4-card flush
            total_score += 4
            breakdown.append("Flush for 4")
            # If starter matches suit for a 5-card flush
            if starter["suit"] == first_suit:
                total_score += 1
                breakdown.append("Flush with starter for 5")

    # Nobs: Jack in hand that matches starter suit, e.g. Jack of ♥️ in hand match 5 ♥️ starter
    for c in hand:
        if c["rank"] == "Jack" and c["suit"] == starter["suit"]:
            total_score += 1
            breakdown.append("His Nobs for 1")
            break

    return total_score, breakdown

def choose_crib_cards(human_player, dealer_player):
    """
    The program is a little human biased. It lets the player choose the cards they want to discard to dealer's crib
    The human player will see their cards and select 2 by index to put in the crib
    """
    print(f"\n{human_player['name']}, choose 2 cards to place in the crib.")
    while len(human_player["hand"]) > 4:
        print("Your hand:")
        for i, card in enumerate(human_player["hand"]):
            print(f"  {i}: {print_card(card)}")
        user_input = input("Enter two card indices (separated by a space): ").strip()
        parts = user_input.split()
        if len(parts) == 2:
            try:
                index1 = int(parts[0])
                index2 = int(parts[1])
                if index1 != index2 and 0 <= index1 < len(human_player["hand"]) and 0 <= index2 < len(human_player["hand"]):
                    # Remove in descending order of index to avoid shifting
                    if index1 > index2:
                        first_discard = human_player["hand"].pop(index1)
                        second_discard = human_player["hand"].pop(index2)
                    else:
                        first_discard = human_player["hand"].pop(index2)
                        second_discard = human_player["hand"].pop(index1)
                    # Cards get added to dealer's crib
                    dealer_player["crib"].append(first_discard)
                    dealer_player["crib"].append(second_discard)
                    break
                else:
                    print("Invalid indices. Try again.")
            except ValueError:
                print("Invalid input. Enter valid numbers.")
        else:
            print("Please enter exactly two indices.")

def computer_choose_crib_cards(computer_player, dealer_player):
    """
    Human bias showing again.. The computer "chooses" two cards to discard to the dealer's crib.
    In reality and for simplicity, it merely discards the first two cards.
    """
    print(f"{computer_player['name']} is selecting cards for the crib...")
    dealer_player["crib"].append(computer_player["hand"].pop(0))
    dealer_player["crib"].append(computer_player["hand"].pop(0))

def play_phase(player_a, player_b):
    """
    The play phase or "pegging" of Cribbage:
    Players alternate playing cards to add up to a running total <= 31
    Points: Reaching exactly 15 or 31 scores 2 pts. (Note: In a future iteration, I'd add logic for the nuanced scoring of runs in this phase.)
    If a player cannot play without exceeding 31, they say "Go", and the other scores 1 pt
    """
    print("\nStarting the play phase...")
    running_total = 0
    current_player = player_a
    opponent_player = player_b

    # Continue until both hands are empty
    while player_a["hand"] or player_b["hand"]:
        print(f"\n{player_a['name']} ({player_a['score']}/121) | {player_b['name']} ({player_b['score']}/121)")
        print(f"Running total: {running_total}")

        if not current_player["hand"]:
            # Switch if current player is out of cards
            current_player, opponent_player = opponent_player, current_player
            continue

        # Determine which cards are playable (won't exceed 31)
        playable = []
        for c in current_player["hand"]:
            if c["value"] + running_total <= 31:
                playable.append(c)

        if not playable:
            # No playable cards - Go
            print(f"{current_player['name']} says Go!")
            player_add_score(opponent_player, 1)
            running_total = 0
            current_player, opponent_player = opponent_player, current_player
            continue

        # If it's the human player's turn
        if current_player["name"] == "Player":
            while True:
                print("Your hand:")
                for i, c in enumerate(current_player["hand"]):
                    print(f"  {i}: {print_card(c)}")
                choice = input("Choose a card to play: ")
                try:
                    idx = int(choice)
                    if 0 <= idx < len(current_player["hand"]):
                        chosen_card = current_player["hand"][idx]
                        # It's important that the card being played can't exceed 31
                        if running_total + chosen_card["value"] <= 31:
                            played_card = player_play_card(current_player, idx)
                            break
                        else:
                            print("That card would exceed 31. Try another card.")
                    else:
                        print("Invalid card number.")
                except ValueError:
                    print("Enter a valid number.")
        else:
            # Human bias again.. the computer chooses randomly from playable cards
            played_card = random.choice(playable)
            current_player["hand"].remove(played_card)
            print(f"{current_player['name']} plays: {print_card(played_card)}")

        running_total += played_card["value"]
        # Scoring during play phase (Note: doesn't include runs that can be scored in this phase yet)
        if running_total == 15:
            print(f"{current_player['name']} scores 2 points for 15!")
            player_add_score(current_player, 2)
        elif running_total == 31:
            print(f"{current_player['name']} scores 2 points for 31!")
            player_add_score(current_player, 2)
            running_total = 0 # reset after hitting 31

        # Switch turns
        current_player, opponent_player = opponent_player, current_player

def count_hands(non_dealer, dealer, starter_card):
    """
    After the play phase, in the following order, count points for:
    - Non-dealer's hand + starter (Note: The non-dealer counts first, which can end the game)
    - Dealer's hand + starter
    - Dealer's crib + starter
    """
    print("\nCounting hands...")

    # Non-dealer's hand
    print(f"{non_dealer['name']}'s hand: {[print_card(c) for c in non_dealer['hand']]} + Starter: {print_card(starter_card)}")
    nd_score, nd_breakdown = calculate_score(non_dealer["hand"], starter_card)
    player_add_score(non_dealer, nd_score)
    if nd_breakdown:
        print(f"{non_dealer['name']} scores {nd_score} points: {', '.join(nd_breakdown)}")
    else:
        print(f"{non_dealer['name']} scores {nd_score} points.")
    print(f"{non_dealer['name']}'s total score: {non_dealer['score']}/121")

    # Dealer's hand
    print(f"{dealer['name']}'s hand: {[print_card(c) for c in dealer['hand']]} + Starter: {print_card(starter_card)}")
    d_score, d_breakdown = calculate_score(dealer["hand"], starter_card)
    player_add_score(dealer, d_score)
    if d_breakdown:
        print(f"{dealer['name']} scores {d_score} points: {', '.join(d_breakdown)}")
    else:
        print(f"{dealer['name']} scores {d_score} points.")
    print(f"{dealer['name']}'s total score: {dealer['score']}/121")

    # Dealer's crib
    print(f"{dealer['name']}'s crib: {[print_card(c) for c in dealer['crib']]} + Starter: {print_card(starter_card)}")
    crib_score, crib_breakdown = calculate_score(dealer["crib"], starter_card)
    player_add_score(dealer, crib_score)
    if crib_breakdown:
        print(f"{dealer['name']} scores {crib_score} points in the crib: {', '.join(crib_breakdown)}")
    else:
        print(f"{dealer['name']} scores {crib_score} points in the crib.")
    print(f"{dealer['name']}'s total score: {dealer['score']}/121")

    reset_crib(dealer)

def start_game():
    """
    Start and run the game until one player reaches 121 points.

    Game Play:
    - Player and Computer alternate dealing
    - Each play gets 6 cards, chooses 2 to discard to the dealer's crib (Human bias: Computer discards automatically)
    - A starter card is revealed
    - Non-dealer starts play
    - Score all hands and crib
    - Repeat until someone reaches 121 points
    """
    print("Welcome to Andy Leonard's CSCI E-7 Cribbage Game!")
    human_player = create_player("Player")
    computer_player = create_player("Computer")

    # Human bias letting human player start as dealer
    dealer_player = human_player
    non_dealer_player = computer_player

    # Continue game until either player reaches 121 points
    while dealer_player["score"] < 121 and non_dealer_player["score"] < 121:
        #Create and shuffle deck
        complete_deck = create_deck()
        shuffle_deck(complete_deck)

        # Deal 6 cards
        dealer_player["hand"] = deal_cards(complete_deck, 6)
        non_dealer_player["hand"] = deal_cards(complete_deck, 6)

        #Reset crib for dealer
        reset_crib(dealer_player)

        # Decide who is dealer and who discards first
        if dealer_player["name"] == "Player":
            # player is dealer
            print("Your hand:")
            for c in dealer_player["hand"]:
                print(f"  {print_card(c)}")
            choose_crib_cards(dealer_player, dealer_player)
            computer_choose_crib_cards(non_dealer_player, dealer_player)
        else:
            # Computer is dealer
            print("Your hand:")
            for c in non_dealer_player["hand"]:
                print(f"  {print_card(c)}")
            choose_crib_cards(non_dealer_player, dealer_player)
            computer_choose_crib_cards(dealer_player, dealer_player)

        #  Keep the original hands for scoring after play phase since play phase conusmes cards
        dealer_original_hand = dealer_player["hand"][:]
        non_dealer_original_hand = non_dealer_player["hand"][:]

        # Deal the starter card
        starter_card = deal_cards(complete_deck, 1)[0]
        print(f"The starter card is {print_card(starter_card)}")

        # Non-dealer starts play
        play_phase(non_dealer_player, dealer_player)

        # Restore hands for scoring
        dealer_player["hand"] = dealer_original_hand
        non_dealer_player["hand"] = non_dealer_original_hand

        # Count the hands and crib
        count_hands(non_dealer_player, dealer_player, starter_card)

        # Switch dealer and non-dealer for next hand
        dealer_player, non_dealer_player = non_dealer_player, dealer_player

    # GGs
    print("Game Over!")
    if dealer_player["score"] >= 121:
        print(f"{dealer_player['name']} wins with {dealer_player['score']} points!")
    else:
        print(f"{non_dealer_player['name']} wins with {non_dealer_player['score']} points!")

if __name__ == "__main__":
    start_game()
