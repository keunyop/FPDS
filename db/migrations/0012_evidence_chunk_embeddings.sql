BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS evidence_chunk_embedding (
    evidence_chunk_embedding_id text PRIMARY KEY,
    evidence_chunk_id text NOT NULL REFERENCES evidence_chunk(evidence_chunk_id) ON DELETE CASCADE,
    vector_namespace text NOT NULL,
    embedding_model_id text NOT NULL,
    embedding_dimensions integer NOT NULL CHECK (embedding_dimensions = 64),
    embedding_source text NOT NULL,
    embedding_source_text_hash text NOT NULL,
    embedding vector(64) NOT NULL,
    embedding_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (evidence_chunk_id, vector_namespace, embedding_model_id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_chunk_embedding_chunk
    ON evidence_chunk_embedding (evidence_chunk_id);

CREATE INDEX IF NOT EXISTS idx_evidence_chunk_embedding_scope
    ON evidence_chunk_embedding (vector_namespace, embedding_model_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_chunk_embedding_vector
    ON evidence_chunk_embedding
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 32);

INSERT INTO migration_history (migration_name)
VALUES ('0012_evidence_chunk_embeddings')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
