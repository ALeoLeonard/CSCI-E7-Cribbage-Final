# Cribbage Game

Welcome to Andy Leonard's **CSCI E-7 Cribbage Game**! This program implements the classic card game of Cribbage, allowing you to play against the computer.

## Features

- Full implementation of Cribbage rules, including:
  - Hand scoring (15s, pairs, runs, flushes, and "His Nobs").
  - The play phase ("pegging") with scoring for 15, 31, and "Go".
  - Crib scoring and automatic dealer switching.
- User-friendly interface with prompts for human moves and card selections.
- Randomized deck shuffling and computer card selection.
- Emoji-enhanced card suits for a fun and clear display of the deck.

## How to Play

1. **Objective**: Be the first player to score 121 points.
2. **Setup**:
   - Each player (you and the computer) is dealt 6 cards.
   - Each player discards 2 cards to the dealer's crib.
3. **Gameplay**:
   - A starter card is revealed.
   - Players alternate playing cards in the **play phase**:
     - Score points for combinations like 15 or 31 during the play.
   - After the play phase, scores are tallied for:
     - Non-dealer's hand, dealer's hand, and the dealer's crib.
   - The roles of dealer and non-dealer switch after each round.
4. **Scoring**:
   - Points are awarded for combinations like 15s, pairs, runs, flushes, and "His Nobs".
   - The game ends when a player reaches 121 points.

## Controls and Input

- When it's your turn to discard to the crib or play a card, follow the on-screen prompts.
- Select cards by their indices (numbers shown next to your cards).
- The computer opponent will make moves automatically.

## Running the Game

Ensure you have Python installed, then run the program with:

```bash
python cribbage.py
```

## Future Improvements

- Add scoring for runs during the play phase.
- Improve the computer's strategy for choosing crib and play cards.
- Enhance the UI with better visualization or potentially a graphical interface.

## Code Highlights

- **Deck Creation**: The deck is built dynamically with suits and ranks mapped to values.
- **Emoji Suits**: Card suits are displayed using emoji for improved readability.
- **Scoring Logic**:
  - `calculate_score`: Computes points for all combinations in a hand.
  - `calculate_runs`: Detects sequences of consecutive cards for runs scoring.
- **Subset Calculation**: Recursive function `get_all_subsets` simplifies detecting 15s in hands.



