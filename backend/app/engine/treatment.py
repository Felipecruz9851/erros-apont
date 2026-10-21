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

    def _parse_date_iso(self, val: object) -> str:
        """
        Converte datas legadas (DD/MM/YYYY., DD/MM/YYYY, YYYY-MM-DD) para YYYY-MM-DD.
        Retorna string vazia caso não seja uma data válida.
        """
        if pd.isna(val) or val is None:
            return ""
        s = str(val).strip().rstrip(".")
        if not s or s == ".":
            return ""
        # Formato DD/MM/YYYY
        m_br = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
        if m_br:
            return f"{m_br.group(3)}-{m_br.group(2)}-{m_br.group(1)}"
        # Formato YYYY-MM-DD
        m_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
        if m_iso:
            return f"{m_iso.group(1)}-{m_iso.group(2)}-{m_iso.group(3)}"
        return s

    def _clean_item_code(self, val: object) -> str:
        """
        Limpa o código do componente removendo sufixos de unidade de medida
        presentes nos links do relatório de consumo (ex: '3COUPCOU378 -M2' -> '3COUPCOU378'
        ou códigos de 15 caracteres colados na unidade como '3LEDDP73000K24V-UN' -> '3LEDDP73000K24V').
        """
        if pd.isna(val) or val is None:
            return ""
        s = str(val).strip().upper()
        # Remove sufixo de unidade precedido ou não por espaço (ex: ' -M2', '-UN', '-PAR', '-KG')
        # Garante que a unidade comece com letra ([A-Z]) para não afetar códigos sintéticos de teste (ex: 'COMP-001')
        s = re.sub(r"\s*-[A-Z][A-Z0-9]{1,3}$", "", s)
        return s.strip()

    def _clean_local_estoque(self, val: object) -> str:
        """
        Limpa o código do local de estoque removendo o sufixo de situação
        presente no relatório de estoque (ex: 'CAPAS LE - L' -> 'CAPAS LE').
        """
        if pd.isna(val) or val is None:
            return ""
        s = str(val).strip().upper()
        s = re.sub(r"\s*-\s*[LIRE]$", "", s)
        return s.strip()

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
        local_filtro_series = (
            df["_local_filtro"].astype(str).str.strip().str.upper()
            if "_local_filtro" in df.columns
            else None
        )

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
            df["local_producao"] = local_filtro_series if local_filtro_series is not None else "GERAL"
        if "fabrica" not in df.columns:
            df["fabrica"] = local_filtro_series if local_filtro_series is not None else "F01"
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
        df["codigo_componente"] = df["codigo_componente"].apply(self._clean_item_code)
        df["fabrica"] = df["fabrica"].astype(str).str.strip().str.upper()
        df["local_producao"] = df["local_producao"].astype(str).str.strip().str.upper()

        # Quando extraído de consumo_alt.php por local (_local_filtro), a coluna 'Local Prod.'
        # refere-se à origem do componente (ou '0' para comprado), enquanto o local de produção da ordem
        # consumidora é o próprio _local_filtro (fábrica da ordem).
        if local_filtro_series is not None:
            df["fabrica"] = local_filtro_series
            df["local_producao"] = local_filtro_series
        else:
            mask_invalid_loc = df["local_producao"].isin(["", "0", ".", "NONE", "NAN"])
            df.loc[mask_invalid_loc, "local_producao"] = df.loc[mask_invalid_loc, "fabrica"]
            mask_valid_loc = ~df["local_producao"].isin(["", "0", ".", "NONE", "NAN"]) & df["fabrica"].isin(["F01", "GERAL", ""])
            df.loc[mask_valid_loc, "fabrica"] = df.loc[mask_valid_loc, "local_producao"]

        df["descricao_componente"] = df["descricao_componente"].astype(str).str.strip()
        df["data_abertura"] = df["data_abertura"].apply(self._parse_date_iso)
        df["data_entrega"] = df["data_entrega"].apply(self._parse_date_iso)

        # Remove linhas de rodapé/totais do relatório legado (ex: '0 itens, 0 horas, custo 0,00' ou 'Total de peças = ...')
        df = df[~df["op"].isin(["", "SEM_OP", "NONE", "NAN", "."])].copy()
        df = df[~df["codigo_componente"].str.upper().str.startswith(("TOTAL", "0 ITENS"))].copy()

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
            elif norm in ["sofre_baixa", "baixa", "baixa_automatica"]:
                target = "sofre_baixa"

            if target and target not in assigned_targets:
                rename_map[col] = target
                assigned_targets.add(target)

        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]

        if "codigo_item" not in df.columns:
            df["codigo_item"] = "SEM_ITEM"
        if "local_estoque" not in df.columns:
            df["local_estoque"] = "GERAL"

        df["codigo_item"] = df["codigo_item"].apply(self._clean_item_code)
        df["local_estoque"] = df["local_estoque"].apply(self._clean_local_estoque)
        df = df[~df["codigo_item"].isin(["", "SEM_ITEM", "NONE", "NAN"])].copy()
        df = df[~df["codigo_item"].str.upper().str.startswith(("TOTAL", "0 ITENS"))].copy()

        # Mantém apenas itens que sofrem baixa automática (Sofre Baixa? == S / SIM)
        if "sofre_baixa" in df.columns:
            df = df[df["sofre_baixa"].astype(str).str.strip().str.upper().isin(["S", "SIM", "TRUE", "1"])].copy()

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

        # Regra de Saldo Disponível: Usa Qtde. (saldo físico no local, ignorando Qt.Reser)
        df["saldo_disponivel"] = df["saldo_fisico"]

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
        assigned = set()
        for col in df_o.columns:
            norm = self._normalize_col_name(col)
            target = None
            if norm in ["ordem", "op"]:
                target = "op"
            elif norm in ["data_entrega", "entrega"]:
                target = "ordem_data_entrega"
            elif norm in ["data_abertura", "abertura"]:
                target = "ordem_data_abertura"
            elif norm in ["descricao_do_item"]:
                target = "ordem_produto"
            elif norm in ["fabrica"]:
                target = "ordem_fabrica"
            if target and target not in assigned:
                ordem_map[col] = target
                assigned.add(target)

        df_o = df_o.rename(columns=ordem_map)
        if "op" not in df_o.columns:
            return df_consumo

        df_o["op"] = df_o["op"].astype(str).str.strip().str.upper()
        df_o = df_o[~df_o["op"].isin(["", "NONE", "NAN", "."])].copy()
        df_o = df_o[~df_o["op"].str.startswith(("0 ITENS", "TOTAL"))].copy()
        if "ordem_data_entrega" in df_o.columns:
            df_o["ordem_data_entrega"] = df_o["ordem_data_entrega"].apply(self._parse_date_iso)
        if "ordem_data_abertura" in df_o.columns:
            df_o["ordem_data_abertura"] = df_o["ordem_data_abertura"].apply(self._parse_date_iso)

        cols_to_merge = ["op"]
        for c in ["ordem_data_entrega", "ordem_data_abertura", "ordem_produto", "ordem_fabrica"]:
            if c in df_o.columns:
                cols_to_merge.append(c)

        df_o_unique = df_o[cols_to_merge].drop_duplicates(subset=["op"])
        merged = pd.merge(df_consumo, df_o_unique, on="op", how="left")

        if "ordem_data_entrega" in merged.columns:
            merged["data_entrega"] = merged["ordem_data_entrega"].replace("", pd.NA).fillna(merged.get("data_entrega", "")).fillna("")
            merged = merged.drop(columns=["ordem_data_entrega"])
        if "ordem_data_abertura" in merged.columns:
            merged["data_abertura"] = merged["ordem_data_abertura"].replace("", pd.NA).fillna(merged.get("data_abertura", "")).fillna("")
            merged = merged.drop(columns=["ordem_data_abertura"])
        if "ordem_produto" in merged.columns:
            merged["produto_op"] = merged["ordem_produto"].replace("", pd.NA).fillna(merged.get("produto_op", "")).fillna("")
            merged = merged.drop(columns=["ordem_produto"])
        if "ordem_fabrica" in merged.columns:
            ordem_fab = merged["ordem_fabrica"].astype(str).str.strip().str.upper()
            # No consumo_alt.php, uma OP da fábrica X pode ter componente produzido no local Y,
            # mas o local de produção da ordem consumidora é a fábrica da ordem (ordem_fabrica / _local_filtro)
            mask_valid_fab = ~ordem_fab.isin(["", "NONE", "NAN", "."])
            merged.loc[mask_valid_fab, "fabrica"] = ordem_fab[mask_valid_fab]
            merged.loc[mask_valid_fab, "local_producao"] = ordem_fab[mask_valid_fab]
            merged = merged.drop(columns=["ordem_fabrica"])

        return merged


treatment_engine = TreatmentEngine()
