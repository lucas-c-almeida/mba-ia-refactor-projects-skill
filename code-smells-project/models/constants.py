"""Named values of the domain. One definition each, so a typo fails instead of inventing a state."""

APP_VERSION = "1.0.0"
REDACTED = "[REDACTED]"

ORDER_STATUS_PENDING = "pendente"
ORDER_STATUS_APPROVED = "aprovado"
ORDER_STATUS_SHIPPED = "enviado"
ORDER_STATUS_DELIVERED = "entregue"
ORDER_STATUS_CANCELED = "cancelado"
ORDER_STATUSES = (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_APPROVED,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_CANCELED,
)

DEFAULT_CATEGORY = "geral"
PRODUCT_CATEGORIES = (
    "informatica",
    "moveis",
    "vestuario",
    DEFAULT_CATEGORY,
    "eletronicos",
    "livros",
)
PRODUCT_NAME_MIN_LENGTH = 2
PRODUCT_NAME_MAX_LENGTH = 200

DEFAULT_USER_TYPE = "cliente"

# Identifiers per `IN (...)` lookup; keeps a statement well under the engine's variable limit.
LOOKUP_BATCH_SIZE = 500

# (revenue must exceed the threshold, discount rate), checked from the highest tier down.
REVENUE_DISCOUNT_TIERS = (
    (10000, 0.1),
    (5000, 0.05),
    (1000, 0.02),
)

OPERATOR_TOKEN_HEADER = "X-Operator-Token"
