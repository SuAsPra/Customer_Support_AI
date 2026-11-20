-- ========================================================================
-- AI Customer Support Coaching Assistant - Milestone 1 Schema
-- SQLite-compatible DDL based on Kabilan's System Design Document
-- ========================================================================

PRAGMA foreign_keys = ON;

-- 1. Sessions table
CREATE TABLE IF NOT EXISTS session (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('simulator', 'manual', 'replay')),
    product_context TEXT NOT NULL,
    scenario TEXT NOT NULL,
    persona TEXT,
    emotional_progression TEXT,
    status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'active', 'completed', 'abandoned')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Replay Transcripts table (optional 1:1 with session for replay mode)
CREATE TABLE IF NOT EXISTS replay_transcript (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    file_format TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
);

-- 3. Messages table
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('customer', 'agent')),
    text TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
    UNIQUE (session_id, turn_number, sender)
);

-- 4. Turn Analysis table (1:1 with customer message)
CREATE TABLE IF NOT EXISTS turn_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE,
    intent TEXT NOT NULL,
    emotion TEXT NOT NULL,
    frustration_level REAL NOT NULL CHECK (frustration_level >= 0 AND frustration_level <= 10),
    satisfaction_trend TEXT NOT NULL CHECK (satisfaction_trend IN ('improving', 'stable', 'declining')),
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE
);

-- 5. Knowledge Base Documents table
CREATE TABLE IF NOT EXISTS kb_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    product_domain TEXT DEFAULT 'general',
    file_hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'indexing', 'indexed', 'failed')),
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Knowledge Base Chunks table
CREATE TABLE IF NOT EXISTS kb_chunk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    section TEXT,
    page_number INTEGER DEFAULT 1,
    token_count INTEGER NOT NULL,
    embedding_ref TEXT NOT NULL,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES kb_document(id) ON DELETE CASCADE,
    UNIQUE (document_id, chunk_index)
);

-- 7. Recommendations table (many-to-many link between message and kb_chunk)
CREATE TABLE IF NOT EXISTS recommendation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    relevance_score REAL NOT NULL,
    rank INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES kb_chunk(id) ON DELETE CASCADE
);

-- 8. Coaching Feedback table
CREATE TABLE IF NOT EXISTS coaching_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE,
    agent_message_id INTEGER,
    suggested_reply TEXT NOT NULL,
    tone_score REAL NOT NULL CHECK (tone_score >= 1 AND tone_score <= 10),
    clarity_score REAL NOT NULL CHECK (clarity_score >= 1 AND clarity_score <= 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE
);

-- 9. Coaching Tips table
CREATE TABLE IF NOT EXISTS coaching_tip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    tip_text TEXT NOT NULL,
    position INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feedback_id) REFERENCES coaching_feedback(id) ON DELETE CASCADE
);

-- 10. Escalation Score table
CREATE TABLE IF NOT EXISTS escalation_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
    level TEXT NOT NULL CHECK (level IN ('low', 'medium', 'high', 'critical')),
    reasoning TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    alert_triggered BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE
);

-- 11. Session Report table
CREATE TABLE IF NOT EXISTS session_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    outcome TEXT NOT NULL,
    resolution_score REAL NOT NULL CHECK (resolution_score >= 0 AND resolution_score <= 100),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
);

-- 12. Report Sentiment Points table
CREATE TABLE IF NOT EXISTS report_sentiment_point (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    emotion TEXT NOT NULL,
    frustration_level REAL NOT NULL,
    FOREIGN KEY (report_id) REFERENCES session_report(id) ON DELETE CASCADE
);

-- 13. Report Recommendations table
CREATE TABLE IF NOT EXISTS report_recommendation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    FOREIGN KEY (report_id) REFERENCES session_report(id) ON DELETE CASCADE
);

-- 14. Agent Execution Audit Log table
CREATE TABLE IF NOT EXISTS agent_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    message_id INTEGER,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    attempts INTEGER DEFAULT 1,
    latency_ms INTEGER DEFAULT 0,
    input_json TEXT,
    output_json TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE SET NULL,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_document_hash ON kb_document(file_hash);
CREATE INDEX IF NOT EXISTS idx_kb_document_status ON kb_document(status);
CREATE INDEX IF NOT EXISTS idx_kb_chunk_doc_id ON kb_chunk(document_id);
CREATE INDEX IF NOT EXISTS idx_message_session_turn ON message(session_id, turn_number);
