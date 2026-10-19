import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional


DEFAULT_SKELETON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "config",
    "tarefas_esqueleto.json",
)


class TaskGenerator:
    """
    Gerador de Tarefas de Extração.
    Lê a matriz configurável em config/tarefas_esqueleto.json e expande
    as tarefas dinamicamente. Suporta a expansão iterativa por local:
    for local in locais: tarefas.append(...)
    garantindo sempre o uso de cod_empresa: "11".
    """

    def __init__(self, skeleton_path: str = DEFAULT_SKELETON_PATH):
        self.skeleton_path = skeleton_path
        self._raw_skeleton: List[Dict[str, Any]] = []
        self.load_skeleton()

    def load_skeleton(self) -> None:
        """Carrega o esqueleto configurável do disco."""
        if not os.path.exists(self.skeleton_path):
            raise FileNotFoundError(f"Esqueleto de tarefas não encontrado em: {self.skeleton_path}")
        with open(self.skeleton_path, "r", encoding="utf-8") as f:
            self._raw_skeleton = json.load(f)

    def generate_tasks(
        self,
        data_inicio: str,
        data_fim: str,
        locais_filtro: Optional[List[str]] = None,
        empresa_padrao: str = "11",
    ) -> List[Dict[str, Any]]:
        """
        Gera a lista concreta de tarefas de scraping a serem executadas pelos workers.
        """
        tarefas: List[Dict[str, Any]] = []

        for template in self._raw_skeleton:
            if not template.get("ativo", True):
                continue

            t_id = template.get("id", "tarefa")
            nome = template.get("nome", t_id)
            grupo = template.get("grupo", "geral")
            url = template.get("url", "")
            metodo = template.get("metodo", "POST").upper()
            headers = deepcopy(template.get("headers", {}))
            iterar = template.get("iterar_por_local", False)
            params_dinamicos = template.get("parametros_dinamicos", {})

            # Base do payload estático configurado no JSON
            payload_base = deepcopy(template.get("payload_estatico", {}))
            # Regra estrita mandatória: sempre usar empresa 11
            payload_base["cod_empresa"] = empresa_padrao

            # Injeção de datas se houver mapeamento dinâmico
            if "data_inicio_campo" in params_dinamicos:
                payload_base[params_dinamicos["data_inicio_campo"]] = data_inicio
            if "data_fim_campo" in params_dinamicos:
                payload_base[params_dinamicos["data_fim_campo"]] = data_fim

            if iterar:
                # Expansão iterativa por local
                locais_disponiveis = template.get("locais_disponiveis", [])
                if locais_filtro:
                    locais = [loc for loc in locais_disponiveis if loc in locais_filtro]
                    if not locais:
                        locais = locais_filtro
                else:
                    locais = locais_disponiveis

                for local in locais:
                    payload_local = deepcopy(payload_base)
                    # O PHP legado espera local[] no POST form
                    payload_local["local[]"] = local

                    tarefas.append(
                        {
                            "task_id": f"{t_id}_{local.replace(' ', '_').replace('-', '_')}",
                            "template_id": t_id,
                            "nome": f"{nome} - {local}",
                            "grupo": grupo,
                            "local": local,
                            "url": url,
                            "metodo": metodo,
                            "headers": headers,
                            "payload": payload_local,
                        }
                    )
            else:
                # Tarefa única não particionada por local (ex: estoque geral)
                tarefas.append(
                    {
                        "task_id": t_id,
                        "template_id": t_id,
                        "nome": nome,
                        "grupo": grupo,
                        "local": None,
                        "url": url,
                        "metodo": metodo,
                        "headers": headers,
                        "payload": payload_base,
                    }
                )

        return tarefas
