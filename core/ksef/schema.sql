-- KSeF Shadow DB schema v1 — persystencja wysyłek faktur do KSeF
-- Single writer (daemon) + N readers (CLI) wspierane przez WAL mode.
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS ksef_wysylka (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    gid_erp           INTEGER NOT NULL,
    rodzaj            TEXT    NOT NULL CHECK (rodzaj IN ('FS', 'FSK', 'FSK_SKONTO')),
    nr_faktury        TEXT    NOT NULL,
    data_wystawienia  DATE    NOT NULL,
    xml_path          TEXT    NOT NULL,
    xml_hash          TEXT    NOT NULL,
    status            TEXT    NOT NULL CHECK (status IN (
                          'DRAFT','QUEUED','AUTH_PENDING',
                          'SENT','ACCEPTED','REJECTED','ERROR'
                      )),
    ksef_session_ref  TEXT,
    ksef_invoice_ref  TEXT,
    ksef_number       TEXT,
    upo_path          TEXT,
    error_code        TEXT,
    error_msg         TEXT,
    attempt           INTEGER NOT NULL DEFAULT 1,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    queued_at         TIMESTAMP,
    sent_at           TIMESTAMP,
    accepted_at       TIMESTAMP,
    rejected_at       TIMESTAMP,
    errored_at        TIMESTAMP,
    UNIQUE (gid_erp, rodzaj, attempt)
);

CREATE INDEX IF NOT EXISTS idx_ksef_status
    ON ksef_wysylka(status);
CREATE INDEX IF NOT EXISTS idx_ksef_gid_rodzaj
    ON ksef_wysylka(gid_erp, rodzaj);
CREATE INDEX IF NOT EXISTS idx_ksef_xml_hash
    ON ksef_wysylka(xml_hash);

CREATE TABLE IF NOT EXISTS ksef_transition (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    wysylka_id      INTEGER NOT NULL REFERENCES ksef_wysylka(id),
    from_status     TEXT    NOT NULL,
    to_status       TEXT    NOT NULL,
    occurred_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meta_json       TEXT
);

CREATE INDEX IF NOT EXISTS idx_ksef_transition_wysylka
    ON ksef_transition(wysylka_id, occurred_at);

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT OR IGNORE INTO schema_version(version) VALUES (1);
