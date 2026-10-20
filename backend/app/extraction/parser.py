import re
from typing import List, Optional
from bs4 import BeautifulSoup
import pandas as pd


class LegacyTableParser:
    """
    Parser resiliente de tabelas legadas com BeautifulSoup4.
    Atende ao Princípio IV da Constituição:
    - Identificação heurística da tabela de dados relevante.
    - Desdobramento correto de colspan e rowspan.
    - Sanitização de entidades HTML (&nbsp;), quebras de linha e espaços espúrios.
    - Conversão para pandas.DataFrame padronizado.
    """

    def __init__(self, parser_backend: str = "lxml"):
        self.parser_backend = parser_backend

    def parse_html_to_dataframe(
        self,
        html_content: str,
        expected_keywords: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Analisa o HTML bruto e localiza a tabela de dados principal,
        retornando um DataFrame do Pandas limpo.
        """
        if not html_content or not html_content.strip():
            return pd.DataFrame()

        soup = BeautifulSoup(html_content, self.parser_backend)
        tables = soup.find_all("table")

        if not tables:
            return pd.DataFrame()

        # Heurística para selecionar a tabela certa:
        # Prioriza tabelas "folha" (que não possuem outras tabelas de layout aninhadas dentro delas)
        leaf_tables = [tbl for tbl in tables if not tbl.find("table")]
        candidate_tables = leaf_tables if leaf_tables else tables

        best_table = None
        best_score = -1

        for tbl in candidate_tables:
            text = tbl.get_text()
            rows = tbl.find_all("tr")
            if len(rows) < 2:
                continue

            score = 0
            if expected_keywords:
                for kw in expected_keywords:
                    if kw.lower() in text.lower():
                        score += 10
            score += len(rows)

            if score > best_score:
                best_score = score
                best_table = tbl

        if not best_table:
            # Fallback para a última tabela candidata ou a que tiver mais linhas
            best_table = max(candidate_tables, key=lambda t: len(t.find_all("tr")))

        return self._extract_table_to_df(best_table)

    def _extract_table_to_df(self, table_element) -> pd.DataFrame:
        rows = table_element.find_all("tr")
        if not rows:
            return pd.DataFrame()

        # Identificação das linhas de cabeçalho e dados
        matrix: List[List[str]] = []
        # Mapa de rowspan: col_idx -> (remaining_rows, value)
        rowspan_map: dict = {}

        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells:
                continue

            row_values: List[str] = []
            col_idx = 0

            # Preenche células pendentes de rowspan de linhas anteriores
            while col_idx in rowspan_map:
                remaining, val = rowspan_map[col_idx]
                row_values.append(val)
                if remaining <= 1:
                    del rowspan_map[col_idx]
                else:
                    rowspan_map[col_idx] = (remaining - 1, val)
                col_idx += 1

            for cell in cells:
                # Verifica se a posição atual já foi preenchida por rowspan
                while col_idx in rowspan_map:
                    remaining, val = rowspan_map[col_idx]
                    row_values.append(val)
                    if remaining <= 1:
                        del rowspan_map[col_idx]
                    else:
                        rowspan_map[col_idx] = (remaining - 1, val)
                    col_idx += 1

                # Limpeza do texto da célula
                cell_text = cell.get_text(separator=" ", strip=True)
                cell_text = re.sub(r"\s+", " ", cell_text).strip()

                colspan = int(cell.get("colspan", 1))
                rowspan = int(cell.get("rowspan", 1))

                for _ in range(colspan):
                    row_values.append(cell_text)
                    if rowspan > 1:
                        rowspan_map[col_idx] = (rowspan - 1, cell_text)
                    col_idx += 1

            if any(val.strip() for val in row_values):
                matrix.append(row_values)

        if not matrix:
            return pd.DataFrame()

        # Heurística para cabeçalhos:
        # A primeira linha que tiver pelo menos 2 colunas válidas é tratada como header
        header = [str(c).strip() for c in matrix[0]]
        # Uniquify headers vazios ou duplicados
        clean_headers = []
        counts = {}
        for i, h in enumerate(header):
            if not h:
                h = f"col_{i}"
            count = counts.get(h, 0)
            if count > 0:
                clean_headers.append(f"{h}_{count}")
            else:
                clean_headers.append(h)
            counts[h] = count + 1

        data_rows = matrix[1:]
        # Ajusta tamanhos caso alguma linha tenha colunas a mais ou a menos
        expected_len = len(clean_headers)
        normalized_data = []
        for r in data_rows:
            if len(r) < expected_len:
                r = r + [""] * (expected_len - len(r))
            elif len(r) > expected_len:
                r = r[:expected_len]
            # Ignora linhas que sejam cabeçalhos repetidos
            if r == header or r == clean_headers:
                continue
            normalized_data.append(r)

        return pd.DataFrame(normalized_data, columns=clean_headers)


# Instância singleton padrão
table_parser = LegacyTableParser()
