from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.services.contacts_service import contacts_service
from backend.app.services.email_service import email_service

router = APIRouter()


class EmailPreviewRequest(BaseModel):
    execution_id: Optional[str] = Field(default=None, description="ID da execução ou 'latest'")
    contact_id: str = Field(..., description="ID do contato cadastrado")
    tipo_filtro: Optional[str] = Field(default="TODOS", description="Filtrar por tipo: TODOS, C (comprado), P (produzido)")


class EmailPreviewResponse(BaseModel):
    contact_id: str
    contact_name: str
    email: str
    locais: List[str]
    dias_uteis: int
    data_ref: str
    total_erros: int
    subject: str
    text_body: str
    html_body: str
    records: List[Dict[str, Any]]


class EmailSendRequest(BaseModel):
    execution_id: Optional[str] = Field(default=None, description="ID da execução ou 'latest'")
    contact_ids: Optional[List[str]] = Field(default=None, description="Lista de IDs de contatos a disparar")
    send_all_with_errors: bool = Field(default=False, description="Disparar para todos que possuam divergências")
    tipo_filtro: Optional[str] = Field(default="TODOS", description="Filtrar por tipo: TODOS, C (comprado), P (produzido)")
    selected_record_ids: Optional[List[str]] = Field(default=None, description="IDs das linhas selecionadas na tabela")
    selected_records: Optional[List[Dict[str, Any]]] = Field(default=None, description="Linhas selecionadas completas enviadas pelo frontend")
    target_email: Optional[str] = Field(default=None, description="E-mail específico para envio avulso")
    target_name: Optional[str] = Field(default=None, description="Nome do destinatário específico")


class EmailSendItemResult(BaseModel):
    contact_id: str
    contact_name: str
    email: str
    locais: List[str]
    total_erros: int
    status: str
    message: str


class EmailSendResponse(BaseModel):
    execution_id: str
    dias_uteis: int
    data_ref: str
    total_processed: int
    total_sent: int
    results: List[EmailSendItemResult]


class ContactEmailSummary(BaseModel):
    contact_id: str
    nome: str
    email: str
    locais: List[str]
    total_erros: int
    ops_com_erro: int


class EmailSummaryResponse(BaseModel):
    execution_id: str
    dias_uteis: int
    data_ref: str
    has_results: bool
    contacts: List[ContactEmailSummary]


@router.get(
    "/summary",
    response_model=EmailSummaryResponse,
    summary="Resumo de erros de apontamento por contato para a tela de envio",
)
def get_contacts_email_summary(
    execution_id: Optional[str] = Query(None),
    tipo_filtro: Optional[str] = Query("TODOS", description="Filtrar tipo: TODOS, C ou P"),
):
    all_contacts = contacts_service.list_contacts()
    records, dias_uteis, data_ref = email_service.get_execution_data(execution_id)

    contacts_summary: List[ContactEmailSummary] = []
    for c in all_contacts:
        c_locais = c.get("locais", [])
        c_errors = email_service.filter_errors_for_contact(records, c_locais, tipo_filtro=tipo_filtro)
        ops_count = len({str(r.get("op", "")).strip() for r in c_errors if r.get("op")})

        contacts_summary.append(
            ContactEmailSummary(
                contact_id=c.get("id", ""),
                nome=c.get("nome", ""),
                email=c.get("email", ""),
                locais=c_locais,
                total_erros=len(c_errors),
                ops_com_erro=ops_count,
            )
        )

    return EmailSummaryResponse(
        execution_id=execution_id or "latest",
        dias_uteis=dias_uteis,
        data_ref=data_ref,
        has_results=bool(records),
        contacts=contacts_summary,
    )


@router.post(
    "/preview",
    response_model=EmailPreviewResponse,
    summary="Prévia do e-mail e da tabela compilada para um contato",
)
def preview_email(payload: EmailPreviewRequest):
    contact = contacts_service.get_contact(payload.contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contato não encontrado")

    records, dias_uteis, data_ref = email_service.get_execution_data(payload.execution_id)
    locais = contact.get("locais", [])
    contact_errors = email_service.filter_errors_for_contact(records, locais, tipo_filtro=payload.tipo_filtro)

    subject, plain_text, html_body = email_service.build_email_content(
        contact_name=contact.get("nome", ""),
        locais=locais,
        error_records=contact_errors,
        dias_uteis=dias_uteis,
        data_ref=data_ref,
        tipo_filtro=payload.tipo_filtro,
    )

    return EmailPreviewResponse(
        contact_id=contact.get("id", ""),
        contact_name=contact.get("nome", ""),
        email=contact.get("email", ""),
        locais=locais,
        dias_uteis=dias_uteis,
        data_ref=data_ref,
        total_erros=len(contact_errors),
        subject=subject,
        text_body=plain_text,
        html_body=html_body,
        records=contact_errors,
    )


@router.post(
    "/send",
    response_model=EmailSendResponse,
    summary="Dispara e-mails com as tabelas filtradas para contatos",
)
def send_emails(payload: EmailSendRequest):
    res = email_service.dispatch_for_contacts(
        execution_id=payload.execution_id,
        contact_ids=payload.contact_ids,
        send_all_with_errors=payload.send_all_with_errors,
        tipo_filtro=payload.tipo_filtro,
        selected_record_ids=payload.selected_record_ids,
        selected_records=payload.selected_records,
        target_email=payload.target_email,
        target_name=payload.target_name,
    )
    return res
