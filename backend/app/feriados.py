import requests
from getpass import getpass
import datetime as dt
import time
from pathlib import Path

BASE_URL = "http://192.168.0.6"
LOGIN_PAGE = f"{BASE_URL}/home/"
LOGIN_POST = f"{BASE_URL}/home/login/"
FERIADOS_URL = f"{BASE_URL}/pcp/feriados.php"

usuario = input("Usuário: ")
senha = getpass("Senha: ")

session = requests.Session()

# 1) GET inicial (gera PHPSESSID)
session.get(LOGIN_PAGE, timeout=10)

# 2) POST multipart/form-data (igual ao navegador)
resp = session.post(
    LOGIN_POST,
    files={
        "pagina_acessada": (None, f"{BASE_URL}/home/app"),
        "action": (None, "login"),
        "usuario": (None, usuario),
        "senha": (None, senha),
        "logar": (None, "Acessar"),
    },
    headers={
        "Referer": LOGIN_PAGE,
        "Origin": BASE_URL,
        "User-Agent": "Mozilla/5.0",
    },
    allow_redirects=True,
    timeout=10,
)

resp.raise_for_status()

print("URL final:", resp.url)
print("Cookies:", session.cookies.get_dict())

# sinal real de sucesso: acesso ao app ou sessão ativa
if "/home/app" not in resp.url and "PHPSESSID" not in session.cookies:
    raise RuntimeError("Login não estabeleceu sessão")

print("Login OK")

ANOS = [2025, 2026, 2027]
datas_feriados = []

# --- calcula total de dias úteis ---
total_dias_uteis = 0
for ano in ANOS:
    data = dt.date(ano, 1, 1)
    fim = dt.date(ano, 12, 31)
    while data <= fim:
        if data.weekday() < 5:
            total_dias_uteis += 1
        data += dt.timedelta(days=1)

processados = 0

# --- processamento ---
for ano in ANOS:
    data = dt.date(ano, 1, 1)
    fim = dt.date(ano, 12, 31)

    while data <= fim:
        if data.weekday() < 5:
            processados += 1
            print(f"{processados} de {total_dias_uteis} — {data.isoformat()}")

            r = session.get(
                FERIADOS_URL,
                params={"dat_ref": data.isoformat()},
                timeout=5,
            )
            r.raise_for_status()
            js = r.json()

            if js.get("success") and js.get("data"):
                for item in js["data"]:
                    if item.get("ies_situa") == "3":
                        datas_feriados.append(item["dat_ref"])

            time.sleep(0.01)

        data += dt.timedelta(days=1)

# --- limpeza final ---
datas_feriados = sorted(set(datas_feriados))

base_dir = Path(__file__).resolve().parent
arquivo = base_dir / "feriados.txt"

with open(arquivo, "w", encoding="utf-8") as f:
    for d in datas_feriados:
        f.write(f"{d}\n")
