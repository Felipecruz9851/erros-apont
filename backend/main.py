import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Garante que a raiz do repositório esteja no sys.path e no PYTHONPATH
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(ROOT_DIR) not in os.environ.get("PYTHONPATH", ""):
    current_pp = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = (
        f"{ROOT_DIR}{os.pathsep}{current_pp}" if current_pp else str(ROOT_DIR)
    )

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.pipeline import router as pipeline_router
from backend.app.api.results import router as results_router
from backend.app.api.contacts import router as contacts_router
from backend.app.api.emails import router as emails_router
from backend.app.core.config import settings

# Diretório de distribuição do frontend React compilado
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
if not FRONTEND_DIST.exists() and (BASE_DIR / "frontend" / "dist").exists():
    FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Auditoria de Erros de Apontamento e Saldo no Local de Produção (Líder Design Style)",
)

# Configuração de CORS para permitir acesso do frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# Registra os roteadores da API v1
app.include_router(
    pipeline_router,
    prefix=f"{settings.API_V1_STR}/pipeline",
    tags=["Pipeline"],
)
app.include_router(
    results_router,
    prefix=f"{settings.API_V1_STR}/results",
    tags=["Resultados"],
)
app.include_router(
    contacts_router,
    prefix=f"{settings.API_V1_STR}/contacts",
    tags=["Contatos"],
)
app.include_router(
    emails_router,
    prefix=f"{settings.API_V1_STR}/emails",
    tags=["Emails"],
)

# Monta os assets estáticos gerados pelo Vite (JS, CSS, imagens)
if (FRONTEND_DIST / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="assets",
    )


@app.get("/")
async def root():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "erro": "Build do frontend não encontrado. Execute 'npm run build' na pasta frontend."
    }


# Suporte a rotas internas do React (Single Page Application / React Router)
# Redireciona requisições não-API para os arquivos estáticos ou para o index.html
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Se for uma chamada para endpoint da API inexistente, devolve 404
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Endpoint não encontrado")

    # Se o arquivo solicitado existir fisicamente (ex: favicon.ico, logo_lider.png), entrega ele
    file_path = FRONTEND_DIST / full_path
    if full_path and file_path.is_file():
        return FileResponse(file_path)

    # Redireciona qualquer rota de página para o index.html
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return {
        "erro": "Build do frontend não encontrado. Execute 'npm run build' na pasta frontend."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        reload_dirs=[str(BASE_DIR)],
        app_dir=str(ROOT_DIR),
    )

