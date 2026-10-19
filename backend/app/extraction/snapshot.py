import os
from typing import List, Optional


DEFAULT_SNAPSHOT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage",
    "snapshots",
)


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


# Instância padrão
snapshot_manager = SnapshotManager()
