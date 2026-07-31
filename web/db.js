/**
 * MySQL persistence — same pattern as BillReminder:
 * import sql/database.sql in MySQL Workbench, then connect with DB_* from .env.
 * Auth: register/login with SHA1(?) password hashing + session (see app.js).
 */
const mysql = require("mysql2/promise");

const DEFAULT_SETTINGS = {
  theme: "default",
  playerTileColor: "#FF0000",
  opponentTileColor: "#ADD8E6",
  questionTimer: 15,
  skips: 3,
  chanceMode: "normal",
};

const host =
  process.env.DB_HOST || process.env.MYSQL_HOST || "127.0.0.1";
const port = Number(process.env.DB_PORT || process.env.MYSQL_PORT || 3306);
const user = process.env.DB_USER || process.env.MYSQL_USER || "root";
const password =
  process.env.DB_PASSWORD ?? process.env.MYSQL_PASSWORD ?? "";
const database =
  process.env.DB_NAME ||
  process.env.MYSQL_DATABASE ||
  "answer_and_conquer";

const useSsl =
  process.env.DB_SSL === "true" ||
  String(host).includes(".mysql.database.azure.com");

const config = {
  host,
  port,
  user,
  password,
  database,
  waitForConnections: true,
  connectionLimit: 10,
  ...(useSsl ? { ssl: { rejectUnauthorized: false } } : {}),
};

let pool;
let ready;

function httpError(message, status) {
  const err = new Error(message);
  err.status = status;
  return err;
}

async function columnExists(conn, tableName, columnName) {
  const [rows] = await conn.execute(
    `SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?`,
    [tableName, columnName]
  );
  return Number(rows[0].cnt) > 0;
}

async function migrateAuthColumns(conn) {
  if (!(await columnExists(conn, "users", "email"))) {
    await conn.query(
      "ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL UNIQUE AFTER username"
    );
  }
  if (!(await columnExists(conn, "users", "password"))) {
    await conn.query(
      "ALTER TABLE users ADD COLUMN password VARCHAR(255) NULL AFTER email"
    );
  }
  if (!(await columnExists(conn, "users", "role"))) {
    await conn.query(
      "ALTER TABLE users ADD COLUMN role VARCHAR(10) NOT NULL DEFAULT 'user' AFTER password"
    );
  }

  // Seed BillReminder-style test accounts if missing
  const [existing] = await conn.execute(
    "SELECT id FROM users WHERE email = ? LIMIT 1",
    ["user@test.com"]
  );
  if (!existing.length) {
    await conn.execute(
      "INSERT INTO users (username, email, password, role) VALUES (?, ?, SHA1(?), ?)",
      ["user1", "user@test.com", "password123", "user"]
    );
    const [inserted] = await conn.execute(
      "SELECT id FROM users WHERE email = ? LIMIT 1",
      ["user@test.com"]
    );
    const uid = Number(inserted[0].id);
    await conn.execute(
      "INSERT IGNORE INTO player_stats (user_id) VALUES (?)",
      [uid]
    );
    await conn.execute(
      "INSERT IGNORE INTO user_settings (user_id) VALUES (?)",
      [uid]
    );
  }
}

async function getPool() {
  if (pool) return pool;
  if (!ready) {
    ready = (async () => {
      if (
        process.env.DB_PASSWORD === undefined &&
        process.env.MYSQL_PASSWORD === undefined
      ) {
        throw new Error(
          "Missing DB_PASSWORD. Copy .env.example to .env and fill in your MySQL credentials."
        );
      }
      pool = mysql.createPool(config);
      await pool.query("SELECT 1");
      const conn = await pool.getConnection();
      try {
        await migrateAuthColumns(conn);
      } finally {
        conn.release();
      }
      return pool;
    })();
  }
  return ready;
}

async function init() {
  await getPool();
  console.log(`Connected to MySQL (${config.database})`);
  return {
    database: "mysql",
    host: config.host,
    port: config.port,
    name: config.database,
  };
}

function clamp(n, min, max) {
  if (Number.isNaN(n)) return min;
  return Math.max(min, Math.min(max, n));
}

function chanceRates(mode) {
  if (mode === "safe") return { overclock: 0.1, tileLoss: 0.2 };
  if (mode === "chaos") return { overclock: 0.45, tileLoss: 0.65 };
  return { overclock: 0.2, tileLoss: 0.4 };
}

function publicUser(row) {
  return {
    id: Number(row.id),
    username: row.username,
    email: row.email,
    role: row.role || "user",
  };
}

async function ensureSettingsRow(userId) {
  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT user_id FROM user_settings WHERE user_id = ? LIMIT 1",
    [userId]
  );
  if (!rows.length) {
    await database.execute("INSERT INTO user_settings (user_id) VALUES (?)", [
      userId,
    ]);
  }
}

async function ensureStatsRow(userId) {
  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT user_id FROM player_stats WHERE user_id = ? LIMIT 1",
    [userId]
  );
  if (!rows.length) {
    await database.execute("INSERT INTO player_stats (user_id) VALUES (?)", [
      userId,
    ]);
  }
}

async function getSettings(userId) {
  await ensureSettingsRow(userId);
  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT * FROM user_settings WHERE user_id = ? LIMIT 1",
    [userId]
  );
  const row = rows[0];
  return {
    theme: row.theme || DEFAULT_SETTINGS.theme,
    playerTileColor: row.player_tile_color || DEFAULT_SETTINGS.playerTileColor,
    opponentTileColor:
      row.opponent_tile_color || DEFAULT_SETTINGS.opponentTileColor,
    questionTimer: Number(row.question_timer) || DEFAULT_SETTINGS.questionTimer,
    skips: Number(row.skips),
    chanceMode: row.chance_mode || DEFAULT_SETTINGS.chanceMode,
  };
}

async function saveSettings(userId, patch) {
  const current = await getSettings(userId);
  const next = {
    theme: patch.theme ?? current.theme,
    playerTileColor: patch.playerTileColor ?? current.playerTileColor,
    opponentTileColor: patch.opponentTileColor ?? current.opponentTileColor,
    questionTimer: clamp(
      Number(patch.questionTimer ?? current.questionTimer),
      5,
      60
    ),
    skips: clamp(Number(patch.skips ?? current.skips), 0, 10),
    chanceMode: ["safe", "normal", "chaos"].includes(patch.chanceMode)
      ? patch.chanceMode
      : current.chanceMode,
  };
  if (!["default", "grey"].includes(next.theme)) next.theme = "default";

  const database = await getPool();
  await database.execute(
    `UPDATE user_settings SET
       theme = ?,
       player_tile_color = ?,
       opponent_tile_color = ?,
       question_timer = ?,
       skips = ?,
       chance_mode = ?
     WHERE user_id = ?`,
    [
      next.theme,
      next.playerTileColor,
      next.opponentTileColor,
      next.questionTimer,
      next.skips,
      next.chanceMode,
      userId,
    ]
  );
  return next;
}

async function getUserById(userId) {
  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT id, username, email, role FROM users WHERE id = ? LIMIT 1",
    [userId]
  );
  if (!rows.length) return null;
  return publicUser(rows[0]);
}

async function sessionPayload(userId) {
  await ensureStatsRow(userId);
  await ensureSettingsRow(userId);
  const user = await getUserById(userId);
  if (!user) return null;
  return {
    user,
    stats: await getStats(userId),
    settings: await getSettings(userId),
  };
}

async function register({ username, email, password, confirmPassword }) {
  const name = String(username || "").trim();
  const mail = String(email || "").trim().toLowerCase();
  const pass = String(password || "");
  const confirm = String(confirmPassword || "");

  if (!name || !mail || !pass || !confirm) {
    throw httpError("Please fill in all fields.", 400);
  }
  if (name.length > 32) {
    throw httpError("Username must be 32 characters or fewer", 400);
  }
  if (pass.length < 6) {
    throw httpError("Password must be at least 6 characters.", 400);
  }
  if (pass !== confirm) {
    throw httpError("Passwords do not match.", 400);
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) {
    throw httpError("Enter a valid email address.", 400);
  }

  const database = await getPool();

  const [byName] = await database.execute(
    "SELECT id FROM users WHERE username = ? LIMIT 1",
    [name]
  );
  if (byName.length) throw httpError("That username is already taken.", 409);

  const [byEmail] = await database.execute(
    "SELECT id FROM users WHERE email = ? LIMIT 1",
    [mail]
  );
  if (byEmail.length) throw httpError("That email is already registered.", 409);

  // SHA1(?) hashes in MySQL — never store plain text (BillReminder L19)
  const [insert] = await database.execute(
    "INSERT INTO users (username, email, password, role) VALUES (?, ?, SHA1(?), ?)",
    [name, mail, pass, "user"]
  );
  const userId = Number(insert.insertId);
  await ensureStatsRow(userId);
  await ensureSettingsRow(userId);
  return sessionPayload(userId);
}

async function login({ email, password }) {
  const mail = String(email || "").trim().toLowerCase();
  const pass = String(password || "");
  if (!mail || !pass) {
    throw httpError("Please fill in all fields.", 400);
  }

  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT id, username, email, role FROM users WHERE email = ? AND password = SHA1(?) LIMIT 1",
    [mail, pass]
  );
  if (!rows.length) {
    throw httpError("Invalid email or password.", 401);
  }

  const user = publicUser(rows[0]);
  await ensureStatsRow(user.id);
  await ensureSettingsRow(user.id);
  return {
    user,
    stats: await getStats(user.id),
    settings: await getSettings(user.id),
  };
}

async function changePassword(userId, currentPassword, newPassword, confirmPassword) {
  const current = String(currentPassword || "");
  const next = String(newPassword || "");
  const confirm = String(confirmPassword || "");

  if (!current || !next || !confirm) {
    throw httpError("Please fill in all password fields.", 400);
  }
  if (next.length < 6) {
    throw httpError("New password must be at least 6 characters.", 400);
  }
  if (next !== confirm) {
    throw httpError("New passwords do not match.", 400);
  }

  const database = await getPool();
  const [rows] = await database.execute(
    "SELECT id FROM users WHERE id = ? AND password = SHA1(?) LIMIT 1",
    [userId, current]
  );
  if (!rows.length) {
    throw httpError("Current password is incorrect.", 401);
  }

  await database.execute("UPDATE users SET password = SHA1(?) WHERE id = ?", [
    next,
    userId,
  ]);
  return { ok: true };
}

async function renameUser(userId, newUsername) {
  const name = String(newUsername || "").trim();
  if (!name) throw httpError("Enter a username", 400);
  if (name.length > 32) {
    throw httpError("Username must be 32 characters or fewer", 400);
  }
  try {
    await (await getPool()).execute(
      "UPDATE users SET username = ? WHERE id = ?",
      [name, userId]
    );
  } catch (err) {
    if (err && err.code === "ER_DUP_ENTRY") {
      throw httpError("That username is already taken", 409);
    }
    throw err;
  }
  return getUserById(userId);
}

async function getStats(userId) {
  const database = await getPool();
  const [rows] = await database.execute(
    `SELECT u.username, s.games_played, s.wins, s.losses,
            s.local_wins, s.ai_wins, s.total_spaces
     FROM users u
     JOIN player_stats s ON s.user_id = u.id
     WHERE u.id = ?
     LIMIT 1`,
    [userId]
  );
  if (!rows.length) return null;
  const row = rows[0];
  const winRate =
    row.games_played === 0 ? 0 : (row.wins / row.games_played) * 100;
  return {
    username: row.username,
    gamesPlayed: row.games_played,
    wins: row.wins,
    losses: row.losses,
    localWins: row.local_wins,
    aiWins: row.ai_wins,
    totalSpaces: row.total_spaces,
    winRate: Math.round(winRate * 10) / 10,
  };
}

async function recordMatch(userId, { mode, result, spacesCaptured }) {
  const database = await getPool();
  const conn = await database.getConnection();
  try {
    await conn.beginTransaction();
    await conn.execute(
      `INSERT INTO matches (user_id, mode, result, spaces_captured)
       VALUES (?, ?, ?, ?)`,
      [userId, mode, result, spacesCaptured]
    );
    await conn.execute(
      `UPDATE player_stats SET
         games_played = games_played + 1,
         wins = wins + CASE WHEN ? = 'win' THEN 1 ELSE 0 END,
         losses = losses + CASE WHEN ? = 'win' THEN 0 ELSE 1 END,
         local_wins = local_wins + CASE WHEN ? = 'win' AND ? IN ('local', 'mp') THEN 1 ELSE 0 END,
         ai_wins = ai_wins + CASE WHEN ? = 'win' AND ? IN ('cpu', 'ai') THEN 1 ELSE 0 END,
         total_spaces = total_spaces + ?
       WHERE user_id = ?`,
      [result, result, result, mode, result, mode, spacesCaptured, userId]
    );
    await conn.commit();
  } catch (err) {
    await conn.rollback();
    throw err;
  } finally {
    conn.release();
  }
  return getStats(userId);
}

async function listTables() {
  const database = await getPool();
  const [rows] = await database.query(
    `SELECT TABLE_NAME AS name
     FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = ?
     ORDER BY TABLE_NAME`,
    [config.database]
  );
  return rows.map((r) => r.name);
}

async function userCount() {
  const database = await getPool();
  const [rows] = await database.query("SELECT COUNT(*) AS n FROM users");
  return Number(rows[0].n);
}

async function healthCheck() {
  const database = await getPool();
  await database.query("SELECT 1 AS ok");
  return {
    status: "ok",
    database: "mysql",
    host: config.host,
    port: config.port,
    name: config.database,
  };
}

async function closePool() {
  if (pool) {
    await pool.end();
    pool = null;
    ready = null;
  }
}

module.exports = {
  init,
  getPool,
  register,
  login,
  changePassword,
  getUserById,
  sessionPayload,
  renameUser,
  getStats,
  getSettings,
  saveSettings,
  recordMatch,
  healthCheck,
  listTables,
  userCount,
  closePool,
  chanceRates,
  DEFAULT_SETTINGS,
  config,
};
