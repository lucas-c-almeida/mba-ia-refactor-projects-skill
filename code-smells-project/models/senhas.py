"""One-way password storage (AP-08), standard library only.

Stored format: pbkdf2_sha256$<iterations>$<salt hex>$<derived key hex>.
"""

import hashlib
import hmac
import secrets

ALGORITMO = "pbkdf2_sha256"
ITERACOES = 200_000
TAMANHO_SALT_BYTES = 16
SEPARADOR = "$"


def _derivar(senha, salt_hex, iteracoes):
    return hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), iteracoes
    ).hex()


def gerar_hash(senha):
    salt_hex = secrets.token_hex(TAMANHO_SALT_BYTES)
    derivada = _derivar(senha, salt_hex, ITERACOES)
    return SEPARADOR.join((ALGORITMO, str(ITERACOES), salt_hex, derivada))


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(ALGORITMO + SEPARADOR)


def verificar(senha, armazenado):
    if not eh_hash(armazenado):
        return False
    try:
        _, iteracoes, salt_hex, esperado = armazenado.split(SEPARADOR)
        calculado = _derivar(senha, salt_hex, int(iteracoes))
    except ValueError:
        return False
    return hmac.compare_digest(calculado, esperado)
