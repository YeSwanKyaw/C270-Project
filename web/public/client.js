(() => {
  const RULES_TEXT =
    "THE CORE RULES\n" +
    "• The Board: 5x5 grid.\n" +
    "• The Goal: Claim spaces by correctly answering trivia. Form a continuous row of four spaces to win.\n" +
    "• The Tiebreaker: If the board fills up, the player with the most spaces wins.\n\n" +
    "POWERS & PENALTIES\n" +
    "• Overclock Power: chance on a correct answer to get an extra adjacent tile.\n" +
    "• Skips: configurable in Settings (default 3).\n" +
    "• Turn Failure Penalty: wrong/timeout may lose a random owned tile.\n\n" +
    "These are the rules for Standard Mode (chance rates change with Safe / Normal / Chaos).";

  const state = {
    user: null,
    stats: null,
    settings: null,
    match: null,
    timerId: null,
    timeLeft: 15,
    rulesNext: null, // 'bot' | 'local' | 'mp'
    pendingBotMode: "cpu",
    socket: null,
    mp: null,
    questionCtx: "solo", // solo | mp
  };

  const $ = (id) => document.getElementById(id);
  const SCREENS = ["login", "menu", "rules", "settings", "stats", "leaderboard", "mp", "game"];

  function showScreen(name) {
    SCREENS.forEach((s) => {
      const el = $(`screen-${s}`);
      if (!el) return;
      const active = s === name;
      el.hidden = !active;
      if (active) {
        el.classList.remove("is-entering");
        void el.offsetWidth;
        el.classList.add("is-entering");
      }
    });
  }

  function setError(el, msg) {
    if (!el) return;
    el.classList.remove("is-ok");
    if (!msg) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = msg;
  }

  function setOk(el, msg) {
    if (!el) return;
    el.classList.add("is-ok");
    el.hidden = false;
    el.textContent = msg || "";
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  function enterApp(payload) {
    state.user = payload.user;
    state.stats = payload.stats;
    applySettings(payload.settings);
    $("menu-user").textContent = `Playing as ${payload.user.username}`;
    showScreen("menu");
  }

  function showAuthPanel(which) {
    const login = $("auth-login");
    const register = $("auth-register");
    const forgot = $("auth-forgot");
    login.hidden = which !== "login";
    register.hidden = which !== "register";
    forgot.hidden = which !== "forgot";
    const active =
      which === "login" ? login : which === "register" ? register : forgot;
    active.classList.remove("panel-swap");
    void active.offsetWidth;
    active.classList.add("panel-swap");
    setError($("login-error"), "");
  }

  function applySettings(settings) {
    if (!settings) return;
    state.settings = settings;
    document.body.classList.toggle("theme-grey", settings.theme === "grey");
    document.documentElement.style.setProperty("--p1", settings.playerTileColor);
    document.documentElement.style.setProperty("--p2", settings.opponentTileColor);
  }

  function renderStats(stats) {
    const fields = [
      ["Player Name", stats.username],
      ["Games Played", stats.gamesPlayed],
      ["Wins", stats.wins],
      ["Losses", stats.losses],
      ["Win Rate", `${stats.winRate}%`],
      ["Local Mode Wins", stats.localWins],
      ["AI Mode Wins", stats.aiWins],
      ["Total Spaces Captured", stats.totalSpaces],
    ];
    $("stats-list").innerHTML = fields
      .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`)
      .join("");
  }

  function renderLeaderboard(leaders) {
    const tbody = $("leaderboard-table").querySelector("tbody");
    const empty = $("leaderboard-empty");
    if (!leaders.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    const meId = state.user?.id;
    tbody.innerHTML = leaders
      .map((row) => {
        const you = meId != null && Number(row.id) === Number(meId);
        return `<tr class="${you ? "is-you" : ""}">
          <td>${row.rank}</td>
          <td>${row.username}${you ? " (you)" : ""}</td>
          <td>${row.wins}</td>
          <td>${row.losses}</td>
          <td>${row.winRate}%</td>
          <td>${row.gamesPlayed}</td>
          <td>${row.totalSpaces}</td>
        </tr>`;
      })
      .join("");
  }

  function fillSettingsForm(settings) {
    $("set-theme").value = settings.theme || "default";
    $("set-p1").value = settings.playerTileColor || "#ff0000";
    $("set-p2").value = settings.opponentTileColor || "#add8e6";
    $("set-timer").value = settings.questionTimer;
    $("set-timer-val").textContent = settings.questionTimer;
    $("set-skips").value = settings.skips;
    $("set-skips-val").textContent = settings.skips;
    $("set-chance").value = settings.chanceMode || "normal";
    $("set-rename").value = state.user?.username || "";
  }

  function renderBoard(match, boardEl, onClick) {
    const firstPaint = !boardEl.dataset.ready;
    boardEl.innerHTML = "";
    match.board.forEach((row, r) => {
      row.forEach((cell, c) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "cell";
        if (firstPaint) {
          btn.classList.add("cell-enter");
          btn.style.setProperty("--i", String(r * 5 + c));
        }
        if (cell === 1) btn.classList.add("p1");
        if (cell === 2) btn.classList.add("p2");
        const canClick =
          match.status === "active" &&
          cell === null &&
          typeof onClick === "function";
        btn.disabled = !canClick;
        if (canClick) btn.addEventListener("click", () => onClick(r, c));
        boardEl.appendChild(btn);
      });
    });
    boardEl.dataset.ready = "1";
  }

  function clearTimer() {
    if (state.timerId) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function openQuestion(payload, ctx) {
    state.questionCtx = ctx;
    clearTimer();
    state.timeLeft = payload.timerSeconds || 15;
    $("question-text").textContent = payload.question;
    $("question-answer").value = "";
    const timerEl = $("question-timer");
    timerEl.textContent = `Time: ${state.timeLeft}s · Skips: ${payload.skipsLeft}`;
    timerEl.classList.toggle("timer-urgent", state.timeLeft <= 5);
    $("btn-skip").disabled = payload.skipsLeft <= 0;
    const qDialog = $("question-dialog");
    qDialog.classList.add("dialog-pop");
    qDialog.showModal();
    $("question-answer").focus();

    state.timerId = setInterval(async () => {
      state.timeLeft -= 1;
      timerEl.textContent = `Time: ${state.timeLeft}s · Skips: ${payload.skipsLeft}`;
      timerEl.classList.toggle("timer-urgent", state.timeLeft <= 5);
      if (state.timeLeft <= 0) {
        clearTimer();
        qDialog.close();
        await submitAnswer({ action: "timeout" });
      }
    }, 1000);
  }

  async function startSoloMatch(mode) {
    const match = await api("/api/matches", {
      method: "POST",
      body: JSON.stringify({ mode }),
    });
    state.match = match;
    if (match.settings) applySettings(match.settings);
    delete $("board").dataset.ready;
    $("game-message").textContent = "Select an empty tile to answer a question.";
    updateSoloHud(match);
    showScreen("game");
  }

  function updateSoloHud(match) {
    const canPlay =
      match.status === "active" &&
      (match.mode === "local" || match.activePlayer === 1);
    renderBoard(match, $("board"), canPlay ? onSelectCell : null);
    $("game-mode").textContent = `Mode: ${match.mode.toUpperCase()}`;
    $("game-turn").textContent =
      match.status === "finished"
        ? " — Game over"
        : ` — Player ${match.activePlayer}'s turn`;
    $("game-skips").textContent = `Skips P1: ${match.skips[1]} | P2: ${match.skips[2]}`;
  }

  async function onSelectCell(row, col) {
    try {
      const payload = await api(`/api/matches/${state.match.matchId}/select`, {
        method: "POST",
        body: JSON.stringify({ row, col }),
      });
      state.match = payload.state;
      updateSoloHud(state.match);
      openQuestion(payload, "solo");
    } catch (err) {
      $("game-message").textContent = err.message;
    }
  }

  async function submitAnswer(body) {
    clearTimer();
    if (state.questionCtx === "mp") {
      ensureSocket();
      state.socket.emit("mp:answer", body);
      return;
    }
    try {
      const result = await api(`/api/matches/${state.match.matchId}/answer`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      state.match = result.state;
      if (result.stats) state.stats = result.stats;
      updateSoloHud(state.match);
      $("game-message").textContent = [result.message, result.botMessage]
        .filter(Boolean)
        .join(" ");
      if (state.match.status === "finished") showResult(state.match.winner, true);
    } catch (err) {
      $("game-message").textContent = err.message;
    }
  }

  function showResult(winner, saved) {
    const title =
      winner === 1 ? "Player 1 wins!" : winner === 2 ? "Player 2 wins!" : "Territory tie";
    $("result-title").textContent = title;
    $("result-body").textContent = saved
      ? "Stats have been saved to the database."
      : "Match ended.";
    const dialog = $("result-dialog");
    dialog.classList.add("dialog-pop");
    dialog.showModal();
  }

  function openRules(next) {
    state.rulesNext = next;
    $("rules-text").textContent = RULES_TEXT;
    $("rules-subtitle").textContent =
      next === "bot"
        ? "Mode: VS Bot"
        : next === "local"
          ? "Mode: Local 2P"
          : "Mode: Online Multiplayer";
    $("rules-mode-pick").hidden = next !== "bot";
    $("btn-rules-start").hidden = next === "bot";
    showScreen("rules");
  }

  // ---- Multiplayer ----
  function ensureSocket() {
    if (state.socket) return state.socket;
    state.socket = io();
    state.socket.on("mp:state", (room) => {
      state.mp = room;
      renderMp(room);
    });
    state.socket.on("mp:error", (payload) => {
      setError($("mp-error"), payload.error || "Multiplayer error");
    });
    return state.socket;
  }

  function renderMp(room) {
    showScreen("mp");
    $("mp-status").textContent = `Room ${room.code} · ${room.status}`;
    $("mp-players").innerHTML = room.players
      .map((p) => `<li>P${p.seat}: ${p.username}</li>`)
      .join("");
    $("btn-mp-start").hidden = !(
      room.status === "lobby" && room.players.length === 2
    );
    $("mp-chat").innerHTML = (room.chat || [])
      .map((m) => `<li><strong>${m.username}:</strong> ${m.text}</li>`)
      .join("");

    const me = room.players.find((p) => p.userId === state.user.id);
    const inGame = room.status === "active" || room.status === "finished";
    const wasHidden = $("mp-game").hidden;
    $("mp-game").hidden = !inGame;
    if (inGame && wasHidden) delete $("mp-board").dataset.ready;

    if (inGame && room.board) {
      const myTurn =
        room.status === "active" && me && me.seat === room.activePlayer && !room.pending;
      renderBoard(
        { board: room.board, status: room.status },
        $("mp-board"),
        myTurn
          ? (r, c) => ensureSocket().emit("mp:select", { row: r, col: c })
          : null
      );
      $("mp-turn").textContent =
        room.status === "finished"
          ? ` — Winner: P${room.winner || "tie"}`
          : ` — Player ${room.activePlayer}'s turn`;
      $("mp-skips").textContent = room.skips
        ? `Skips P1: ${room.skips[1]} | P2: ${room.skips[2]}`
        : "";
    }

    if (
      room.pending &&
      me &&
      room.pending.seat === me.seat &&
      !$("question-dialog").open
    ) {
      openQuestion(
        {
          question: room.pending.question,
          timerSeconds: room.pending.timerSeconds,
          skipsLeft: room.pending.skipsLeft,
        },
        "mp"
      );
    }

    if (room.status === "finished" && !$("result-dialog").open) {
      showResult(room.winner, true);
    }
  }

  // ---- Events ----
  $("btn-show-register").addEventListener("click", () => showAuthPanel("register"));
  $("btn-show-login").addEventListener("click", () => showAuthPanel("login"));
  $("btn-show-forgot").addEventListener("click", () => showAuthPanel("forgot"));
  $("btn-forgot-login").addEventListener("click", () => showAuthPanel("login"));

  $("btn-login").addEventListener("click", async () => {
    setError($("login-error"), "");
    try {
      const data = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({
          email: $("login-email").value,
          password: $("login-password").value,
        }),
      });
      enterApp(data);
    } catch (err) {
      setError($("login-error"), err.message);
    }
  });

  $("btn-register").addEventListener("click", async () => {
    setError($("login-error"), "");
    try {
      const data = await api("/api/register", {
        method: "POST",
        body: JSON.stringify({
          username: $("reg-username").value,
          email: $("reg-email").value,
          password: $("reg-password").value,
          confirmPassword: $("reg-confirm").value,
        }),
      });
      enterApp(data);
    } catch (err) {
      setError($("login-error"), err.message);
    }
  });

  $("btn-forgot").addEventListener("click", async () => {
    setError($("login-error"), "");
    try {
      const result = await api("/api/forgot-password", {
        method: "POST",
        body: JSON.stringify({
          email: $("forgot-email").value,
          username: $("forgot-username").value,
          newPassword: $("forgot-password").value,
          confirmPassword: $("forgot-confirm").value,
        }),
      });
      $("forgot-password").value = "";
      $("forgot-confirm").value = "";
      showAuthPanel("login");
      setOk($("login-error"), result.message || "Password reset. You can log in now.");
    } catch (err) {
      setError($("login-error"), err.message);
    }
  });

  ["login-email", "login-password"].forEach((id) => {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") $("btn-login").click();
    });
  });
  ["reg-username", "reg-email", "reg-password", "reg-confirm"].forEach((id) => {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") $("btn-register").click();
    });
  });
  ["forgot-email", "forgot-username", "forgot-password", "forgot-confirm"].forEach((id) => {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") $("btn-forgot").click();
    });
  });

  $("btn-play-bot").addEventListener("click", () => openRules("bot"));
  $("btn-play-local").addEventListener("click", () => openRules("local"));
  $("btn-play-mp").addEventListener("click", () => openRules("mp"));

  $("btn-rules-back").addEventListener("click", () => showScreen("menu"));
  $("btn-rules-start").addEventListener("click", async () => {
    try {
      if (state.rulesNext === "local") await startSoloMatch("local");
      else if (state.rulesNext === "mp") {
        ensureSocket();
        showScreen("mp");
        setError($("mp-error"), "");
      }
    } catch (err) {
      setError($("menu-error"), err.message);
      showScreen("menu");
    }
  });

  document.querySelectorAll("[data-bot-mode]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await startSoloMatch(btn.dataset.botMode);
      } catch (err) {
        setError($("menu-error"), err.message);
        showScreen("menu");
      }
    });
  });

  $("btn-settings").addEventListener("click", async () => {
    try {
      const settings = await api(`/api/settings/${state.user.id}`);
      applySettings(settings);
      fillSettingsForm(settings);
      $("set-pw-current").value = "";
      $("set-pw-new").value = "";
      $("set-pw-confirm").value = "";
      $("settings-msg").textContent = "";
      showScreen("settings");
    } catch (err) {
      setError($("menu-error"), err.message);
    }
  });

  $("set-timer").addEventListener("input", () => {
    $("set-timer-val").textContent = $("set-timer").value;
  });
  $("set-skips").addEventListener("input", () => {
    $("set-skips-val").textContent = $("set-skips").value;
  });

  $("settings-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const settings = await api(`/api/settings/${state.user.id}`, {
        method: "PUT",
        body: JSON.stringify({
          theme: $("set-theme").value,
          playerTileColor: $("set-p1").value,
          opponentTileColor: $("set-p2").value,
          questionTimer: Number($("set-timer").value),
          skips: Number($("set-skips").value),
          chanceMode: $("set-chance").value,
        }),
      });
      applySettings(settings);

      const newName = $("set-rename").value.trim();
      if (newName && newName !== state.user.username) {
        const renamed = await api("/api/rename", {
          method: "POST",
          body: JSON.stringify({ username: newName }),
        });
        state.user = renamed.user;
        state.stats = renamed.stats;
        $("menu-user").textContent = `Playing as ${state.user.username}`;
      }

      const cur = $("set-pw-current").value;
      const next = $("set-pw-new").value;
      const confirm = $("set-pw-confirm").value;
      if (cur || next || confirm) {
        await api("/api/password", {
          method: "POST",
          body: JSON.stringify({
            currentPassword: cur,
            newPassword: next,
            confirmPassword: confirm,
          }),
        });
        $("set-pw-current").value = "";
        $("set-pw-new").value = "";
        $("set-pw-confirm").value = "";
      }

      $("settings-msg").textContent = "Settings saved.";
    } catch (err) {
      $("settings-msg").textContent = err.message;
    }
  });

  $("btn-settings-back").addEventListener("click", () => showScreen("menu"));

  $("btn-stats").addEventListener("click", async () => {
    try {
      state.stats = await api(`/api/stats/${state.user.id}`);
      renderStats(state.stats);
      showScreen("stats");
    } catch (err) {
      setError($("menu-error"), err.message);
    }
  });
  $("btn-stats-back").addEventListener("click", () => showScreen("menu"));

  $("btn-leaderboard").addEventListener("click", async () => {
    try {
      setError($("menu-error"), "");
      const data = await api("/api/leaderboard");
      renderLeaderboard(data.leaders || []);
      showScreen("leaderboard");
    } catch (err) {
      setError($("menu-error"), err.message);
    }
  });
  $("btn-leaderboard-back").addEventListener("click", () => showScreen("menu"));

  $("btn-logout").addEventListener("click", async () => {
    try {
      await api("/api/logout", { method: "POST", body: "{}" });
    } catch {
      /* still clear local state */
    }
    state.user = null;
    if (state.socket) {
      state.socket.emit("mp:leave");
      state.socket.disconnect();
      state.socket = null;
    }
    $("login-password").value = "";
    showAuthPanel("login");
    showScreen("login");
  });

  $("btn-quit").addEventListener("click", () => {
    clearTimer();
    state.match = null;
    showScreen("menu");
  });

  $("question-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    clearTimer();
    $("question-dialog").close();
    await submitAnswer({ action: "answer", answer: $("question-answer").value });
  });
  $("btn-skip").addEventListener("click", async () => {
    clearTimer();
    $("question-dialog").close();
    await submitAnswer({ action: "skip" });
  });
  $("btn-result-ok").addEventListener("click", () => {
    $("result-dialog").close();
    showScreen("menu");
  });

  $("btn-mp-create").addEventListener("click", () => {
    setError($("mp-error"), "");
    ensureSocket().emit("mp:create", {
      userId: state.user.id,
      username: state.user.username,
    });
  });
  $("btn-mp-join").addEventListener("click", () => {
    setError($("mp-error"), "");
    ensureSocket().emit("mp:join", {
      code: $("mp-code").value.trim().toUpperCase(),
      userId: state.user.id,
      username: state.user.username,
    });
  });
  $("btn-mp-start").addEventListener("click", () => ensureSocket().emit("mp:start"));
  $("btn-mp-leave").addEventListener("click", () => {
    if (state.socket) state.socket.emit("mp:leave");
    state.mp = null;
    showScreen("menu");
  });
  $("mp-chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const text = $("mp-chat-input").value;
    $("mp-chat-input").value = "";
    ensureSocket().emit("mp:chat", { text });
  });

  (async () => {
    const el = $("db-status");
    if (el) {
      try {
        const info = await api("/api/db");
        el.textContent = info.connected
          ? `Database connected (${info.database}) · ${info.userCount} user(s)`
          : "Database not connected";
        el.classList.toggle("is-online", !!info.connected);
        el.classList.toggle("is-offline", !info.connected);
      } catch (err) {
        el.textContent = `Database not connected — run npm start. ${err.message}`;
        el.classList.add("is-offline");
        el.classList.remove("is-online");
      }
    }

    try {
      const me = await api("/api/me");
      enterApp(me);
    } catch {
      showAuthPanel("login");
      showScreen("login");
    }
  })();
})();
