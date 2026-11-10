USE SIGA_SAP;
GO

IF OBJECT_ID(N'dbo.Materials', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Materials (
        MaterialCode NVARCHAR(50) PRIMARY KEY,
        Description NVARCHAR(255) NOT NULL,
        BaseUnit NVARCHAR(20) NOT NULL DEFAULT 'EA'
    );
END
GO

IF OBJECT_ID(N'dbo.MaterialAuditLog', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.MaterialAuditLog (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        AuditAction NVARCHAR(20) NOT NULL,
        MaterialCode NVARCHAR(50) NOT NULL,
        OldDescription NVARCHAR(255) NULL,
        NewDescription NVARCHAR(255) NULL,
        OldBaseUnit NVARCHAR(20) NULL,
        NewBaseUnit NVARCHAR(20) NULL,
        ChangedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END
GO

CREATE OR ALTER TRIGGER dbo.trg_Materials_Audit
ON dbo.Materials
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.MaterialAuditLog (
        AuditAction,
        MaterialCode,
        OldDescription,
        NewDescription,
        OldBaseUnit,
        NewBaseUnit,
        ChangedAt
    )
    SELECT
        CASE
            WHEN i.MaterialCode IS NOT NULL AND d.MaterialCode IS NULL THEN 'INSERT'
            WHEN i.MaterialCode IS NOT NULL AND d.MaterialCode IS NOT NULL THEN 'UPDATE'
            WHEN i.MaterialCode IS NULL AND d.MaterialCode IS NOT NULL THEN 'DELETE'
        END,
        COALESCE(i.MaterialCode, d.MaterialCode),
        d.Description,
        i.Description,
        d.BaseUnit,
        i.BaseUnit,
        SYSUTCDATETIME()
    FROM inserted i
    FULL OUTER JOIN deleted d ON d.MaterialCode = i.MaterialCode;
END
GO

IF OBJECT_ID(N'dbo.Bins', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Bins (
        BinCode NVARCHAR(50) PRIMARY KEY,
        ZoneCode NVARCHAR(50) NOT NULL,
        Aisle NVARCHAR(20) NOT NULL,
        LevelCode NVARCHAR(20) NOT NULL
    );
END
GO

IF OBJECT_ID(N'dbo.Inventory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Inventory (
        InventoryID INT IDENTITY(1,1) PRIMARY KEY,
        MaterialCode NVARCHAR(50) NOT NULL,
        BinCode NVARCHAR(50) NOT NULL,
        Quantity INT NOT NULL,
        CONSTRAINT FK_Inventory_Material FOREIGN KEY (MaterialCode) REFERENCES dbo.Materials(MaterialCode),
        CONSTRAINT FK_Inventory_Bin FOREIGN KEY (BinCode) REFERENCES dbo.Bins(BinCode)
    );
END
GO

IF OBJECT_ID(N'dbo.Transactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Transactions (
        TransactionID INT IDENTITY(1,1) PRIMARY KEY,
        TransactionType NVARCHAR(30) NOT NULL,
        MaterialCode NVARCHAR(50) NOT NULL,
        SourceBin NVARCHAR(50) NULL,
        DestinationBin NVARCHAR(50) NULL,
        Quantity INT NOT NULL,
        TransactionDate DATETIME NOT NULL DEFAULT GETDATE(),
        Notes NVARCHAR(255) NULL
    );
END
GO

-- Inserción de Materiales (Fila por fila con validación individual)
IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-001')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-001', N'Batería 12V 60Ah', 'EA');

IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-002')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-002', N'Rodamiento de bola 6205', 'EA');

IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-003')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-003', N'Cable eléctrico 2.5mm', 'MT');

IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-004')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-004', N'Perno M8 x 30', 'EA');

IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-005')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-005', N'Lubricante industrial', 'LT');

IF NOT EXISTS (SELECT 1 FROM dbo.Materials WHERE MaterialCode = 'MAT-006')
    INSERT INTO dbo.Materials (MaterialCode, Description, BaseUnit) VALUES ('MAT-006', N'Módulo electrónico de tensión', 'EA');
GO

-- Inserción de Bins (Fila por fila con validación individual)
IF NOT EXISTS (SELECT 1 FROM dbo.Bins WHERE BinCode = 'A-01-01')
    INSERT INTO dbo.Bins (BinCode, ZoneCode, Aisle, LevelCode) VALUES ('A-01-01', 'A', '01', '01');

IF NOT EXISTS (SELECT 1 FROM dbo.Bins WHERE BinCode = 'A-01-02')
    INSERT INTO dbo.Bins (BinCode, ZoneCode, Aisle, LevelCode) VALUES ('A-01-02', 'A', '01', '02');

IF NOT EXISTS (SELECT 1 FROM dbo.Bins WHERE BinCode = 'B-02-01')
    INSERT INTO dbo.Bins (BinCode, ZoneCode, Aisle, LevelCode) VALUES ('B-02-01', 'B', '02', '01');

IF NOT EXISTS (SELECT 1 FROM dbo.Bins WHERE BinCode = 'C-03-01')
    INSERT INTO dbo.Bins (BinCode, ZoneCode, Aisle, LevelCode) VALUES ('C-03-01', 'C', '03', '01');
GO

-- Inserción de Inventario inicial (Fila por fila con validación individual)
IF NOT EXISTS (SELECT 1 FROM dbo.Inventory WHERE MaterialCode = 'MAT-001' AND BinCode = 'A-01-01')
    INSERT INTO dbo.Inventory (MaterialCode, BinCode, Quantity) VALUES ('MAT-001', 'A-01-01', 50);

IF NOT EXISTS (SELECT 1 FROM dbo.Inventory WHERE MaterialCode = 'MAT-002' AND BinCode = 'B-02-01')
    INSERT INTO dbo.Inventory (MaterialCode, BinCode, Quantity) VALUES ('MAT-002', 'B-02-01', 30);
GO
IF OBJECT_ID(N'dbo.WorkOrders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.WorkOrders (
        OrderID NVARCHAR(50) PRIMARY KEY,
        Description NVARCHAR(255) NOT NULL,
        Center NVARCHAR(100) NULL,
        Equipment NVARCHAR(100) NULL,
        Responsible NVARCHAR(100) NULL,
        Priority NVARCHAR(50) NULL,
        OrderType NVARCHAR(50) NOT NULL,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Pendiente',
        MaterialCode NVARCHAR(50) NULL,
        Quantity INT NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        Notes NVARCHAR(255) NULL
    );
END
GO

IF OBJECT_ID(N'dbo.Roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Roles (
        RoleID INT IDENTITY(1,1) PRIMARY KEY,
        RoleName NVARCHAR(50) NOT NULL UNIQUE
    );
END
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        UserName NVARCHAR(50) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(200) NOT NULL,
        RoleName NVARCHAR(50) NOT NULL,
        FullName NVARCHAR(100) NOT NULL,
        IsActive BIT NOT NULL DEFAULT 1
    );
END
GO

IF OBJECT_ID(N'dbo.OperationAudit', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.OperationAudit (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        MaterialCode NVARCHAR(50) NOT NULL,
        OperationType NVARCHAR(50) NOT NULL,
        PreviousQuantity INT NULL,
        ResultingQuantity INT NULL,
        PreviousLocation NVARCHAR(50) NULL,
        NewLocation NVARCHAR(50) NULL,
        UserName NVARCHAR(100) NOT NULL,
        OperationDate DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        Notes NVARCHAR(255) NULL
    );
END
GO

-- Inserción de Roles
IF NOT EXISTS (SELECT 1 FROM dbo.Roles WHERE RoleName = N'Pañolero')
    INSERT INTO dbo.Roles (RoleName) VALUES (N'Pañolero');

IF NOT EXISTS (SELECT 1 FROM dbo.Roles WHERE RoleName = N'Supervisor')
    INSERT INTO dbo.Roles (RoleName) VALUES (N'Supervisor');

IF NOT EXISTS (SELECT 1 FROM dbo.Roles WHERE RoleName = N'Producción')
    INSERT INTO dbo.Roles (RoleName) VALUES (N'Producción');
GO

-- Inserción de Usuarios base
IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE UserName = N'paniolero')
    INSERT INTO dbo.Users (UserName, PasswordHash, RoleName, FullName, IsActive) 
    VALUES (N'paniolero', N'1234', N'Pañolero', N'Usuario Pañolero', 1);

IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE UserName = N'supervisor')
    INSERT INTO dbo.Users (UserName, PasswordHash, RoleName, FullName, IsActive) 
    VALUES (N'supervisor', N'1234', N'Supervisor', N'Usuario Supervisor', 1);

IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE UserName = N'produccion')
    INSERT INTO dbo.Users (UserName, PasswordHash, RoleName, FullName, IsActive) 
    VALUES (N'produccion', N'1234', N'Producción', N'Usuario Producción', 1);
GO
USE SIGA_SAP;
GO