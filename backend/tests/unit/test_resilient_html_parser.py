from backend.app.extraction.parser import LegacyTableParser, table_parser


def test_parser_unclosed_tags_and_malformed_html():
    """Garante que tags não fechadas e HTML quebrado sejam interpretados com robustez."""
    html = """
    <html>
    <body>
    <table>
        <tr><th>Código</th><th>Descrição</th><th>Qtd
        <tr><td>CMP-01<td>Parafuso Sextavado<td>10
        <tr><td>CMP-02<td>Porca Autotravante<td>25
    </table>
    </body>
    </html>
    """
    df = table_parser.parse_html_to_polars(html)
    assert not df.is_empty()
    assert df.shape == (2, 3)
    assert df["Código"].to_list() == ["CMP-01", "CMP-02"]
    assert df["Qtd"].to_list() == ["10", "25"]


def test_parser_nested_layout_tables_leaf_selection():
    """Garante que o parser identifique a tabela interna de dados (folha), ignorando a tabela externa de layout."""
    html = """
    <table id="layout_outer">
        <tr>
            <td>Menu Lateral</td>
            <td>
                <table id="data_inner">
                    <tr><th>OP</th><th>Local</th><th>Status</th></tr>
                    <tr><td>1001</td><td>COLCHOES</td><td>LIBERADA</td></tr>
                    <tr><td>1002</td><td>ESTOFADOS</td><td>PROCESSO</td></tr>
                </table>
            </td>
        </tr>
    </table>
    """
    df = table_parser.parse_html_to_polars(html, expected_keywords=["OP", "Status"])
    assert not df.is_empty()
    assert "OP" in df.columns
    assert "Local" in df.columns
    assert df.shape[0] == 2
    assert df["OP"].to_list() == ["1001", "1002"]


def test_parser_colspan_and_rowspan_expansion():
    """Garante o desdobramento correto de células com colspan e rowspan."""
    html = """
    <table>
        <tr>
            <th colspan="2">Grupo</th>
            <th>Valor</th>
        </tr>
        <tr>
            <td rowspan="2">Fábrica 01</td>
            <td>Subgrupo A</td>
            <td>100</td>
        </tr>
        <tr>
            <td>Subgrupo B</td>
            <td>200</td>
        </tr>
    </table>
    """
    df = table_parser.parse_html_to_polars(html)
    assert not df.is_empty()
    assert df.shape == (2, 3)
    # A primeira coluna deve conter 'Fábrica 01' em ambas as linhas devido ao rowspan
    col0_name = df.columns[0]
    assert df[col0_name].to_list() == ["Fábrica 01", "Fábrica 01"]
    assert df["Valor"].to_list() == ["100", "200"]


def test_parser_extracts_local_from_href():
    """Garante a extração do parâmetro local= do link de consumo em relatórios consolidados."""
    html = """
    <html>
    <body>
    <table>
        <tr><th>Item</th><th>Descrição</th></tr>
        <tr>
            <td><a href="consumo.php?num_ordem=198&local=COLCHOES">CMP-01 -UN</a></td>
            <td>Espuma D33</td>
        </tr>
        <tr>
            <td><a href="consumo.php?num_ordem=199&local=ESTOFADOS">CMP-02 -M2</a></td>
            <td>Tecido Veludo</td>
        </tr>
    </table>
    </body>
    </html>
    """
    df = table_parser.parse_html_to_polars(html)
    assert not df.is_empty()
    assert "_local_filtro" in df.columns
    assert df["_local_filtro"].to_list() == ["COLCHOES", "ESTOFADOS"]


def test_parser_fallback_on_extreme_anomaly():
    """Garante que caso o motor C falhe, o fallback BS4 entra em ação transparentemente."""
    parser = LegacyTableParser()
    # Força exceção no método C
    parser._parse_lxml_to_polars = lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Simulated C error"))

    html = """
    <table>
        <tr><th>OP</th><th>Item</th></tr>
        <tr><td>5001</td><td>COMP-99</td></tr>
    </table>
    """
    df = parser.parse_html_to_polars(html)
    assert not df.is_empty()
    assert "OP" in df.columns
    assert df["OP"].to_list() == ["5001"]
