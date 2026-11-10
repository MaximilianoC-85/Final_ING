import tkinter as tk
from tkinter import ttk, messagebox

from auth_service import AuthService
from sap_integration import SAPIntegrationClient
from warehouse_db import DatabaseManager


class SigasapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGA-SAP WM")
        self.root.geometry("1400x860")
        self.root.configure(bg="#09111d")

        self.configure_table_styles()

        self.db = DatabaseManager()
        self.auth = AuthService(self.db)
        self.sap_api = SAPIntegrationClient("https://api.sap.local")

        self.current_user = None
        self.build_login_window()

    def configure_table_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Dark.Treeview",
                        background="#0f172a",
                        foreground="#e2e8f0",
                        fieldbackground="#0f172a",
                        rowheight=28,
                        borderwidth=0)
        style.map("Dark.Treeview",
                  background=[("selected", "#1d4ed8")],
                  foreground=[("selected", "#ffffff")])
        style.configure("Dark.Treeview.Heading",
                        background="#111827",
                        foreground="#dbeafe",
                        relief="flat",
                        font=("Segoe UI", 9, "bold"))
        style.map("Dark.Treeview.Heading",
                  background=[("active", "#1e293b")])

        style.configure("Dark.TCombobox",
                        fieldbackground="#0f172a",
                        background="#0f172a",
                        foreground="#e2e8f0",
                        selectbackground="#1d4ed8",
                        selectforeground="#ffffff")
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", "#0f172a")],
                  foreground=[("readonly", "#e2e8f0")])

        style.configure("Dark.TEntry",
                        fieldbackground="#0f172a",
                        foreground="#e2e8f0",
                        insertcolor="#e2e8f0")

        # Explicit aliases for the rest of the app.
        style.configure("DarkAzure.Treeview",
                        background="#0f172a",
                        foreground="#e2e8f0",
                        fieldbackground="#0f172a",
                        rowheight=28,
                        borderwidth=0)
        style.map("DarkAzure.Treeview",
                  background=[("selected", "#1d4ed8")],
                  foreground=[("selected", "#ffffff")])
        style.configure("DarkAzure.Treeview.Heading",
                        background="#111827",
                        foreground="#dbeafe",
                        relief="flat",
                        font=("Segoe UI", 9, "bold"))
        style.map("DarkAzure.Treeview.Heading",
                  background=[("active", "#1e293b")])
        style.configure("DarkAzure.TCombobox",
                        fieldbackground="#0f172a",
                        background="#0f172a",
                        foreground="#e2e8f0",
                        selectbackground="#1d4ed8",
                        selectforeground="#ffffff")
        style.map("DarkAzure.TCombobox",
                  fieldbackground=[("readonly", "#0f172a")],
                  foreground=[("readonly", "#e2e8f0")])
        style.configure("DarkAzure.TEntry",
                        fieldbackground="#0f172a",
                        foreground="#e2e8f0",
                        insertcolor="#e2e8f0")

    def build_login_window(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("SIGA-SAP - Login")
        self.login_window.geometry("430x320")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg="#0b1220")
        self.login_window.protocol("WM_DELETE_WINDOW", self.root.destroy)

        card = tk.Frame(self.login_window, bg="#111827", bd=0, highlightthickness=0)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        card.columnconfigure(0, weight=1)

        tk.Label(card, text="SIGA-SAP", font=("Segoe UI", 24, "bold"), fg="#f8fafc", bg="#111827").grid(row=0, column=0, pady=(18, 6))
        tk.Label(card, text="Sistema de gestión de almacén", font=("Segoe UI", 10), fg="#94a3b8", bg="#111827").grid(row=1, column=0, pady=(0, 18))

        tk.Label(card, text="Usuario", fg="#dbeafe", bg="#111827", anchor="w", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", padx=26)
        self.username_entry = tk.Entry(card, width=30, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0", bd=0, highlightthickness=1, highlightbackground="#334155", highlightcolor="#3b82f6")
        self.username_entry.grid(row=3, column=0, padx=26, pady=(4, 10), sticky="ew")

        tk.Label(card, text="Contraseña", fg="#dbeafe", bg="#111827", anchor="w", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", padx=26)
        self.password_entry = tk.Entry(card, width=30, show="*", bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0", bd=0, highlightthickness=1, highlightbackground="#334155", highlightcolor="#3b82f6")
        self.password_entry.grid(row=5, column=0, padx=26, pady=(4, 18), sticky="ew")

        tk.Button(
            card,
            text="Ingresar",
            command=self.login,
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=18,
            pady=10,
            activebackground="#1d4ed8",
            activeforeground="white",
        ).grid(row=6, column=0, sticky="ew", padx=26, pady=(0, 18))

        self.root.withdraw()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        user = self.auth.authenticate(username, password)
        if user is None:
            messagebox.showerror("Acceso", "Usuario o contraseña inválidos.")
            return

        self.current_user = user
        self.login_window.destroy()
        self.root.deiconify()
        self.build_main_ui()
        
    def logout(self):
        """Cierra la ventana principal actual y vuelve a mostrar el login."""
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de que deseas salir?"):
            # Cierra la conexión a la base de datos si está abierta
            try:
                if self.db and self.db.conn:
                    self.db.conn.close()
            except Exception:
                pass

            # Destruye la ventana principal actual
            self.root.withdraw()
            
            # Limpia el usuario actual
            self.current_user = None
            
            # Vuelve a invocar la ventana de login
            self.build_login_window()

    def build_main_ui(self):
        self.root.title(f"SIGA-SAP WM - {self.current_user.role}")
        self.root.geometry("1460x900")
        self.root.configure(bg="#09111d")
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self.root, bg="#0f172a", width=240, padx=16, pady=18)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        title = tk.Label(sidebar, text="SIGA-SAP", font=("Segoe UI", 18, "bold"), fg="#f8fafc", bg="#0f172a")
        title.pack(anchor="w", pady=(8, 18))

        subtitle = tk.Label(sidebar, text="Warehouse Management", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a")
        subtitle.pack(anchor="w", pady=(0, 18))

        # Reglas de visualización por rol según tu solicitud:
        # - Pañolero: sin Dashboard ni Órdenes.
        # - Producción: sin Dashboard.
        user_role = (self.current_user.role or "").strip().lower()
        is_panolero = "pañol" in user_role or "paniol" in user_role
        is_produccion = "producc" in user_role

        allowed_sections = {
            "dashboard": not is_panolero and not is_produccion,
            "materials": self.auth.can(self.current_user, "view_materials"),
            "locations": self.auth.can(self.current_user, "update_stock") or self.auth.can(self.current_user, "update_location"),
            "orders": (self.auth.can(self.current_user, "manage_work_orders") or self.auth.can(self.current_user, "view_work_orders")) and not is_panolero,
            "audit": self.auth.can(self.current_user, "view_audit"),
        }

        self.nav_buttons = {}
        nav_definitions = [
            ("dashboard", "Dashboard"),
            ("materials", "Materiales"),
            ("locations", "Stock y ubicación"),
            ("orders", "Órdenes"),
            ("audit", "Auditoría"),
        ]

        for key, label in nav_definitions:
            if allowed_sections.get(key, False):
                btn = tk.Button(
                    sidebar,
                    text=label,
                    command=lambda k=key: self.show_section(k),
                    bg="#111827",
                    fg="#e2e8f0",
                    activebackground="#1e293b",
                    activeforeground="#f8fafc",
                    bd=0,
                    padx=14,
                    pady=12,
                    anchor="w",
                    font=("Segoe UI", 10, "bold"),
                    width=20,
                    justify="left",
                )
                btn.pack(fill="x", pady=4)
                self.nav_buttons[key] = btn

        sidebar_bottom = tk.Frame(sidebar, bg="#0f172a")
        sidebar_bottom.pack(side="bottom", fill="x", pady=(20, 12))
        tk.Label(sidebar_bottom, text=f"Usuario: {self.current_user.username}", fg="#cbd5e1", bg="#0f172a", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(sidebar_bottom, text=f"Rol: {self.current_user.role}", fg="#93c5fd", bg="#0f172a", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 8))

        tk.Button(
            sidebar_bottom,
            text="Cerrar sesión",
            command=self.logout,
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            bd=0,
            padx=10,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            justify="left",
        ).pack(fill="x", pady=(4, 0))

        content = tk.Frame(self.root, bg="#0b1220")
        content.grid(row=0, column=1, sticky="nsew", padx=(18, 18), pady=18)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        top_bar = tk.Frame(content, bg="#111827", padx=18, pady=16, height=68)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)
        tk.Label(top_bar, text="Panel de control", font=("Segoe UI", 20, "bold"), fg="#f8fafc", bg="#111827").pack(anchor="w")
        tk.Label(top_bar, text="SIGA-SAP / Operaciones de almacén", fg="#94a3b8", bg="#111827").pack(anchor="w", pady=(4, 0))

        self.sections = {}
        
        self.dashboard_tab = tk.Frame(content, bg="#0b1220") if allowed_sections["dashboard"] else None
        self.materials_tab = tk.Frame(content, bg="#0b1220") if allowed_sections["materials"] else None
        self.locations_tab = tk.Frame(content, bg="#0b1220") if allowed_sections["locations"] else None
        self.orders_tab = tk.Frame(content, bg="#0b1220") if allowed_sections["orders"] else None
        self.audit_tab = tk.Frame(content, bg="#0b1220") if allowed_sections["audit"] else None

        tab_mapping = {
            "dashboard": self.dashboard_tab,
            "materials": self.materials_tab,
            "locations": self.locations_tab,
            "orders": self.orders_tab,
            "audit": self.audit_tab,
        }

        for key, frame in tab_mapping.items():
            if frame is not None and allowed_sections.get(key, False):
                frame.grid(row=1, column=0, sticky="nsew")
                frame.grid_remove()
                self.sections[key] = frame

        if allowed_sections["dashboard"]:
            self.build_dashboard()
        if allowed_sections["materials"]:
            self.build_materials_tab()
        if allowed_sections["locations"]:
            self.build_locations_tab()
        if allowed_sections["orders"]:
            self.build_orders_tab()
        if allowed_sections["audit"]:
            self.build_audit_tab()

        # Seleccionar la primera sección disponible por defecto
        first_available = next((k for k, allowed in allowed_sections.items() if allowed), "materials")
        self.show_section(first_available)
        self.connect_database()

    def show_section(self, section_name: str):
        for key, frame in self.sections.items():
            if key == section_name:
                frame.grid()
                frame.tkraise()
            else:
                frame.grid_remove()

        for key, btn in self.nav_buttons.items():
            if key == section_name:
                btn.configure(bg="#1d4ed8", fg="white")
            else:
                btn.configure(bg="#111827", fg="#e2e8f0")

    def apply_role_rules(self):
        # Definir permisos exactos basados en el servicio de autenticación
        allowed = {
            "dashboard": True,  # Todos pueden ver el dashboard principal
            "materials": self.auth.can(self.current_user, "view_materials"),
            "locations": self.auth.can(self.current_user, "update_stock") or self.auth.can(self.current_user, "update_location"),
            "orders": self.auth.can(self.current_user, "manage_work_orders") or self.auth.can(self.current_user, "view_work_orders"),
            "audit": self.auth.can(self.current_user, "view_audit"),
        }

        # 1. Ocultar o mostrar los botones del menú lateral dinámicamente
        for key, btn in self.nav_buttons.items():
            if not allowed.get(key, True):
                btn.pack_forget()  # Oculta el botón completamente del menú
            else:
                btn.pack(fill="x", pady=4)  # Muestra el botón si está permitido

        # 2. Ocultar los marcos (tabs) prohibidos para que no se puedan renderizar
        for key, frame in self.sections.items():
            if not allowed.get(key, True):
                frame.grid_remove()
                
    def build_dashboard(self):
        self.dashboard_tab.configure(bg="#0b1220")
        self.dashboard_tab.columnconfigure((0, 1, 2, 3), weight=1)

        self.card_labels = []
        for idx, (title, value, color) in enumerate([
            ("Materiales", "0", "#2563eb"),
            ("Ubicaciones", "0", "#059669"),
            ("Stock total", "0", "#d97706"),
            ("Transacciones", "0", "#7c3aed"),
        ]):
            card = tk.Frame(self.dashboard_tab, bg=color, padx=14, pady=16, bd=0)
            card.grid(row=0, column=idx, sticky="nsew", padx=8, pady=8)
            tk.Label(card, text=title, font=("Segoe UI", 10), bg=color, fg="white").pack(anchor="w")
            label = tk.Label(card, text=value, font=("Segoe UI", 22, "bold"), bg=color, fg="white")
            label.pack(anchor="w", pady=(8, 0))
            self.card_labels.append(label)

        table_frame = tk.LabelFrame(self.dashboard_tab, text="Inventario simulado de SAP", font=("Segoe UI", 10, "bold"), bg="#111827", fg="#e2e8f0", bd=1, relief="flat")
        table_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.columnconfigure(0, weight=1)

        self.inventory_tree = ttk.Treeview(table_frame, columns=("code", "description", "stock", "location"), show="headings", style="Dark.Treeview")
        self.inventory_tree.heading("code", text="Material")
        self.inventory_tree.heading("description", text="Descripción")
        self.inventory_tree.heading("stock", text="Stock")
        self.inventory_tree.heading("location", text="Ubicación")
        self.inventory_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_materials_tab(self):
        self.materials_tab.configure(bg="#0b1220")
        table_frame = tk.LabelFrame(self.materials_tab, text="Catálogo simulado de SAP", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.columnconfigure(0, weight=1)

        search_frame = tk.Frame(table_frame, bg="#111827")
        search_frame.pack(fill="x", padx=8, pady=(8, 0))
        tk.Label(search_frame, text="Buscar material:", bg="#111827", fg="#e2e8f0").pack(side="left", padx=(0, 8))
        self.material_search_var = tk.StringVar()
        self.material_search_var.trace_add("write", lambda *_: self.refresh_materials_search())
        tk.Entry(search_frame, textvariable=self.material_search_var, width=35, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0").pack(side="left", fill="x", expand=True)
        tk.Button(search_frame, text="Escanear QR", command=self.simulate_qr_scan, bg="#0f766e", fg="white", bd=0, padx=10, pady=6).pack(side="left", padx=(8, 0))

        self.materials_tree = ttk.Treeview(table_frame, columns=("code", "description", "stock", "location", "zone", "aisle", "rack", "position"), show="headings", style="Dark.Treeview")
        self.materials_tree.heading("code", text="Código")
        self.materials_tree.heading("description", text="Descripción")
        self.materials_tree.heading("stock", text="Stock")
        self.materials_tree.heading("location", text="Ubicación")
        self.materials_tree.heading("zone", text="Depósito")
        self.materials_tree.heading("aisle", text="Sector")
        self.materials_tree.heading("rack", text="Estantería")
        self.materials_tree.heading("position", text="Posición")
        self.materials_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_locations_tab(self):
        self.locations_tab.configure(bg="#0b1220")
        form = tk.LabelFrame(self.locations_tab, text="Identificación del material y operación permitida", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        form.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Material / código:", bg="#111827", fg="#e2e8f0").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.material_field = tk.Entry(form, width=30, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.material_field.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Búsqueda dinámica:", bg="#111827", fg="#e2e8f0").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.material_lookup_var = tk.StringVar()
        self.material_lookup_var.trace_add("write", lambda *_: self.refresh_material_match_list())
        self.material_lookup_entry = tk.Entry(form, textvariable=self.material_lookup_var, width=30, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.material_lookup_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        self.match_listbox = tk.Listbox(form, height=6, width=40, bg="#0f172a", fg="#e2e8f0", selectbackground="#1d4ed8")
        self.match_listbox.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
        self.match_listbox.bind("<<ListboxSelect>>", self.on_material_selected)

        tk.Label(form, text="Ubicación actual:", bg="#111827", fg="#e2e8f0").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        self.current_location_field = tk.Entry(form, width=25, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.current_location_field.grid(row=3, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Nueva ubicación:", bg="#111827", fg="#e2e8f0").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        self.new_location_field = tk.Entry(form, width=25, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.new_location_field.grid(row=4, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Cantidad a operar:", bg="#111827", fg="#e2e8f0").grid(row=5, column=0, sticky="w", padx=8, pady=6)
        self.delta_field = tk.Entry(form, width=20, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.delta_field.grid(row=5, column=1, sticky="w", padx=8, pady=6)

        tk.Label(form, text="Tipo de operación:", bg="#111827", fg="#e2e8f0").grid(row=6, column=0, sticky="w", padx=8, pady=6)
        self.operation_field = ttk.Combobox(form, values=["INCREMENTO", "REDUCCION", "REUBICACION"], state="readonly", width=25)
        self.operation_field.current(0)
        self.operation_field.grid(row=6, column=1, sticky="ew", padx=8, pady=6)

        tk.Button(form, text="Ejecutar operación", command=self.execute_operation, bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=12, pady=8).grid(row=7, column=1, sticky="w", padx=8, pady=12)

        table_frame = tk.LabelFrame(self.locations_tab, text="Ubicaciones del pañol", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.columnconfigure(0, weight=1)

        self.locations_tree = ttk.Treeview(table_frame, columns=("material", "location", "stock", "zone", "aisle", "rack", "position"), show="headings", style="Dark.Treeview")
        self.locations_tree.heading("material", text="Material")
        self.locations_tree.heading("location", text="Ubicación")
        self.locations_tree.heading("stock", text="Stock")
        self.locations_tree.heading("zone", text="Depósito")
        self.locations_tree.heading("aisle", text="Sector")
        self.locations_tree.heading("rack", text="Estantería")
        self.locations_tree.heading("position", text="Posición")
        self.locations_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_orders_tab(self):
        self.orders_tab.configure(bg="#0b1220")
        if not self.auth.can(self.current_user, "manage_work_orders"):
            tk.Label(self.orders_tab, text="No tiene permisos para gestionar órdenes de trabajo.", bg="#111827", fg="#f8fafc", font=("Segoe UI", 11)).pack(padx=20, pady=20)
            return

        form = tk.LabelFrame(self.orders_tab, text="Crear, consultar y modificar órdenes de trabajo", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        form.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Buscar OT:", bg="#111827", fg="#e2e8f0").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.order_search_var = tk.StringVar()
        self.order_search_var.trace_add("write", lambda *_: self.refresh_order_match_list())
        self.order_search_entry = tk.Entry(form, textvariable=self.order_search_var, width=28, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_search_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        self.order_match_listbox = tk.Listbox(form, height=6, width=45, bg="#0f172a", fg="#e2e8f0", selectbackground="#1d4ed8")
        self.order_match_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=6)
        self.order_match_listbox.bind("<<ListboxSelect>>", self.on_order_selected)

        tk.Label(form, text="N° OT:", bg="#111827", fg="#e2e8f0").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.order_id_field = tk.Entry(form, width=20, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_id_field.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Descripción:", bg="#111827", fg="#e2e8f0").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        self.order_desc_field = tk.Entry(form, width=35, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_desc_field.grid(row=3, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Centro:", bg="#111827", fg="#e2e8f0").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        self.order_center_field = tk.Entry(form, width=20, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_center_field.grid(row=4, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Equipo / puesto:", bg="#111827", fg="#e2e8f0").grid(row=5, column=0, sticky="w", padx=8, pady=6)
        self.order_equipment_field = tk.Entry(form, width=20, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_equipment_field.grid(row=5, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Responsable:", bg="#111827", fg="#e2e8f0").grid(row=6, column=0, sticky="w", padx=8, pady=6)
        self.order_responsible_field = tk.Entry(form, width=20, bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.order_responsible_field.grid(row=6, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Prioridad:", bg="#111827", fg="#e2e8f0").grid(row=7, column=0, sticky="w", padx=8, pady=6)
        self.order_priority_field = ttk.Combobox(form, values=["Baja", "Media", "Alta", "Urgente"], state="readonly", width=20)
        self.order_priority_field.current(1)
        self.order_priority_field.grid(row=7, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Tipo:", bg="#111827", fg="#e2e8f0").grid(row=8, column=0, sticky="w", padx=8, pady=6)
        self.order_type_field = ttk.Combobox(form, values=["Producción", "Mantenimiento"], state="readonly", width=20)
        self.order_type_field.current(0)
        self.order_type_field.grid(row=8, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(form, text="Estado:", bg="#111827", fg="#e2e8f0").grid(row=9, column=0, sticky="w", padx=8, pady=6)
        self.order_status_field = ttk.Combobox(form, values=["Pendiente", "En curso", "Cerrada", "Anulada"], state="readonly", width=20)
        self.order_status_field.current(0)
        self.order_status_field.grid(row=9, column=1, sticky="ew", padx=8, pady=6)

        tk.Button(form, text="Guardar OT", command=self.save_order, bg="#059669", fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=12, pady=8).grid(row=10, column=1, sticky="w", padx=8, pady=12)

        table_frame = tk.LabelFrame(self.orders_tab, text="Órdenes actuales", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.columnconfigure(0, weight=1)

        self.orders_tree = ttk.Treeview(table_frame, columns=("id", "description", "center", "equipment", "responsible", "priority", "type", "status"), show="headings", style="Dark.Treeview")
        self.orders_tree.heading("id", text="N° OT")
        self.orders_tree.heading("description", text="Descripción")
        self.orders_tree.heading("center", text="Centro")
        self.orders_tree.heading("equipment", text="Equipo")
        self.orders_tree.heading("responsible", text="Responsable")
        self.orders_tree.heading("priority", text="Prioridad")
        self.orders_tree.heading("type", text="Tipo")
        self.orders_tree.heading("status", text="Estado")
        self.orders_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_audit_tab(self):
        self.audit_tab.configure(bg="#0b1220")
        if not self.auth.can(self.current_user, "view_audit"):
            tk.Label(self.audit_tab, text="No tiene permisos para acceder a la auditoría.", bg="#111827", fg="#f8fafc", font=("Segoe UI", 11)).pack(padx=20, pady=20)
            return

        table_frame = tk.LabelFrame(self.audit_tab, text="Historial de transacciones", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 10, "bold"), bd=1, relief="flat")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.columnconfigure(0, weight=1)

        self.audit_tree = ttk.Treeview(table_frame, columns=("material", "operation", "prev_qty", "result_qty", "prev_loc", "new_loc", "user", "date"), show="headings", style="Dark.Treeview")
        self.audit_tree.heading("material", text="Material")
        self.audit_tree.heading("operation", text="Operación")
        self.audit_tree.heading("prev_qty", text="Cant. anterior")
        self.audit_tree.heading("result_qty", text="Cant. resultante")
        self.audit_tree.heading("prev_loc", text="Ubicación anterior")
        self.audit_tree.heading("new_loc", text="Ubicación nueva")
        self.audit_tree.heading("user", text="Usuario")
        self.audit_tree.heading("date", text="Fecha")
        self.audit_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def connect_database(self):
        try:
            self.db.connect()
            # ensure_schema() ahora se encarga de todo ejecutando seed_db.sql
            self.db.ensure_schema() 
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Conexión", f"No se pudo conectar a la BD de prueba: {exc}")
            
    def refresh_all(self):
        # Solo actualiza el dashboard si la pestaña existe para el rol actual
        if hasattr(self, "card_labels") and self.card_labels:
            self.refresh_dashboard()
            
        if hasattr(self, "materials_tree"):
            self.refresh_materials()
            
        if hasattr(self, "locations_tree"):
            self.refresh_locations()
            
        if hasattr(self, "orders_tree"):
            self.refresh_orders()
            
        if hasattr(self, "audit_tree"):
            self.refresh_audit()

    def refresh_dashboard(self):
        rows = self.db.list_sap_materials()
        self.card_labels[0].configure(text=str(len(rows)))
        self.card_labels[1].configure(text=str(len({r[3] for r in rows})))
        self.card_labels[2].configure(text=str(sum(int(r[2]) for r in rows)))
        self.card_labels[3].configure(text=str(len(self.db.get_audit_logs(100))))

        self.inventory_tree.delete(*self.inventory_tree.get_children())
        for material_code, description, stock, location, unit, zone, aisle, rack, position in rows:
            self.inventory_tree.insert("", "end", values=(material_code, description, stock, location))

    def refresh_materials(self):
        self.materials_tree.delete(*self.materials_tree.get_children())
        rows = self.db.search_materials(self.material_search_var.get() if hasattr(self, "material_search_var") else "")
        for material_code, description, stock, location, unit, zone, aisle, rack, position in rows:
            self.materials_tree.insert("", "end", values=(material_code, description, stock, location, zone, aisle, rack, position))

    def refresh_materials_search(self):
        self.refresh_materials()

    def refresh_locations(self):
        self.locations_tree.delete(*self.locations_tree.get_children())
        rows = self.db.list_sap_materials()
        for material_code, description, stock, location, unit, zone, aisle, rack, position in rows:
            self.locations_tree.insert("", "end", values=(material_code, location, stock, zone, aisle, rack, position))

    def refresh_orders(self):
        if not hasattr(self, "orders_tree"):
            return
        self.orders_tree.delete(*self.orders_tree.get_children())
        rows = self.db.search_work_orders(self.order_search_var.get() if hasattr(self, "order_search_var") else "")
        for order_id, description, center, equipment, responsible, priority, order_type, status, material_code, quantity, is_active, notes in rows:
            self.orders_tree.insert("", "end", values=(order_id, description, center, equipment, responsible, priority, order_type, status))

    def refresh_order_match_list(self):
        if not hasattr(self, "order_match_listbox"):
            return
        self.order_match_listbox.delete(0, tk.END)
        query = self.order_search_var.get().strip()
        for order_id, description, center, equipment, responsible, priority, order_type, status, material_code, quantity, is_active, notes in self.db.search_work_orders(query):
            self.order_match_listbox.insert(tk.END, f"{order_id} - {description} ({order_type})")

    def refresh_audit(self):
        if not hasattr(self, "audit_tree"):
            return
        if not self.auth.can(self.current_user, "view_audit"):
            return

        self.audit_tree.delete(*self.audit_tree.get_children())
        for material_code, operation_type, previous_quantity, result_quantity, previous_location, new_location, user_name, operation_date in self.db.get_audit_logs(100):
            self.audit_tree.insert("", "end", values=(material_code, operation_type, previous_quantity or "-", result_quantity or "-", previous_location or "-", new_location or "-", user_name, operation_date))

    def simulate_qr_scan(self):
        material_code = self.material_lookup_var.get().strip() or "MAT-001"
        self.material_field.delete(0, tk.END)
        self.material_field.insert(0, material_code)
        self.material_lookup_var.set(material_code)
        self.load_material_details(material_code)

    def refresh_material_match_list(self):
        if not hasattr(self, "match_listbox"):
            return
        self.match_listbox.delete(0, tk.END)
        query = self.material_lookup_var.get().strip()
        for material_code, description, stock, location, unit, zone, aisle, rack, position in self.db.search_materials(query):
            self.match_listbox.insert(tk.END, f"{material_code} - {description} ({location})")

    def on_material_selected(self, event):
        selected = self.match_listbox.get(self.match_listbox.curselection())
        material_code = selected.split(" - ", 1)[0]
        self.material_field.delete(0, tk.END)
        self.material_field.insert(0, material_code)
        self.load_material_details(material_code)

    def on_order_selected(self, event):
        selected = self.order_match_listbox.get(self.order_match_listbox.curselection())
        order_id = selected.split(" - ", 1)[0]
        row = self.db.get_work_order(order_id)
        if row is None:
            return
        order_id, description, center, equipment, responsible, priority, order_type, status, material_code, quantity, is_active, notes = row
        self.order_id_field.delete(0, tk.END)
        self.order_id_field.insert(0, order_id)
        self.order_desc_field.delete(0, tk.END)
        self.order_desc_field.insert(0, description)
        self.order_center_field.delete(0, tk.END)
        self.order_center_field.insert(0, center or "")
        self.order_equipment_field.delete(0, tk.END)
        self.order_equipment_field.insert(0, equipment or "")
        self.order_responsible_field.delete(0, tk.END)
        self.order_responsible_field.insert(0, responsible or "")
        self.order_priority_field.set(priority or "Media")
        self.order_type_field.set(order_type or "Producción")
        self.order_status_field.set(status or "Pendiente")

    def load_material_details(self, material_code: str):
        row = self.db.get_sap_material(material_code)
        if row is None:
            self.current_location_field.delete(0, tk.END)
            return
            
        material_code, description, stock, location, unit, zone, aisle, rack, position = row
        
        # Mostramos simplemente el BinCode en ubicación actual
        self.current_location_field.delete(0, tk.END)
        self.current_location_field.insert(0, location)  # location es el BinCode (ej: A-01-01)
        
        self.new_location_field.delete(0, tk.END)
        self.new_location_field.insert(0, location)
        
        self.material_field.delete(0, tk.END)
        self.material_field.insert(0, material_code)

    def execute_operation(self):
        if not self.current_user:
            return
        if not self.auth.can(self.current_user, "update_stock") and not self.auth.can(self.current_user, "update_location"):
            messagebox.showerror("Permisos", "No tiene permisos para ejecutar operaciones de stock o ubicación.")
            return

        material_code = self.material_field.get().strip().upper()
        current_location = self.current_location_field.get().strip().upper()
        new_location = self.new_location_field.get().strip().upper()
        operation = self.operation_field.get().strip()

        if not material_code:
            messagebox.showwarning("Validación", "Debe indicar el material.")
            return

        material = self.db.get_sap_material(material_code)
        if material is None:
            messagebox.showerror("Material", f"El material {material_code} no existe en la base temporal de SAP.")
            return

        previous_qty = int(material[2])
        previous_location = current_location or material[3]

        try:
            if operation == "INCREMENTO":
                if not self.auth.can(self.current_user, "update_stock"):
                    messagebox.showerror("Permisos", "Su rol no puede incrementar stock.")
                    return
                delta = int(self.delta_field.get().strip()) if self.delta_field.get().strip() else 0
                if delta <= 0:
                    raise ValueError("La cantidad de incremento debe ser mayor a cero.")
                new_qty = self.db.update_sap_material_stock(material_code, delta)
                self.db.log_operation(material_code, "INCREMENTO_STOCK", previous_qty, new_qty, previous_location, previous_location, self.current_user.username, f"Incremento de {delta} unidades")
                messagebox.showinfo("Operación", "Incremento de stock registrado correctamente.")

            elif operation == "REDUCCION":
                if not self.auth.can(self.current_user, "update_stock"):
                    messagebox.showerror("Permisos", "Su rol no puede reducir stock.")
                    return
                delta = int(self.delta_field.get().strip()) if self.delta_field.get().strip() else 0
                if delta <= 0:
                    raise ValueError("La cantidad de reducción debe ser mayor a cero.")
                if previous_qty < delta:
                    raise ValueError("La reducción supera el stock disponible.")
                new_qty = self.db.update_sap_material_stock(material_code, -delta)
                self.db.log_operation(material_code, "REDUCCION_STOCK", previous_qty, new_qty, previous_location, previous_location, self.current_user.username, f"Reducción de {delta} unidades")
                messagebox.showinfo("Operación", "Reducción de stock registrada correctamente.")

            elif operation == "REUBICACION":
                if not self.auth.can(self.current_user, "update_location"):
                    messagebox.showerror("Permisos", "Su rol no puede modificar ubicaciones.")
                    return
                if not current_location or not new_location:
                    raise ValueError("Debe completar la ubicación actual y la nueva ubicación.")
                self.db.update_sap_material_location(material_code, new_location)
                self.db.log_operation(material_code, "MODIFICACION_UBICACION", previous_qty, previous_qty, previous_location, new_location, self.current_user.username, "Cambio de ubicación")
                messagebox.showinfo("Operación", "Ubicación actualizada correctamente.")

            else:
                raise ValueError("Operación no válida.")

            self.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Validación", str(exc))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def save_order(self):
        if not self.auth.can(self.current_user, "manage_work_orders"):
            messagebox.showerror("Permisos", "No tiene permisos para gestionar órdenes de trabajo.")
            return

        order_id = self.order_id_field.get().strip().upper()
        description = self.order_desc_field.get().strip()
        center = self.order_center_field.get().strip()
        equipment = self.order_equipment_field.get().strip()
        responsible = self.order_responsible_field.get().strip()
        priority = self.order_priority_field.get().strip()
        order_type = self.order_type_field.get().strip()
        status = self.order_status_field.get().strip()

        if not order_id or not description or not center or not equipment or not responsible:
            messagebox.showwarning("Validación", "Complete los campos obligatorios de la OT.")
            return

        try:
            row = self.db.get_work_order(order_id)
            if row is None:
                self.db.create_work_order(order_id, description, center, equipment, responsible, priority, order_type, status)
                messagebox.showinfo("OT", f"Orden {order_id} creada correctamente.")
            else:
                self.db.update_work_order(order_id, description=description, center=center, equipment=equipment,
                                        responsible=responsible, priority=priority, order_type=order_type, status=status)
                messagebox.showinfo("OT", f"Orden {order_id} actualizada correctamente.")
            self.refresh_orders()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main():
    root = tk.Tk()
    root.withdraw()
    app = SigasapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
