-- deployer_procedures.sql
-- Stored procedures dla CEiM_Deployer — bezpieczne zarządzanie schematami i użytkownikami AI
-- Wymaganie: CEiM_Deployer dostaje EXECUTE na te 3 procedury; zero bezpośrednich uprawnień systemowych.
-- Właściciel schematów AI: CDN (ownership chaining do tabel produkcyjnych).


-- ============================================================
-- Tabela kontrolna
-- ============================================================

IF OBJECT_ID('dbo.deployer_created_users', 'U') IS NULL
    CREATE TABLE dbo.deployer_created_users (
        UserName   nvarchar(128) NOT NULL PRIMARY KEY,
        LoginName  nvarchar(128) NOT NULL,
        created_at datetime2    NOT NULL DEFAULT GETDATE()
    );
GO


-- ============================================================
-- 1. dbo.AI_CreateSchema(@Name)
--    Tworzy schemat z prefiksem AI, AUTHORIZATION CDN.
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.AI_CreateSchema
    @Name nvarchar(128)
AS
BEGIN
    SET NOCOUNT ON;

    IF LEFT(@Name, 2) <> N'AI'
    BEGIN
        RAISERROR('Schemat musi mieć prefiks AI.', 16, 1);
        RETURN;
    END

    IF EXISTS (SELECT 1 FROM sys.schemas WHERE name = @Name)
    BEGIN
        RAISERROR('Schemat już istnieje: %s', 16, 1, @Name);
        RETURN;
    END

    DECLARE @sql nvarchar(500) =
        N'CREATE SCHEMA ' + QUOTENAME(@Name) + N' AUTHORIZATION CDN';
    EXEC sp_executesql @sql;
END;
GO


-- ============================================================
-- 2. dbo.AI_CreateUser(@UserName, @LoginName)
--    Tworzy użytkownika DB i rejestruje go w tabeli kontrolnej.
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.AI_CreateUser
    @UserName  nvarchar(128),
    @LoginName nvarchar(128)
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1 FROM sys.database_principals
        WHERE name = @UserName AND type IN ('S', 'U', 'G')
    )
    BEGIN
        RAISERROR('Użytkownik już istnieje: %s', 16, 1, @UserName);
        RETURN;
    END

    DECLARE @sql nvarchar(500) =
        N'CREATE USER ' + QUOTENAME(@UserName) +
        N' FOR LOGIN ' + QUOTENAME(@LoginName);
    EXEC sp_executesql @sql;

    INSERT INTO dbo.deployer_created_users (UserName, LoginName)
    VALUES (@UserName, @LoginName);
END;
GO


-- ============================================================
-- 3. dbo.AI_GrantSchemaAccess(@UserName, @SchemaName)
--    Nadaje SELECT na schemacie AI użytkownikowi z tabeli kontrolnej.
-- ============================================================

CREATE OR ALTER PROCEDURE dbo.AI_GrantSchemaAccess
    @UserName   nvarchar(128),
    @SchemaName nvarchar(128)
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (
        SELECT 1 FROM dbo.deployer_created_users WHERE UserName = @UserName
    )
    BEGIN
        RAISERROR('Użytkownik nie jest w tabeli deployer_created_users: %s', 16, 1, @UserName);
        RETURN;
    END

    IF LEFT(@SchemaName, 2) <> N'AI'
    BEGIN
        RAISERROR('Schemat musi mieć prefiks AI: %s', 16, 1, @SchemaName);
        RETURN;
    END

    IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = @SchemaName)
    BEGIN
        RAISERROR('Schemat nie istnieje: %s', 16, 1, @SchemaName);
        RETURN;
    END

    DECLARE @sql nvarchar(500) =
        N'GRANT SELECT ON SCHEMA::' + QUOTENAME(@SchemaName) +
        N' TO ' + QUOTENAME(@UserName);
    EXEC sp_executesql @sql;
END;
GO


-- ============================================================
-- Uprawnienia dla CEiM_Deployer
-- ============================================================

GRANT EXECUTE ON dbo.AI_CreateSchema      TO [CEiM_Deployer];
GRANT EXECUTE ON dbo.AI_CreateUser        TO [CEiM_Deployer];
GRANT EXECUTE ON dbo.AI_GrantSchemaAccess TO [CEiM_Deployer];
GO
