# Guia de Identidade e UI/UX: Estilo Lider Design (Interface Web)

Este documento serve como instrução fundamental para a aplicação da identidade visual e princípios de design de interface (UI/UX) inspirados na **Lider Design** em projetos web, aplicativos e painéis de sistema.

# 1\. Princípios de Interface (UX/UI)

A interface deve refletir a essência do **Mobiliário de Alta Decoração Brasileiro**: sofisticada, limpa e funcional. O objetivo da interface é ser "invisível" o suficiente para deixar que os produtos (ou as informações principais) sejam os protagonistas.

* **Minimalismo Funcional:** Sem excesso de bordas, sombras carregadas ou elementos decorativos desnecessários.  
* **Espaçamento Generoso (Whitespace):** Uso amplo de respiros entre os elementos (margens e paddings) para transmitir luxo e organização.  
* **Navegação Fluida:** Transições suaves e sem sobressaltos. Interações (hover) devem ser elegantes (ex: leve mudança de opacidade ou cor, sem movimentos bruscos).

# 2\. Paleta de Cores

A paleta web deve ser majoritariamente neutra, com as cores de destaque reservadas para CTAs (Call to Actions) ou indicativos de estado.

| Categoria | Aplicação | Tonalidade & Código Hex |
| :---- | :---- | :---- |
| **Backgrounds (Fundos)** | Primário | Branco puro (`#FFFFFF`) ou Off-White/Gelo (`#F8F8F8`) |
|  | Secundário | Cinza claro neutro (`#EDEDED`) ou tons sutis de areia |
| **Textos (Tipografia)** | Títulos e Principais | Grafite escuro / Preto Suave (`#222222` ou `#1A1A1A`) |
|  | Secundários / Legendas | Cinza médio (`#666666` ou `#757575`) |
| **Destaques (Acentos)** | Links ativos, ícones e tags | Tons Terrosos / Madeira (`#8B5A2B`, `#A0522D` ou bege acinzentado) |

# 3\. Tipografia

A tipografia deve combinar elegância com alta legibilidade.

* **Títulos (Headings \- H1, H2, H3):** Fontes geométricas sem serifa (ex: *Montserrat, Lato, Poppins*) ou fontes serifadas modernas e elegantes (ex: *Playfair Display, Lora*) para transmitir tradição e autoria. Peso: Regular ou Medium.  
* **Corpo de Texto (Body Text):** Fontes sem serifa, limpas e de fácil leitura (ex: *Inter, Roboto, Open Sans*). Peso: Light ou Regular.  
* **Hierarquia:** Contraste claro de tamanho entre títulos e parágrafos. Evitar o uso excessivo de negrito; preferir a variação de tamanho para criar hierarquia visual.

# 4\. Elementos Visuais e Componentes

* **Botões (Buttons):**  
  * *Primários:* Sólidos, retangulares, com cantos levemente arredondados (raio de borda de 2px a 4px) ou totalmente retos. Fundo escuro (`#222222`) com texto claro.  
  * *Secundários:* Estilo "Ghost" (apenas contorno fino e texto) para ações de menor peso.  
* **Cards de Produto/Informação:** Sem bordas marcadas. Divisão feita por espaçamento ou fundos levemente acinzentados. Quando houver sombra (Box-shadow), deve ser extremamente difusa, suave e quase imperceptível (ex: `rgba(0,0,0, 0.05)`).  
* **Imagens:** Devem ser em alta resolução, ocupando boa parte do layout (Edge-to-edge). Os cantos das imagens devem seguir o padrão do projeto (geralmente retos na alta decoração para um visual mais arquitetônico).  
* **Ícones:** Ícones de linha (Line icons), finos e minimalistas. Evitar ícones preenchidos ou coloridos demais.

# 5\. Instruções Diretas para Agentes (Desenvolvimento Front-end)

**Prompt base para o agente codificador:**  
"Gere componentes de interface (HTML/CSS/JS, React, Vue, etc.) adotando a estética web da **Lider Design**. Utilize uma paleta de cores baseada em fundos claros (\#F8F8F8, \#FFFFFF) e textos escuros (\#1A1A1A). Aplique espaçamentos amplos (paddings de `24px` a `48px` em containers). Os botões devem ser minimalistas (cantos quase retos, background escuro). Remova bordas pesadas e priorize divisões de layout através de whitespace ou linhas de 1px super claras (\#E0E0E0). O resultado deve parecer um catálogo de luxo digital."