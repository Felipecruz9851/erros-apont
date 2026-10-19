import requests
from bs4 import BeautifulSoup
import json

cookies = {"PHPSESSID": "3eeero9cktl23hpo78aba98gai"}
headers = {"User-Agent": "Mozilla/5.0"}

locais = [
    'COLCHOES', 'BOX', 'ESTOF UL', 'CC ACABA01', 'ARMARIO UL', 'UL ACABA01',
    'COZINHA', 'PES ACABA', 'VIDRACARIA', 'PORTAS', 'LAMINAD UL', 'TAMPOS UL',
    'UL FABRI01', 'CORTE', 'CADEIRAS', 'CC FABRI01', 'CORTE LE', 'PEZINHO',
    'CC FABRI03', 'PLANEJADOS', 'LE FABRI02', 'LE FABRI03', 'LE FABRI06',
    'FIBRA', 'ALMOFADAS', 'CAPAS LE', 'METALURGIA', 'ALUMINIO', 'INOX',
    'PLASMA', 'ATELIE', 'ATELIE2', 'UL-ALMOX05', 'REVENDA', 'AT INSUMO',
    'AT SOFA', 'AT MOVEIS', 'AT KIT', 'AT VIDRO', 'KIT', 'TAPA FURO',
    'ACESSORIOS', 'COLMEIAS', 'C PILOTO', 'MOSTRUARIO', 'LAMINACAO1',
    'EMBALAGEM', 'OSSOPAINEL', 'TAPETES', 'LE FABRI01', 'PLAN_ESP'
]

# Test 1: Consumo with all locals and date range
payload_consumo = [
    ('cod_empresa', '11'),
    ('dati', '2024-01-01'),
    ('datf', '2026-12-31'),
    ('num_ordem', ''),
    ('logis', 'N'),
    ('kit', 'N'),
    ('padrao', 'A'),
    ('item_desc', '1'),
    ('baixa', 'S'),
    ('min', 'N'),
    ('loc_compon', ''),
    ('submit', 'Consultar')
]
for loc in locais:
    payload_consumo.append(('local[]', loc))

print("Fetching Consumo...")
try:
    r_con = requests.post("http://192.168.0.6/pcp/consumo_alt.php", data=payload_consumo, cookies=cookies, headers=headers, timeout=60)
    print("Consumo status:", r_con.status_code, "Length:", len(r_con.content))
    with open("storage/snapshots/consumo_result.html", "wb") as f:
        f.write(r_con.content)
    soup_con = BeautifulSoup(r_con.content, "html.parser")
    tables = soup_con.find_all("table")
    print(f"Consumo tables: {len(tables)}")
    for i, t in enumerate(tables):
        rows = t.find_all("tr")
        print(f"  Table {i}: {len(rows)} rows")
        if len(rows) > 1:
            print("  Header:", [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])][:12])
            print("  Sample row 1:", [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])][:12])
except Exception as e:
    print("Consumo error:", e)

# Test 2: Atrasadas with all locals and date range
payload_atrasadas = [
    ('cod_empresa', '11'),
    ('inicio', '2024-01-01'),
    ('fim', '2026-12-31'),
    ('ordem', 'entrega,'),
    ('dat_liberac', 'S'),
    ('item_desc', 'S'),
    ('submit', 'Consultar')
]
for loc in locais:
    payload_atrasadas.append(('local[]', loc))

print("\nFetching Atrasadas...")
try:
    r_atr = requests.post("http://192.168.0.6/pcp/atrasadas.php", data=payload_atrasadas, cookies=cookies, headers=headers, timeout=60)
    print("Atrasadas status:", r_atr.status_code, "Length:", len(r_atr.content))
    with open("storage/snapshots/atrasadas_result.html", "wb") as f:
        f.write(r_atr.content)
    soup_atr = BeautifulSoup(r_atr.content, "html.parser")
    tables = soup_atr.find_all("table")
    print(f"Atrasadas tables: {len(tables)}")
    for i, t in enumerate(tables):
        rows = t.find_all("tr")
        print(f"  Table {i}: {len(rows)} rows")
        if len(rows) > 1:
            print("  Header:", [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])][:12])
            print("  Sample row 1:", [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])][:12])
except Exception as e:
    print("Atrasadas error:", e)
