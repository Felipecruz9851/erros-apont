import datetime as dt
import json
import os
import threading
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings


class TaskProfiler:
    """
    Gerenciador de Telemetria e Escalonamento LPT (Longest Processing Time First).
    Registra o histórico de tempo de execução de cada tarefa individual em JSON
    e reordena a fila de tarefas para que os workers iniciem pelas tarefas mais pesadas,
    maximizando a taxa de ocupação dos workers e minimizando o tempo ocioso final (tail latency).
    """

    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file or settings.TASK_TIMES_FILE
        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_storage_dir()
        self.load_profiles()

    def _ensure_storage_dir(self) -> None:
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

    def load_profiles(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            if not os.path.exists(self.storage_file):
                self._cache = {}
                return self._cache
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
            return self._cache

    def save_profiles(self) -> None:
        with self._lock:
            temp_file = f"{self.storage_file}.tmp"
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)
                if os.path.exists(self.storage_file):
                    os.replace(temp_file, self.storage_file)
                else:
                    os.rename(temp_file, self.storage_file)
            except Exception:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass

    def record_duration(
        self,
        task_id: str,
        duration_seconds: float,
        grupo: str = "",
        local: Optional[str] = None,
        rows_extracted: int = 0,
    ) -> None:
        """Registra e atualiza a média móvel de tempo de execução de uma tarefa."""
        duration_seconds = round(float(duration_seconds), 3)
        now_iso = dt.datetime.now().isoformat()

        with self._lock:
            current = self._cache.get(task_id)
            if current:
                count = current.get("count", 1) + 1
                old_avg = current.get("avg_duration_seconds", duration_seconds)
                new_avg = round(((old_avg * (count - 1)) + duration_seconds) / count, 3)
                min_dur = min(current.get("min_duration_seconds", duration_seconds), duration_seconds)
                max_dur = max(current.get("max_duration_seconds", duration_seconds), duration_seconds)

                current.update({
                    "last_duration_seconds": duration_seconds,
                    "avg_duration_seconds": new_avg,
                    "min_duration_seconds": min_dur,
                    "max_duration_seconds": max_dur,
                    "count": count,
                    "last_rows_extracted": rows_extracted,
                    "grupo": grupo or current.get("grupo", ""),
                    "local": local or current.get("local", ""),
                    "updated_at": now_iso,
                })
            else:
                self._cache[task_id] = {
                    "last_duration_seconds": duration_seconds,
                    "avg_duration_seconds": duration_seconds,
                    "min_duration_seconds": duration_seconds,
                    "max_duration_seconds": duration_seconds,
                    "count": 1,
                    "last_rows_extracted": rows_extracted,
                    "grupo": grupo,
                    "local": local or "",
                    "updated_at": now_iso,
                }

        self.save_profiles()

    def get_expected_duration(self, task: Dict[str, Any]) -> float:
        """Retorna o tempo esperado da tarefa baseado no histórico de execuções."""
        task_id = task.get("task_id", "")
        profile = self._cache.get(task_id)
        if profile and "avg_duration_seconds" in profile:
            return float(profile["avg_duration_seconds"])

        # Fallback 1: média pelo grupo e local
        grupo = task.get("grupo", "")
        local = task.get("local", "")
        matched_durations = [
            p.get("avg_duration_seconds", 1.0)
            for tid, p in self._cache.items()
            if p.get("local") == local and local
        ]
        if matched_durations:
            return sum(matched_durations) / len(matched_durations)

        # Fallback 2: média geral do grupo
        group_durations = [
            p.get("avg_duration_seconds", 1.0)
            for tid, p in self._cache.items()
            if p.get("grupo") == grupo and grupo
        ]
        if group_durations:
            return sum(group_durations) / len(group_durations)

        return 1.0

    def order_tasks_lpt(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Escalonamento LPT (Longest Processing Time First):
        Reordena a lista de tarefas colocando as tarefas historicamente mais demoradas
        no início da fila. As mais rápidas ficam para o final para preencher as lacunas dos workers.
        """
        if not tasks:
            return []

        # Garante que os perfis mais recentes foram lidos
        self.load_profiles()

        # Ordena decrescente pelo tempo esperado
        ordered = sorted(
            tasks,
            key=lambda t: self.get_expected_duration(t),
            reverse=True,
        )
        return ordered


task_profiler = TaskProfiler()
