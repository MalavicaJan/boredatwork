BEGIN;

-- Existing session tokens are intentionally invalidated.
-- The new application stores SHA-256 hashes instead of raw tokens.
TRUNCATE TABLE sessions;

ALTER TABLE sessions
    DROP CONSTRAINT IF EXISTS sessions_user_id_fkey;

ALTER TABLE sessions
    ALTER COLUMN id TYPE VARCHAR(64);

ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS created_at timestamptz;

ALTER TABLE sessions
    ALTER COLUMN expires_at TYPE timestamptz
    USING expires_at AT TIME ZONE 'UTC';

UPDATE sessions
SET created_at = expires_at - INTERVAL '30 days'
WHERE created_at IS NULL;

ALTER TABLE sessions
    ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE sessions
    ALTER COLUMN expires_at SET NOT NULL;

ALTER TABLE sessions
    ADD CONSTRAINT sessions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS ix_sessions_expires_at
    ON sessions (expires_at);

COMMIT;
