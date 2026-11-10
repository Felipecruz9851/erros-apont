import asyncio
import getpass
import sys
import time
from typing import Any, Dict, List
import httpx
import polars as pl
from backend.app.core.config import settings
from backend.app.extraction.parser import table_parser
from backend.app.extraction.worker import ExtractionWorker, execute_task_pool


LOCAIS_51 = [
    "COLCHOES", "BOX", "ESTOF UL", "CC ACABA01", "ARMARIO UL", "UL ACABA01",
    "COZINHA", "PES ACABA", "VIDRACARIA", "PORTAS", "LAMINAD UL", "TAMPOS UL",
    "UL FABRI01", "CORTE", "CADEIRAS", "CC FABRI01", "CORTE LE", "PEZINHO",
    "CC FABRI03", "PLANEJADOS", "LE FABRI02", "LE FABRI03", "LE FABRI06",
    "FIBRA", "ALMOFADAS", "CAPAS LE", "METALURGIA", "ALUMINIO", "INOX",
    "PLASMA", "ATELIE", "ATELIE2", "UL-ALMOX05", "REVENDA", "AT INSUMO",
    "AT SOFA", "AT MOVEIS", "AT KIT", "AT VIDRO", "KIT", "TAPA FURO",
    "ACESSORIOS", "COLMEIAS", "C PILOTO", "MOSTRUARIO", "LAMINACAO1",
    "EMBALAGEM", "OSSOPAINEL", "TAPETES", "LE FABRI01", "PLAN_ESP"
]


async def run_benchmark(username: str, password: str, endpoint_choice: str = "ordens_atrasadas"):
    """
    Executa o benchmark confrontando a abordagem Segmentada (51 requisições separadas)
    versus a abordagem Agrupada (1 requisição consolidada contendo todos os locais).
    """
    base_url = settings.INTRANET_HOST.rstrip("/")

    if endpoint_choice == "consumo_insumos":
        endpoint_name = "Consumo de Insumos (consumo_alt.php)"
        url = f"{base_url}/pcp/consumo_alt.php"
        base_payload = {
            "cod_empresa": "11",
            "dati": "2024-01-01",
            "datf": "2026-12-31",
            "num_ordem": "",
            "logis": "",
            "kit": "",
            "padrao": "",
            "item_desc": "",
            "baixa": "S",
            "min": "",
            "loc_compon": "",
            "submit": "Consultar",
        }
        campo_local = "local[]"
    else:
        endpoint_name = "Ordens Atrasadas (atrasadas.php)"
        url = f"{base_url}/pcp/atrasadas.php"
        base_payload = {
            "cod_empresa": "11",
            "inicio": "2024-01-01",
            "fim": "2026-12-31",
            "ordem": "entrega,",
            "dat_liberac": "S",
            "item_desc": "S",
            "submit": "Consultar",
        }
        campo_local = "local[]"

    print("\n" + "=" * 70)
    print(f"BENCHMARK: {endpoint_name.upper()}")
    print("Confrontando: 51 Requisições Segmentadas  VS  1 Requisição Agrupada")
    print("=" * 70)

    # 1. Login inicial para obter sessão de teste
    print("\n[1/3] Realizando autenticação inicial na intranet...")
    async with ExtractionWorker(username=username, password=password) as auth_worker:
        await auth_worker.login()
        cookies = dict(auth_worker.session.cookies)
        print("  ✓ Autenticação realizada com sucesso (PHPSESSID obtido).")

    # -------------------------------------------------------------
    # 2. Execução Segmentada (51 requisições em pool de 10 workers)
    # -------------------------------------------------------------
    print("\n[2/3] Executando Abordagem SEGMENTADA (51 tarefas em pool com 10 workers)...")
    tasks_segmentadas = []
    for i, loc in enumerate(LOCAIS_51):
        p = dict(base_payload)
        p[campo_local] = loc
        tasks_segmentadas.append({
            "task_id": f"seg_{i}_{loc}",
            "url": url,
            "metodo": "POST",
            "grupo": endpoint_choice,
            "payload": p,
            "local": loc,
        })

    t0_seg = time.perf_counter()
    raw_seg = await execute_task_pool(
        execution_id="bench_seg",
        tasks=tasks_segmentadas,
        username=username,
        password=password,
        cookies=None,  # Cada worker cria e autentica sua própria sessão PHP isolada
        concurrency_limit=10,
    )
    t1_seg = time.perf_counter()
    duracao_seg = t1_seg - t0_seg

    dfs_seg = [r["dataframe"] for r in raw_seg if r.get("status") == "SUCCESS" and r.get("dataframe") is not None]
    total_linhas_seg = sum(len(d) for d in dfs_seg)
    sucessos_seg = sum(1 for r in raw_seg if r.get("status") == "SUCCESS")

    print(f"  ✓ Segmentada Concluída: {sucessos_seg}/51 tarefas respondidas.")
    print(f"  ⏱ Tempo Total Segmentado: {duracao_seg:.2f} segundos")
    print(f"  📊 Linhas Totais Extraídas: {total_linhas_seg}")

    # -------------------------------------------------------------
    # 3. Execução Agrupada (1 única requisição com todos os 51 locais)
    # -------------------------------------------------------------
    print("\n[3/3] Executando Abordagem AGRUPADA (1 única requisição com 51 locais juntos)...")
    import urllib.parse
    payload_agrupado = []
    for k, v in base_payload.items():
        payload_agrupado.append((k, v))
    for loc in LOCAIS_51:
        payload_agrupado.append((campo_local, loc))

    encoded_body = urllib.parse.urlencode(payload_agrupado).encode("utf-8")
    post_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    t0_agrup = time.perf_counter()
    async with ExtractionWorker(username=username, password=password, cookies=cookies) as worker_agrup:
        response = await worker_agrup.session.post(
            url,
            content=encoded_body,
            headers=post_headers,
            timeout=120.0,
        )
        response.raise_for_status()
        html_agrup = response.text
        df_agrup = table_parser.parse_html_to_polars(html_agrup)
    t1_agrup = time.perf_counter()
    duracao_agrup = t1_agrup - t0_agrup

    total_linhas_agrup = len(df_agrup)

    print("  ✓ Agrupada Concluída: 1 requisição completada com sucesso.")
    print(f"  ⏱ Tempo Total Agrupado: {duracao_agrup:.2f} segundos")
    print(f"  📊 Linhas Totais Extraídas: {total_linhas_agrup}")

    # -------------------------------------------------------------
    # 4. Relatório e Análise Comparativa
    # -------------------------------------------------------------
    speedup = duracao_seg / max(duracao_agrup, 0.001)
    reducao_pct = ((duracao_seg - duracao_agrup) / max(duracao_seg, 0.001)) * 100

    print("\n" + "=" * 70)
    print("QUADRO COMPARATIVO DE PERFORMANCE")
    print("=" * 70)
    print(f"{'Métrica':<35} | {'Segmentada (51 reqs)':<22} | {'Agrupada (1 req)':<18}")
    print("-" * 80)
    print(f"{'Quantidade de Requisições HTTP':<35} | {'51 requisições':<22} | {'1 requisição':<18}")
    print(f"{'Tempo Total de Extração':<35} | {f'{duracao_seg:.2f} s':<22} | {f'{duracao_agrup:.2f} s':<18}")
    print(f"{'Linhas Extraídas':<35} | {f'{total_linhas_seg} linhas':<22} | {f'{total_linhas_agrup} linhas':<18}")
    print(f"{'Throughput da Conexão':<35} | {f'{51 / duracao_seg:.2f} req/s':<22} | {f'Consolidada em {duracao_agrup:.2f}s':<18}")
    print("-" * 80)
    print(f"🚀 Fator de Aceleração (Speedup): {speedup:.2f}x MAIS RÁPIDO!")
    print(f"⚡ Redução do Tempo de Espera:    {reducao_pct:.1f}% menor!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        user = sys.argv[1]
        pwd = sys.argv[2]
        ep = sys.argv[3] if len(sys.argv) > 3 else "ordens_atrasadas"
    else:
        print("Informe as credenciais da intranet para disparar o teste contra 192.168.0.6:")
        user = input("Usuário: ")
        pwd = getpass.getpass("Senha: ")
        ep = input("Endpoint [1 para ordens_atrasadas, 2 para consumo_insumos] (padrão 1): ").strip()
        ep = "consumo_insumos" if ep == "2" else "ordens_atrasadas"

    asyncio.run(run_benchmark(user, pwd, ep))
