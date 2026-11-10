from dataclasses import dataclass


@dataclass
class AppUser:
    username: str
    role: str


class AuthService:
    def __init__(self, db=None):
        self.db = db
        # Usuarios en memoria de respaldo por si la base de datos falla o aún no sincroniza
        self.USERS = {
            "pañolero": {
                "password": "1234",
                "role": "Pañolero",
            },
            "paniolero": {
                "password": "1234",
                "role": "Pañolero",
            },
            "supervisor": {
                "password": "1234",
                "role": "Supervisor",
            },
            "produccion": {
                "password": "1234",
                "role": "Producción",
            },
        }

        self.PERMISSIONS = {
            "Pañolero": {
                "view_materials",
                "view_locations",
                "update_stock",
                "update_location",
                "view_work_orders",
            },
            "Supervisor": {
                "view_materials",
                "view_locations",
                "update_stock",
                "update_location",
                "view_work_orders",
                "manage_work_orders",
                "view_audit",
            },
            "Producción": {
                "view_materials",
                "view_work_orders",
                "manage_work_orders",
            },
        }

    def _candidate_usernames(self, username: str):
        raw = (username or "").strip()
        if not raw:
            return []
        lowercase = raw.lower()
        candidates = {raw, lowercase}
        if "ñ" in lowercase:
            candidates.add(lowercase.replace("ñ", "n"))
        if "n" in lowercase and "paniolero" in lowercase:
            candidates.add(lowercase.replace("n", "ñ", 1))
        return list(candidates)

    def _authenticate_from_db(self, username: str, password: str):
        if self.db is None or not hasattr(self.db, "get_user"):
            return None
        try:
            for candidate in self._candidate_usernames(username):
                user = self.db.get_user(candidate, password)
                if user:
                    return AppUser(username=user.get("UserName", candidate), role=user.get("RoleName", "Pañolero"))
        except Exception:
            return None
        return None

    def authenticate(self, username: str, password: str):
        # 1. Intento principal: Buscar en la base de datos SQL
        db_user = self._authenticate_from_db(username, password)
        if db_user is not None:
            return db_user

        # 2. Respaldo de seguridad: Si la BD falla o no encuentra al usuario, busca en memoria
        clean_input = (username or "").strip().lower()
        user_data = self.USERS.get(clean_input)
        
        if not user_data:
            for candidate in self._candidate_usernames(username):
                user_data = self.USERS.get(candidate.lower())
                if user_data is not None:
                    break
                    
        if not user_data:
            return None
            
        if user_data["password"] != (password or ""):
            return None
            
        return AppUser(username=(username or "").strip(), role=user_data["role"])

    def can(self, user: AppUser, action: str) -> bool:
        if user is None:
            return False
        return action in self.PERMISSIONS.get(user.role, set())