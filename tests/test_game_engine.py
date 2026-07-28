"""Unit tests for GameEngine — used by Jenkins CI (no GUI required)."""

import random

import pytest

from desktop.core.game_engine import BOARD_SIZE, GameEngine, STARTING_SKIPS


@pytest.fixture
def engine():
    return GameEngine()


def test_board_starts_empty(engine):
    assert len(engine.board) == BOARD_SIZE * BOARD_SIZE
    assert all(owner is None for owner in engine.board.values())
    assert engine.active_player == 1
    assert engine.skips == {1: STARTING_SKIPS, 2: STARTING_SKIPS}


def test_claim_space_success(engine):
    engine.overclock_bonus_chance = 0.0
    assert engine.claim_space(0, 0) is True
    assert engine.board[(0, 0)] == 1


def test_claim_space_rejects_occupied(engine):
    engine.overclock_bonus_chance = 0.0
    assert engine.claim_space(1, 1) is True
    assert engine.claim_space(1, 1) is False


def test_claim_space_out_of_bounds(engine):
    assert engine.claim_space(-1, 0) is False
    assert engine.claim_space(0, 5) is False


def test_switch_turn(engine):
    engine.switch_turn()
    assert engine.active_player == 2
    engine.switch_turn()
    assert engine.active_player == 1


def test_horizontal_win(engine):
    engine.overclock_bonus_chance = 0.0
    for col in range(4):
        engine.active_player = 1
        assert engine.claim_space(0, col) is True
    assert engine.check_win_condition(1) is True
    assert engine.check_win_condition(2) is False


def test_vertical_win(engine):
    engine.overclock_bonus_chance = 0.0
    for row in range(4):
        engine.active_player = 2
        assert engine.claim_space(row, 0) is True
    assert engine.check_win_condition(2) is True


def test_no_win_with_three_in_a_row(engine):
    engine.overclock_bonus_chance = 0.0
    for col in range(3):
        engine.active_player = 1
        engine.claim_space(2, col)
    assert engine.check_win_condition(1) is False


def test_reset_game(engine):
    engine.overclock_bonus_chance = 0.0
    engine.claim_space(0, 0)
    engine.switch_turn()
    engine.skips[1] = 0
    engine.reset_game()
    assert engine.board[(0, 0)] is None
    assert engine.active_player == 1
    assert engine.skips == {1: STARTING_SKIPS, 2: STARTING_SKIPS}


def test_fail_turn_with_skip_deducts_skip(engine):
    engine.tile_loss_chance = 1.0
    engine.overclock_bonus_chance = 0.0
    engine.claim_space(0, 0)
    lost = engine.fail_turn(1, used_skip=True)
    assert lost is False
    assert engine.skips[1] == STARTING_SKIPS - 1
    assert engine.board[(0, 0)] == 1


def test_fail_turn_can_lose_tile(engine):
    engine.overclock_bonus_chance = 0.0
    engine.tile_loss_chance = 1.0
    engine.claim_space(0, 0)
    random.seed(1)
    lost = engine.fail_turn(1, used_skip=False)
    assert lost is True
    assert engine.board[(0, 0)] is None


def test_territory_winner(engine):
    engine.overclock_bonus_chance = 0.0
    engine.active_player = 1
    engine.claim_space(0, 0)
    engine.claim_space(0, 1)
    engine.active_player = 2
    engine.claim_space(1, 0)
    assert engine.get_territory_winner() == 1


def test_is_board_full_false_when_empty(engine):
    assert engine.is_board_full() is False


def test_get_adjacent_coordinates_corner(engine):
    neighbors = engine.get_adjacent_coordinates(0, 0)
    assert set(neighbors) == {(0, 1), (1, 0)}
