-- DevFlow schema (no demo data). Runs automatically the first time the
-- PostgreSQL container starts (mounted into /docker-entrypoint-initdb.d).

CREATE TABLE IF NOT EXISTS services (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(80)  NOT NULL UNIQUE,
    version          VARCHAR(30)  NOT NULL,
    environment      VARCHAR(20)  NOT NULL CHECK (environment IN ('development','staging','production')),
    status           VARCHAR(20)  NOT NULL DEFAULT 'running' CHECK (status IN ('running','stopped','failed')),
    description      VARCHAR(255) DEFAULT '',
    last_deployed_at TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deployments (
    id          SERIAL PRIMARY KEY,
    service_id  INTEGER     NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    version     VARCHAR(30) NOT NULL,
    status      VARCHAR(20) NOT NULL,
    method      VARCHAR(30) NOT NULL DEFAULT 'Docker Compose',
    deployed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               SERIAL PRIMARY KEY,
    pipeline_name    VARCHAR(80) NOT NULL,
    build_number     INTEGER     NOT NULL,
    status           VARCHAR(20) NOT NULL,
    duration_seconds INTEGER     DEFAULT 0,
    trigger          VARCHAR(40) DEFAULT 'Manual',
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deployments_service ON deployments(service_id);

-- No sample data is inserted: a fresh install starts with 0 services,
-- 0 deployments and 0 pipeline runs. Real records come from the app and Jenkins.
