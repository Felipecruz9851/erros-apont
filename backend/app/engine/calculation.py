from typing import List
import pandas as pd


class CalculationEngine:
    """
    Motor de Cálculo de Saldo e Apontamento Analítico.
    Executa a alocação cumulativa sequencial escalonada por data de entrega da OP:
    - OPs com entrega mais urgente alocam o saldo físico disponível no local de produção.
    - Ordens subsequentes cuja demanda acumulada exceder o saldo remanescente geram erro de apontamento.
    - Componentes sem saldo no local de produção específico da ordem são flagrados imediatamente,
      mesmo se houver saldo em almoxarifados ou depósitos centrais.
    """

    def calculate_pointing_errors(
        self,
        df_consumo: pd.DataFrame,
        df_estoque: pd.DataFrame,
    ) -> pd.DataFrame:
        if df_consumo.empty:
            return pd.DataFrame(
                columns=[
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
                    "baixa_automatica",
                    "qtd_necessaria",
                    "saldo_inicial_local",
                    "saldo_remanescente",
                    "deficit_saldo",
                    "status_divergencia",
                    "severidade",
                ]
            )

        # 1. Filtra estritamente componentes com baixa automática
        df_c = df_consumo[df_consumo["baixa_automatica"] == True].copy()

        # 2. Ordena cronologicamente por data de entrega (fila de prioridade)
        # Se data de entrega estiver vazia, ordena por data de abertura e OP
        if "data_entrega" in df_c.columns:
            df_c["_sort_data_entrega"] = df_c["data_entrega"].fillna("9999-12-31")
        else:
            df_c["_sort_data_entrega"] = "9999-12-31"

        if "data_abertura" in df_c.columns:
            df_c["_sort_data_abertura"] = df_c["data_abertura"].fillna("9999-12-31")
        else:
            df_c["_sort_data_abertura"] = "9999-12-31"
        df_c = df_c.sort_values(
            by=["codigo_componente", "local_producao", "_sort_data_entrega", "_sort_data_abertura", "op"]
        ).reset_index(drop=True)

        # 3. Cria mapa de saldo inicial disponível por (codigo_item, local_estoque)
        stock_map = {}
        if not df_estoque.empty:
            for _, row in df_estoque.iterrows():
                key = (str(row["codigo_item"]).strip().upper(), str(row["local_estoque"]).strip().upper())
                stock_map[key] = float(row.get("saldo_disponivel", 0.0))

        # 4. Alocação cumulativa e detecção de déficits
        erros: List[dict] = []
        grupos = df_c.groupby(["codigo_componente", "local_producao"], sort=False)

        for (cod_comp, loc_prod), group_rows in grupos:
            # Saldo inicial disponível no local exato de produção
            saldo_inicial = stock_map.get((cod_comp, loc_prod), 0.0)
            saldo_corrente = saldo_inicial
            prioridade = 1

            for _, row in group_rows.iterrows():
                op = str(row["op"]).strip()
                fabrica = str(row.get("fabrica", "F01")).strip()
                qtd_necessaria = float(row.get("qtd_necessaria", 0.0))
                saldo_rem = saldo_corrente

                # Verifica suficiência de saldo
                if saldo_rem < qtd_necessaria:
                    # Déficit detectado
                    deficit = round(qtd_necessaria - max(0.0, saldo_rem), 4)
                    
                    # Classificação do status
                    if saldo_inicial <= 0.0:
                        status_div = "SALDO_ZERADO_NO_LOCAL"
                    else:
                        status_div = "SALDO_INSUFICIENTE"

                    # Severidade
                    if deficit >= (qtd_necessaria * 0.5) or saldo_rem <= 0.0:
                        severidade = "ALTA"
                    else:
                        severidade = "MEDIA"

                    erros.append(
                        {
                            "id": f"{fabrica}-{op}-{cod_comp}",
                            "fabrica": fabrica,
                            "op": op,
                            "data_abertura": row.get("data_abertura", ""),
                            "data_entrega": row.get("data_entrega", ""),
                            "prioridade_fila": prioridade,
                            "produto_op": row.get("produto_op", ""),
                            "local_producao": loc_prod,
                            "codigo_componente": cod_comp,
                            "descricao_componente": row.get("descricao_componente", ""),
                            "baixa_automatica": True,
                            "qtd_necessaria": qtd_necessaria,
                            "saldo_inicial_local": round(saldo_inicial, 4),
                            "saldo_remanescente": round(saldo_rem, 4),
                            "deficit_saldo": deficit,
                            "status_divergencia": status_div,
                            "severidade": severidade,
                        }
                    )

                # Deduz consumo da fila cumulativa
                saldo_corrente -= qtd_necessaria
                prioridade += 1

        return pd.DataFrame(erros)


calculation_engine = CalculationEngine()
