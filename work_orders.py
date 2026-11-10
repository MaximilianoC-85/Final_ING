import json
import os
import pyodbc
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class WorkOrder:
    order_id: str
    description: str
    order_type: str
    status: str
    center: Optional[str] = None
    equipment: Optional[str] = None
    responsible: Optional[str] = None
    priority: Optional[str] = None
    material_code: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None
    is_active: bool = True


class WorkOrderService:
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

    def list_orders(self) -> List[WorkOrder]:
        self.connect()
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT OrderID, Description, OrderType, Status, Center, Equipment, 
                   Responsible, Priority, MaterialCode, Quantity, Notes, IsActive 
            FROM dbo.WorkOrders
            ORDER BY OrderID
            """
        ).fetchall()
        
        return [
            WorkOrder(
                order_id=row[0], description=row[1], order_type=row[2], status=row[3],
                center=row[4], equipment=row[5], responsible=row[6], priority=row[7],
                material_code=row[8], quantity=row[9], notes=row[10], is_active=bool(row[11])
            ) for row in rows
        ]

    def create_order(self, order_id: str, description: str, order_type: str, status: str = "Pendiente", 
                     center: str = None, equipment: str = None, responsible: str = None, 
                     priority: str = None, material_code: str = None, quantity: int = None, notes: str = None) -> WorkOrder:
        self.connect()
        cursor = self.conn.cursor()
        
        if cursor.execute("SELECT 1 FROM dbo.WorkOrders WHERE OrderID = ?", (order_id,)).fetchone():
            raise ValueError(f"La orden {order_id} ya existe.")
            
        cursor.execute(
            """
            INSERT INTO dbo.WorkOrders (
                OrderID, Description, OrderType, Status, Center, Equipment, 
                Responsible, Priority, MaterialCode, Quantity, Notes, IsActive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (order_id, description, order_type, status, center, equipment, 
             responsible, priority, material_code, quantity, notes)
        )
        self.conn.commit()
        
        return WorkOrder(
            order_id, description, order_type, status, center, equipment, 
            responsible, priority, material_code, quantity, notes, True
        )

    def get_order(self, order_id: str) -> Optional[WorkOrder]:
        self.connect()
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT OrderID, Description, OrderType, Status, Center, Equipment, 
                   Responsible, Priority, MaterialCode, Quantity, Notes, IsActive 
            FROM dbo.WorkOrders WHERE OrderID = ?
            """, (order_id,)
        ).fetchone()
        
        if not row:
            return None
            
        return WorkOrder(
            order_id=row[0], description=row[1], order_type=row[2], status=row[3],
            center=row[4], equipment=row[5], responsible=row[6], priority=row[7],
            material_code=row[8], quantity=row[9], notes=row[10], is_active=bool(row[11])
        )

    def update_order(self, order_id: str, description: str = None, order_type: str = None, 
                     status: str = None, center: str = None, equipment: str = None, 
                     responsible: str = None, priority: str = None, material_code: str = None, 
                     quantity: int = None, notes: str = None, is_active: bool = None) -> WorkOrder:
        self.connect()
        
        # Verificar que exista usando el método get_order
        current_order = self.get_order(order_id)
        if not current_order:
            raise ValueError(f"No existe la orden {order_id}.")
            
        # Construir consulta de actualización dinámica
        values = []
        if description is not None: values.append(("Description", description))
        if order_type is not None: values.append(("OrderType", order_type))
        if status is not None: values.append(("Status", status))
        if center is not None: values.append(("Center", center))
        if equipment is not None: values.append(("Equipment", equipment))
        if responsible is not None: values.append(("Responsible", responsible))
        if priority is not None: values.append(("Priority", priority))
        if material_code is not None: values.append(("MaterialCode", material_code))
        if quantity is not None: values.append(("Quantity", quantity))
        if notes is not None: values.append(("Notes", notes))
        if is_active is not None: values.append(("IsActive", 1 if is_active else 0))

        if not values:
            return current_order

        columns = ", ".join(f"{key} = ?" for key, _ in values)
        params = [value for _, value in values] + [order_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE dbo.WorkOrders SET {columns}, UpdatedAt = SYSUTCDATETIME() WHERE OrderID = ?", params)
        self.conn.commit()
        
        return self.get_order(order_id)