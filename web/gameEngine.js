/**
 * Port of game_engine.py — 5x5 claim-the-space rules (no I/O).
 */
const BOARD_SIZE = 5;
const CONNECT_LENGTH = 4;
const STARTING_SKIPS = 3;
const TILE_LOSS_CHANCE = 0.4;
const OVERCLOCK_BONUS_CHANCE = 0.2;

const DIRECTIONS = [
  [0, 1],
  [1, 0],
  [1, 1],
  [1, -1],
];

const ADJACENT = [
  [-1, 0],
  [1, 0],
  [0, -1],
  [0, 1],
];

function key(row, col) {
  return `${row},${col}`;
}

class GameEngine {
  constructor(options = {}) {
    this.board = {};
    for (let r = 0; r < BOARD_SIZE; r++) {
      for (let c = 0; c < BOARD_SIZE; c++) {
        this.board[key(r, c)] = null;
      }
    }
    this.activePlayer = 1;
    const skips = Number.isFinite(options.skips)
      ? options.skips
      : STARTING_SKIPS;
    this.skips = { 1: skips, 2: skips };
    this.tileLossChance =
      options.tileLossChance ?? TILE_LOSS_CHANCE;
    this.overclockBonusChance =
      options.overclockBonusChance ?? OVERCLOCK_BONUS_CHANCE;
  }

  resetGame() {
    for (const k of Object.keys(this.board)) this.board[k] = null;
    this.activePlayer = 1;
    const s = this.skips[1];
    this.skips = { 1: s, 2: s };
  }

  switchTurn() {
    this.activePlayer = this.activePlayer === 1 ? 2 : 1;
  }

  getAdjacentCoordinates(row, col) {
    const neighbors = [];
    for (const [dr, dc] of ADJACENT) {
      const nr = row + dr;
      const nc = col + dc;
      if (key(nr, nc) in this.board) neighbors.push([nr, nc]);
    }
    return neighbors;
  }

  claimSpace(row, col) {
    const k = key(row, col);
    if (!(k in this.board) || this.board[k] !== null) return false;

    this.board[k] = this.activePlayer;

    if (Math.random() < this.overclockBonusChance) {
      const empty = this.getAdjacentCoordinates(row, col).filter(
        ([r, c]) => this.board[key(r, c)] === null
      );
      if (empty.length) {
        const [br, bc] = empty[Math.floor(Math.random() * empty.length)];
        this.board[key(br, bc)] = this.activePlayer;
      }
    }
    return true;
  }

  failTurn(player, usedSkip = false) {
    let tileLost = false;
    if (usedSkip) {
      if (this.skips[player] > 0) this.skips[player] -= 1;
    } else if (Math.random() < this.tileLossChance) {
      const owned = Object.entries(this.board)
        .filter(([, owner]) => owner === player)
        .map(([k]) => k);
      if (owned.length) {
        const lost = owned[Math.floor(Math.random() * owned.length)];
        this.board[lost] = null;
        tileLost = true;
      }
    }
    return tileLost;
  }

  _runIsComplete(row, col, dr, dc, player) {
    const endR = row + dr * (CONNECT_LENGTH - 1);
    const endC = col + dc * (CONNECT_LENGTH - 1);
    if (endR < 0 || endR >= BOARD_SIZE || endC < 0 || endC >= BOARD_SIZE) {
      return false;
    }
    for (let step = 0; step < CONNECT_LENGTH; step++) {
      if (this.board[key(row + dr * step, col + dc * step)] !== player) {
        return false;
      }
    }
    return true;
  }

  checkWinCondition(player) {
    for (let r = 0; r < BOARD_SIZE; r++) {
      for (let c = 0; c < BOARD_SIZE; c++) {
        if (this.board[key(r, c)] !== player) continue;
        for (const [dr, dc] of DIRECTIONS) {
          if (this._runIsComplete(r, c, dr, dc, player)) return true;
        }
      }
    }
    return false;
  }

  isBoardFull() {
    return Object.values(this.board).every((owner) => owner !== null);
  }

  getTerritoryWinner() {
    let p1 = 0;
    let p2 = 0;
    for (const owner of Object.values(this.board)) {
      if (owner === 1) p1 += 1;
      if (owner === 2) p2 += 1;
    }
    if (p1 > p2) return 1;
    if (p2 > p1) return 2;
    return 0;
  }

  countSpaces(player) {
    return Object.values(this.board).filter((o) => o === player).length;
  }

  /** Flat 25-cell board for bot API: "" empty, "X" P1, "O" P2 */
  toFlatBoard() {
    const flat = [];
    for (let r = 0; r < BOARD_SIZE; r++) {
      for (let c = 0; c < BOARD_SIZE; c++) {
        const owner = this.board[key(r, c)];
        flat.push(owner === 1 ? "X" : owner === 2 ? "O" : "");
      }
    }
    return flat;
  }

  snapshot() {
    const grid = [];
    for (let r = 0; r < BOARD_SIZE; r++) {
      const row = [];
      for (let c = 0; c < BOARD_SIZE; c++) {
        row.push(this.board[key(r, c)]);
      }
      grid.push(row);
    }
    return {
      board: grid,
      activePlayer: this.activePlayer,
      skips: { ...this.skips },
    };
  }
}

module.exports = {
  GameEngine,
  BOARD_SIZE,
  CONNECT_LENGTH,
  STARTING_SKIPS,
};
