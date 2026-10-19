---
modulo: "Motor_Calculo_Pandas"
tipo: "dominio"
data_atualizacao: 2026-10-19
tags: [regras-negocio, calculo, parametros, pandas, json, tratamento, baixa-automatica, estoque]
---

# Regra: Motor_Calculo_Pandas

**Contexto:** Camada de domínio analítico responsável pela esteira de transformação pós-extração: tratamento dos dois relatórios extraídos da intranet (**Consumo de Componentes por Ordem** e **Estoque**), filtro de insumos que sofrem **baixa automática**, cruzamento de saldos por **local de produção** da ordem consumidora e montagem do DataFrame consolidado de erros em JSON.

## Fases da Execução

1. **Tratamento e Normalização dos Dados (`clean_and_normalize`):**
   - Sanitização de espaços e caracteres das tabelas HTML legadas.
   - Normalização dos identificadores de itens, ordens e códigos de locais de estoque/produção (remoção de formatações espúrias).
   - Conversão de tipos: quantidades e saldos como `float`, datas e códigos como `string`.
2. **Filtro de Baixa Automática (`filter_automatic_deduction`):**
   - Seleção estrita dos componentes no relatório de consumo onde o indicador de baixa automática está ativo (`baixa_automatica == True`).
   - Componentes de baixa manual são preservados no contexto de ordens, mas excluídos da verificação de saldo automático para evitar falsos positivos.
3. **Cruzamento de Saldos por Local de Produção (`cross_match_stock_by_location`):**
   - Realização de junção (*merge/join*) entre o DataFrame de consumo e o DataFrame de estoque utilizando como chave composta:
     - `codigo_componente`
     - `local_producao` (local atribuído à OP que consome o insumo) vs `local_estoque` (local do relatório de estoque)
4. **Identificação de Divergências e Cálculo de Déficit (`calculate_pointing_errors`):**
   - Condição de erro: `saldo_disponivel.fillna(0) < quantidade_necessaria`
   - Cálculo de déficit: `deficit = quantidade_necessaria - saldo_disponivel`
   - Categorização:
     - `SALDO_INSUFICIENTE`: Saldo existe no local, mas não atende a quantidade total da OP.
     - `SALDO_ZERADO_NO_LOCAL`: Saldo é zero ou inexistente no local de produção da ordem (mesmo que haja saldo em outros almoxarifados).
5. **Montagem do DataFrame de Saída em JSON (`assemble_output_json`):**
   - Estruturação do DataFrame com as colunas finais: `fabrica`, `op`, `produto_op`, `local_producao`, `codigo_componente`, `descricao_componente`, `baixa_automatica`, `qtd_necessaria`, `saldo_disponivel`, `deficit`, `status_divergencia`.
   - Serialização determinística para JSON orientada à renderização no frontend.

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
