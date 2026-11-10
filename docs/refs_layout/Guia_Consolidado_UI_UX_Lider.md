# Guia de Desenvolvimento e UI/UX (Estilo Líder Design + Arquitetura Atual)

Este guia foi elaborado para agentes e desenvolvedores que atuam no ecossistema do projeto (especialmente no frontend React), mesclando a arquitetura e componentes atuais com as diretrizes de design supremas da **Líder Design**. Em caso de divergências entre a base de código legada e este documento, **este guia tem precedência**.

## 1. Princípios de Arquitetura Frontend

O projeto atual utiliza a seguinte pilha tecnológica e estrutural, que deve ser mantida, porém estilizada conforme as novas regras:

- **Framework:** React com Vite.
- **Estilização:** Tailwind CSS (utilizando classes utilitárias e variáveis no `tailwind.config.js`).
- **Composição da Tela (Dashboard):**
  - **Sidebar:** Fixa à esquerda (exibição de logomarca, configurações e resumos numéricos).
  - **Header:** Fixo no topo (títulos da página, totalizadores de registros e botões de ação/exportação globais).
  - **Main Content:** Espaço de rolagem contendo os cartões de métricas (MetricsCards) e a tabela de dados principal (PurchaseTable).
- **Gerenciamento de Estado:** React Hooks tradicionais (`useState`, `useEffect`, `useCallback`) em componentes funcionais.

## 2. Princípios de Interface (UX/UI) - O Estilo Líder

A interface deve ser vista como um "catálogo de luxo digital". A regra de ouro é: **o conteúdo é o protagonista, a interface deve ser invisível.**

- **Minimalismo Funcional:** Elimine bordas espessas, excesso de cores e sombras carregadas.
- **Whitespace (Espaçamento):** Use espaçamentos generosos (paddings de `24px` a `48px` em containers principais). O espaço em branco transmite luxo e organização.
- **Navegação Elegante:** Evite animações bruscas. Efeitos de hover devem ser sutis (mudanças leves de opacidade ou cor de fundo).

## 3. Diretrizes Visuais (Resolução de Conflitos)

A base de código atual possui configurações no Tailwind (como cores verdes, sombras pesadas e bordas muito arredondadas) que **devem ser substituídas/sobrescritas** pelas seguintes regras:

### 3.1 Paleta de Cores
A interface deve ser predominantemente neutra e monocromática, utilizando destaques com muita parcimônia.

| Elemento | Regra / Código Hexadecimal | Tailwind Sugerido |
| :--- | :--- | :--- |
| **Fundos Primários** | Branco puro (`#FFFFFF`) ou Off-White/Gelo (`#F8F8F8`) | `bg-white`, `bg-[#F8F8F8]` |
| **Fundos Secundários** | Cinza claro neutro (`#EDEDED`) para distinguir seções levemente | `bg-[#EDEDED]` |
| **Texto (Títulos)** | Grafite Escuro / Preto Suave (`#1A1A1A` ou `#222222`) | `text-[#1A1A1A]` |
| **Texto (Corpo)** | Cinza Médio (`#666666` ou `#757575`) | `text-[#666666]` |
| **Destaques / CTAs Sec.** | Tons Terrosos / Madeira (`#8B5A2B`, `#A0522D`) | `text-[#8B5A2B]`, `border-[#A0522D]` |

*Nota sobre a base atual:* As referências a `primary` (verde) no Tailwind devem ser gradativamente substituídas por ações com fundo escuro (`#222222`) ou tons terrosos, caso exijam destaque.

### 3.2 Tipografia
Abandone fontes nativas de sistema (como Segoe UI) para elementos de destaque, adotando uma combinação mais editorial.

- **Headings (Títulos, H1-H3):** Fontes geométricas sem serifa (*Montserrat*, *Poppins*) ou serifadas modernas (*Playfair Display*). Peso: Regular ou Medium.
- **Body (Textos, Tabelas, Legendas):** Fontes sem serifa com alta legibilidade (*Inter*, *Roboto*). Peso: Light ou Regular.
- **Hierarquia:** Use tamanho da fonte em vez de "font-bold" para diferenciar títulos de subtítulos. O uso de negrito deve ser restrito.

### 3.3 Formas, Bordas e Sombras (Substituindo o padrão atual)

A base legada possui raios de borda (`borderRadius`) de `14px` e `16px` e sombras de `20%` de opacidade. **Isto deve mudar imediatamente:**

- **Border Radius (Cantos):** Use cantos quase retos ou totalmente retos para um visual mais arquitetônico. Limite o raio de borda para `2px` ou `4px` (`rounded-sm` no Tailwind).
- **Sombras (Box-shadow):** Devem ser quase imperceptíveis. Se necessárias para separar cards do fundo, use sombras extremamente difusas: `box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05)` (ou Tailwind customizado para `0.05` de opacidade).
- **Bordas (Borders):** Substitua bordas escuras/grossas por linhas super finas de `1px` em tons muito claros, como `#E0E0E0`, ou prefira a divisão por espaçamento (whitespace).

## 4. Componentes Específicos

- **Botões (Buttons):**
  - **Primários:** Fundo escuro (`#222222`), texto claro, cantos retos ou 2-4px, sem sombra pesada de hover.
  - **Secundários:** Estilo *Ghost* (fundo transparente, borda fina cinza ou preta, texto escuro).
- **Cards e Tabelas (ex: `PurchaseTable` / `MetricsCards`):**
  - Fundo branco contra um canvas `#F8F8F8`.
  - Separe as linhas da tabela com linhas super finas ou "zebra" muito sutil (ex: `bg-white` e `bg-gray-50`).
- **Ícones:** Utilize ícones em estilo linha (Line Icons), finos e sem preenchimento colorido para manter o aspecto requintado.

## 5. Prompt Base para o Agente (Memorização de Contexto)

Sempre que precisar criar ou refatorar componentes neste projeto, o agente deve carregar este contexto mentalmente ou injetar o seguinte *prompt*:

> *"Atuarei criando ou refatorando um componente React/Tailwind. Adotarei a arquitetura atual (Dashboard, Header, Sidebar) mas estilizarei estritamente sob a estética Lider Design. Usarei fundos claros (#F8F8F8, #FFFFFF) e texto escuro (#1A1A1A). Os paddings serão generosos (24px a 48px). Botões e cards terão cantos retos (ou máx 4px de border-radius) e cores sóbrias (botões primários escuros, destaques em tons de madeira/terra). Sombras serão removidas ou limitadas a 5% de opacidade. O visual final será limpo, organizado e luxuoso."*
