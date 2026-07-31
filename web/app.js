/**
 * Answer and Conquer — web server
 * Browser → Express + Socket.IO → MySQL (+ optional Flask bot)
 */
const path = require("path");
const fs = require("fs");
const http = require("http");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });

const express = require("express");
const session = require("express-session");
const cors = require("cors");
const { Server } = require("socket.io");
const { v4: uuidv4 } = require("uuid");

const db = require("./db");
const { GameEngine } = require("./gameEngine");

const PORT = Number(process.env.WEB_PORT || process.env.PORT || 3000);
const BOT_API_BASE = (process.env.BOT_API_BASE || "http://127.0.0.1:5050").replace(
  /\/$/,
  ""
);
const isProduction = process.env.NODE_ENV === "production";

const QUESTIONS = JSON.parse(
  fs.readFileSync(
    process.env.QUESTIONS_PATH || path.join(__dirname, "..", "questions.json"),
    "utf8"
  )
);

const sessions = new Map();
/** @type {Map<string, object>} */
const rooms = new Map();

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: true, credentials: true } });

app.set("trust proxy", 1);
app.use(
  cors({
    origin: true,
    credentials: true,
  })
);
app.use(express.json());
app.use(
  session({
    secret: process.env.SESSION_SECRET || "answer-and-conquer-session-secret",
    resave: false,
    saveUninitialized: false,
    cookie: {
      maxAge: 1000 * 60 * 60 * 24 * 7,
      secure: isProduction,
      sameSite: "lax",
    },
  })
);
app.use(express.static(path.join(__dirname, "public")));

function requireAuth(req, res, next) {
  if (req.session?.user?.id) return next();
  return res.status(401).json({ error: "Please log in." });
}

function sessionUser(req) {
  return req.session?.user || null;
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function engineFromSettings(settings) {
  const rates = db.chanceRates(settings.chanceMode);
  return new GameEngine({
    skips: settings.skips,
    overclockBonusChance: rates.overclock,
    tileLossChance: rates.tileLoss,
  });
}

function publicState(session) {
  const snap = session.engine.snapshot();
  return {
    matchId: session.id,
    mode: session.mode,
    username: session.username,
    status: session.status,
    winner: session.winner,
    board: snap.board,
    activePlayer: snap.activePlayer,
    skips: snap.skips,
    timerSeconds: session.timerSeconds,
    settings: session.settings || null,
  };
}

async function finishSolo(session) {
  const engine = session.engine;
  if (engine.checkWinCondition(1)) {
    session.status = "finished";
    session.winner = 1;
  } else if (engine.checkWinCondition(2)) {
    session.status = "finished";
    session.winner = 2;
  } else if (engine.isBoardFull()) {
    session.status = "finished";
    session.winner = engine.getTerritoryWinner();
  }

  if (session.status === "finished" && !session.statsRecorded) {
    const result = session.winner === 1 ? "win" : "loss";
    session.stats = await db.recordMatch(session.userId, {
      mode: session.mode,
      result: session.winner === 0 ? "loss" : result,
      spacesCaptured: engine.countSpaces(1),
    });
    session.statsRecorded = true;
  }
}

async function fetchBotMove(mode, flatBoard) {
  const botMode = mode === "ai" ? "ai" : "cpu";
  try {
    const res = await fetch(`${BOT_API_BASE}/api/get_bot_move`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: botMode, board_state: flatBoard }),
    });
    if (!res.ok) throw new Error("bot");
    const data = await res.json();
    if (typeof data.move !== "number") throw new Error("bad");
    return data.move;
  } catch {
    const empty = [];
    flatBoard.forEach((cell, i) => {
      if (!cell) empty.push(i);
    });
    return empty.length
      ? empty[Math.floor(Math.random() * empty.length)]
      : null;
  }
}

function roomCode() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 5; i++) {
    code += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return rooms.has(code) ? roomCode() : code;
}

function roomPublic(room) {
  return {
    code: room.code,
    status: room.status,
    players: room.players.map((p) => ({
      userId: p.userId,
      username: p.username,
      seat: p.seat,
    })),
    chat: room.chat.slice(-40),
    board: room.engine ? room.engine.snapshot().board : null,
    activePlayer: room.engine ? room.engine.activePlayer : null,
    skips: room.engine ? { ...room.engine.skips } : null,
    winner: room.winner,
    pending: room.pending
      ? {
          seat: room.pending.seat,
          row: room.pending.row,
          col: room.pending.col,
          question: room.pending.question,
          timerSeconds: room.pending.timerSeconds,
          skipsLeft: room.engine.skips[room.pending.seat],
        }
      : null,
  };
}

async function finishMp(room) {
  const engine = room.engine;
  if (engine.checkWinCondition(1)) {
    room.status = "finished";
    room.winner = 1;
  } else if (engine.checkWinCondition(2)) {
    room.status = "finished";
    room.winner = 2;
  } else if (engine.isBoardFull()) {
    room.status = "finished";
    room.winner = engine.getTerritoryWinner();
  }

  if (room.status === "finished" && !room.statsRecorded) {
    room.statsRecorded = true;
    for (const p of room.players) {
      const won = room.winner === 0 ? false : room.winner === p.seat;
      await db.recordMatch(p.userId, {
        mode: "mp",
        result: won ? "win" : "loss",
        spacesCaptured: engine.countSpaces(p.seat),
      });
    }
  }
}

// ---------- REST ----------
app.get("/api/db", async (_req, res) => {
  try {
    const info = await db.healthCheck();
    const tables = await db.listTables();
    const count = await db.userCount();
    res.json({ connected: true, ...info, tables, userCount: count });
  } catch (err) {
    res.status(500).json({ connected: false, error: err.message });
  }
});

app.get("/health", async (_req, res) => {
  try {
    res.json({
      status: "ok",
      connected: true,
      ...(await db.healthCheck()),
      botApiBase: BOT_API_BASE,
    });
  } catch (err) {
    res.status(500).json({ status: "error", connected: false, message: err.message });
  }
});

app.post("/api/register", async (req, res) => {
  try {
    const payload = await db.register(req.body || {});
    req.session.user = {
      id: payload.user.id,
      username: payload.user.username,
      email: payload.user.email,
      role: payload.user.role,
    };
    res.status(201).json(payload);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.post("/api/login", async (req, res) => {
  try {
    const payload = await db.login(req.body || {});
    req.session.user = {
      id: payload.user.id,
      username: payload.user.username,
      email: payload.user.email,
      role: payload.user.role,
    };
    res.json(payload);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.post("/api/logout", (req, res) => {
  req.session.destroy((err) => {
    if (err) return res.status(500).json({ error: "Could not log out." });
    res.clearCookie("connect.sid");
    res.json({ ok: true });
  });
});

app.get("/api/me", async (req, res) => {
  try {
    const sess = sessionUser(req);
    if (!sess?.id) return res.status(401).json({ error: "Please log in." });
    const payload = await db.sessionPayload(sess.id);
    if (!payload) {
      req.session.destroy(() => {});
      return res.status(401).json({ error: "Please log in." });
    }
    req.session.user = {
      id: payload.user.id,
      username: payload.user.username,
      email: payload.user.email,
      role: payload.user.role,
    };
    res.json(payload);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/password", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    await db.changePassword(
      userId,
      req.body?.currentPassword,
      req.body?.newPassword,
      req.body?.confirmPassword
    );
    res.json({ ok: true, message: "Password updated." });
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.post("/api/forgot-password", async (req, res) => {
  try {
    const result = await db.forgotPassword(req.body || {});
    res.json(result);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.get("/api/stats/:userId", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    if (Number(req.params.userId) !== userId) {
      return res.status(403).json({ error: "Forbidden" });
    }
    const stats = await db.getStats(userId);
    if (!stats) return res.status(404).json({ error: "User not found" });
    res.json(stats);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/leaderboard", requireAuth, async (req, res) => {
  try {
    const leaders = await db.getLeaderboard(20);
    res.json({ leaders });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/settings/:userId", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    if (Number(req.params.userId) !== userId) {
      return res.status(403).json({ error: "Forbidden" });
    }
    res.json(await db.getSettings(userId));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put("/api/settings/:userId", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    if (Number(req.params.userId) !== userId) {
      return res.status(403).json({ error: "Forbidden" });
    }
    res.json(await db.saveSettings(userId, req.body || {}));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/rename", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    const user = await db.renameUser(userId, req.body?.username);
    req.session.user.username = user.username;
    res.json({
      user,
      stats: await db.getStats(user.id),
      settings: await db.getSettings(user.id),
    });
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.post("/api/matches", requireAuth, async (req, res) => {
  try {
    const userId = sessionUser(req).id;
    const mode = req.body?.mode;
    if (!["cpu", "ai", "local"].includes(mode)) {
      return res.status(400).json({ error: "mode (cpu|ai|local) required" });
    }
    const stats = await db.getStats(userId);
    if (!stats) return res.status(404).json({ error: "User not found" });
    const settings = await db.getSettings(userId);

    if (mode === "ai" || mode === "cpu") {
      try {
        await fetch(`${BOT_API_BASE}/api/start_match`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode }),
        });
      } catch {
        /* optional */
      }
    }

    const id = uuidv4();
    const engine = engineFromSettings(settings);
    sessions.set(id, {
      id,
      userId,
      username: stats.username,
      mode,
      engine,
      settings,
      timerSeconds: settings.questionTimer,
      deck: shuffle(QUESTIONS),
      deckIndex: 0,
      status: "active",
      winner: null,
      statsRecorded: false,
      pendingCell: null,
    });
    res.status(201).json(publicState(sessions.get(id)));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/matches/:id", requireAuth, (req, res) => {
  const match = sessions.get(req.params.id);
  if (!match) return res.status(404).json({ error: "Match not found" });
  if (match.userId !== sessionUser(req).id) {
    return res.status(403).json({ error: "Forbidden" });
  }
  res.json(publicState(match));
});

app.post("/api/matches/:id/select", requireAuth, (req, res) => {
  const match = sessions.get(req.params.id);
  if (!match) return res.status(404).json({ error: "Match not found" });
  if (match.userId !== sessionUser(req).id) {
    return res.status(403).json({ error: "Forbidden" });
  }
  if (match.status !== "active") {
    return res.status(400).json({ error: "Match is finished", state: publicState(match) });
  }
  if (match.engine.activePlayer !== 1 && match.mode !== "local") {
    return res.status(400).json({ error: "Not your turn" });
  }

  const row = Number(req.body?.row);
  const col = Number(req.body?.col);
  if (Number.isNaN(row) || Number.isNaN(col) || row < 0 || row > 4 || col < 0 || col > 4) {
    return res.status(400).json({ error: "Invalid cell" });
  }
  if (match.engine.board[`${row},${col}`] !== null) {
    return res.status(400).json({ error: "Cell already claimed" });
  }

  if (match.deckIndex >= match.deck.length) {
    match.deck = shuffle(QUESTIONS);
    match.deckIndex = 0;
  }
  const q = match.deck[match.deckIndex++];
  match.pendingCell = { row, col, answer: String(q.answer).toLowerCase() };

  res.json({
    question: q.question,
    timerSeconds: match.timerSeconds,
    skipsLeft: match.engine.skips[match.engine.activePlayer],
    state: publicState(match),
  });
});

app.post("/api/matches/:id/answer", requireAuth, async (req, res) => {
  const match = sessions.get(req.params.id);
  if (!match) return res.status(404).json({ error: "Match not found" });
  if (match.userId !== sessionUser(req).id) {
    return res.status(403).json({ error: "Forbidden" });
  }
  if (!match.pendingCell) return res.status(400).json({ error: "No pending question" });

  const { row, col, answer: expected } = match.pendingCell;
  const player = match.engine.activePlayer;
  const action = req.body?.action || "answer";
  const given = String(req.body?.answer || "").trim().toLowerCase();
  let message = "";
  match.pendingCell = null;

  if (action === "skip") {
    if (match.engine.skips[player] <= 0) {
      return res.status(400).json({ error: "No skips left" });
    }
    match.engine.failTurn(player, true);
    message = "Skip used — turn ends.";
    match.engine.switchTurn();
  } else if (action === "timeout" || given !== expected) {
    const lost = match.engine.failTurn(player, false);
    message =
      action === "timeout"
        ? lost
          ? "Time up — you lost a tile."
          : "Time up — turn ends."
        : lost
          ? "Wrong answer — you lost a tile."
          : "Wrong answer — turn ends.";
    match.engine.switchTurn();
  } else {
    match.engine.claimSpace(row, col);
    message = "Correct — space claimed!";
    await finishSolo(match);
    if (match.status === "active") match.engine.switchTurn();
  }

  await finishSolo(match);

  let botMessage = null;
  if (
    match.status === "active" &&
    match.mode !== "local" &&
    match.engine.activePlayer === 2
  ) {
    const move = await fetchBotMove(match.mode, match.engine.toFlatBoard());
    if (move !== null) {
      const br = Math.floor(move / 5);
      const bc = move % 5;
      match.engine.claimSpace(br, bc);
      botMessage = `Bot claimed (${br}, ${bc}).`;
      await finishSolo(match);
      if (match.status === "active") match.engine.switchTurn();
    }
  }

  res.json({
    message,
    botMessage,
    expectedAnswer: expected,
    state: publicState(match),
    stats: match.stats || null,
  });
});

// ---------- Socket.IO multiplayer ----------
io.on("connection", (socket) => {
  socket.data.roomCode = null;

  socket.on("mp:create", async ({ userId, username }) => {
    try {
      const uid = Number(userId);
      const uname = username || "Player";
      const code = roomCode();
      const settings = await db.getSettings(uid);
      const room = {
        code,
        status: "lobby",
        hostSocketId: socket.id,
        players: [
          {
            socketId: socket.id,
            userId: uid,
            username: uname,
            seat: 1,
          },
        ],
        settings,
        engine: null,
        deck: shuffle(QUESTIONS),
        deckIndex: 0,
        pending: null,
        chat: [],
        winner: null,
        statsRecorded: false,
      };
      rooms.set(code, room);
      socket.join(code);
      socket.data.roomCode = code;
      socket.emit("mp:state", roomPublic(room));
    } catch (err) {
      socket.emit("mp:error", { error: err.message });
    }
  });

  socket.on("mp:join", ({ code, userId, username }) => {
    const room = rooms.get(String(code || "").toUpperCase());
    if (!room) return socket.emit("mp:error", { error: "Room not found" });
    if (room.status !== "lobby") {
      return socket.emit("mp:error", { error: "Game already started" });
    }
    if (room.players.length >= 2) {
      return socket.emit("mp:error", { error: "Room is full" });
    }
    room.players.push({
      socketId: socket.id,
      userId: Number(userId),
      username: username || "Player",
      seat: 2,
    });
    socket.join(room.code);
    socket.data.roomCode = room.code;
    io.to(room.code).emit("mp:state", roomPublic(room));
  });

  socket.on("mp:chat", ({ text }) => {
    const room = rooms.get(socket.data.roomCode);
    if (!room) return;
    const player = room.players.find((p) => p.socketId === socket.id);
    if (!player) return;
    const msg = String(text || "").trim().slice(0, 200);
    if (!msg) return;
    room.chat.push({
      username: player.username,
      text: msg,
      at: new Date().toISOString(),
    });
    io.to(room.code).emit("mp:state", roomPublic(room));
  });

  socket.on("mp:start", () => {
    const room = rooms.get(socket.data.roomCode);
    if (!room) return;
    if (socket.id !== room.hostSocketId) {
      return socket.emit("mp:error", { error: "Only the host can start" });
    }
    if (room.players.length < 2) {
      return socket.emit("mp:error", { error: "Need 2 players" });
    }
    room.engine = engineFromSettings(room.settings);
    room.status = "active";
    room.pending = null;
    room.winner = null;
    room.statsRecorded = false;
    io.to(room.code).emit("mp:state", roomPublic(room));
  });

  socket.on("mp:select", ({ row, col }) => {
    const room = rooms.get(socket.data.roomCode);
    if (!room || room.status !== "active" || !room.engine) return;
    if (room.pending) {
      return socket.emit("mp:error", { error: "Answer the current question first" });
    }
    const player = room.players.find((p) => p.socketId === socket.id);
    if (!player || player.seat !== room.engine.activePlayer) {
      return socket.emit("mp:error", { error: "Not your turn" });
    }
    const r = Number(row);
    const c = Number(col);
    if (room.engine.board[`${r},${c}`] !== null) {
      return socket.emit("mp:error", { error: "Cell taken" });
    }
    if (room.deckIndex >= room.deck.length) {
      room.deck = shuffle(QUESTIONS);
      room.deckIndex = 0;
    }
    const q = room.deck[room.deckIndex++];
    room.pending = {
      seat: player.seat,
      row: r,
      col: c,
      answer: String(q.answer).toLowerCase(),
      question: q.question,
      timerSeconds: room.settings.questionTimer,
    };
    io.to(room.code).emit("mp:state", roomPublic(room));
  });

  socket.on("mp:answer", async ({ action, answer }) => {
    const room = rooms.get(socket.data.roomCode);
    if (!room || !room.pending || !room.engine) return;
    const player = room.players.find((p) => p.socketId === socket.id);
    if (!player || player.seat !== room.pending.seat) {
      return socket.emit("mp:error", { error: "Not your question" });
    }

    const { row, col, answer: expected, seat } = room.pending;
    const act = action || "answer";
    const given = String(answer || "").trim().toLowerCase();
    room.pending = null;

    if (act === "skip") {
      if (room.engine.skips[seat] <= 0) {
        return socket.emit("mp:error", { error: "No skips left" });
      }
      room.engine.failTurn(seat, true);
      room.engine.switchTurn();
    } else if (act === "timeout" || given !== expected) {
      room.engine.failTurn(seat, false);
      room.engine.switchTurn();
    } else {
      room.engine.claimSpace(row, col);
      await finishMp(room);
      if (room.status === "active") room.engine.switchTurn();
    }

    await finishMp(room);
    io.to(room.code).emit("mp:state", roomPublic(room));
  });

  socket.on("mp:leave", () => {
    leaveRoom(socket);
  });

  socket.on("disconnect", () => {
    leaveRoom(socket);
  });
});

function leaveRoom(socket) {
  const code = socket.data.roomCode;
  if (!code) return;
  const room = rooms.get(code);
  if (!room) return;
  room.players = room.players.filter((p) => p.socketId !== socket.id);
  socket.leave(code);
  socket.data.roomCode = null;
  if (room.players.length === 0) {
    rooms.delete(code);
  } else {
    if (room.hostSocketId === socket.id) {
      room.hostSocketId = room.players[0].socketId;
    }
    if (room.status === "active") {
      room.status = "abandoned";
    }
    io.to(code).emit("mp:state", roomPublic(room));
  }
}

async function start() {
  try {
    const info = await db.init();
    server.listen(PORT, "0.0.0.0", () => {
      console.log("========================================");
      console.log(" Answer and Conquer — full web app");
      console.log("========================================");
      console.log(` App:     http://127.0.0.1:${PORT}`);
      console.log(
        ` DB:      MySQL ${info.host}:${info.port}/${info.name}`
      );
      console.log(` Bot:     ${BOT_API_BASE}`);
      console.log(` Sockets: multiplayer rooms enabled`);
      console.log("========================================");
    });

    server.on("error", (err) => {
      if (err.code === "EADDRINUSE") {
        console.error(
          `\nPort ${PORT} in use. Open http://127.0.0.1:${PORT} or free the port, then npm start.\n`
        );
        process.exit(1);
      }
      throw err;
    });
  } catch (err) {
    console.error("Failed to connect to MySQL:", err.message);
    console.error("Check DB_HOST / DB_USER / DB_PASSWORD / DB_NAME in .env");
    console.error("Import sql/database.sql in MySQL Workbench first (same as BillReminder).");
    process.exit(1);
  }
}

if (require.main === module) {
  start();
}

module.exports = { app, start, server, io };
