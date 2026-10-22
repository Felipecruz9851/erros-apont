from typing import List, Optional
from pydantic import BaseModel, Field


class ContactBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120, description="Nome do responsável / contato")
    email: str = Field(..., min_length=5, max_length=120, description="Endereço de e-mail do contato")
    locais: List[str] = Field(..., min_length=1, description="Lista de locais de produção atribuídos")


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[str] = Field(None, min_length=5, max_length=120)
    locais: Optional[List[str]] = Field(None, min_length=1)


class ContactResponse(ContactBase):
    id: str
    created_at: str
    updated_at: str
