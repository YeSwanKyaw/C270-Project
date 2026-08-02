# Answer and Conquer (Web-first)

Browser game with **MySQL** stats and optional Flask bot for Smart AI / CPU.

## Project layout

```
desktop/     Legacy Tkinter UI (screens, engine, LAN network)
bot/         Flask Smart AI / CPU API (gamemode.py)
web/         Express + Socket.IO website (app.js, public/, db.js)
devops/      Dockerfile, Jenkinsfile, Ansible
sql/         database.sql (import in MySQL Workbench)
Assets/      Images for desktop gamemode select
tests/       pytest for bot + desktop engine
```

Root keeps: `package.json`, `docker-compose.yml`, `questions.json`, `.env`, `main.py` (shim → desktop).

## Quick start

1. **Import the database** (same workflow as BillReminder):
   - Open MySQL Workbench / DBeaver
   - Run [`sql/database.sql`](sql/database.sql)
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

Jenkins runs **CI** (test + build Docker images) and **CD** (Ansible deploys web + bot + MySQL). Desktop Tkinter is not deployed.

| Stage | What happens |
|--------|----------------|
| Checkout | Pull repo from Git |
| Test Python bot | `pytest tests/` |
| Test Node web | `npm test` in `web/` (may start MySQL via Compose) |
| Build images | `devops/Dockerfile` (bot) + `web/Dockerfile` (web) |
| Push images | Only if Jenkins env `DOCKER_REGISTRY` is set |
| Deploy | Ansible on `main` / `master` → Docker Compose on target host |

### Files

- Pipeline: [`devops/Jenkinsfile`](devops/Jenkinsfile) — set Jenkins **Script Path** to `devops/Jenkinsfile`
- Ansible: [`devops/ansible/`](devops/ansible/) (`inventory.ini`, `playbook.yml`, compose template)
- Bot image: [`devops/Dockerfile`](devops/Dockerfile)
- Web image: [`web/Dockerfile`](web/Dockerfile)

### Jenkins credentials (IDs must match)

| Credential ID | Type | Used for |
|---------------|------|----------|
| `groq-api-key` | Secret text | Smart AI bot (`GROQ_API_KEY`) |
| `ansible-ssh-key` | SSH Username with private key | Ansible SSH to deploy host |
| `docker-registry` | Username/password (optional) | Push/pull images when `DOCKER_REGISTRY` is set |

### Agent requirements

Git, Python 3 + venv, Node/npm, Docker + Compose plugin, Ansible, and network access to the deploy host (or localhost).

### Wire a Jenkins job

1. Create a **Pipeline** job → **Pipeline script from SCM**.
2. Point SCM at this GitHub repo; branch `master` (or `main`).
3. Set **Script Path** to `devops/Jenkinsfile`.
4. Add the credentials above (IDs exact).
5. Optional: set job/env `DOCKER_REGISTRY` (e.g. Docker Hub namespace) to enable Push.
6. **Build Now** (or push to `master`) and confirm stages: Test → Build → Deploy.

### Local CD smoke (no Jenkins)

Build and run the stack:

```bash
docker compose up -d --build
```

Or deploy with Ansible to **localhost** (default inventory):

```bash
ansible-playbook -i devops/ansible/inventory.ini devops/ansible/playbook.yml \
  -e "bot_image=answer-and-conquer-bot:latest" \
  -e "web_image=answer-and-conquer-web:latest" \
  -e "groq_api_key=YOUR_KEY"
```

### Deploy to EC2

1. In [`devops/ansible/inventory.ini`](devops/ansible/inventory.ini), comment out the local host and set `ansible_host` / `ansible_user` for your instance.
2. Open security-group TCP **3000** (web) and **5050** (bot).
3. Prefer setting `DOCKER_REGISTRY` so the instance can `docker pull` images built by Jenkins.
4. Use the same Jenkins credentials (`ansible-ssh-key` = EC2 key).

### Verify after deploy

```bash
docker ps   # expect aac-web, aac-bot-api, aac-mysql
curl http://127.0.0.1:3000/health
```

App UI: **http://HOST:3000** (localhost or EC2 public IP).

Ansible installs under `/opt/answer-and-conquer` (compose, `.env`, and `sql/database.sql` for MySQL init).

## Legacy desktop

```bash
python main.py
```

Use only if you need the old Tkinter UI; new work targets the web app.
## Test CI/CD pipeline
Updated by Reeve for CI/CD testing