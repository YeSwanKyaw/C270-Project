"""
GameEngine: core backend logic for "Answer and Conquer".

Handles board state, turn management, win detection, territory
tie-breaking, and RNG-driven turn outcomes (tile-loss penalties,
skip consumables, overclock bonuses) for a 5x5 two-player
claim-the-space game. Contains no GUI, I/O, or question-database
code — it is meant to be driven by whatever front-end (Tkinter,
CLI, tests) calls into it.
"""

import random
from typing import Dict, List, Optional, Tuple

BOARD_SIZE = 5
CONNECT_LENGTH = 4
STARTING_SKIPS = 3
TILE_LOSS_CHANCE = 0.40
OVERCLOCK_BONUS_CHANCE = 0.20

# Direction vectors for the four axes a line can run along:
# horizontal, vertical, and the two diagonals.
_DIRECTIONS = [
    (0, 1),   # horizontal →
    (1, 0),   # vertical ↓
    (1, 1),   # diagonal ↘
    (1, -1),  # diagonal ↙
]

# Orthogonal offsets used for adjacency lookups (overclock bonus).
_ADJACENT_OFFSETS = [
    (-1, 0),  # up
    (1, 0),   # down
    (0, -1),  # left
    (0, 1),   # right
]


class GameEngine:
    """Core game state and rules for Answer and Conquer.

    Board is a dict keyed by (row, col) tuples, 0-indexed, covering
    (0,0) through (4,4). Values are None (empty), 1, or 2.
    """

    def __init__(self):
        self.board: Dict[Tuple[int, int], Optional[int]] = {
            (row, col): None
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
        }
        self.active_player: int = 1
        self.skips: Dict[int, int] = {1: STARTING_SKIPS, 2: STARTING_SKIPS}
        # ==================== START OF GAME SETTINGS ====================
        self.tile_loss_chance = TILE_LOSS_CHANCE
        self.overclock_bonus_chance = OVERCLOCK_BONUS_CHANCE
        # ===================== END OF GAME SETTINGS =====================

    def reset_game(self) -> None:
        """Reinitializes the board, active player, and skips for a new
        match, without needing to construct a new GameEngine instance.

        Intended to be called by the GUI after a win/tie popup's
        "Restart" action is confirmed.
        """
        self.board = {
            (row, col): None
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
        }
        self.active_player = 1
        self.skips = {1: STARTING_SKIPS, 2: STARTING_SKIPS}

    def switch_turn(self) -> None:
        """Alternates the active player between 1 and 2."""
        self.active_player = 2 if self.active_player == 1 else 1

    def get_adjacent_coordinates(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Returns the orthogonal (up/down/left/right) neighbors of
        (row, col) that fall within the 5x5 board bounds.
        """
        neighbors = []
        for delta_row, delta_col in _ADJACENT_OFFSETS:
            neighbor = (row + delta_row, col + delta_col)
            if neighbor in self.board:
                neighbors.append(neighbor)
        return neighbors

    def claim_space(self, row: int, col: int) -> bool:
        """Assigns the active player to (row, col) if it is empty.

        Returns True if the claim succeeded, False if the coordinate
        is out of bounds or already occupied.

        On a successful claim there is a 20% ("Overclock Bonus")
        chance the player also claims one random adjacent tile that
        is currently empty.
        """
        if (row, col) not in self.board:
            return False
        if self.board[(row, col)] is not None:
            return False

        self.board[(row, col)] = self.active_player

        # ==================== START OF GAME SETTINGS ====================
        if random.random() < self.overclock_bonus_chance:
        # ===================== END OF GAME SETTINGS =====================
            empty_neighbors = [
                neighbor
                for neighbor in self.get_adjacent_coordinates(row, col)
                if self.board[neighbor] is None
            ]
            if empty_neighbors:
                bonus_tile = random.choice(empty_neighbors)
                self.board[bonus_tile] = self.active_player

        return True

    def fail_turn(self, player: int, used_skip: bool = False) -> bool:
        """Resolves a failed turn (wrong answer or timeout) for `player`.

        If `used_skip` is True, one skip is deducted from the player's
        inventory (if any remain) and the tile-loss penalty is
        completely negated — the player simply loses their turn.

        Otherwise, there is a 40% chance the player loses one of their
        currently owned tiles, chosen at random and reset to None.

        Ends the turn by switching the active player. Returns True if
        a tile was lost as a result of the penalty, False otherwise.
        """
        tile_lost = False

        if used_skip:
            if self.skips[player] > 0:
                self.skips[player] -= 1
        # ==================== START OF GAME SETTINGS ====================
        elif random.random() < self.tile_loss_chance:
        # ===================== END OF GAME SETTINGS =====================
            owned_tiles = [
                coord for coord, owner in self.board.items() if owner == player
            ]
            if owned_tiles:
                lost_tile = random.choice(owned_tiles)
                self.board[lost_tile] = None
                tile_lost = True

        
        return tile_lost

    def check_win_condition(self, player: int) -> bool:
        """Returns True if `player` has 4 continuous spaces in a row,
        horizontally, vertically, or on either diagonal.

        For efficiency, each cell is only checked as the *start* of a
        run: for every occupied cell belonging to `player`, walk 4
        cells in each of the 4 directions and confirm they're all in
        bounds and owned by `player`. This checks every possible
        4-length line on the board exactly once per direction without
        needing to enumerate lines separately.
        """
        for (row, col), owner in self.board.items():
            if owner != player:
                continue
            for delta_row, delta_col in _DIRECTIONS:
                if self._run_is_complete(row, col, delta_row, delta_col, player):
                    return True
        return False

    def _run_is_complete(
        self, row: int, col: int, delta_row: int, delta_col: int, player: int
    ) -> bool:
        """Checks if a 4-length run starting at (row, col) and moving
        by (delta_row, delta_col) each step stays in bounds and is
        entirely owned by `player`.
        """
        end_row = row + delta_row * (CONNECT_LENGTH - 1)
        end_col = col + delta_col * (CONNECT_LENGTH - 1)
        if not (0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE):
            return False

        for step in range(CONNECT_LENGTH):
            r = row + delta_row * step
            c = col + delta_col * step
            if self.board[(r, c)] != player:
                return False
        return True

    def is_board_full(self) -> bool:
        """Returns True if there are no empty spaces left on the board."""
        return all(owner is not None for owner in self.board.values())

    def get_territory_winner(self) -> int:
        """Counts spaces owned by each player.

        Returns 1 or 2 for the player with more spaces, or 0 if both
        players own an equal number of spaces.
        """
        player_one_count = sum(1 for owner in self.board.values() if owner == 1)
        player_two_count = sum(1 for owner in self.board.values() if owner == 2)

        if player_one_count > player_two_count:
            return 1
        if player_two_count > player_one_count:
            return 2
        return 0


if __name__ == "__main__":
    # Quick simulation: Player 1 claims a horizontal line of 4 to win.
    engine = GameEngine()

    moves = [
        (1, (0, 0)),  # Player 1
        (2, (1, 0)),  # Player 2
        (1, (0, 1)),
        (2, (1, 1)),
        (1, (0, 2)),
        (2, (1, 2)),
        (1, (0, 3)),  # Player 1 completes 4-in-a-row horizontally
    ]

    print("Simulating a quick match...\n")
    for expected_player, (row, col) in moves:
        assert engine.active_player == expected_player, "Turn order drifted!"
        success = engine.claim_space(row, col)
        print(
            f"Player {engine.active_player} claims {(row, col)}: "
            f"{'OK' if success else 'FAILED'}"
        )

        if engine.check_win_condition(engine.active_player):
            print(f"\nPlayer {engine.active_player} wins with 4-in-a-row!")
            break

        engine.switch_turn()
    else:
        print("\nNo 4-in-a-row yet.")

    print("\nFinal board:")
    for row in range(BOARD_SIZE):
        print([engine.board[(row, col)] for col in range(BOARD_SIZE)])

    if not engine.check_win_condition(1) and not engine.check_win_condition(2):
        if engine.is_board_full():
            winner = engine.get_territory_winner()
            print(f"\nBoard full. Territory winner: {winner if winner else 'Tie'}")
        else:
            print("\nGame still in progress.")

    # --- RNG mechanics demo: overclock bonus, tile-loss penalty, skips ---
    print("\n" + "=" * 50)
    print("Simulating RNG mechanics on a fresh board")
    print("=" * 50)

    random.seed(7)  # fixed seed so this demo prints the same result every run
    rng_engine = GameEngine()

    print(f"\nStarting skips: {rng_engine.skips}")

    print("\n-- Overclock bonus checks (claim_space) --")
    for row, col in [(2, 2), (0, 0), (4, 4), (1, 3)]:
        before = {c: v for c, v in rng_engine.board.items() if v is not None}
        rng_engine.claim_space(row, col)
        after = {c: v for c, v in rng_engine.board.items() if v is not None}
        bonus_tiles = set(after) - set(before) - {(row, col)}
        bonus_note = f" (+ overclock bonus at {bonus_tiles.pop()})" if bonus_tiles else ""
        print(f"Player {rng_engine.active_player} claims {(row, col)}{bonus_note}")
        rng_engine.switch_turn()

    print("\n-- Failed turn WITHOUT a skip (40% tile-loss chance) --")
    lost = rng_engine.fail_turn(rng_engine.active_player)
    print(
        f"Player {rng_engine.active_player} failed their turn: "
        f"{'lost a tile' if lost else 'no tile lost'}"
    )

    print("\n-- Failed turn WITH a skip (penalty fully negated) --")
    active_before_skip = rng_engine.active_player
    skips_before = rng_engine.skips[active_before_skip]
    lost = rng_engine.fail_turn(active_before_skip, used_skip=True)
    print(
        f"Player {active_before_skip} used a skip "
        f"({skips_before} -> {rng_engine.skips[active_before_skip]} remaining): "
        f"{'lost a tile (unexpected!)' if lost else 'no tile lost, as expected'}"
    )

    print(f"\nFinal skips: {rng_engine.skips}")
    print("Final RNG demo board:")
    for row in range(BOARD_SIZE):
        print([rng_engine.board[(row, col)] for col in range(BOARD_SIZE)])
