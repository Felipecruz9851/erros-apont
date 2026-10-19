---
script: "Gerador_Tarefas_Scraping"
tipo: "automacao"
linguagem: "python"
gatilho: "evento"
data_atualizacao: 2026-10-19
tags: [automacao, script, tarefas, configuracao, pipeline, auth, esqueleto, expansao-locais]
---

# Automação: Gerador_Tarefas_Scraping

**Objetivo:** Consumir as credenciais de login fornecidas pelo usuário no frontend, carregar o esqueleto de tarefas de [config/tarefas_esqueleto.json](file:///c:/Users/engli/Desktop/Erros-apont/config/tarefas_esqueleto.json) e expandir a lista de tarefas através de iteração por local (`for local in locais: tarefas.append(...)`), permitindo total flexibilidade e controle manual.

## Estratégia de Expansão por Local

Quando um endpoint contiver a lista de `locais_disponiveis` e a flag `iterar_por_local: true`, o gerador executa um laço sobre os locais para gerar uma tarefa de extração dedicada para cada fábrica/local de produção:

```python
def gerar_tarefas_expansao(config_templates, credentials, data_inicio, data_fim, locais_selecionados=None):
    tarefas = []
    
    for template in config_templates:
        if not template.get("ativo", True):
            continue
            
        locais = template.get("locais_disponiveis", [])
        if locais_selecionados:
            locais = [loc for loc in locais if loc in locais_selecionados]
            
        # Padrão de iteração por local configurável pelo usuário:
        if template.get("iterar_por_local", False) and locais:
            for local in locais:
                payload = dict(template.get("payload_estatico", {}))
                payload["local[]"] = local  # Alvo de local específico
                
                # Injeta os campos dinâmicos de data
                if "parametros_dinamicos" in template:
                    din = template["parametros_dinamicos"]
                    payload[din["data_inicio_campo"]] = data_inicio
                    payload[din["data_fim_campo"]] = data_fim
                    
                tarefas.append({
                    "id": f"{template['id']}_{local}",
                    "nome": f"{template['nome']} [{local}]",
                    "grupo": template["grupo"],
                    "url": template["url"],
                    "metodo": template["metodo"],
                    "payload": payload,
                    "headers": template.get("headers", {})
                })
        else:
            # Tarefa consolidada única (ex: Estoque por Local com todos os itens)
            payload = dict(template.get("payload_estatico", {}))
            if "parametros_dinamicos" in template:
                din = template["parametros_dinamicos"]
                payload[din["data_inicio_campo"]] = data_inicio
                payload[din["data_fim_campo"]] = data_fim
                
            tarefas.append({
                "id": template["id"],
                "nome": template["nome"],
                "grupo": template["grupo"],
                "url": template["url"],
                "metodo": template["metodo"],
                "payload": payload,
                "headers": template.get("headers", {})
            })
            
    return tarefas
```

## Arquivos Afetados

**➡️ Modifica/Lê:** [config/tarefas_esqueleto.json](file:///c:/Users/engli/Desktop/Erros-apont/config/tarefas_esqueleto.json)  
**➡️ Envia para:** [[04-Infra-Dados/Extrator_Workers_e_HTML]]  
**⬅️ Invocado por:** [[02-Backend-API/Rotas_FastAPI_e_Sessao]]
