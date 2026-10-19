import threading
import time
from typing import Dict, Optional, Tuple


class InMemorySecurityManager:
    """
    Gerenciador de credenciais e tokens em memória efêmera.
    Atende estritamente ao Princípio II da Constituição:
    - Zero persistência de credenciais em disco.
    - Zero registro de senhas em logs ou traces.
    - Expiração automática após o ciclo de execução.
    """

    def __init__(self, default_ttl_seconds: int = 1800):
        self._credentials: Dict[str, Tuple[str, str, float]] = {}  # execution_id -> (user, pass, expire_at)
        self._sessions: Dict[str, Tuple[Dict[str, str], float]] = {}  # execution_id -> (cookies, expire_at)
        self._lock = threading.Lock()
        self._ttl = default_ttl_seconds

    def store_credentials(self, execution_id: str, username: str, password: str) -> None:
        """Armazena temporariamente credenciais em memória para a execução."""
        with self._lock:
            self._cleanup_expired()
            self._credentials[execution_id] = (username, password, time.time() + self._ttl)

    def get_credentials(self, execution_id: str) -> Optional[Tuple[str, str]]:
        """Recupera usuário e senha efêmeros."""
        with self._lock:
            record = self._credentials.get(execution_id)
            if not record:
                return None
            user, pwd, expire_at = record
            if time.time() > expire_at:
                del self._credentials[execution_id]
                return None
            return (user, pwd)

    def store_session_cookies(self, execution_id: str, cookies: Dict[str, str]) -> None:
        """Armazena cookies de sessão (ex: PHPSESSID) em memória."""
        with self._lock:
            self._sessions[execution_id] = (cookies, time.time() + self._ttl)

    def get_session_cookies(self, execution_id: str) -> Optional[Dict[str, str]]:
        """Recupera cookies de sessão em memória."""
        with self._lock:
            record = self._sessions.get(execution_id)
            if not record:
                return None
            cookies, expire_at = record
            if time.time() > expire_at:
                del self._sessions[execution_id]
                return None
            return cookies

    def purge_execution(self, execution_id: str) -> None:
        """Remove imediatamente todos os rastros de credenciais e cookies de uma execução."""
        with self._lock:
            self._credentials.pop(execution_id, None)
            self._sessions.pop(execution_id, None)

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_creds = [k for k, (_, _, exp) in self._credentials.items() if now > exp]
        for k in expired_creds:
            del self._credentials[k]
        expired_sess = [k for k, (_, exp) in self._sessions.items() if now > exp]
        for k in expired_sess:
            del self._sessions[k]


# Instância global singleton
security_manager = InMemorySecurityManager()
