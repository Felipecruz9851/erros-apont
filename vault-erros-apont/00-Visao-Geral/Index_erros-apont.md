---
projeto: "erros-apont"
data_criacao: 2026-10-19
status: ativo
tags: [index, arquitetura, extrator, pandas, fastapi, pipeline, pcp, baixa-automatica]
---

# Visão Geral: erros-apont

**Resumo:** Sistema de auditoria e análise de erros de apontamento de ordens de produção (OPs) em todas as fábricas. O pipeline extrai dois relatórios da intranet (**Consumo de Componentes por Ordem** e **Estoque**), filtra componentes com **baixa automática** e verifica se há saldo disponível suficiente no **local de produção** da ordem consumidora, consolidando os déficits em DataFrames Pandas e expondo-os via FastAPI na interface web sob o **Estilo Líder Design**.

## Arquitetura e Fluxo do Pipeline

```mermaid
graph TD
    UI[Frontend: Tela de Login e Senha] -->|1. Credenciais| API[Backend FastAPI]
    API -->|2. Inicia Pipeline com Credenciais| GEN[Gerador de Tarefas: Consome Login]
    GEN -->|3. Dispara Tarefas de Scraping Duplo| POOL[Pool de Workers Assíncronos]
    POOL -->|4. Extrai Relatório 1| R1[Relatório: Consumo de Componentes por Ordem - Todas as Fábricas]
    POOL -->|4. Extrai Relatório 2| R2[Relatório: Estoque por Local/Depósito]
    R1 & R2 -->|5. HTML Bruto| SNAP[Snapshots HTML Completos]
    SNAP -->|6. Parser Resiliente| BS4[Extrator Heurístico BeautifulSoup]
    BS4 -->|7. DataFrames Brutos: Consumo e Estoque| CLEAN[Tratamento de Dados: Limpeza, Tipos, Chaves de Local]
    CLEAN -->|8. Filtro Baixa Automática| FILTER[Filtro: Componentes com Baixa Automática]
    FILTER & CLEAN -->|9. Cruzamento: Item + Local de Produção| CALC[Motor de Cálculo Pandas: Identificação de Déficit de Saldo]
    CALC -->|10. DataFrame de Erros Consolidado| JSON[Montagem do DataFrame de Saída em JSON]
    JSON -->|11. Payload Estruturado com KPIs| API
    API -->|12. Exposição para Dashboard| UI
```

## Índice de Módulos

- [[01-Frontend-UI/Interface_Login_e_Resultados]]
- [[02-Backend-API/Rotas_FastAPI_e_Sessao]]
- [[03-Dominio-Calculos/Motor_Calculo_Pandas]]
- [[04-Infra-Dados/Extrator_Workers_e_HTML]]
- [[05-Automacoes/Gerador_Tarefas_Scraping]]
- [[erros-apont-logbook/LOGBOOK_INDEX|Diário de Bordo]]
- [[../.specify/memory/constitution.md|Constituição do Projeto (v1.1.0)]]
- [[../specs/001-frontend-ui-layout/spec.md|Especificação Ativa: 001-frontend-ui-layout]]
