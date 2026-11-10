import json
from typing import Any, Dict, Optional
from urllib import error, request


class SAPIntegrationClient:
    def __init__(self, base_url: str = "https://api.sap.local"):
        self.base_url = base_url.rstrip("/")

    def _post_json(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        api_url = f"{self.base_url}{endpoint}"

        try:
            req = request.Request(api_url, data=data, headers=headers, method="POST")
            with request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8")
                if not body:
                    return {"status": "ok", "message": "Sin contenido de respuesta"}
                return json.loads(body)
        except error.HTTPError as exc:
            response_text = exc.read().decode("utf-8", errors="replace")
            return {
                "status": "error",
                "code": exc.code,
                "message": f"Error HTTP en SAP: {response_text or exc.reason}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"No se pudo conectar con SAP: {exc}",
            }

    def send_stock_adjustment(self, material_code: str, location: str, delta: int, user: str) -> Dict[str, Any]:
        payload = {
            "module": "SIGA_SAP",
            "operation": "stock_adjustment",
            "materialCode": material_code,
            "location": location,
            "delta": delta,
            "user": user,
            "source": "wm_app",
        }
        return self._post_json("/api/sap/stock-adjustment", payload)

    def send_location_change(self, material_code: str, previous_location: str, new_location: str, user: str) -> Dict[str, Any]:
        payload = {
            "module": "SIGA_SAP",
            "operation": "location_change",
            "materialCode": material_code,
            "previousLocation": previous_location,
            "newLocation": new_location,
            "user": user,
            "source": "wm_app",
        }
        return self._post_json("/api/sap/location-change", payload)
