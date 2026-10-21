---
modulo: "Motor_Calculo_Pandas"
tipo: "dominio"
data_atualizacao: 2026-10-20
tags: [regras-negocio, calculo, parametros, pandas, json, tratamento, baixa-automatica, estoque, janela-3-dias]
---

# Regra: Motor_Calculo_Pandas

**Contexto:** Camada de domínio analítico responsável pela esteira de transformação pós-extração: tratamento dos relatórios extraídos da intranet (**Consumo de Componentes por Ordem**, **Ordens de Produção / Atrasadas** e **Estoque por Local**), filtro de insumos que sofrem **baixa automática**, ordenação pela data de entrega das ordens mais urgentes/antigas para as mais futuras, abatimento cumulativo do saldo físico (`Qtde.`) no **local de produção** da ordem consumidora e avaliação na janela de até 3 dias da **data atual** informada no frontend.

## Fases da Execução

1. **Tratamento e Normalização dos Dados (`clean_and_normalize`):**
   - Seleção de tabelas folha (`leaf_tables`) no parser `BeautifulSoup` para evitar tabelas de layout aninhadas do HTML legado.
   - Sanitização de códigos de itens no consumo: remoção do sufixo de unidade de medida precedido ou não por espaço (ex.: `'3COUPCOU378 -M2'` $\rightarrow$ `'3COUPCOU378'` e códigos de 15 caracteres colados na unidade como `'3LEDDP73000K24V-UN'` $\rightarrow$ `'3LEDDP73000K24V'`).
   - Normalização do local de estoque em `estoque_lote.php` (remoção do sufixo de situação `' - L'` em `'Local - Sit'`, ex.: `'CAPAS LE - L'` $\rightarrow$ `'CAPAS LE'`).
   - Padronização de datas (`DD/MM/YYYY.` $\rightarrow$ `YYYY-MM-DD`) e enriquecimento das OPs com `data_abertura`, `data_entrega` e `fabrica` extraídas de `atrasadas.php` (consulta geral `2000-01-01` a `2050-12-31`).
   - Definição de `saldo_disponivel = saldo_fisico` (`Qtde.`, ignorando `Qt.Reser`).
2. **Filtro de Baixa Automática e Data de Abertura (`calculate_pointing_errors`):**
   - Seleção estrita dos componentes onde `baixa_automatica == True`.
   - Filtragem das ordens com `data_abertura <= data_atual` (consulta de `2000-01-01` até a data atual preenchida no frontend).
3. **Fila de Prioridade e Abatimento Cumulativo no Local de Produção:**
   - Ordenação das ordens por data de entrega das mais antigas/atrasadas para as mais futuras (`_sort_data_entrega`, `_sort_data_abertura`, `op`).
   - Agrupamento por `(codigo_componente, local_producao)` e abatimento cumulativo do saldo a cada ordem atendida.
4. **Classificação na Janela de Entrega (até +3 dias da Data Atual):**
   - **Ignoradas:** Ordens com `data_entrega > data_atual + 3 dias` são ignoradas do resultado final.
   - **Passíveis de Erro de Apontamento (`SALDO_INSUFICIENTE` / `SALDO_ZERADO_NO_LOCAL`):** Ordens com `data_entrega <= data_atual + 3 dias` (incluindo atrasadas e janela de 0 a 3 dias) cujo saldo remanescente no local de produção da ordem é menor que `qtd_necessaria`.
   - **Atendidas (`OK`):** Ordens na janela de até 3 dias com componentes disponíveis em quantidade suficiente no local de produção, tendo seu consumo abatido do saldo para as ordens seguintes.
5. **Montagem do DataFrame de Saída em JSON (`serialize_results`):**
   - Estruturação com KPIs separando `total_erros_apontamento` (apenas divergências reais) dos itens `OK` na janela, expondo todos os registros avaliados para o dashboard.

## Lógica e Parâmetros

- **Variáveis de Entrada Obrigatórias:**
  - `df_consumo_ordem`: DataFrame contendo as OPs de todas as fábricas e seus componentes.
  - `df_estoque`: DataFrame contendo saldos disponíveis por item e depósito/local.
- **Condicionais Críticas:**
  - O saldo DEVE ser validado no local de produção da OP; saldo positivo em local divergente não anula o erro de apontamento.
- **Saída Esperada:** Dicionário com métricas agregadas (total analisado, total com déficit, conformidade por fábrica) e a lista de registros detalhados de erros de apontamento em JSON.

## Dependências

**⬅️ Consumido por:** [[02-Backend-API/Rotas_FastAPI_e_Sessao]]  
**⬅️ Recebe dados de:** [[04-Infra-Dados/Extrator_Workers_e_HTML]]
