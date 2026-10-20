import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.core.security import security_manager
from backend.app.extraction.worker import execute_task_pool
from backend.app.models.domain import ExecutionState
from backend.app.models.requests import StagesProgress, StatusResponse
from backend.app.tasks.generator import TaskGenerator


class ExecutionContext:
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.state: ExecutionState = "IDLE"
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.progress_pct: int = 0
        self.stages = StagesProgress()
        self.tasks_total: int = 0
        self.tasks_completed: int = 0
        self.error_message: Optional[str] = None
        
        # Estruturas de dados em memória
        self.raw_results: List[Dict[str, Any]] = []
        self.dfs_by_group: Dict[str, pd.DataFrame] = {}
        self.divergences_df: pd.DataFrame = pd.DataFrame()
        self.final_response: Optional[Dict[str, Any]] = None

    def get_elapsed_seconds(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

    def to_status_response(self) -> StatusResponse:
        return StatusResponse(
            execution_id=self.execution_id,
            stage=self.state,
            progress_pct=self.progress_pct,
            stages=self.stages,
            tasks_completed=self.tasks_completed,
            tasks_total=self.tasks_total,
            elapsed_seconds=self.get_elapsed_seconds(),
            error_message=self.error_message,
        )


class PipelineOrchestrator:
    """
    Orquestrador dos 6 estágios sequenciais da Constituição v1.1.0:
    I. Ingestão de Credenciais e Disparo
    II. Extração Assíncrona Multi-Fábrica
    III. Tratamento e Normalização Modular
    IV. Motor de Cálculo de Saldo e Apontamento (Alocação Cumulativa)
    V. Montagem do JSON de Saída
    VI. Exposição na API
    """

    def __init__(self):
        self._contexts: Dict[str, ExecutionContext] = {}
        self.task_generator = TaskGenerator()

    def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        return self._contexts.get(execution_id)

    def create_execution(self) -> ExecutionContext:
        exec_id = f"exec_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        ctx = ExecutionContext(exec_id)
        self._contexts[exec_id] = ctx
        return ctx

    async def start_pipeline_background(
        self,
        execution_id: str,
        username: str,
        password: str,
        data_inicio: str,
        data_fim: str,
        fabricas: Optional[List[str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        """Dispara a execução completa em background."""
        ctx = self.get_context(execution_id)
        if not ctx:
            return

        asyncio.create_task(
            self._run_stages(
                ctx=ctx,
                username=username,
                password=password,
                data_inicio=data_inicio,
                data_fim=data_fim,
                fabricas=fabricas,
                cookies=cookies,
            )
        )

    async def _run_stages(
        self,
        ctx: ExecutionContext,
        username: str,
        password: str,
        data_inicio: str,
        data_fim: str,
        fabricas: Optional[List[str]],
        cookies: Optional[Dict[str, str]],
    ) -> None:
        try:
            # ESTÁGIO 1: Autenticação e Preparação dos Workers
            ctx.state = "AUTHENTICATING"
            ctx.stages.auth = "IN_PROGRESS"
            ctx.progress_pct = 5

            security_manager.store_credentials(ctx.execution_id, username, password)

            # Gera tarefas expandidas por local conforme config/tarefas_esqueleto.json
            tasks = self.task_generator.generate_tasks(
                data_inicio=data_inicio,
                data_fim=data_fim,
                locais_filtro=fabricas,
                empresa_padrao="11",
            )
            ctx.tasks_total = len(tasks)
            ctx.tasks_completed = 0

            def _on_auth_done():
                # Transição automática após cada worker do pool concluir seu login individual
                ctx.stages.auth = "COMPLETED"
                ctx.state = "EXTRACTING"
                ctx.stages.extraction = "IN_PROGRESS"
                ctx.progress_pct = 10

            def _on_task_done(res: Dict[str, Any]):
                ctx.tasks_completed += 1
                if ctx.tasks_total > 0:
                    pct = 10 + int((ctx.tasks_completed / ctx.tasks_total) * 40)
                    ctx.progress_pct = min(pct, 50)

            # ESTÁGIO 2: Executa o pool de workers (cada worker faz login próprio 1x no seu ciclo de vida)
            raw_results = await execute_task_pool(
                execution_id=ctx.execution_id,
                tasks=tasks,
                username=username,
                password=password,
                cookies=cookies,
                concurrency_limit=5,
                on_auth_completed=_on_auth_done,
                on_task_completed=_on_task_done,
            )
            ctx.raw_results = raw_results
            ctx.stages.extraction = "COMPLETED"
            ctx.progress_pct = 50

            # Agrupa os DataFrames extraídos por grupo
            dfs_consumo = []
            dfs_estoque = []
            dfs_ordens = []

            for r in raw_results:
                df = r.get("dataframe")
                if df is not None and not df.empty:
                    grp = df.get("_grupo", pd.Series()).iloc[0] if "_grupo" in df.columns else ""
                    if grp == "consumo_ordem":
                        dfs_consumo.append(df)
                    elif grp == "estoque_local":
                        dfs_estoque.append(df)
                    elif grp == "ordens_producao":
                        dfs_ordens.append(df)

            ctx.dfs_by_group = {
                "consumo": pd.concat(dfs_consumo, ignore_index=True) if dfs_consumo else pd.DataFrame(),
                "estoque": pd.concat(dfs_estoque, ignore_index=True) if dfs_estoque else pd.DataFrame(),
                "ordens": pd.concat(dfs_ordens, ignore_index=True) if dfs_ordens else pd.DataFrame(),
            }

            # ESTÁGIO 3: Tratamento de Dados Modular
            ctx.state = "TREATING"
            ctx.stages.treatment = "IN_PROGRESS"
            ctx.progress_pct = 60

            from backend.app.engine.treatment import treatment_engine
            cleaned_consumo, cleaned_estoque = treatment_engine.clean_and_normalize(
                df_consumo=ctx.dfs_by_group["consumo"],
                df_estoque=ctx.dfs_by_group["estoque"],
                df_ordens=ctx.dfs_by_group.get("ordens"),
            )
            ctx.dfs_by_group["consumo_clean"] = cleaned_consumo
            ctx.dfs_by_group["estoque_clean"] = cleaned_estoque

            ctx.stages.treatment = "COMPLETED"
            ctx.progress_pct = 75

            # ESTÁGIO 4: Cálculo e Análise (Alocação Cumulativa)
            ctx.state = "CALCULATING"
            ctx.stages.calculation = "IN_PROGRESS"
            ctx.progress_pct = 80

            from backend.app.engine.calculation import calculation_engine
            divergences_df = calculation_engine.calculate_pointing_errors(
                df_consumo=cleaned_consumo,
                df_estoque=cleaned_estoque,
                data_atual=data_fim,
                include_ok=True,
            )
            ctx.divergences_df = divergences_df
            ctx.stages.calculation = "COMPLETED"
            ctx.progress_pct = 90

            # ESTÁGIO 5: Serialização e Montagem do JSON
            ctx.state = "SERIALIZING"
            ctx.stages.serialization = "IN_PROGRESS"

            from backend.app.engine.serializer import serialize_results
            total_ops_janela = (
                int(divergences_df["op"].nunique())
                if not divergences_df.empty and "op" in divergences_df.columns
                else 0
            )
            final_json = serialize_results(
                execution_id=ctx.execution_id,
                divergences_df=divergences_df,
                total_ops_analisadas=total_ops_janela,
                total_componentes_baixa_auto=len(divergences_df) if not divergences_df.empty else 0,
                elapsed_seconds=ctx.get_elapsed_seconds(),
            )
            ctx.final_response = final_json
            ctx.stages.serialization = "COMPLETED"
            ctx.stages.presentation = "COMPLETED"

            # ESTÁGIO 6: Conclusão
            ctx.state = "COMPLETED"
            ctx.progress_pct = 100
            ctx.end_time = time.time()

        except Exception as e:
            if ctx.state == "AUTHENTICATING":
                ctx.stages.auth = "FAILED"
            elif ctx.state == "EXTRACTING":
                ctx.stages.extraction = "FAILED"
            elif ctx.state == "TREATING":
                ctx.stages.treatment = "FAILED"
            elif ctx.state == "CALCULATING":
                ctx.stages.calculation = "FAILED"
            elif ctx.state == "SERIALIZING":
                ctx.stages.serialization = "FAILED"
            ctx.state = "FAILED"
            ctx.error_message = str(e)
            ctx.end_time = time.time()
        finally:
            # Purga senhas em memória após a finalização
            security_manager.purge_execution(ctx.execution_id)


# Instância global singleton
orchestrator = PipelineOrchestrator()
