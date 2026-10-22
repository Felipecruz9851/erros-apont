from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.app.models.contacts import ContactCreate, ContactResponse, ContactUpdate
from backend.app.services.contacts_service import contacts_service

router = APIRouter()


@router.get("", response_model=List[ContactResponse], summary="Lista todos os contatos cadastrados")
def list_contacts():
    return contacts_service.list_contacts()


@router.get("/locations", response_model=List[str], summary="Lista os locais de produção disponíveis")
def list_available_locations():
    return contacts_service.get_available_locations()


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED, summary="Cadastra novo contato")
def create_contact(payload: ContactCreate):
    created = contacts_service.create_contact(
        nome=payload.nome,
        email=payload.email,
        locais=payload.locais,
    )
    return created


@router.get("/{contact_id}", response_model=ContactResponse, summary="Obtém um contato específico")
def get_contact(contact_id: str):
    contact = contacts_service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contato não encontrado")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse, summary="Atualiza dados do contato")
def update_contact(contact_id: str, payload: ContactUpdate):
    updated = contacts_service.update_contact(
        contact_id=contact_id,
        nome=payload.nome,
        email=payload.email,
        locais=payload.locais,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contato não encontrado")
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove contato cadastrado")
def delete_contact(contact_id: str):
    deleted = contacts_service.delete_contact(contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contato não encontrado")
    return None
