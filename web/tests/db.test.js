const { describe, it, before, after } = require("node:test");
const assert = require("node:assert/strict");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "..", "..", ".env") });

describe("MySQL db auth", () => {
  let db;
  let mysqlOk = false;
  const stamp = Date.now();
  const email = `test_${stamp}@example.com`;
  const username = `TestPlayer_${stamp}`;
  const password = "password123";

  before(async () => {
    process.env.DB_HOST = process.env.DB_HOST || process.env.MYSQL_HOST || "127.0.0.1";
    process.env.DB_PORT = process.env.DB_PORT || process.env.MYSQL_PORT || "3306";
    process.env.DB_USER = process.env.DB_USER || process.env.MYSQL_USER || "root";
    process.env.DB_PASSWORD =
      process.env.DB_PASSWORD ?? process.env.MYSQL_PASSWORD ?? "";
    process.env.DB_NAME =
      process.env.DB_NAME ||
      process.env.MYSQL_DATABASE ||
      "answer_and_conquer";
    delete require.cache[require.resolve("../db")];
    db = require("../db");
    try {
      await db.init();
      mysqlOk = true;
    } catch (err) {
      console.warn("MySQL unavailable — skipping DB tests:", err.message);
      mysqlOk = false;
    }
  });

  after(async () => {
    if (mysqlOk && db?.closePool) await db.closePool();
  });

  it("registers and logs in with SHA1 password", async (t) => {
    if (!mysqlOk) return t.skip("MySQL not available");
    const registered = await db.register({
      username,
      email,
      password,
      confirmPassword: password,
    });
    assert.ok(registered.user.id);
    assert.equal(registered.user.email, email);
    assert.equal(registered.stats.gamesPlayed, 0);

    const loggedIn = await db.login({ email, password });
    assert.equal(loggedIn.user.id, registered.user.id);
    assert.equal(loggedIn.user.username, username);

    await assert.rejects(
      () => db.login({ email, password: "wrong-pass" }),
      /Invalid email or password/i
    );
  });

  it("changes password", async (t) => {
    if (!mysqlOk) return t.skip("MySQL not available");
    const user = (await db.login({ email, password })).user;
    await db.changePassword(user.id, password, "newpass1", "newpass1");
    await assert.rejects(
      () => db.login({ email, password }),
      /Invalid email or password/i
    );
    const again = await db.login({ email, password: "newpass1" });
    assert.equal(again.user.id, user.id);
  });

  it("rejects empty registration", async (t) => {
    if (!mysqlOk) return t.skip("MySQL not available");
    await assert.rejects(() => db.register({}), /fill in all fields/i);
  });
});
