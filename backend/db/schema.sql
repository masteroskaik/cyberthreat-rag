-- Schéma PostgreSQL du projet CyberThreat RAG
-- À exécuter sur Neon (SQL Editor) ou en local avant de lancer le pipeline.

CREATE EXTENSION IF NOT EXISTS vector;

-- Table des CVE (National Vulnerability Database)
CREATE TABLE IF NOT EXISTS cves (
    id TEXT PRIMARY KEY,                  -- ex: CVE-2024-12345
    description TEXT NOT NULL,
    cvss_score NUMERIC,
    cvss_severity TEXT,
    published_at TIMESTAMP,
    last_modified_at TIMESTAMP,
    affected_products JSONB DEFAULT '[]',
    raw_data JSONB
);

-- Table CISA KEV (vulnérabilités activement exploitées)
CREATE TABLE IF NOT EXISTS kev_entries (
    cve_id TEXT PRIMARY KEY REFERENCES cves(id) ON DELETE CASCADE,
    vulnerability_name TEXT,
    date_added DATE,
    required_action TEXT,
    due_date DATE,
    known_ransomware_use TEXT
);

-- Table des techniques MITRE ATT&CK
CREATE TABLE IF NOT EXISTS attack_techniques (
    id TEXT PRIMARY KEY,                  -- ex: T1059
    name TEXT NOT NULL,
    description TEXT,
    tactics JSONB DEFAULT '[]',
    platforms JSONB DEFAULT '[]',
    external_references JSONB DEFAULT '[]'
);

ALTER TABLE attack_techniques ADD COLUMN IF NOT EXISTS platforms JSONB DEFAULT '[]';
ALTER TABLE attack_techniques ADD COLUMN IF NOT EXISTS external_references JSONB DEFAULT '[]';

-- Table des chunks vectorisés (le cœur du retrieval RAG)
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,            -- 'cve', 'kev', 'attack_technique'
    source_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(256),                -- dimension du modèle Cohere embed-v4.0
    metadata JSONB DEFAULT '{}',
    content_tsv TSVECTOR                  -- pour la recherche full-text (partie "mots-clés" de l'hybride)
);

-- Index pour la recherche vectorielle (approximation rapide par IVFFlat)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index pour la recherche full-text
CREATE INDEX IF NOT EXISTS idx_chunks_tsv
    ON chunks USING GIN (content_tsv);

-- Trigger pour maintenir content_tsv à jour automatiquement
CREATE OR REPLACE FUNCTION chunks_tsv_update() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chunks_tsv ON chunks;
CREATE TRIGGER trg_chunks_tsv
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION chunks_tsv_update();
