---
modulo: "Interface_Login_e_Resultados"
tipo: "frontend"
linguagem: "typescript/react"
data_atualizacao: 2026-10-19
tags: [codigo, frontend, react, vite, tailwind, lider-design, dashboard]
---

# Módulo: Interface_Login_e_Resultados (Estilo Líder Design)

**Responsabilidade:** Interface visual web em React + TypeScript + Vite + Tailwind CSS estritamente alinhada ao Estilo Líder Design (canvas neutro `#F8F8F8`, divisórias finas de 1px `#E0E0E0`, botões retangulares escuros `#1A1A1A` e respiros generosos). Permite ingestão de credenciais, acompanhamento em tempo real das 6 fases do pipeline e auditoria interativa de erros de apontamento.

## Componentes Implementados (`frontend/src/components/`)
* `LoginCard.tsx` (`auth/`): Card elegante e discreto para ingestão de usuário/senha da intranet e delimitação do recorte temporal (`data_inicio` e `data_fim`).
* `PipelineMonitor.tsx` (`monitor/`): Rastreador visual das 6 fases do pipeline com chips de estado, contadores de tarefas e barra de progresso ultrafina.
* `MetricsCards.tsx` (`dashboard/`): Cartões em estilo editorial destacando KPIs essenciais (OPs Analisadas, Insumos com Baixa Automática, Erros de Apontamento e Taxa de Conformidade).
* `PointingErrorsTable.tsx` (`dashboard/`): Tabela analítica com divisórias de 1px, cabeçalho fixo, ordenação por coluna, busca textual multi-campo, filtros por fábrica/severidade e paginação.
* `ContactsManager.tsx` (`contacts/`): Tela e modal de cadastro/modificação de contatos e atribuição múltipla de locais de produção.
* `EmailDispatcher.tsx` (`emails/`): Painel de listagem de destinatários, visualização de prévia e tabela filtrada, disparo em lote e individual com mensagem padronizada em dias úteis.
* `Header.tsx` & `Sidebar.tsx` (`layout/`): Topo e barra lateral fixa fornecendo alternância entre os módulos de Auditoria, Envio de E-mails e Cadastro de Destinatários.
* `usePipeline.ts` (`hooks/`): Hook desacoplado para despacho de análise, polling assíncrono de status e recuperação de resultados.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* Usuário final (auditor de estoque, analista de PCP).

**➡️ Quem este módulo chama (Saída/Uso):**
* [[Rotas_FastAPI_e_Sessao]]
* **Bibliotecas Externas:** React 18, Vite, Tailwind CSS, Lucide React, Axios.
