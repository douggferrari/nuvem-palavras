"""Nuvem de palavras ao vivo: o público lê o QR, responde a pergunta em /r e
a resposta entra na nuvem projetada em /."""
import io
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import segno
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, termos

VERSAO = "1.0"
BASE = Path(__file__).resolve().parent
MAX_NA_NUVEM = 120
# Identifica a pessoa para valer "uma resposta por pessoa". É por navegador:
# janela anônima burla, mas IP não serve (no escritório todos saem pelo mesmo).
COOKIE_PESSOA = "nuvem_pessoa"
UM_ANO = 365 * 24 * 3600


@asynccontextmanager
async def ciclo_de_vida(_app):
    db.criar_esquema()
    yield


app = FastAPI(lifespan=ciclo_de_vida, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["versao"] = VERSAO


def url_resposta(request: Request) -> str:
    """Endereço que vai no QR. URL_PUBLICA fixa o domínio; sem ela, vale o host
    da requisição (no Railway, abrir pelo *.up.railway.app geraria QR errado)."""
    base = os.environ.get("URL_PUBLICA") or str(request.base_url)
    return base.rstrip("/") + "/r"


def pagina(request: Request, nome: str, status_code: int = 200, **contexto):
    return templates.TemplateResponse(request, nome, contexto, status_code=status_code)


def pergunta_atual() -> str:
    with db.conectar() as con:
        return db.pergunta(con)


def resposta_da_pessoa(request: Request) -> str | None:
    pessoa = request.cookies.get(COOKIE_PESSOA)
    if not pessoa:
        return None
    with db.conectar() as con:
        return db.resposta_de(con, pessoa)


# ---------- público ----------

@app.get("/")
def nuvem(request: Request):
    url_curta = url_resposta(request).split("://", 1)[-1]
    return pagina(request, "nuvem.html", pergunta=pergunta_atual(), url_curta=url_curta)


@app.get("/api/nuvem")
def api_nuvem():
    with db.conectar() as con:
        dados = {
            "pergunta": db.pergunta(con),
            "total": db.total_respostas(con),
            "termos": db.contagem(con)[:MAX_NA_NUVEM],
        }
    return JSONResponse(dados, headers={"Cache-Control": "no-store"})


@app.get("/r")
def responder(request: Request):
    sua = resposta_da_pessoa(request)
    if sua is not None:
        return pagina(request, "obrigado.html", resposta=sua, ja_respondeu=True)
    return pagina(request, "responder.html", pergunta=pergunta_atual())


@app.post("/r")
def enviar(request: Request, resposta: str = Form("")):
    termo = termos.limpar(resposta)
    if not termo:
        return pagina(request, "responder.html", status_code=422, pergunta=pergunta_atual(),
                      erro="Escreva uma palavra antes de enviar.")
    pessoa = request.cookies.get(COOKIE_PESSOA, "")[:64] or secrets.token_urlsafe(16)
    with db.conectar() as con:
        registrada = db.adicionar(con, pessoa, termo)
    # Quem já tinha respondido volta para /r, que mostra a resposta original.
    destino = RedirectResponse("/r/obrigado" if registrada else "/r", status_code=303)
    destino.set_cookie(COOKIE_PESSOA, pessoa, max_age=UM_ANO, httponly=True, samesite="lax",
                       secure=request.url.scheme == "https")
    return destino


@app.get("/r/obrigado")
def obrigado(request: Request):
    return pagina(request, "obrigado.html", resposta=resposta_da_pessoa(request), ja_respondeu=False)


@app.get("/qr.svg")
def qr_svg(request: Request):
    buf = io.BytesIO()
    segno.make(url_resposta(request), error="m").save(
        buf, kind="svg", border=2, omitsize=True, xmldecl=False)
    return Response(buf.getvalue(), media_type="image/svg+xml")


@app.get("/qr.png")
def qr_png(request: Request, baixar: bool = False):
    buf = io.BytesIO()
    segno.make(url_resposta(request), error="m").save(buf, kind="png", scale=20, border=4)
    headers = {"Content-Disposition": 'attachment; filename="qr-nuvem.png"'} if baixar else {}
    return Response(buf.getvalue(), media_type="image/png", headers=headers)


# ---------- admin ----------

_basic = HTTPBasic(auto_error=False)


def exigir_admin(cred: HTTPBasicCredentials | None = Depends(_basic)):
    senha = os.environ.get("ADMIN_PASSWORD")
    if not senha:
        raise HTTPException(503, "Defina ADMIN_PASSWORD para liberar o /admin.")
    if cred is None or not secrets.compare_digest(cred.password.encode(), senha.encode()):
        raise HTTPException(401, "Senha incorreta.",
                            headers={"WWW-Authenticate": 'Basic realm="Nuvem de palavras"'})


def mesma_origem(request: Request):
    """O navegador reenvia a senha do Basic sozinho; sem esta checagem, outro
    site conseguiria postar nos formulários do admin."""
    origem = request.headers.get("origin")
    if origem and urlsplit(origem).netloc != request.headers.get("host"):
        raise HTTPException(403, "Origem não permitida.")


ADMIN = [Depends(exigir_admin)]
ADMIN_POST = [Depends(exigir_admin), Depends(mesma_origem)]


@app.get("/admin", dependencies=ADMIN)
def admin(request: Request):
    with db.conectar() as con:
        contexto = {
            "pergunta": db.pergunta(con),
            "total": db.total_respostas(con),
            "termos": db.contagem(con),
        }
    return pagina(request, "admin.html", url_resposta=url_resposta(request), **contexto)


@app.post("/admin/pergunta", dependencies=ADMIN_POST)
def admin_pergunta(texto: str = Form("")):
    texto = " ".join(texto.split())[:200]
    if texto:
        with db.conectar() as con:
            db.salvar_pergunta(con, texto)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/limpar", dependencies=ADMIN_POST)
def admin_limpar():
    with db.conectar() as con:
        db.limpar(con)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/remover", dependencies=ADMIN_POST)
def admin_remover(chave: str = Form(...)):
    with db.conectar() as con:
        db.remover(con, chave)
    return RedirectResponse("/admin", status_code=303)
