-- TrackQ — one-time MySQL setup
-- Run this file once against your local MySQL server before starting the backend.
-- Usage (from the backend/ folder):
--   mysql -u root -p < sql/init.sql
--
-- What it does:
--   1. Creates the `trackq_db` schema (utf8mb4 so emoji/unicode player names work)
--   2. Creates a dedicated app user `trackq_user` — safer than using root in .env
--   3. Grants that user full access to trackq_db only (not other schemas)

-- 1. Schema
CREATE DATABASE IF NOT EXISTS trackq_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. Dedicated user
--    Replace 'CHANGE_ME_STRONG_PASSWORD' with a real password, then paste the
--    same password into backend/.env under DATABASE_URL.
CREATE USER IF NOT EXISTS 'trackq_user'@'localhost'
    IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';

-- 3. Permissions — scoped to trackq_db only
GRANT ALL PRIVILEGES ON trackq_db.* TO 'trackq_user'@'localhost';

FLUSH PRIVILEGES;

-- Sanity check (optional — run manually after the script)
-- SHOW DATABASES;
-- SELECT User, Host FROM mysql.user WHERE User = 'trackq_user';
