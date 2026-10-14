"""Named constants for values that used to be repeated literals."""

API_VERSION = "1.0.0"

# How long a connection waits for a locked database, in seconds.
SQLITE_TIMEOUT_SEGUNDOS = 10

# Product rules
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Order status vocabulary
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [
    STATUS_PENDENTE,
    STATUS_APROVADO,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
]

# Sales report: revenue above the threshold earns the rate (checked from the highest tier down).
FAIXAS_DESCONTO = ((10000, 0.1), (5000, 0.05), (1000, 0.02))

# Returned in place of a secret value; the field and its type are kept.
VALOR_MASCARADO = "********"
