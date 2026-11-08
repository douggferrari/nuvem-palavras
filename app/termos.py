"""Regras que transformam o texto digitado no termo da nuvem."""
import unicodedata

MAX_RESPOSTA = 40
_BORDAS = " .,;:!?¡¿\"'“”‘’«»()[]{}<>-–—…*#_/|"


def limpar(resposta: str) -> str:
    """Espaços colapsados e pontuação das pontas fora; "" se não sobrar nada.
    A resposta inteira é um termo só: "falta de clareza" não vira três palavras."""
    return " ".join(resposta.split()).strip(_BORDAS)[:MAX_RESPOSTA].rstrip(_BORDAS)


def chave_de(termo: str) -> str:
    """'Organizada', 'organizada' e 'ORGANIZADA' viram a mesma chave, com ou sem acento."""
    decomposto = unicodedata.normalize("NFKD", termo.casefold())
    return "".join(c for c in decomposto if not unicodedata.combining(c))
