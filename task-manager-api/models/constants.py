"""Domain constants shared by the models, controllers and routes."""

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'

VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
FINAL_STATUSES = (STATUS_DONE, STATUS_CANCELLED)
DEFAULT_STATUS = STATUS_PENDING

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = (
    (1, 'critical'),
    (2, 'high'),
    (3, 'medium'),
    (4, 'low'),
    (5, 'minimal'),
)

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
PASSWORD_MIN_LENGTH = 4

DEFAULT_CATEGORY_COLOR = '#000000'
DATE_INPUT_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7

EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

# Value returned in place of a stored credential.
REDACTED_SECRET = '********'

# Prefix of the placeholder token the login endpoint has always returned.
LOGIN_TOKEN_PREFIX = 'fake-jwt-token-'
