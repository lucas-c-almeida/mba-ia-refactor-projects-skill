"""Named domain values shared by validation, queries and reports."""

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
STATUS_DONE = 'done'
CLOSED_STATUSES = (STATUS_DONE, 'cancelled')
USER_ROLES = ('user', 'admin', 'manager')

DEFAULT_STATUS = 'pending'
DEFAULT_ROLE = 'user'
DEFAULT_PRIORITY = 3
MIN_PRIORITY = 1
MAX_PRIORITY = 5
HIGH_PRIORITY_MAX = 2

# Priority level -> label used by the summary report.
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

DEFAULT_CATEGORY_COLOR = '#000000'
DUE_DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7

EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
