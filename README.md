# SIGA-SAP WM (Sistema Integral de Gestión de Almacén)

Sistema de gestión de almacén (Warehouse Management) desarrollado en **Python** con **Tkinter** para la interfaz gráfica, conectado de manera directa a **SQL Server** mediante `pyodbc`, integrando control de roles, trazabilidad de operaciones, auditoría y ejecución automatizada de scripts de base de datos.

---

## 🚀 Características Principales

* **Arquitectura de Base de Datos Centralizada (`SIGA_SAP`)**: Conexión nativa a SQL Server eliminando tablas de simulación y utilizando esquemas relacionales reales (`Materials`, `Bins`, `Inventory`, `WorkOrders`, `Users`, `Roles`, `OperationAudit`).
* **Automatización de Esquema (`seed_db.sql`)**: Inicialización y creación automática de tablas, restricciones, llaves foráneas y datos iniciales mediante un único archivo SQL maestro ejecutado por bloques desde Python.
* **Control de Acceso basado en Roles (RBAC)**: Autenticación de usuarios validada contra la base de datos (con respaldo en memoria) y jerarquía de permisos estrictamente aplicada en la interfaz gráfica:
  * **Pañolero**: Gestión de materiales, stock y ubicaciones (sin acceso a Dashboard ni Órdenes).
  * **Producción**: Visualización de materiales y gestión de órdenes de producción (sin acceso a Dashboard).
  * **Supervisor**: Acceso total a todas las secciones, gestión de órdenes, auditoría y control operativo.
* **Gestión de Stock y Ubicaciones**: 
  * Operaciones de incremento, reducción y reubicación de inventario con validaciones de stock negativo.
  * Creación dinámica y automática de nuevas ubicaciones (`BinCode`) al vuelo si estas no existen en el maestro.
* **Órdenes de Trabajo (OT)**: Creación, consulta y modificación de órdenes de trabajo para mantenimiento y producción con soporte de filtrado dinámico.
* **Auditoría de Transacciones**: Registro detallado e inmutable de cada movimiento de stock, cambio de ubicación y operaciones de usuario con marcas de tiempo precisas (`DATETIME2`).
* **Soporte Unicode y Acentos (`COLLATE`)**: Manejo nativo de caracteres especiales, tildes y búsquedas insensibles a acentos (`Accent-Insensitive`) en catálogos y materiales.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.x
* **Interfaz Gráfica:** Tkinter / TTK (con estilos personalizados en modo oscuro)
* **Base de Datos:** Microsoft SQL Server
* **Driver de Conexión:** `pyodbc` (ODBC Driver 17 for SQL Server)
* **Control de Versiones:** Git / GitHub

---

## ⚙️ Requisitos Previos e Instalación

1. **Instalar Python 3.x** en tu equipo.
2. **Instalar el driver ODBC para SQL Server** (ODBC Driver 17 o superior).
3. **Instalar las dependencias de Python** ejecutando en tu terminal:
   ```bash
   pip install pyodbc

---

## 📂 Estructura del Proyecto
```text
SIGA-SAP-WM/
│
├── main.py               # Punto de entrada principal y vistas de la interfaz (Tkinter)
├── warehouse_db.py       # Capa de persistencia y gestión de conexión con SQL Server
├── auth_service.py       # Servicio de autenticación de usuarios y control de permisos (RBAC)
├── sap_integration.py    # Cliente de integración simulada con servicios SAP
├── seed_db.sql           # Script maestro SQL (Esquema de tablas, triggers y datos iniciales)
├── db_config.json        # Archivo de configuración local de conexión (generado automáticamente)
└── README.md             # Documentación del proyecto

---

## 🛠️ Configuración y Ejecución
1. Clonar el repositorio o descargar los archivos en tu PC.
2. Asegúrate de tener SQL Server corriendo localmente (por ejemplo, en localhost).
3. El archivo de configuración db_config.json se autogenerará con los valores por defecto al iniciar la aplicación. Si necesitas cambiar el servidor, edítalo con la estructura:
JSON

{
  "server": "localhost",
  "database": "SIGA_SAP",
  "trusted_connection": true
}
4. Ejecutar la aplicación:

python main.py

---

## 🔑 Credenciales de Acceso por Defecto

Puedes iniciar sesión con los siguientes usuarios precargados en la base de datos:

    Pañolero:

        Usuario: pañolero (o paniolero)

        Contraseña: 1234

    Supervisor:

        Usuario: supervisor

        Contraseña: 1234

    Producción:

        Usuario: produccion

        Contraseña: 1234