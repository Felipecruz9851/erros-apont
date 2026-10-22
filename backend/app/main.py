from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.pipeline import router as pipeline_router
from backend.app.api.results import router as results_router
from backend.app.api.contacts import router as contacts_router
from backend.app.api.emails import router as emails_router
from backend.app.core.config import settings

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
