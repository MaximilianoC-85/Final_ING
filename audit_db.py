import json
import os
from datetime import datetime
import pyodbc

class AuditDatabase:
    DEFAULT_CONFIG = {
        "server": "DESKTOP-K1MB889", 
        "database": "SIGA_SAP",
        "username": "",
        "password": "",
        "trusted_connection": True,
    }

    def __init__(self, config_path: str = "audit_db_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.conn = None

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                merged = self.DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
            except (json.JSONDecodeError, OSError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as fh:
            json.dump(self.config, fh, indent=2)

    def get_connection_string(self):
        server = self.config.get("server", "localhost")
        database = self.config.get("database", "SIGA_SAP")
        
        if self.config.get("trusted_connection", True):
            return (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                f"SERVER={server};DATABASE={database};Trusted_Connection=yes;"
                "Encrypt=yes;TrustServerCertificate=yes;"
            )
            
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        return (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
            "Encrypt=yes;TrustServerCertificate=yes;"
        )

    def connect(self):
        if self.conn is not None:
            return
            
        try:
            self.conn = pyodbc.connect(self.get_connection_string())
            # Esto es clave para que los usuarios o notas con tildes no den error
            self.conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
            self.conn.setencoding(encoding="utf-8")
            return True
        except Exception as exc:
            raise RuntimeError(f"No se pudo conectar a la base de auditoría: {exc}") from exc

    def log_operation(self, material_code: str, operation_type: str, user_name: str, 
                      previous_quantity: int = None, resulting_quantity: int = None,
                      previous_location: str = None, new_location: str = None, notes: str = None):
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO dbo.OperationAudit (
                MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                PreviousLocation, NewLocation, UserName, OperationDate, Notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                material_code,
                operation_type,
                previous_quantity,
                resulting_quantity,
                previous_location,
                new_location,
                user_name,
                datetime.now(),
                notes,
            ),
        )
        self.conn.commit()

    def get_recent_operations(self, limit: int = 100):
        self.connect()
        cursor = self.conn.cursor()
        
        return cursor.execute(
            """
            SELECT TOP (?) MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                   PreviousLocation, NewLocation, UserName, OperationDate, Notes
            FROM dbo.OperationAudit
            ORDER BY AuditID DESC
            """,
            (limit,),
        ).fetchall()