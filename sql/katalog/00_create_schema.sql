-- ============================================================
-- Schemat AIOP (AI Operacyjny) -- widoki katalogowe CEiM
-- Uruchom jako admin na bazie Comarch XL
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'AIOP')
    EXEC('CREATE SCHEMA AIOP');
GO
