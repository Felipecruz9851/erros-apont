import os
import pickle
from typing import Any, Dict, List, Optional
import pandas as pd


DEFAULT_SNAPSHOT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage",
    "snapshots",
)

LATEST_PICKLE_FILENAME = "latest_extraction.pkl"


class SnapshotManager:
    """
    Gerenciador de snapshots HTML brutos.
    Garante o Princípio III da Constituição:
    - Persistência imutável do payload HTML bruto antes do parsing.
    - Auditabilidade e capacidade de reprodução offline.
    """

    def __init__(self, snapshot_dir: str = DEFAULT_SNAPSHOT_DIR):
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Substitui caracteres inválidos em nomes de arquivos."""
        for c in r'<>:"/\|?*':
            name = name.replace(c, "_")
        return name

    def save_snapshot(self, execution_id: str, task_id: str, html_content: str) -> str:
        """Salva o HTML bruto em arquivo .html e retorna o caminho absoluto."""
        safe_exec = self._sanitize_filename(execution_id)
        safe_task = self._sanitize_filename(task_id)
        file_name = f"{safe_exec}_{safe_task}.html"
        file_path = os.path.join(self.snapshot_dir, file_name)

        with open(file_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(html_content)

        return file_path

    def load_snapshot(self, execution_id: str, task_id: str) -> Optional[str]:
        """Carrega o conteúdo de um snapshot previamente persistido."""
        safe_exec = self._sanitize_filename(execution_id)
        safe_task = self._sanitize_filename(task_id)
        file_name = f"{safe_exec}_{safe_task}.html"
        file_path = os.path.join(self.snapshot_dir, file_name)

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def list_snapshots(self, execution_id: str) -> List[str]:
        """Lista os arquivos de snapshot para uma execução específica."""
        safe_exec = self._sanitize_filename(execution_id)
        prefix = f"{safe_exec}_"
        snapshots = []
        if os.path.exists(self.snapshot_dir):
            for fname in os.listdir(self.snapshot_dir):
                if fname.startswith(prefix) and fname.endswith(".html"):
                    snapshots.append(os.path.join(self.snapshot_dir, fname))
        return snapshots

    def save_pickle_snapshot(self, dfs_by_group: Dict[str, pd.DataFrame], execution_id: str = "") -> str:
        """
        Salva o dicionário de DataFrames extraídos ('consumo', 'estoque', 'ordens')
        em um arquivo pickle (latest_extraction.pkl) para carregamento rápido sem novo scraping.
        """
        payload = {
            "execution_id": execution_id,
            "dfs_by_group": {
                "consumo": dfs_by_group.get("consumo", pd.DataFrame()),
                "estoque": dfs_by_group.get("estoque", pd.DataFrame()),
                "ordens": dfs_by_group.get("ordens", pd.DataFrame()),
            },
        }
        latest_path = os.path.join(self.snapshot_dir, LATEST_PICKLE_FILENAME)
        with open(latest_path, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        return latest_path

    def load_pickle_snapshot(self) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Carrega os DataFrames do último snapshot pickle salvo em disco, se existir.
        """
        latest_path = os.path.join(self.snapshot_dir, LATEST_PICKLE_FILENAME)
        if not os.path.exists(latest_path):
            return None
        with open(latest_path, "rb") as f:
            data: Dict[str, Any] = pickle.load(f)
        if isinstance(data, dict) and "dfs_by_group" in data:
            return data["dfs_by_group"]
        if isinstance(data, dict):
            return data
        return None


    def clear_html_snapshots(self, execution_id: Optional[str] = None) -> int:
        """
        Remove os arquivos HTML temporários da pasta de snapshots (preservando latest_extraction.pkl e .gitkeep).
        Se execution_id for omitido, limpa todos os .html da pasta.
        Retorna a quantidade de arquivos removidos.
        """
        if not os.path.exists(self.snapshot_dir):
            return 0

        prefix = f"{self._sanitize_filename(execution_id)}_" if execution_id else ""
        removed = 0
        for fname in os.listdir(self.snapshot_dir):
            if not fname.endswith(".html"):
                continue
            if prefix and not fname.startswith(prefix):
                continue
            fpath = os.path.join(self.snapshot_dir, fname)
            try:
                os.remove(fpath)
                removed += 1
            except OSError:
                pass
        return removed


# Instância padrão
snapshot_manager = SnapshotManager()
