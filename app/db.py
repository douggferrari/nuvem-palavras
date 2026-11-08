"""SQLite em DATA_DIR (no Railway, o volume montado em /data)."""
import os
import sqlite3
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path

from .termos import chave_de

DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
DB_PATH = DATA_DIR / "nuvem.db"

PERGUNTA_PADRAO = (
    "Me conta em uma palavra, qual a sua percepção em relação "
    "à gestão dos nossos projetos atualmente?"
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS config (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa TEXT NOT NULL UNIQUE,  -- id do cookie do navegador: uma resposta por pessoa
    termo TEXT NOT NULL,      -- como a pessoa escreveu
    chave TEXT NOT NULL,      -- sem caixa e sem acento: agrupa as grafias
    criada_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_respostas_chave ON respostas (chave);
"""


@contextmanager
def conectar():
    con = sqlite3.connect(DB_PATH, timeout=15)
    try:
        with con:  # commit no fim, rollback se der erro
            yield con
    finally:
        con.close()


def criar_esquema():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with conectar() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(ESQUEMA)
        # PERGUNTA só vale no primeiro boot; depois quem manda é o /admin.
        con.execute(
            "INSERT OR IGNORE INTO config (chave, valor) VALUES ('pergunta', ?)",
            (os.environ.get("PERGUNTA") or PERGUNTA_PADRAO,),
        )


def pergunta(con) -> str:
    return con.execute("SELECT valor FROM config WHERE chave = 'pergunta'").fetchone()[0]


def salvar_pergunta(con, texto: str):
    con.execute("UPDATE config SET valor = ? WHERE chave = 'pergunta'", (texto,))


def adicionar(con, pessoa: str, termo: str) -> bool:
    """Grava a resposta; False se a pessoa já tinha respondido. O UNIQUE em
    `pessoa` segura também o duplo toque no botão (dois POSTs juntos)."""
    cur = con.execute(
        "INSERT INTO respostas (pessoa, termo, chave) VALUES (?, ?, ?)"
        " ON CONFLICT (pessoa) DO NOTHING",
        (pessoa, termo, chave_de(termo)),
    )
    return cur.rowcount == 1


def resposta_de(con, pessoa: str) -> str | None:
    linha = con.execute("SELECT termo FROM respostas WHERE pessoa = ?", (pessoa,)).fetchone()
    return linha[0] if linha else None


def total_respostas(con) -> int:
    return con.execute("SELECT COUNT(*) FROM respostas").fetchone()[0]


def contagem(con) -> list[dict]:
    """Termos agrupados pela chave, mais frequentes primeiro. O texto exibido é
    a grafia mais usada no grupo (no empate, a que chegou primeiro)."""
    grafias = defaultdict(Counter)
    for chave, termo in con.execute("SELECT chave, termo FROM respostas ORDER BY id"):
        grafias[chave][termo] += 1
    itens = [
        {"chave": chave, "texto": c.most_common(1)[0][0], "n": c.total()}
        for chave, c in grafias.items()
    ]
    itens.sort(key=lambda t: (-t["n"], t["chave"]))
    return itens


def limpar(con):
    """Rodada nova: apaga tudo e libera todo mundo para responder de novo."""
    con.execute("DELETE FROM respostas")


def remover(con, chave: str):
    """Tira o termo da nuvem; quem o escreveu pode responder de novo."""
    con.execute("DELETE FROM respostas WHERE chave = ?", (chave,))
