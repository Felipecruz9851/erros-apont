import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings


class ContactsService:
    """
    Gerencia o armazenamento persistente em JSON dos contatos e suas atribuições de locais de produção.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path or settings.CONTACTS_FILE)
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Garante a existência do diretório e do arquivo JSON."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            # Inicializa com lista vazia
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _read_data(self) -> List[Dict[str, Any]]:
        self._ensure_storage()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        temp_file.replace(self.file_path)

    def list_contacts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self._read_data()

    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            contacts = self._read_data()
            for c in contacts:
                if c.get("id") == contact_id:
                    return c
        return None

    def create_contact(self, nome: str, email: str, locais: List[str]) -> Dict[str, Any]:
        with self._lock:
            contacts = self._read_data()
            now_iso = datetime.now().isoformat()
            new_id = f"ct_{uuid.uuid4().hex[:8]}"
            
            clean_locais = sorted(list({str(loc).strip().upper() for loc in locais if str(loc).strip()}))

            new_contact = {
                "id": new_id,
                "nome": nome.strip(),
                "email": email.strip().lower(),
                "locais": clean_locais,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            contacts.append(new_contact)
            self._write_data(contacts)
            return new_contact

    def update_contact(
        self,
        contact_id: str,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        locais: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            contacts = self._read_data()
            found = None
            for c in contacts:
                if c.get("id") == contact_id:
                    if nome is not None:
                        c["nome"] = nome.strip()
                    if email is not None:
                        c["email"] = email.strip().lower()
                    if locais is not None:
                        c["locais"] = sorted(list({str(loc).strip().upper() for loc in locais if str(loc).strip()}))
                    c["updated_at"] = datetime.now().isoformat()
                    found = c
                    break

            if found:
                self._write_data(contacts)
            return found

    def delete_contact(self, contact_id: str) -> bool:
        with self._lock:
            contacts = self._read_data()
            orig_len = len(contacts)
            contacts = [c for c in contacts if c.get("id") != contact_id]
            if len(contacts) < orig_len:
                self._write_data(contacts)
                return True
            return False

    def get_available_locations(self) -> List[str]:
        """
        Retorna a lista de todos os locais de produção conhecidos a partir do tarefas_esqueleto.json.
        """
        locations = set()
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        skeleton_file = root_dir / "config" / "tarefas_esqueleto.json"

        if skeleton_file.exists():
            try:
                with open(skeleton_file, "r", encoding="utf-8") as f:
                    tarefas = json.load(f)
                    for t in tarefas:
                        locs = t.get("locais_disponiveis", [])
                        for l in locs:
                            if l and isinstance(l, str):
                                locations.add(l.strip().upper())
            except Exception:
                pass

        if not locations:
            # Fallback padrão das unidades industriais da Líder
            locations = {
                "COLCHOES", "BOX", "ESTOF UL", "CC ACABA01", "ARMARIO UL",
                "UL ACABA01", "COZINHA", "PES ACABA", "VIDRACARIA", "PORTAS",
                "LAMINAD UL", "TAMPOS UL", "UL FABRI01", "CORTE", "CADEIRAS",
                "CC FABRI01", "CORTE LE", "PEZINHO", "CC FABRI03", "PLANEJADOS",
                "LE FABRI02", "LE FABRI03", "LE FABRI06", "FIBRA", "ALMOFADAS",
                "CAPAS LE", "METALURGIA", "ALUMINIO", "INOX", "PLASMA",
                "ATELIE", "ATELIE2", "UL-ALMOX05", "REVENDA", "AT INSUMO",
                "AT SOFA", "AT MOVEIS", "AT KIT", "AT VIDRO", "KIT",
                "TAPA FURO", "ACESSORIOS", "COLMEIAS", "C PILOTO", "MOSTRUARIO",
                "LAMINACAO1", "EMBALAGEM", "OSSOPAINEL", "TAPETES", "LE FABRI01", "PLAN_ESP"
            }

        return sorted(list(locations))


contacts_service = ContactsService()
