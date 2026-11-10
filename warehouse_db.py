import json
import os
import re
from datetime import datetime

import pyodbc


class DatabaseManager:
    DEFAULT_CONFIG = {
        "server": "DESKTOP-K1MB889",
        "database": "SIGA_SAP",
        "username": "",
        "password": "",
        "trusted_connection": True,
    }

    def __init__(self, config_path: str = "db_config.json"):
        self.config_path = os.path.abspath(
            config_path if os.path.isabs(config_path) else os.path.join(os.path.dirname(__file__), config_path)
        )
        self.config = self.load_config()
        self.conn = None

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                merged = self.DEFAULT_CONFIG.copy()
                merged.update(data)
                return self._normalize_config(merged)
            except (json.JSONDecodeError, OSError):
                return self._normalize_config(self.DEFAULT_CONFIG.copy())
        return self._normalize_config(self.DEFAULT_CONFIG.copy())

    def _normalize_config(self, config):
        normalized = dict(config)
        for key in ("server", "database", "username", "password"):
            value = normalized.get(key)
            normalized[key] = str(value) if value is not None else ""
        normalized["trusted_connection"] = bool(normalized.get("trusted_connection", True))
        return normalized

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as fh:
            json.dump(self._normalize_config(self.config), fh, indent=2)

    def get_server_candidates(self):
        configured = str(self.config.get("server") or "DESKTOP-K1MB889").strip()
        candidates = []
        seen = set()
        for value in [
            configured,
            configured.replace("tcp:", "").replace("\\", ""),
            "DESKTOP-K1MB889",
            "localhost",
            "(local)",
            ".",
            "MSSQLSERVER",
            "tcp:DESKTOP-K1MB889,1433",
            "tcp:127.0.0.1,1433",
            "tcp:localhost,1433",
        ]:
            if value and isinstance(value, str) and value not in seen:
                candidates.append(value)
                seen.add(value)
        return candidates

    def connect(self):
        last_error = None
        for server in self.get_server_candidates():
            conn_string = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                f"SERVER={server};DATABASE={str(self.config.get('database') or 'SIGA_SAP')};"
                "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;LoginTimeout=10;"
            )
            try:
                self.conn = pyodbc.connect(conn_string)
                self.conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
                self.conn.setencoding(encoding="utf-8")
                return True
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            "No se pudo conectar a SQL Server con la base SIGA_SAP. Verifique que el servidor esté en ejecución, "
            "que el nombre sea correcto y que la autenticación esté habilitada. "
            f"Detalle técnico: {last_error}"
        ) from last_error

    def run_sql_file(self, filepath: str):
        """Lee y ejecuta un archivo .sql bloque por bloque separando por 'GO'."""
        if self.conn is None:
            raise RuntimeError("La conexión a la base de datos no está activa.")
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No se encontró el archivo SQL: {filepath}")

        cursor = self.conn.cursor()
        with open(filepath, 'r', encoding='utf-8') as file:
            sql_script = file.read()

        batches = re.split(r'(?i)\bGO\b', sql_script)

        for batch in batches:
            batch = batch.strip()
            if batch:
                try:
                    cursor.execute(batch)
                except Exception as exc:
                    raise RuntimeError(f"Error ejecutando el script SQL:\n{batch}\nDetalle: {exc}")

        self.conn.commit()

    def ensure_schema(self, sql_file_name: str = "seed_db.sql"):
        """Busca y ejecuta el archivo SQL asegurando que esté en la misma carpeta que este script."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(current_dir, sql_file_name)

        self.run_sql_file(sql_file_path)

    def get_user(self, username: str, password: str):
        if self.conn is None:
            return None
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT UserName, RoleName, PasswordHash
            FROM dbo.Users
            WHERE UserName = ? AND PasswordHash = ? AND IsActive = 1
            """,
            (username.strip(), password.strip()),
        ).fetchone()
        
        if row is None:
            return None
        return {"UserName": row[0], "RoleName": row[1], "PasswordHash": row[2]}

    def list_sap_materials(self):
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        return cursor.execute(
            """
            SELECT
                m.MaterialCode,
                m.Description,
                ISNULL(i.Quantity, 0) AS Stock,
                ISNULL(b.BinCode, '') AS Location,
                m.BaseUnit AS Unit,
                ISNULL(b.ZoneCode, '') AS ZoneCode,
                ISNULL(b.Aisle, '') AS Aisle,
                COALESCE(b.LevelCode, '') AS Rack,
                ISNULL(b.BinCode, '') AS Position
            FROM dbo.Materials m
            LEFT JOIN dbo.Inventory i ON i.MaterialCode = m.MaterialCode
            LEFT JOIN dbo.Bins b ON b.BinCode = i.BinCode
            ORDER BY m.MaterialCode
            """
        ).fetchall()

    def get_sap_material(self, material_code: str):
        if self.conn is None:
            return None
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT
                m.MaterialCode,
                m.Description,
                ISNULL(i.Quantity, 0) AS Stock,
                ISNULL(b.BinCode, '') AS Location,
                m.BaseUnit AS Unit,
                ISNULL(b.ZoneCode, '') AS ZoneCode,
                ISNULL(b.Aisle, '') AS Aisle,
                COALESCE(b.LevelCode, '') AS Rack,
                ISNULL(b.BinCode, '') AS Position
            FROM dbo.Materials m
            LEFT JOIN dbo.Inventory i ON i.MaterialCode = m.MaterialCode
            LEFT JOIN dbo.Bins b ON b.BinCode = i.BinCode
            WHERE m.MaterialCode = ?
            """,
            (material_code.strip().upper(),),
        ).fetchone()
        return row

    def search_materials(self, query: str):
        if self.conn is None:
            return []
        if not query or not query.strip():
            return self.list_sap_materials()
            
        q = f"%{query.strip()}%"
        cursor = self.conn.cursor()
        
        return cursor.execute(
            """
            SELECT
                m.MaterialCode,
                m.Description,
                ISNULL(i.Quantity, 0) AS Stock,
                ISNULL(b.BinCode, '') AS Location,
                m.BaseUnit AS Unit,
                ISNULL(b.ZoneCode, '') AS ZoneCode,
                ISNULL(b.Aisle, '') AS Aisle,
                COALESCE(b.LevelCode, '') AS Rack,
                ISNULL(b.BinCode, '') AS Position
            FROM dbo.Materials m
            LEFT JOIN dbo.Inventory i ON i.MaterialCode = m.MaterialCode
            LEFT JOIN dbo.Bins b ON b.BinCode = i.BinCode
            WHERE m.MaterialCode COLLATE Modern_Spanish_CI_AI LIKE ? 
               OR m.Description COLLATE Modern_Spanish_CI_AI LIKE ?
            ORDER BY m.MaterialCode
            """,
            (q, q),
        ).fetchall()

    def update_sap_material_stock(self, material_code: str, delta: int):
        if self.conn is None:
            raise RuntimeError("No hay conexión a la base de datos para actualizar stock del material.")

        material_code = material_code.strip().upper()
        cursor = self.conn.cursor()
        current = cursor.execute(
            "SELECT Quantity FROM dbo.Inventory WHERE MaterialCode = ?",
            (material_code,),
        ).fetchone()

        if current is None:
            default_bin = cursor.execute("SELECT TOP 1 BinCode FROM dbo.Bins ORDER BY BinCode").fetchone()
            current_quantity = 0
            cursor.execute(
                "INSERT INTO dbo.Inventory (MaterialCode, Quantity, BinCode) VALUES (?, ?, ?)",
                (material_code, current_quantity, default_bin[0] if default_bin else None),
            )
        else:
            current_quantity = int(current[0]) if current[0] is not None else 0

        new_stock = current_quantity + int(delta)
        if new_stock < 0:
            raise ValueError(f"No se puede dejar stock negativo para {material_code}.")

        cursor.execute(
            "UPDATE dbo.Inventory SET Quantity = ? WHERE MaterialCode = ?",
            (new_stock, material_code),
        )
        self.conn.commit()
        return new_stock

    def update_sap_material_location(self, material_code: str, new_location: str):
        if self.conn is None:
            raise RuntimeError("No hay conexión a la base de datos para actualizar ubicación del material.")

        material_code = material_code.strip().upper()
        new_location = new_location.strip().upper()
        cursor = self.conn.cursor()

        # 1. Verificar si la nueva ubicación ya existe en la tabla Bins
        bin_check = cursor.execute(
            "SELECT BinCode FROM dbo.Bins WHERE BinCode = ?",
            (new_location,)
        ).fetchone()

        # Si la ubicación NO existe, la creamos automáticamente con valores por defecto
        if bin_check is None:
            # Intentamos deducir la Zona y el Pasillo del formato estándar (ej: "A-01-01" -> Zona 'A', Aisle '01')
            parts = new_location.split('-')
            zone_code = parts[0] if len(parts) > 0 else "GENERAL"
            aisle = parts[1] if len(parts) > 1 else "01"
            level_code = parts[2] if len(parts) > 2 else "01"

            cursor.execute(
                """
                INSERT INTO dbo.Bins (BinCode, ZoneCode, Aisle, LevelCode)
                VALUES (?, ?, ?, ?)
                """,
                (new_location, zone_code, aisle, level_code)
            )

        # 2. Verificar si el material ya tiene un registro en Inventory
        existing = cursor.execute(
            "SELECT MaterialCode FROM dbo.Inventory WHERE MaterialCode = ?",
            (material_code,),
        ).fetchone()

        if existing is None:
            # Si no tiene inventario previo, creamos el registro con cantidad 0 y el nuevo BinCode
            cursor.execute(
                "INSERT INTO dbo.Inventory (MaterialCode, Quantity, BinCode) VALUES (?, 0, ?)",
                (material_code, new_location),
            )
        else:
            # Si ya existe, actualizamos su ubicación (BinCode)
            cursor.execute(
                "UPDATE dbo.Inventory SET BinCode = ? WHERE MaterialCode = ?",
                (new_location, material_code),
            )

        self.conn.commit()

    def log_operation(self, material_code: str, operation_type: str, previous_quantity: int, result_quantity: int,
                     previous_location: str, new_location: str, user_name: str, notes: str = ""):
        if self.conn is None:
            return
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.OperationAudit (
                MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                PreviousLocation, NewLocation, UserName, OperationDate, Notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (material_code.strip().upper(), operation_type, previous_quantity, result_quantity, previous_location, new_location, user_name, datetime.now(), notes),
        )
        self.conn.commit()

    def get_audit_logs(self, limit: int = 100):
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        return cursor.execute(
            """
            SELECT TOP (?) MaterialCode, OperationType, PreviousQuantity, ResultingQuantity,
                   PreviousLocation, NewLocation, UserName, OperationDate
            FROM dbo.OperationAudit
            ORDER BY AuditID DESC
            """,
            (limit,),
        ).fetchall()

    def list_work_orders(self):
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        return cursor.execute(
            """
            SELECT OrderID, Description, Center, Equipment, Responsible, Priority, OrderType, Status, MaterialCode, Quantity, IsActive, Notes
            FROM dbo.WorkOrders
            ORDER BY OrderID
            """
        ).fetchall()

    def search_work_orders(self, query: str):
        if self.conn is None:
            return []
        if not query or not query.strip():
            return self.list_work_orders()
        q = f"%{query.strip()}%"
        cursor = self.conn.cursor()
        return cursor.execute(
            """
            SELECT OrderID, Description, Center, Equipment, Responsible, Priority, OrderType, Status, MaterialCode, Quantity, IsActive, Notes
            FROM dbo.WorkOrders
            WHERE OrderID LIKE ? OR Description LIKE ? OR Equipment LIKE ? OR Responsible LIKE ?
            ORDER BY OrderID
            """,
            (q, q, q, q),
        ).fetchall()

    def get_work_order(self, order_id: str):
        if self.conn is None:
            return None
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT OrderID, Description, Center, Equipment, Responsible, Priority, OrderType, Status, MaterialCode, Quantity, IsActive, Notes
            FROM dbo.WorkOrders
            WHERE OrderID = ?
            """,
            (order_id.strip().upper(),),
        ).fetchone()
        return row

    def create_work_order(self, order_id: str, description: str, center: str, equipment: str, responsible: str,
                          priority: str, order_type: str, status: str, material_code: str | None = None,
                          quantity: int | None = None, notes: str | None = None):
        if self.conn is None:
            raise RuntimeError("No hay conexión a la base de datos para crear la OT.")
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.WorkOrders (
                OrderID, Description, Center, Equipment, Responsible, Priority, OrderType, Status,
                MaterialCode, Quantity, IsActive, Notes, CreatedAt, UpdatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
            """,
            (order_id.strip().upper(), description, center, equipment, responsible, priority, order_type, status,
             material_code.strip().upper() if material_code else None, quantity, notes),
        )
        self.conn.commit()

    def update_work_order(self, order_id: str, description: str | None = None, center: str | None = None,
                          equipment: str | None = None, responsible: str | None = None, priority: str | None = None,
                          order_type: str | None = None, status: str | None = None, material_code: str | None = None,
                          quantity: int | None = None, notes: str | None = None, is_active: bool | None = None):
        if self.conn is None:
            raise RuntimeError("No hay conexión a la base de datos para actualizar la OT.")
        current = self.get_work_order(order_id)
        if current is None:
            raise ValueError(f"La OT {order_id} no existe.")

        values = []
        if description is not None:
            values.append(("Description", description))
        if center is not None:
            values.append(("Center", center))
        if equipment is not None:
            values.append(("Equipment", equipment))
        if responsible is not None:
            values.append(("Responsible", responsible))
        if priority is not None:
            values.append(("Priority", priority))
        if order_type is not None:
            values.append(("OrderType", order_type))
        if status is not None:
            values.append(("Status", status))
        if material_code is not None:
            values.append(("MaterialCode", material_code.strip().upper()))
        if quantity is not None:
            values.append(("Quantity", quantity))
        if notes is not None:
            values.append(("Notes", notes))
        if is_active is not None:
            values.append(("IsActive", 1 if is_active else 0))

        if not values:
            return current

        columns = ", ".join(f"{key} = ?" for key, _ in values)
        params = [value for _, value in values] + [order_id.strip().upper()]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE dbo.WorkOrders SET {columns}, UpdatedAt = SYSUTCDATETIME() WHERE OrderID = ?", params)
        self.conn.commit()
        return self.get_work_order(order_id)