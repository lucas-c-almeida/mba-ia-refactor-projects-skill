"""
Named constants for values that were previously magic literals scattered across the
delivery layer (AP-15): the product category vocabulary, the order status vocabulary
and the sales-report discount tiers. Defining each once means every reader — schema
default, boundary validation, the report — agrees by construction instead of by care.
"""

# --- Product categories -----------------------------------------------------------
CATEGORIA_INFORMATICA = "informatica"
CATEGORIA_MOVEIS = "moveis"
CATEGORIA_VESTUARIO = "vestuario"
CATEGORIA_GERAL = "geral"
CATEGORIA_ELETRONICOS = "eletronicos"
CATEGORIA_LIVROS = "livros"

CATEGORIAS_VALIDAS = (
    CATEGORIA_INFORMATICA,
    CATEGORIA_MOVEIS,
    CATEGORIA_VESTUARIO,
    CATEGORIA_GERAL,
    CATEGORIA_ELETRONICOS,
    CATEGORIA_LIVROS,
)

# --- Order status -------------------------------------------------------------------
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"

STATUS_VALIDOS = (
    STATUS_PENDENTE,
    STATUS_APROVADO,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
)

# --- Sales report discount policy ----------------------------------------------------
# A pricing rule, owned by the business, not by engineering (catalog AP-15: escalated
# to MEDIUM for exactly this reason). Named here so it is at least discoverable and
# changeable in one place; RP-15 recommends moving it to configuration if it changes
# outside the release cycle.
DISCOUNT_TIER_HIGH_THRESHOLD = 10000
DISCOUNT_TIER_HIGH_RATE = 0.10
DISCOUNT_TIER_MID_THRESHOLD = 5000
DISCOUNT_TIER_MID_RATE = 0.05
DISCOUNT_TIER_LOW_THRESHOLD = 1000
DISCOUNT_TIER_LOW_RATE = 0.02
