CREATE ROLE aswo LOGIN SUPERUSER PASSWORD 'Stewie12';

CREATE TABLE osu_user (
    osu_username TEXT,
    user_id BIGINT PRIMARY KEY
);

CREATE TABLE prefix (
    guild_id BIGINT,
    prefix TEXT
);

CREATE TABLE replay_config (
   	user_id BIGINT PRIMARY KEY,
    skin_id INT
);