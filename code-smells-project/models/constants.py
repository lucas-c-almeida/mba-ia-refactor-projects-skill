"""Domain constants: the single definition of every enumerated value and business threshold."""

APP_VERSION = "1.0.0"

# Order statuses
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = (
    STATUS_PENDENTE,
    STATUS_APROVADO,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
)

# Product categories
CATEGORIA_PADRAO = "geral"
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

# Product name length limits (enforced on creation)
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# User types
TIPO_USUARIO_PADRAO = "cliente"

# Sales report discount tiers: (gross revenue strictly above, discount rate), highest first.
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)

# Placeholder shown wherever a secret value used to be exposed.
VALOR_OCULTO = "***"

# Name shown for an order item whose product no longer exists.
PRODUTO_DESCONHECIDO = "Desconhecido"
