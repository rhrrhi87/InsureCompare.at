-- File: docker/postgres-init/01-extensions.sql
--
-- Enable extensions that the application code is prepared to use. The
-- ``vector`` extension only succeeds on a postgres image that ships with the
-- pgvector library; it is wrapped in DO/EXCEPTION so the standard
-- ``postgres:16-alpine`` boots cleanly without it.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

DO $$
BEGIN
    EXECUTE 'CREATE EXTENSION IF NOT EXISTS vector';
EXCEPTION WHEN undefined_file THEN
    RAISE NOTICE 'pgvector not available in this image; embedding columns will use JSONB.';
END
$$;
