import json
import os
import pyodbc
from datetime import datetime
from typing import Dict, List, Optional


class AuditService:
    DEFAULT_CONFIG = {
        "server": "DESKTOP-K1MB889", 
        "database": "SIGA_SAP",
        "username": "",
        "password": "",
        "trusted_connection": True,
    }

    def __init__(self, config_path: str = "db_config.json"):
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

    def connect(self):
        if self.conn is not None:
            return
            
        server = self.config.get("server", "localhost")
        database = self.config.get("database", "SIGA_SAP")
        
        if self.config.get("trusted_connection", True):
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
        else:
            username = self.config.get("username", "")
            password = self.config.get("password", "")
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
            
        self.conn = pyodbc.connect(conn_str)

    def log_transaction(self, material_code: str, operation_type: str, previous_quantity: Optional[int], result_quantity: Optional[int],
                       previous_location: Optional[str], new_location: Optional[str], username: str, notes: str = "") -> Dict:
        self.connect()
        cursor = self.conn.cursor()
        
        now = datetime.now()
        
        cursor.execute(
            """
            INSERT INTO dbo.OperationAudit (
                MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                PreviousLocation, NewLocation, UserName, OperationDate, Notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (material_code, operation_type, previous_quantity, result_quantity, 
             previous_location, new_location, username, now, notes)
        )
        self.conn.commit()
        
        # Devolvemos el diccionario para mantener compatibilidad con el resto del código
        return {
            "material_code": material_code,
            "operation_type": operation_type,
            "previous_quantity": previous_quantity,
            "result_quantity": result_quantity,
            "previous_location": previous_location,
            "new_location": new_location,
            "username": username,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes,
        }

    def list_transactions(self, limit: int = 100) -> List[Dict]:
        """Devuelve los últimos registros de auditoría (por defecto los últimos 100)."""
        self.connect()
        cursor = self.conn.cursor()
        
        # Ordenamos por AuditID DESC para ver siempre los más recientes primero
        rows = cursor.execute(
            """
            SELECT MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                   PreviousLocation, NewLocation, UserName, OperationDate, Notes
            FROM dbo.OperationAudit
            ORDER BY AuditID DESC
            """
        ).fetchmany(limit)
        
        records = []
        for row in rows:
            records.append({
                "material_code": row[0],
                "operation_type": row[1],
                "previous_quantity": row[2],
                "result_quantity": row[3],
                "previous_location": row[4],
                "new_location": row[5],
                "username": row[6],
                # Convertimos el objeto datetime de SQL a string para mantener compatibilidad
                "timestamp": row[7].strftime("%Y-%m-%d %H:%M:%S") if row[7] else None,
                "notes": row[8],
            })
            
        return records