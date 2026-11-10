from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set, Union
import pandas as pd
import polars as pl


class CalculationEngine:
    """
    Motor de Cálculo de Saldo e Apontamento Analítico de Alta Performance (Polars + Pandas).
    Regras de Negócio:
    1. Filtra ordens com data de abertura <= data_atual (preenchida no frontend).
    2. Organiza a fila de consumo por data de entrega das ordens mais urgentes/antigas
       para as mais futuras (ex: entrega 15/10 consome antes de 20/10, que consome antes de 22/10).
    3. Abate cumulativamente o estoque disponível (Qtde física no local de produção da ordem)
       a cada ordem atendida para o mesmo componente e local de produção (Window Functions Vetorizadas).
    4. Avalia a janela de entrega em relação à data_atual:
       - Ordens com data de entrega <= data_atual + N dias úteis (desconsiderando sábados, domingos e feriados):
         - Se não houver saldo suficiente no local de produção da ordem -> Passível de Erro de Apontamento
           (SALDO_INSUFICIENTE ou SALDO_ZERADO_NO_LOCAL).
         - Se houver saldo suficiente no local de produção da ordem -> Marcada como OK.
       - Ordens com data de entrega > data_atual + N dias úteis -> Ignoradas do resultado final.
    """

    COLS = [
        "id",
        "fabrica",
        "op",
        "data_abertura",
        "data_entrega",
        "prioridade_fila",
        "produto_op",
        "local_producao",
        "codigo_componente",
        "descricao_componente",
        "tipo_componente",
        "baixa_automatica",
        "qtd_necessaria",
        "saldo_inicial_local",
        "saldo_remanescente",
        "deficit_saldo",
        "status_divergencia",
        "severidade",
    ]

    def _parse_dt(self, val: object) -> Optional[datetime]:
        if val is None or pd.isna(val):
            return None
        s = str(val).strip().rstrip(".")
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s[:10], fmt)
            except ValueError:
                continue
        return None

    def load_feriados(self) -> Set[str]:
        """
        Carrega lista de feriados em YYYY-MM-DD do arquivo feriados.txt.
        """
        feriados_file = Path(__file__).resolve().parent.parent / "feriados.txt"
        if not feriados_file.exists():
            return set()
        try:
            with open(feriados_file, "r", encoding="utf-8") as f:
                return {
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                }
        except Exception:
            return set()

    def add_business_days(
        self, start_date: datetime, days: int, holidays: Optional[Set[str]] = None
    ) -> datetime:
        """
        Calcula a data limite avançando N dias úteis (segunda a sexta-feira),
        desconsiderando finais de semana e feriados constantes na base.
        """
        if holidays is None:
            holidays = self.load_feriados()
        if days <= 0:
            return start_date
        curr = start_date
        added = 0
        while added < days:
            curr += timedelta(days=1)
            # weekday: 0=segunda ... 4=sexta, 5=sábado, 6=domingo
            if curr.weekday() < 5 and curr.strftime("%Y-%m-%d") not in holidays:
                added += 1
        return curr

    def calculate_pointing_errors_polars(
        self,
        df_consumo: Union[pl.DataFrame, pd.DataFrame],
        df_estoque: Union[pl.DataFrame, pd.DataFrame],
        data_atual: Optional[str] = None,
        include_ok: bool = True,
        dias_uteis: int = 3,
    ) -> pl.DataFrame:
        """
        Motor de cálculo vetorizado em Polars (Rust multi-threaded).
        Elimina loops linha a linha através de window functions de soma cumulativa sobre
        ['codigo_componente', 'local_producao'].
        """
        plc = pl.from_pandas(df_consumo) if isinstance(df_consumo, pd.DataFrame) else df_consumo
        ple = pl.from_pandas(df_estoque) if isinstance(df_estoque, pd.DataFrame) else df_estoque

        if plc is None or plc.is_empty():
            return pl.DataFrame(schema={c: pl.Utf8 for c in self.COLS})

        # 1. Filtra estritamente componentes com baixa automática
        if "baixa_automatica" in plc.columns:
            plc = plc.filter(pl.col("baixa_automatica") == True)
        if plc.is_empty():
            return pl.DataFrame(schema={c: pl.Utf8 for c in self.COLS})

        # Validação da data de referência
        ref_dt = self._parse_dt(data_atual)
        if ref_dt is None:
            raise ValueError(
                f"Data atual de referência inválida ou ausente: {data_atual!r}. "
                "Informe a data no frontend (formato YYYY-MM-DD)."
            )
        holidays = self.load_feriados()
        limit_dt = self.add_business_days(ref_dt, days=dias_uteis, holidays=holidays)
        ref_str = ref_dt.strftime("%Y-%m-%d")
        limit_str = limit_dt.strftime("%Y-%m-%d")

        # 2. Filtra abertura <= data_atual (se preenchida)
        if "data_abertura" in plc.columns:
            plc = plc.filter(
                (pl.col("data_abertura").is_null())
                | (pl.col("data_abertura") == "")
                | (pl.col("data_abertura") <= ref_str)
            )
        if plc.is_empty():
            return pl.DataFrame(schema={c: pl.Utf8 for c in self.COLS})

        # 3. Filtra entrega válida e <= limit_dt
        if "data_entrega" in plc.columns:
            plc = plc.filter(
                (pl.col("data_entrega").is_not_null())
                & (pl.col("data_entrega") != "")
                & (pl.col("data_entrega") <= limit_str)
            )
        if plc.is_empty():
            return pl.DataFrame(schema={c: pl.Utf8 for c in self.COLS})

        # Garante colunas de tipagem no estoque
        if ple is not None and not ple.is_empty() and "codigo_item" in ple.columns and "local_estoque" in ple.columns:
            stk = ple.group_by(["codigo_item", "local_estoque"]).agg(
                pl.col("saldo_disponivel").cast(pl.Float64).sum()
            )
        else:
            stk = pl.DataFrame(schema={"codigo_item": pl.Utf8, "local_estoque": pl.Utf8, "saldo_disponivel": pl.Float64})

        # 4. Normaliza colunas e piso de quantidade necessária
        sort_abertura = (
            pl.when((pl.col("data_abertura").is_null()) | (pl.col("data_abertura") == ""))
            .then(pl.lit("9999-12-31"))
            .otherwise(pl.col("data_abertura"))
        )

        plc = plc.with_columns(
            pl.when(pl.col("qtd_necessaria") <= 0.0)
            .then(1.0)
            .otherwise(pl.col("qtd_necessaria"))
            .cast(pl.Float64)
            .alias("qtd_necessaria"),
            sort_abertura.alias("_sort_abertura"),
        ).sort(["codigo_componente", "local_producao", "data_entrega", "_sort_abertura", "op"])

        # 5. Join do saldo inicial de estoque
        plc = plc.join(
            stk,
            left_on=["codigo_componente", "local_producao"],
            right_on=["codigo_item", "local_estoque"],
            how="left",
        )
        plc = plc.with_columns(
            pl.col("saldo_disponivel").fill_null(0.0).alias("saldo_inicial_local")
        )

        # 6. Alocação cumulativa vetorizada
        prev_cumsum = (
            pl.col("qtd_necessaria")
            .cum_sum()
            .over(["codigo_componente", "local_producao"])
            - pl.col("qtd_necessaria")
        )
        saldo_rem = (pl.col("saldo_inicial_local") - prev_cumsum).clip(lower_bound=0.0)

        plc = plc.with_columns(
            pl.int_range(1, pl.len() + 1).over(["codigo_componente", "local_producao"]).alias("prioridade_fila"),
            saldo_rem.alias("saldo_remanescente"),
        )

        deficit = (
            pl.when(pl.col("saldo_remanescente") < pl.col("qtd_necessaria"))
            .then((pl.col("qtd_necessaria") - pl.col("saldo_remanescente")).round(4))
            .otherwise(0.0)
        )

        status_div = (
            pl.when(pl.col("saldo_remanescente") >= pl.col("qtd_necessaria"))
            .then(pl.lit("OK"))
            .when(pl.col("saldo_inicial_local") <= 0.0)
            .then(pl.lit("SALDO_ZERADO_NO_LOCAL"))
            .otherwise(pl.lit("SALDO_INSUFICIENTE"))
        )

        plc = plc.with_columns(
            deficit.alias("deficit_saldo"),
            status_div.alias("status_divergencia"),
        )

        severidade = (
            pl.when(pl.col("status_divergencia") == "OK")
            .then(pl.lit("OK"))
            .when(
                (pl.col("deficit_saldo") >= pl.col("qtd_necessaria") * 0.5)
                | (pl.col("saldo_remanescente") <= 0.0)
            )
            .then(pl.lit("ALTA"))
            .otherwise(pl.lit("MEDIA"))
        )

        plc = plc.with_columns(
            severidade.alias("severidade"),
            (
                pl.col("fabrica").cast(pl.Utf8)
                + "-"
                + pl.col("op").cast(pl.Utf8)
                + "-"
                + pl.col("codigo_componente").cast(pl.Utf8)
            ).alias("id"),
        )

        if not include_ok:
            plc = plc.filter(pl.col("status_divergencia") != "OK")

        # Ordenação final estável por entrega, fila, op e código do componente
        plc = plc.sort(["data_entrega", "prioridade_fila", "op", "codigo_componente"])

        # Seleciona as colunas oficiais garantindo presença de todas
        existing_cols = [c for c in self.COLS if c in plc.columns]
        return plc.select(existing_cols)

    def calculate_pointing_errors(
        self,
        df_consumo: Union[pd.DataFrame, pl.DataFrame],
        df_estoque: Union[pd.DataFrame, pl.DataFrame],
        data_atual: Optional[str] = None,
        include_ok: bool = True,
        dias_uteis: int = 3,
    ) -> pd.DataFrame:
        """
        Ponto de entrada unificado: executa o motor vetorizado em Polars e devolve
        um pd.DataFrame para as camadas de serialização e exportação.
        """
        res_pl = self.calculate_pointing_errors_polars(
            df_consumo=df_consumo,
            df_estoque=df_estoque,
            data_atual=data_atual,
            include_ok=include_ok,
            dias_uteis=dias_uteis,
        )
        return res_pl.to_pandas() if not res_pl.is_empty() else pd.DataFrame(columns=self.COLS)


calculation_engine = CalculationEngine()
