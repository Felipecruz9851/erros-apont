---
modulo: "Motor_Calculo_Polars_e_Pandas"
tipo: "dominio"
data_atualizacao: 2026-11-10
tags: [regras-negocio, calculo, parametros, polars, pandas, json, tratamento, baixa-automatica, estoque, janela-3-dias, vetorizacao]
---

# Regra: Motor_Calculo_Polars_e_Pandas

**Contexto:** Camada de domínio analítico responsável pela esteira de transformação de alta performance pós-extração: tratamento dos relatórios extraídos da intranet (**Consumo de Componentes por Ordem**, **Ordens de Produção / Atrasadas** e **Estoque por Local**), filtro de insumos que sofrem **baixa automática**, ordenação pela data de entrega das ordens mais urgentes/antigas para as mais futuras, abatimento cumulativo do saldo físico (`Qtde.`) no **local de produção** da ordem consumidora e avaliação na janela de até N dias úteis da **data atual** informada no frontend.

## Arquitetura de Performance (Migração Polars e Vetorização)

O motor de cálculo e tratamento foi modernizado com **Polars** (Rust multi-threaded), eliminando loops em Python (`iterrows`, `groupby` iterativo) e substituindo-os por **window functions** analíticas:

$$\text{Consumo Acumulado Anterior} = \sum_{i=1}^{k-1} \text{qtd\_necessaria}_i$$
$$\text{Saldo Remanescente para a Ordem } k = \max\left(0, \text{Saldo Inicial Local} - \text{Consumo Acumulado Anterior}\right)$$

### Resultados de Benchmark:
- **Aceleração:** ~20.7x mais rápido que o motor legado em Pandas.
- **Precisão:** 100.0% de equivalência exata validada por teste de regressão double-entry (`test_confrontation_pandas_vs_polars.py`).

## Fases da Execução

1. **Tratamento e Normalização dos Dados (`clean_and_normalize`):**
   - Parser HTML C de alta performance com `lxml.html` e fallback resiliente para `BeautifulSoup` para desdobramento de `colspan`, `rowspan` e detecção de tabelas folha.
   - Sanitização de códigos de itens no consumo: remoção do sufixo de unidade de medida precedido ou não por espaço (ex.: `'3COUPCOU378 -M2'` $\rightarrow$ `'3COUPCOU378'` e códigos de 15 caracteres colados na unidade como `'3LEDDP73000K24V-UN'` $\rightarrow$ `'3LEDDP73000K24V'`).
   - Sanitização de identificadores de OP (`_clean_op`): remoção de trechos residuais de código PHP/HTML vazados nos relatórios (ex.: `'1985883 if ($exibir_codbar == "S") ...'` $\rightarrow$ `'1985883'`), assegurando cruzamento correto com `atrasadas.php`.
   - Normalização do local de estoque em `estoque_lote.php` (remoção do sufixo de situação `' - L'` em `'Local - Sit'`, ex.: `'CAPAS LE - L'` $\rightarrow$ `'CAPAS LE'`).
   - Padronização de datas (`DD/MM/YYYY.` $\rightarrow$ `YYYY-MM-DD`) e enriquecimento das OPs com `data_abertura`, `data_entrega`, `fabrica`, `ordem_saldo` e produto extraídas de `atrasadas.php`.
   - Fallback de produto (`_resolver_produto`): quando a descrição do produto da OP estiver vazia ou ausente, adota automaticamente o código do item (`Item` em `atrasadas.php`).
   - Fallback de quantidade necessária (`qtd_necessaria`): quando o consumo do componente vier zerado (`0,0000`) ou não informado no relatório legado, adota automaticamente o saldo da OP (`ordem_saldo`) ou piso de 1.0 unidade, assegurando que componentes com baixa automática obrigatória sem saldo no local de produção sejam devidamente apontados como erro (`SALDO_ZERADO_NO_LOCAL`) com déficit correspondente.
   - Definição de `saldo_disponivel = saldo_fisico` (`Qtde.`, ignorando `Qt.Reser`).
   - **Padronização Estrita de 2 Casas Decimais (`_parse_float`):** conversão precisa via `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` eliminando disparidades entre relatórios com 3 e 2 casas decimais tanto na ingestão de consumo e estoque quanto na alocação cumulativa e serialização.
2. **Filtro de Baixa Automática, Data de Abertura e Data de Entrega Válida (`calculate_pointing_errors_polars`):**
   - Seleção estrita dos componentes onde `baixa_automatica == True`.
   - Filtragem das ordens com `data_abertura <= data_atual` (quando preenchida).
   - Filtragem estrita de ordens com `data_entrega` válida dentro da janela temporal; ordens sem cronograma/data de entrega são desconsideradas.
3. **Fila de Prioridade e Abatimento Cumulativo Vetorizado:**
   - Ordenação das ordens por data de entrega das mais antigas/atrasadas para as mais futuras (`data_entrega`, `_sort_abertura`, `op`).
   - Cálculo instantâneo via window function `.cum_sum().over(["codigo_componente", "local_producao"])`.
4. **Classificação na Janela de Entrega (Janela em Dias Úteis):**
   - Calculada estritamente em **dias úteis**, desconsiderando finais de semana e feriados em `backend/app/feriados.txt`.
   - **Ignoradas:** Ordens com `data_entrega > data_atual + N dias úteis`.
   - **Passíveis de Erro (`SALDO_INSUFICIENTE` / `SALDO_ZERADO_NO_LOCAL`):** Ordens com déficit de componentes no local de produção.
   - **Atendidas (`OK`):** Ordens com saldo suficiente no local.
5. **Montagem do Resultado JSON (`serialize_results`):**
   - Suporte nativo tanto para `polars.DataFrame` (`df.to_dicts()`) quanto para `pandas.DataFrame`.

## Dependências

**⬅️ Consumido por:** [[02-Backend-API/Rotas_FastAPI_e_Sessao]]  
**⬅️ Recebe dados de:** [[04-Infra-Dados/Extrator_Workers_e_HTML]]
