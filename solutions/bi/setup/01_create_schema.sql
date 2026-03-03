-- ============================================================
-- Skrypt inicjalizacyjny schematu BI
-- Uruchamia: DBA (konto z uprawnieniami DDL)
-- Baza: ERPXL_CEIM
-- ============================================================

-- 1. Utwórz schema
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'BI')
    EXEC('CREATE SCHEMA BI');
GO

-- 2. Utwórz konto read-only dla bota i Power BI
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'CEiM_BI')
BEGIN
    -- Zmień hasło przed uruchomieniem!
    CREATE LOGIN CEiM_BI WITH PASSWORD = 'ZMIEN_TO_HASLO';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'CEiM_BI')
    CREATE USER CEiM_BI FOR LOGIN CEiM_BI;
GO

-- 3. Uprawnienia: SELECT na całym schemacie BI (tylko)
GRANT SELECT ON SCHEMA::BI TO CEiM_BI;
GO

-- 4. Brak dostępu do CDN.* (domyślne — nie dawaj żadnych uprawnień do CDN)
-- Weryfikacja:
-- SELECT HAS_PERMS_BY_NAME('CDN.TwrKarty', 'OBJECT', 'SELECT');  -- powinno zwrócić 0

-- ============================================================
-- UWAGI:
-- - Widoki w schemacie BI są tworzone przez konto DBA (nie CEiM_BI)
-- - CEiM_BI: SELECT na BI.* ONLY
-- - W widokach używamy DATEADD(d, kolumna, '18001228') do konwersji dat Clarion
-- - CDN.NumerDokumentu / CDN.DokMapTypDokumentu niedostępne dla CEiM_Reader
--   → numery dokumentów konstruowane ręcznie w widokach
-- ============================================================
