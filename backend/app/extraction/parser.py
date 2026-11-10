import re
from typing import Any, Dict, List, Optional
import lxml.html
from bs4 import BeautifulSoup
import pandas as pd
import polars as pl


class LegacyTableParser:
    """
    Parser resiliente de tabelas legadas de alta performance com lxml.html e fallback para BeautifulSoup4.
    Atende ao Princípio IV da Constituição:
    - Identificação heurística da tabela de dados relevante (prioriza tabelas folha).
    - Desdobramento correto de colspan e rowspan.
    - Sanitização de entidades HTML (&nbsp;), quebras de linha e espaços espúrios.
    - Captura de parâmetros dinâmicos embutidos em links (ex: 'local=' em href).
    - Conversão direta para polars.DataFrame e pandas.DataFrame padronizados.
    """

    def __init__(self, parser_backend: str = "lxml"):
        self.parser_backend = parser_backend

    def parse_html_to_polars(
        self,
        html_content: str,
        expected_keywords: Optional[List[str]] = None,
    ) -> pl.DataFrame:
        """
        Analisa o HTML bruto com motor C de alta performance (lxml.html) e localiza a tabela principal,
        retornando um polars.DataFrame tipado.
        Caso ocorra qualquer anomalia na estrutura C, aciona automaticamente o fallback para BS4.
        """
        if not html_content or not html_content.strip():
            return pl.DataFrame()

        try:
            return self._parse_lxml_to_polars(html_content, expected_keywords)
        except Exception:
            # Fallback seguro para o parser BeautifulSoup caso o lxml encontre alguma anomalia extrema
            df_pd = self._parse_bs4_to_pandas(html_content, expected_keywords)
            return pl.from_pandas(df_pd) if not df_pd.empty else pl.DataFrame()

    def parse_html_to_dataframe(
        self,
        html_content: str,
        expected_keywords: Optional[List[str]] = None,
        as_polars: bool = False,
    ) -> Any:
        """
        Compatibilidade retroativa: analisa o HTML e retorna DataFrame.
        Por padrão retorna pandas.DataFrame para callers legados, ou polars.DataFrame se as_polars=True.
        """
        df_pl = self.parse_html_to_polars(html_content, expected_keywords)
        if as_polars:
            return df_pl
        return df_pl.to_pandas() if not df_pl.is_empty() else pd.DataFrame()

    def _parse_lxml_to_polars(
        self,
        html_content: str,
        expected_keywords: Optional[List[str]] = None,
    ) -> pl.DataFrame:
        doc = lxml.html.fromstring(html_content)
        tables = ([doc] if doc.tag == "table" else []) + doc.xpath(".//table")
        if not tables:
            return pl.DataFrame()

        # Heurística para selecionar a tabela certa:
        # Prioriza tabelas "folha" (que não possuem outras tabelas aninhadas dentro delas)
        leaf_tables = [tbl for tbl in tables if len(tbl.xpath(".//table")) == 0]
        candidate_tables = leaf_tables if leaf_tables else tables

        best_table = None
        best_score = -1

        for tbl in candidate_tables:
            text = tbl.text_content()
            rows = tbl.xpath(".//tr")
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

        if best_table is None:
            best_table = max(candidate_tables, key=lambda t: len(t.xpath(".//tr")))

        rows = best_table.xpath(".//tr")
        if not rows:
            return pl.DataFrame()

        matrix: List[List[str]] = []
        rowspan_map: Dict[int, tuple] = {}

        for row in rows:
            cells = row.xpath("./th | ./td")
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
                while col_idx in rowspan_map:
                    remaining, val = rowspan_map[col_idx]
                    row_values.append(val)
                    if remaining <= 1:
                        del rowspan_map[col_idx]
                    else:
                        rowspan_map[col_idx] = (remaining - 1, val)
                    col_idx += 1

                # Limpeza rápida de texto e remoção de espaços espúrios
                cell_text = " ".join(cell.text_content().split()).strip()

                try:
                    colspan = int(cell.get("colspan", 1))
                except (ValueError, TypeError):
                    colspan = 1

                try:
                    rowspan = int(cell.get("rowspan", 1))
                except (ValueError, TypeError):
                    rowspan = 1

                for _ in range(colspan):
                    row_values.append(cell_text)
                    if rowspan > 1:
                        rowspan_map[col_idx] = (rowspan - 1, cell_text)
                    col_idx += 1

            if any(v.strip() for v in row_values):
                matrix.append(row_values)

        if not matrix:
            return pl.DataFrame()

        header = [str(c).strip() for c in matrix[0]]
        clean_headers: List[str] = []
        counts: Dict[str, int] = {}
        for i, h in enumerate(header):
            if not h:
                h = f"col_{i}"
            count = counts.get(h, 0)
            if count > 0:
                clean_headers.append(f"{h}_{count}")
            else:
                clean_headers.append(h)
            counts[h] = count + 1

        expected_len = len(clean_headers)
        norm_data: List[List[str]] = []
        for r in matrix[1:]:
            if len(r) < expected_len:
                r = r + [""] * (expected_len - len(r))
            elif len(r) > expected_len:
                r = r[:expected_len]
            # Ignora repetições de cabeçalhos no meio do relatório
            if r == header or r == clean_headers:
                continue
            norm_data.append(r)

        col_dict = {h: [row[i] for row in norm_data] for i, h in enumerate(clean_headers)}
        df = pl.DataFrame(col_dict)

        # Se o HTML contiver links para consumo.php com parâmetro local=, extrai diretamente
        if not df.is_empty() and "Item" in df.columns and "consumo.php?" in html_content:
            locais_extraidos: List[str] = []
            for row in rows[1:]:
                a_tags = row.xpath(".//a[@href]")
                loc = ""
                for a in a_tags:
                    href = a.get("href", "")
                    if "local=" in href:
                        m = re.search(r"[?&]local=([^&]+)", href)
                        if m:
                            loc = m.group(1).strip()
                            break
                locais_extraidos.append(loc)

            if len(locais_extraidos) == len(df) and any(locais_extraidos):
                df = df.with_columns(pl.Series("_local_filtro", locais_extraidos))

        return df

    def _parse_bs4_to_pandas(
        self,
        html_content: str,
        expected_keywords: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Parser clássico de fallback com BeautifulSoup4."""
        soup = BeautifulSoup(html_content, self.parser_backend)
        tables = soup.find_all("table")
        if not tables:
            return pd.DataFrame()

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
            best_table = max(candidate_tables, key=lambda t: len(t.find_all("tr")))

        rows = best_table.find_all("tr")
        if not rows:
            return pd.DataFrame()

        matrix: List[List[str]] = []
        rowspan_map: dict = {}

        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells:
                continue

            row_values: List[str] = []
            col_idx = 0

            while col_idx in rowspan_map:
                remaining, val = rowspan_map[col_idx]
                row_values.append(val)
                if remaining <= 1:
                    del rowspan_map[col_idx]
                else:
                    rowspan_map[col_idx] = (remaining - 1, val)
                col_idx += 1

            for cell in cells:
                while col_idx in rowspan_map:
                    remaining, val = rowspan_map[col_idx]
                    row_values.append(val)
                    if remaining <= 1:
                        del rowspan_map[col_idx]
                    else:
                        rowspan_map[col_idx] = (remaining - 1, val)
                    col_idx += 1

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

        header = [str(c).strip() for c in matrix[0]]
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
        expected_len = len(clean_headers)
        normalized_data = []
        for r in data_rows:
            if len(r) < expected_len:
                r = r + [""] * (expected_len - len(r))
            elif len(r) > expected_len:
                r = r[:expected_len]
            if r == header or r == clean_headers:
                continue
            normalized_data.append(r)

        df = pd.DataFrame(normalized_data, columns=clean_headers)
        if not df.empty and "Item" in df.columns and "consumo.php?" in html_content:
            locais_extraidos = []
            for row in best_table.find_all("tr")[1:]:
                a_tag = row.find("a", href=True)
                if a_tag and "local=" in a_tag["href"]:
                    m = re.search(r"[?&]local=([^&]+)", a_tag["href"])
                    locais_extraidos.append(m.group(1).strip() if m else "")
                else:
                    locais_extraidos.append("")
            if len(locais_extraidos) == len(df) and any(locais_extraidos):
                df["_local_filtro"] = locais_extraidos

        return df


# Instância singleton padrão
table_parser = LegacyTableParser()
