"""Armazenamento unidirecional de senhas (PBKDF2-HMAC-SHA256, biblioteca padrão)."""
import functools
import hashlib
import hmac
import secrets

ALGORITMO = "pbkdf2_sha256"
ITERACOES = 600_000
TAMANHO_SAL_BYTES = 16
_SEPARADOR = "$"


def gerar_hash(senha):
    sal = secrets.token_bytes(TAMANHO_SAL_BYTES)
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES)
    return _SEPARADOR.join((ALGORITMO, str(ITERACOES), sal.hex(), derivada.hex()))


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(ALGORITMO + _SEPARADOR)


def verificar(senha, armazenado):
    """Comparação em tempo constante contra um hash no formato de `gerar_hash`."""
    if not eh_hash(armazenado):
        return False
    try:
        _, iteracoes, sal_hex, derivada_hex = armazenado.split(_SEPARADOR)
        derivada = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(sal_hex), int(iteracoes)
        )
    except ValueError:
        return False
    return hmac.compare_digest(derivada.hex(), derivada_hex)


@functools.lru_cache(maxsize=1)
def _hash_ficticio():
    """Hash de uma senha aleatória, gerado uma vez: iguala o custo do login quando o
    e-mail não existe, para que o tempo de resposta não revele contas existentes."""
    return gerar_hash(secrets.token_urlsafe(16))


def verificar_ficticio(senha):
    verificar(senha, _hash_ficticio())
    return False
