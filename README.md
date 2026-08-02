# Answer and Conquer (Web-first)

Browser game with **MySQL** stats and optional Flask bot for Smart AI / CPU.

## Project layout

```
desktop/     Legacy Tkinter UI (screens, engine, LAN network)
bot/         Flask Smart AI / CPU API (gamemode.py)
web/         Express + Socket.IO website (app.js, public/, db.js)
sql/         database.sql (import in MySQL Workbench)
Assets/      Images for desktop gamemode select
tests/       pytest for bot + desktop engine
```

Root keeps: `package.json`, `questions.json`, `.env`, `main.py` (shim → desktop).

## Quick start

1. **Import the database** (same workflow as BillReminder):
   - Open MySQL Workbench / DBeaver
   - Run [`sql/database.sql`](sql/database.sql)
2. Copy `.env.example` → `.env` and set your MySQL login + session secret:
   ```
   DB_HOST=mysql-2e31fad1-azrielthekiller-37d5.l.aivencloud.com
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=answer_and_conquer
   SESSION_SECRET=change-this-to-a-long-random-string
   ```
3. Start the web app:
   ```bash
   cd web
   npm install
   npm start app.js
   ```
4. Open **http://localhost:3000** for local testing, or visit our live production site at **https://c270-project.onrender.com/

**Test login:** email `user@test.com` / password `password123`  
Passwords use MySQL `SHA1(?)` (same as BillReminder). Sessions last 1 week.

Optional bot (Smart AI / better CPU):

```bash
pip install -r requirements.txt
python bot/gamemode.py
```

## Features (web)

| Screen | What it does |
|--------|----------------|
| Login / Register | Email + password (`SHA1`), session cookie remembers you |
| Main menu | VS Bot, Local 2P, Online Multiplayer, Stats, Settings |
| Rules lobby | Pre-match rules (same content as desktop rules lobby) |
| Settings | Theme, tile colors, timer, skips, chance mode, rename, change password |
| Game | 5×5 board + trivia; settings applied to engine |
| Online MP | Socket.IO rooms (create/join code), chat, synced board |
| Stats | Wins / losses / spaces from MySQL |

Database: import [`sql/database.sql`](sql/database.sql), then connect with `DB_*` in `.env`

## Architecture

```
Browser (:3000)
  ├─ Express REST  →  MySQL (stats + settings)
  ├─ Socket.IO     →  multiplayer rooms
  └─ HTTP          →  Flask bot (:5050) for cpu/ai moves
```

## Environment (`.env`)

See `.env.example` — `DB_*`, `SESSION_SECRET`, `BOT_API_BASE`, `GROQ_API_KEY`, `WEB_PORT`.

## Tests

```bash
npm test                 # Node engine + DB tests
python -m pytest tests/  # Python bot / engine tests
```

## CI/CD


### Deploy to Render (Cloud Production)

Our application is deployed using Render's fully managed web services.

1. **Create Web Services:** In the Render dashboard, create separate "Web Services" for the Node.js frontend and the Flask bot.
2. **Connect Repository:** Link the services directly to the `main` branch of this GitHub repository.
3. **Environment Configuration:** In the Render "Environment" tab for each service, input the required variables (e.g., `DB_HOST`, `DB_PASSWORD`, `GROQ_API_KEY`) ensuring sensitive keys are not hardcoded.
4. **Auto-Deploy:** Render will automatically build and spin up the instances. Any future commits pushed to GitHub will trigger an automatic redeployment.


### Verify after deploy

1. Open the Render dashboard and confirm both the Web and Bot services show a green `Live` status.
2. Check the "Logs" tab in Render to ensure there are no startup errors.
3. Visit the live application URL provided by Render (e.g., `https://your-app-name.onrender.com`).
## Legacy desktop

```bash
python main.py
```

Use only if you need the old Tkinter UI; new work targets the web app.
## Test CI/CD pipeline
Updated by Reeve for CI/CD testing hello there