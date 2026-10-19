import re
from typing import Optional, Tuple
import pandas as pd


class TreatmentEngine:
    """
    Camada modular e incremental de tratamento e saneamento de dados.
    Projetada para permitir que o usuário refine e adicione novas transformações
    aos poucos, desacoplada da extração e do cálculo.
    """

    def clean_and_normalize(
        self,
        df_consumo: pd.DataFrame,
        df_estoque: pd.DataFrame,
        df_ordens: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Executa a normalização das fontes de dados brutas e retorna
        (df_consumo_normalizado, df_estoque_normalizado).
        """
        c_clean = self.normalize_consumo(df_consumo)
        e_clean = self.normalize_estoque(df_estoque)

        # Se houver relatório de ordens/atrasadas com datas, complementa o consumo
        if df_ordens is not None and not df_ordens.empty:
            c_clean = self.enrich_consumo_with_ordens(c_clean, df_ordens)

        return c_clean, e_clean

    def _normalize_col_name(self, col: str) -> str:
        s = col.lower().strip()
        s = re.sub(r"[.\-_/]", " ", s)
        s = re.sub(r"\s+", "_", s).strip("_")
        return s

    def normalize_consumo(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "op",
                    "fabrica",
                    "codigo_componente",
                    "descricao_componente",
                    "baixa_automatica",
                    "qtd_necessaria",
                    "unidade_medida",
                    "local_producao",
                    "data_abertura",
                    "data_entrega",
                    "produto_op",
                ]
            )

        df = df.copy()
        # Normaliza nomes de colunas sem conflitos
        rename_map = {}
        assigned_targets = set()
        for col in df.columns:
            norm = self._normalize_col_name(col)
            target = None
            if norm in ["item", "codigo", "cod_item", "codigo_componente"]:
                target = "codigo_componente"
            elif norm in ["op", "ordem", "num_ordem"]:
                target = "op"
            elif norm in ["local_prod", "local_producao", "loc_prod"]:
                target = "local_producao"
            elif norm in ["consumo", "qtd", "quantidade", "qtd_necessaria"]:
                target = "qtd_necessaria"
            elif norm == "consumo_estrut" and "qtd_necessaria" not in assigned_targets:
                target = "qtd_necessaria"
            elif norm in ["baixa", "sofre_baixa", "baixa_automatica"]:
                target = "baixa"
            elif norm in ["den_item", "descricao", "descricao_componente"]:
                target = "descricao_componente"
            elif norm in ["fabrica", "_local_filtro"]:
                target = "fabrica"
            elif norm in ["data_abertura", "dat_abertura", "dati"]:
                target = "data_abertura"
            elif norm in ["data_entrega", "dat_entrega", "datf", "entrega"]:
                target = "data_entrega"

            if target and target not in assigned_targets:
                rename_map[col] = target
                assigned_targets.add(target)

        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]

        # Garante colunas essenciais
        if "op" not in df.columns:
            df["op"] = "SEM_OP"
        if "codigo_componente" not in df.columns:
            df["codigo_componente"] = "SEM_CODIGO"
        if "local_producao" not in df.columns:
            df["local_producao"] = df.get("_local_filtro", "GERAL")
        if "fabrica" not in df.columns:
            df["fabrica"] = df.get("_local_filtro", "F01")
        if "descricao_componente" not in df.columns:
            df["descricao_componente"] = ""
        if "produto_op" not in df.columns:
            df["produto_op"] = "PRODUTO NÃO INFORMADO"
        if "data_abertura" not in df.columns:
            df["data_abertura"] = ""
        if "data_entrega" not in df.columns:
            df["data_entrega"] = ""

        # Limpeza e tipagem
        df["op"] = df["op"].astype(str).str.strip().str.upper()
        df["codigo_componente"] = df["codigo_componente"].astype(str).str.strip().str.upper()
        df["local_producao"] = df["local_producao"].astype(str).str.strip().str.upper()
        df["fabrica"] = df["fabrica"].astype(str).str.strip().str.upper()
        df["descricao_componente"] = df["descricao_componente"].astype(str).str.strip()

        # Tratamento de quantidade necessária
        def _parse_float(val):
            try:
                if pd.isna(val) or val == "":
                    return 0.0
                val_str = str(val).replace(".", "").replace(",", ".")
                return float(val_str)
            except Exception:
                return 0.0

        if "qtd_necessaria" in df.columns:
            df["qtd_necessaria"] = df["qtd_necessaria"].apply(_parse_float)
        else:
            df["qtd_necessaria"] = 0.0

        # Filtro estrito de baixa automática (baixa == 'S' ou True)
        if "baixa" in df.columns:
            df["baixa_automatica"] = df["baixa"].astype(str).str.strip().str.upper().isin(["S", "SIM", "TRUE", "1"])
        else:
            df["baixa_automatica"] = True

        # Restringe aos componentes de baixa automática conforme regra de negócio central
        df = df[df["baixa_automatica"] == True].copy()

        return df

    def normalize_estoque(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "codigo_item",
                    "local_estoque",
                    "saldo_disponivel",
                    "saldo_fisico",
                    "saldo_reservado",
                ]
            )

        df = df.copy()
        rename_map = {}
        assigned_targets = set()
        for col in df.columns:
            norm = self._normalize_col_name(col)
            target = None
            if norm in ["item", "codigo", "cod_item", "codigo_item"]:
                target = "codigo_item"
            elif norm in ["local", "local_estoque", "local_sit", "local_prod"]:
                target = "local_estoque"
            elif norm in ["qtde", "qtde_", "saldo_fisico", "saldo"]:
                target = "saldo_fisico"
            elif norm in ["qt_reser", "saldo_reservado", "reservado"]:
                target = "saldo_reservado"

            if target and target not in assigned_targets:
                rename_map[col] = target
                assigned_targets.add(target)

        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]

        if "codigo_item" not in df.columns:
            df["codigo_item"] = "SEM_ITEM"
        if "local_estoque" not in df.columns:
            df["local_estoque"] = "GERAL"

        df["codigo_item"] = df["codigo_item"].astype(str).str.strip().str.upper()
        df["local_estoque"] = df["local_estoque"].astype(str).str.strip().str.upper()

        def _parse_float(val):
            try:
                if pd.isna(val) or val == "":
                    return 0.0
                val_str = str(val).replace(".", "").replace(",", ".")
                return float(val_str)
            except Exception:
                return 0.0

        if "saldo_fisico" in df.columns:
            df["saldo_fisico"] = df["saldo_fisico"].apply(_parse_float)
        else:
            df["saldo_fisico"] = 0.0

        if "saldo_reservado" in df.columns:
            df["saldo_reservado"] = df["saldo_reservado"].apply(_parse_float)
        else:
            df["saldo_reservado"] = 0.0

        # Regra de Saldo Disponível: Saldo Físico - Saldo Reservado
        df["saldo_disponivel"] = df["saldo_fisico"] - df["saldo_reservado"]

        # Agrega saldos se houver múltiplos lotes no mesmo item e local
        df_agrupado = (
            df.groupby(["codigo_item", "local_estoque"], as_index=False)[
                ["saldo_disponivel", "saldo_fisico", "saldo_reservado"]
            ]
            .sum()
        )

        return df_agrupado

    def enrich_consumo_with_ordens(self, df_consumo: pd.DataFrame, df_ordens: pd.DataFrame) -> pd.DataFrame:
        """Enriquece o consumo com as datas de abertura e entrega extraídas de ordens."""
        if df_consumo.empty or df_ordens.empty:
            return df_consumo

        df_o = df_ordens.copy()
        # Mapeia colunas de ordens
        ordem_map = {}
        for col in df_o.columns:
            norm = self._normalize_col_name(col)
            if norm in ["ordem", "op"]:
                ordem_map[col] = "op"
            elif norm in ["data_entrega", "entrega"]:
                ordem_map[col] = "ordem_data_entrega"
            elif norm in ["data_abertura", "abertura"]:
                ordem_map[col] = "ordem_data_abertura"
            elif norm in ["descricao_do_item", "cliente"]:
                ordem_map[col] = "ordem_produto"

        df_o = df_o.rename(columns=ordem_map)
        if "op" not in df_o.columns:
            return df_consumo

        df_o["op"] = df_o["op"].astype(str).str.strip().str.upper()
        cols_to_merge = ["op"]
        for c in ["ordem_data_entrega", "ordem_data_abertura", "ordem_produto"]:
            if c in df_o.columns:
                cols_to_merge.append(c)

        df_o_unique = df_o[cols_to_merge].drop_duplicates(subset=["op"])
        merged = pd.merge(df_consumo, df_o_unique, on="op", how="left")

        if "ordem_data_entrega" in merged.columns:
            merged["data_entrega"] = merged["ordem_data_entrega"].fillna(merged.get("data_entrega", ""))
            merged = merged.drop(columns=["ordem_data_entrega"])
        if "ordem_data_abertura" in merged.columns:
            merged["data_abertura"] = merged["ordem_data_abertura"].fillna(merged.get("data_abertura", ""))
            merged = merged.drop(columns=["ordem_data_abertura"])
        if "ordem_produto" in merged.columns:
            merged["produto_op"] = merged["ordem_produto"].fillna(merged.get("produto_op", ""))
            merged = merged.drop(columns=["ordem_produto"])

        return merged


treatment_engine = TreatmentEngine()
