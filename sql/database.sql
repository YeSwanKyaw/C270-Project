-- C270 Answer and Conquer — MySQL schema
-- Same workflow as BillReminder:
--   1. Open MySQL Workbench / DBeaver
--   2. Connect to your MySQL server
--   3. Run this whole script (sql/database.sql)
--   4. Put matching DB_* values in .env, then npm start

CREATE DATABASE IF NOT EXISTS answer_and_conquer;
USE answer_and_conquer;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE player_stats (
    user_id INT NOT NULL PRIMARY KEY,
    games_played INT NOT NULL DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    local_wins INT NOT NULL DEFAULT 0,
    ai_wins INT NOT NULL DEFAULT 0,
    total_spaces INT NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    mode VARCHAR(16) NOT NULL,
    result VARCHAR(16) NOT NULL,
    spaces_captured INT NOT NULL DEFAULT 0,
    played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_settings (
    user_id INT NOT NULL PRIMARY KEY,
    theme VARCHAR(16) NOT NULL DEFAULT 'default',
    player_tile_color VARCHAR(16) NOT NULL DEFAULT '#FF0000',
    opponent_tile_color VARCHAR(16) NOT NULL DEFAULT '#ADD8E6',
    question_timer INT NOT NULL DEFAULT 15,
    skips INT NOT NULL DEFAULT 3,
    chance_mode VARCHAR(16) NOT NULL DEFAULT 'normal',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE OR REPLACE VIEW v_player_statistics AS
SELECT
    u.id AS user_id,
    u.username,
    u.email,
    s.games_played,
    s.wins,
    s.losses,
    CASE
        WHEN s.games_played = 0 THEN 0.0
        ELSE ROUND((s.wins * 100.0) / s.games_played, 1)
    END AS win_rate,
    s.local_wins,
    s.ai_wins,
    s.total_spaces
FROM users u
JOIN player_stats s ON s.user_id = u.id;

-- Test accounts: password is password123 (SHA1 hashed like BillReminder)
INSERT INTO users (username, email, password, role) VALUES
('admin', 'admin@test.com', SHA1('password123'), 'admin'),
('user1', 'user@test.com', SHA1('password123'), 'user');

INSERT INTO player_stats (user_id) VALUES (1), (2);
INSERT INTO user_settings (user_id) VALUES (1), (2);
