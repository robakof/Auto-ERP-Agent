-- =============================================================================
-- JAS shipments tracking — rejestr wysłanych WZ do JAS FBG
-- Cel: idempotentność (nie wysyłaj WZ drugi raz) + audit trail
-- Wykonać jednorazowo przez SSMS lub administratora bazy
-- =============================================================================

CREATE TABLE AILO.jas_shipments (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    wz_id       INT           NOT NULL,
    numer_wz    NVARCHAR(50)  NOT NULL,
    jas_id      INT           NULL,       -- ID zwrócone przez JAS API (NULL gdy błąd)
    sent_at     DATETIME      NOT NULL DEFAULT GETDATE(),
    status      NVARCHAR(20)  NOT NULL DEFAULT 'sent',  -- 'sent' | 'error'
    error_msg   NVARCHAR(MAX) NULL
);

-- Unikalność: jeden rekord 'sent' per wz_id
CREATE UNIQUE INDEX uix_jas_shipments_wz_sent
    ON AILO.jas_shipments(wz_id)
    WHERE status = 'sent';

-- Szybki lookup po wz_id
CREATE INDEX ix_jas_shipments_wz
    ON AILO.jas_shipments(wz_id);
