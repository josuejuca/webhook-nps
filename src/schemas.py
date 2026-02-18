from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict

class ConjugeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(..., min_length=2)
    sexo: str
    data_de_nascimento: date
    email: EmailStr
    telefone: str

class DadosClienteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(..., min_length=2)
    sexo: str
    data_de_nascimento: date
    email: EmailStr
    telefone: str
    estado_civil: str
    conjuge: Optional[ConjugeSchema] = None

class DadosEmpreendimentoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str
    endereco: str
    unidade: str
    bloco: str
    vagas: List[str] = Field(default_factory=list)

class WebhookPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id_venda: int
    status: str
    data_criacao: datetime
    data_atualizacao: datetime
    dados_empreendimento: DadosEmpreendimentoSchema
    dados_cliente: DadosClienteSchema
