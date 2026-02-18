import json
from datetime import datetime, timezone

from fastapi import Body, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from .db import Base, engine, get_db
from .models import WebhookLog, WebhookData
from .schemas import WebhookPayloadSchema
from .security import require_api_key

app = FastAPI(title="Webhook API", version="1.0.0")


def _payload_example():
    return {
        "id_venda": 6010,
        "status": "processo_finalizado",
        "data_criacao": "2026-02-03T10:30:00Z",
        "data_atualizacao": "2026-02-03T12:45:00Z",
        "dados_empreendimento": {
            "nome": "UNION 511",
            "endereco": "CRNW 511 - BLOCO A LOTE 01 - NOROESTE",
            "unidade": "1234",
            "bloco": "Bloco B",
            "vagas": ["157R"],
        },
        "dados_cliente": {
            "nome": "HERMINIO DE SOUSA JUNIOR",
            "sexo": "MASCULINO",
            "data_de_nascimento": "1985-08-20",
            "email": "HERMSOU3SA@TESTE.COM ",
            "telefone": "61 9 9999-9999",
            "estado_civil": "CASADO(A)",
            "conjuge": {
                "nome": "MONICA CRISTINA ALTAF JULIEN DE SOUSA",
                "sexo": "FEMININO",
                "data_de_nascimento": "1985-08-20",
                "email": "MCJ3ULIEN@TESTE.COM",
                "telefone": "61 9 9999-9999",
            },
        },
    }


def _simplify_pydantic_errors(errors):
    simplified = []
    for err in errors or []:
        simplified.append(
            {
                "type": err.get("type"),
                "loc": err.get("loc"),
                "msg": err.get("msg"),
            }
        )
    return simplified


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    # FastAPI valida o body antes de entrar no handler da rota.
    # Aqui devolvemos um 400 mais estável e sem detalhes internos.
    try:
        raw = await request.body()
        safe_raw = raw.decode("utf-8", errors="replace") if raw else ""
    except Exception:
        safe_raw = ""

    # Tenta capturar JSON (se existir) para log. Caso falhe, guarda raw.
    payload_for_log: dict
    if safe_raw:
        try:
            parsed = json.loads(safe_raw)
            payload_for_log = parsed if isinstance(parsed, dict) else {"_non_object_json": parsed}
        except Exception:
            payload_for_log = {"_raw": safe_raw}
    else:
        payload_for_log = {"_raw": ""}

    errors = _simplify_pydantic_errors(exc.errors())

    # Melhor esforço de log (não derruba a API se o DB estiver fora).
    try:
        from .db import SessionLocal

        db = SessionLocal()
        try:
            db.add(WebhookLog(payload=payload_for_log, valid=False))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass

    return JSONResponse(
        status_code=400,
        content={
            "detail": "Payload inválido (schema).",
            "errors": errors,
        },
    )

@app.on_event("startup")
def on_startup():
    # cria tabelas automaticamente (para MVP). Em produção, prefira Alembic.
    Base.metadata.create_all(bind=engine)

def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _event_id(id_venda: int) -> str:
    # evt_YYYYMMDD_<id_venda>
    d = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"evt_{d}_{id_venda}"

@app.post(
    "/webhook",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": {
                        "exemplo": {
                            "summary": "Exemplo de payload",
                            "value": _payload_example(),
                        }
                    }
                }
            },
        }
    },
)
async def receive_webhook(
    request: Request,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
    payload: WebhookPayloadSchema = Body(...),
):
    def _return_500(detail: str):
        try:
            db.rollback()
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"detail": detail})

    payload_any = payload.model_dump(mode="json")

    # 3) se válido: salva em logs (valid=true) e em data
    log = WebhookLog(payload=payload_any, valid=True)
    db.add(log)

    data_row = WebhookData(
        id_venda=payload.id_venda,
        status=payload.status,
        payload=payload_any,
    )
    db.add(data_row)

    try:
        db.commit()
    except SQLAlchemyError:
        return _return_500("Erro ao persistir webhook no banco de dados.")

    return {
        "status": "received",
        "mensagem": "Webhook processado com sucesso",
        "event_id": _event_id(payload.id_venda),
        "processado_em": _utc_now_iso(),
    }
