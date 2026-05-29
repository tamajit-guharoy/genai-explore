-- Cognee PostgreSQL initialization script
-- Creates the schema for Cognee's relational store

-- Enable pgvector extension for vector operations (optional fallback)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Document tracking table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash TEXT NOT NULL,
    file_path TEXT,
    dataset_name TEXT NOT NULL,
    user_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_dataset ON documents(dataset_name);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);

-- Chunk tracking table
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    token_count INT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);

-- Dataset permissions table
CREATE TABLE IF NOT EXISTS dataset_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('reader', 'writer', 'admin', 'owner')),
    granted_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dataset_name, user_id)
);

CREATE INDEX IF NOT EXISTS idx_permissions_dataset ON dataset_permissions(dataset_name);
CREATE INDEX IF NOT EXISTS idx_permissions_user ON dataset_permissions(user_id);

-- Session memory table (V2 API)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    user_id TEXT,
    data JSONB NOT NULL,
    is_promoted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_session ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
