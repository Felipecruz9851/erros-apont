from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set
import pandas as pd


class CalculationEngine:
    """
    Motor de Cálculo de Saldo e Apontamento Analítico.
    Regras de Negócio:
    1. Filtra ordens com data de abertura <= data_atual (preenchida no frontend).
    2. Organiza a fila de consumo por data de entrega das ordens mais urgentes/antigas
       para as mais futuras (ex: entrega 15/10 consome antes de 20/10, que consome antes de 22/10).
    3. Abate cumulativamente o estoque disponível (Qtde física no local de produção da ordem)
       a cada ordem atendida para o mesmo componente e local de produção.
    4. Avalia a janela de entrega em relação à data_atual:
       - Ordens com data de entrega <= data_atual + N dias úteis (desconsiderando sábados, domingos e feriados):
         - Se não houver saldo suficiente no local de produção da ordem -> Passível de Erro de Apontamento
           (SALDO_INSUFICIENTE ou SALDO_ZERADO_NO_LOCAL).
         - Se houver saldo suficiente no local de produção da ordem -> Marcada como OK.
       - Ordens com data de entrega > data_atual + N dias úteis -> Ignoradas do resultado final.
    """

    def _parse_dt(self, val: object) -> Optional[datetime]:
        if pd.isna(val) or not val:
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

    def calculate_pointing_errors(
        self,
        df_consumo: pd.DataFrame,
        df_estoque: pd.DataFrame,
        data_atual: Optional[str] = None,
        include_ok: bool = True,
        dias_uteis: int = 3,
    ) -> pd.DataFrame:
        cols = [
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
        if df_consumo.empty:
            return pd.DataFrame(columns=cols)

        # 1. Filtra estritamente componentes com baixa automática
        df_c = df_consumo[df_consumo["baixa_automatica"] == True].copy()
        if df_c.empty:
            return pd.DataFrame(columns=cols)

        # A data de referência é SEMPRE a informada no frontend (campo "Data atual" -> data_fim).
        # Não há fallback silencioso: sem data válida, os filtros de abertura/entrega seriam ignorados.
        ref_dt = self._parse_dt(data_atual)
        if ref_dt is None:
            raise ValueError(
                f"Data atual de referência inválida ou ausente: {data_atual!r}. "
                "Informe a data no frontend (formato YYYY-MM-DD)."
            )
        limit_dt = self.add_business_days(ref_dt, days=dias_uteis)

        # 2. Filtra ordens com data de abertura <= data_atual (quando ambas existirem)
        if "data_abertura" in df_c.columns:
            def _abertura_valida(val: object) -> bool:
                dt_ab = self._parse_dt(val)
                if dt_ab is None:
                    return True
                return dt_ab <= ref_dt

            df_c = df_c[df_c["data_abertura"].apply(_abertura_valida)].copy()
            if df_c.empty:
                return pd.DataFrame(columns=cols)

        # 3. Filtra ordens com data de entrega válida dentro do limite (ordens sem data de entrega não pertencem à janela)
        if "data_entrega" in df_c.columns:
            def _entrega_valida(val: object) -> bool:
                dt_ent = self._parse_dt(val)
                if dt_ent is None:
                    return False
                if limit_dt is not None:
                    return dt_ent <= limit_dt
                return True

            df_c = df_c[df_c["data_entrega"].apply(_entrega_valida)].copy()
            if df_c.empty:
                return pd.DataFrame(columns=cols)

        # 4. Ordena cronologicamente pela data de entrega (das mais antigas/atrasadas para as mais futuras)
        df_c["_sort_data_entrega"] = df_c["data_entrega"].astype(str)
        if "data_abertura" in df_c.columns:
            df_c["_sort_data_abertura"] = df_c["data_abertura"].replace("", "9999-12-31").fillna("9999-12-31")
        else:
            df_c["_sort_data_abertura"] = "9999-12-31"

        df_c = df_c.sort_values(
            by=["codigo_componente", "local_producao", "_sort_data_entrega", "_sort_data_abertura", "op"]
        ).reset_index(drop=True)

        # 4. Cria mapa de saldo inicial disponível por (codigo_item, local_estoque)
        stock_map = {}
        if not df_estoque.empty:
            for _, row in df_estoque.iterrows():
                key = (str(row["codigo_item"]).strip().upper(), str(row["local_estoque"]).strip().upper())
                stock_map[key] = stock_map.get(key, 0.0) + float(row.get("saldo_disponivel", 0.0))

        # 5. Alocação cumulativa e classificação na janela de até 3 dias da data_atual
        registros: List[dict] = []
        grupos = df_c.groupby(["codigo_componente", "local_producao"], sort=False)

        for (cod_comp, loc_prod), group_rows in grupos:
            saldo_inicial = stock_map.get((cod_comp, loc_prod), 0.0)
            saldo_corrente = saldo_inicial
            prioridade = 1

            for _, row in group_rows.iterrows():
                op = str(row["op"]).strip()
                fabrica = str(row.get("fabrica", loc_prod)).strip()
                qtd_necessaria = float(row.get("qtd_necessaria", 0.0))
                data_ent_str = str(row.get("data_entrega", "") or "").strip()
                dt_ent = self._parse_dt(data_ent_str)

                # Se a ordem não possui data de entrega válida ou ultrapassa a janela limite, é ignorada
                if dt_ent is None:
                    continue
                if limit_dt is not None and dt_ent > limit_dt:
                    continue

                saldo_rem = saldo_corrente

                tipo_comp = str(row.get("tipo_componente", "C")).strip().upper()
                if not tipo_comp or tipo_comp not in ["P", "C"]:
                    tipo_comp = "P" if tipo_comp.startswith("P") else "C"

                # Verifica se há componentes disponíveis em quantidade suficiente no local de produção
                if saldo_rem < qtd_necessaria:
                    deficit = round(qtd_necessaria - max(0.0, saldo_rem), 4)
                    if saldo_inicial <= 0.0:
                        status_div = "SALDO_ZERADO_NO_LOCAL"
                    else:
                        status_div = "SALDO_INSUFICIENTE"

                    if deficit >= (qtd_necessaria * 0.5) or saldo_rem <= 0.0:
                        severidade = "ALTA"
                    else:
                        severidade = "MEDIA"

                    # Abate do estoque o que foi possível consumir (zera o saldo disponível para as próximas OPs)
                    saldo_corrente = max(0.0, saldo_corrente - qtd_necessaria)

                    registros.append(
                        {
                            "id": f"{fabrica}-{op}-{cod_comp}",
                            "fabrica": fabrica,
                            "op": op,
                            "data_abertura": row.get("data_abertura", ""),
                            "data_entrega": data_ent_str,
                            "prioridade_fila": prioridade,
                            "produto_op": row.get("produto_op", ""),
                            "local_producao": loc_prod,
                            "codigo_componente": cod_comp,
                            "descricao_componente": row.get("descricao_componente", ""),
                            "tipo_componente": tipo_comp,
                            "baixa_automatica": True,
                            "qtd_necessaria": qtd_necessaria,
                            "saldo_inicial_local": round(saldo_inicial, 4),
                            "saldo_remanescente": round(saldo_rem, 4),
                            "deficit_saldo": deficit,
                            "status_divergencia": status_div,
                            "severidade": severidade,
                        }
                    )
                else:
                    # Ordem atendida: abate a quantidade consumida do saldo disponível para as próximas ordens
                    saldo_corrente = round(saldo_corrente - qtd_necessaria, 4)

                    if include_ok:
                        registros.append(
                            {
                                "id": f"{fabrica}-{op}-{cod_comp}",
                                "fabrica": fabrica,
                                "op": op,
                                "data_abertura": row.get("data_abertura", ""),
                                "data_entrega": data_ent_str,
                                "prioridade_fila": prioridade,
                                "produto_op": row.get("produto_op", ""),
                                "local_producao": loc_prod,
                                "codigo_componente": cod_comp,
                                "descricao_componente": row.get("descricao_componente", ""),
                                "tipo_componente": tipo_comp,
                                "baixa_automatica": True,
                                "qtd_necessaria": qtd_necessaria,
                                "saldo_inicial_local": round(saldo_inicial, 4),
                                "saldo_remanescente": round(saldo_rem, 4),
                                "deficit_saldo": 0.0,
                                "status_divergencia": "OK",
                                "severidade": "OK",
                            }
                        )

                prioridade += 1

        if not registros:
            return pd.DataFrame(columns=cols)

        df_out = pd.DataFrame(registros)
        # Organiza o resultado geral pela data de entrega (das mais antigas/urgentes para as mais recentes)
        df_out["_sort_ent"] = df_out["data_entrega"].replace("", "9999-12-31").fillna("9999-12-31")
        df_out = df_out.sort_values(by=["_sort_ent", "prioridade_fila", "op"]).drop(columns=["_sort_ent"]).reset_index(drop=True)
        return df_out


calculation_engine = CalculationEngine()
