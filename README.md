# Answer and Conquer (Web-first)

Browser game with **MySQL** stats and optional Flask bot for Smart AI / CPU.

Tkinter (`main.py`) remains in the repo as **legacy desktop** code. The primary app is the website.

## Quick start

1. **Import the database** (same workflow as BillReminder):
   - Open MySQL Workbench / DBeaver
   - Run [`database.sql`](database.sql)
2. Copy `.env.example` → `.env` and set your MySQL login + session secret:
   ```
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=answer_and_conquer
   SESSION_SECRET=change-this-to-a-long-random-string
   ```
3. Start the web app:
   ```bash
   npm install
   npm start
   ```
4. Open **http://127.0.0.1:3000**

**Test login (from `database.sql`):** email `user@test.com` / password `password123`  
Passwords are stored with MySQL `SHA1(?)` (same as BillReminder). Sessions last 1 week.

Optional bot (Smart AI / better CPU):

```bash
pip install -r requirements.txt
python gamemode.py
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

Database: import [`database.sql`](database.sql), then connect with `DB_*` in `.env`

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

Jenkins builds **bot** + **web** images and Ansible deploys them (see `Jenkinsfile`, `ansible/`). Desktop Tkinter is not deployed.

## Legacy desktop

```bash
python main.py
```

Use only if you need the old Tkinter UI; new work targets the web app.
