-- One-shot for Aiven (Azriel): paste/run this if the DB already exists.
-- Safe to re-run; does not recreate tables or seed data.

CREATE OR REPLACE VIEW v_global_leaderboard AS
SELECT
    u.id AS user_id,
    u.username,
    s.games_played,
    s.wins,
    s.losses,
    CASE
        WHEN s.games_played = 0 THEN 0.0
        ELSE ROUND((s.wins * 100.0) / s.games_played, 1)
    END AS win_rate,
    s.total_spaces
FROM users u
JOIN player_stats s ON s.user_id = u.id
ORDER BY s.wins DESC, win_rate DESC, s.total_spaces DESC, u.username ASC;
