"""One-way password storage with the standard library's scrypt KDF.

Stored format: scrypt$<n>$<r>$<p>$<salt hex>$<hash hex>. Rows written by the previous
code hold the password as given; they are still verified, and re-hashed on the next
successful sign-in (see UsuarioController.autenticar).
"""
import hashlib
import hmac
import secrets

_PREFIXO = "scrypt"
_N, _R, _P = 2 ** 14, 8, 1
_TAMANHO_SAL = 16
_TAMANHO_HASH = 32

# Stored for an account that must not be able to sign in (a seeded account whose
# password was not configured). It never matches any input.
SENHA_INUTILIZAVEL = "!"


def _derivar(senha: str, sal: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(senha.encode("utf-8"), salt=sal, n=n, r=r, p=p,
                          maxmem=128 * n * r * 2, dklen=_TAMANHO_HASH)


def gerar_hash(senha: str) -> str:
    sal = secrets.token_bytes(_TAMANHO_SAL)
    derivada = _derivar(senha, sal, _N, _R, _P)
    return f"{_PREFIXO}${_N}${_R}${_P}${sal.hex()}${derivada.hex()}"


def e_hash(armazenada: str) -> bool:
    return armazenada.startswith(_PREFIXO + "$")


def e_legada(armazenada) -> bool:
    """A value the previous code stored as given."""
    return isinstance(armazenada, str) and armazenada != SENHA_INUTILIZAVEL and not e_hash(armazenada)


def verificar(senha: str, armazenada) -> bool:
    if not isinstance(armazenada, str) or armazenada == SENHA_INUTILIZAVEL:
        return False
    if e_hash(armazenada):
        try:
            _, n, r, p, sal_hex, hash_hex = armazenada.split("$")
            derivada = _derivar(senha, bytes.fromhex(sal_hex), int(n), int(r), int(p))
        except ValueError:
            return False
        return hmac.compare_digest(derivada.hex(), hash_hex)
    return hmac.compare_digest(senha.encode("utf-8"), armazenada.encode("utf-8"))
