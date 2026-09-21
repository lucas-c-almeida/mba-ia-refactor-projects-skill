"""Configuração da aplicação: lida do ambiente uma única vez, imutável depois disso.

Nenhum outro módulo lê variáveis de ambiente. Valores inseguros (debug) são opt-in.
Veja `.env.example` para a lista completa de chaves.
"""
import logging
import os
import secrets
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VERSAO_API = "1.0.0"


class ErroConfiguracao(RuntimeError):
    """Configuração inválida detectada na inicialização."""


def _booleano(nome, padrao):
    valor = os.environ.get(nome)
    if valor is None or valor == "":
        return padrao
    normalizado = valor.strip().lower()
    if normalizado in ("1", "true", "yes", "on"):
        return True
    if normalizado in ("0", "false", "no", "off"):
        return False
    raise ErroConfiguracao(f"valor booleano inválido para {nome}: {valor!r}")


def _inteiro(nome, padrao):
    valor = os.environ.get(nome)
    if valor is None or valor == "":
        return padrao
    try:
        return int(valor)
    except ValueError as erro:
        raise ErroConfiguracao(f"valor inteiro inválido para {nome}: {valor!r}") from erro


def _lista(nome, padrao):
    valor = os.environ.get(nome)
    if valor is None or valor.strip() == "":
        return padrao
    return tuple(item.strip() for item in valor.split(",") if item.strip())


@dataclass(frozen=True)
class Configuracao:
    chave_secreta: str
    debug: bool
    host: str
    porta: int
    caminho_banco: str
    ambiente: str
    origens_cors: tuple


def carregar_configuracao():
    chave_secreta = os.environ.get("SECRET_KEY")
    if not chave_secreta:
        # A aplicação não usa sessão assinada hoje; uma chave efêmera evita um segredo
        # no código sem impedir o boot. Defina SECRET_KEY antes de introduzir sessões.
        chave_secreta = secrets.token_urlsafe(32)
        logger.warning("SECRET_KEY não definida: usando chave efêmera gerada no boot")

    return Configuracao(
        chave_secreta=chave_secreta,
        debug=_booleano("APP_DEBUG", False),
        # Mesmos valores que a aplicação usava antes, agora explícitos e configuráveis.
        host=os.environ.get("APP_HOST", "0.0.0.0"),
        porta=_inteiro("APP_PORT", 5000),
        caminho_banco=os.environ.get("DATABASE_PATH", "loja.db"),
        ambiente=os.environ.get("APP_ENV", "producao"),
        origens_cors=_lista("CORS_ORIGINS", ("*",)),
    )
