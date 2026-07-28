const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { GameEngine, BOARD_SIZE, STARTING_SKIPS } = require("../gameEngine");

describe("GameEngine", () => {
  it("starts with empty board", () => {
    const engine = new GameEngine();
    assert.equal(Object.keys(engine.board).length, BOARD_SIZE * BOARD_SIZE);
    assert.equal(engine.activePlayer, 1);
    assert.equal(engine.skips[1], STARTING_SKIPS);
  });

  it("claims a space", () => {
    const engine = new GameEngine();
    engine.overclockBonusChance = 0;
    assert.equal(engine.claimSpace(0, 0), true);
    assert.equal(engine.board["0,0"], 1);
    assert.equal(engine.claimSpace(0, 0), false);
  });

  it("detects horizontal win", () => {
    const engine = new GameEngine();
    engine.overclockBonusChance = 0;
    for (let c = 0; c < 4; c++) {
      engine.activePlayer = 1;
      engine.claimSpace(0, c);
    }
    assert.equal(engine.checkWinCondition(1), true);
  });

  it("exports flat board for bot API", () => {
    const engine = new GameEngine();
    engine.overclockBonusChance = 0;
    engine.claimSpace(0, 0);
    const flat = engine.toFlatBoard();
    assert.equal(flat.length, 25);
    assert.equal(flat[0], "X");
  });
});
