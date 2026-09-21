# 05 — Refactoring Playbook

Eighteen transformations, one for each catalog entry (RP-16 covers two). Each states its
**contract impact**: `safe` (apply automatically) or `contract-changing` (gated per
`04-architecture-guidelines.md` §6 — propose, do not apply).

Examples span **Python, JavaScript/TypeScript, Go, Ruby and PHP**, deliberately: the patterns are
not stack-bound, and reading the same idea in five syntaxes is the proof. The domains — warehouse
inventory, room booking, library loans, sensor telemetry, fleet maintenance — are invented and
neutral. Translate the shape, not the syntax.

**Method for every transformation:** make one behaviour-preserving move at a time; keep the public
surface fixed unless the gate says otherwise; re-run the validation harness after each meaningful
step, not only at the end. If a step cannot be made behaviour-preserving, stop and propose it.

| Id | Transformation | Fixes | Contract |
|---|---|---|---|
| RP-01 | Externalize configuration and secrets | AP-01 | safe |
| RP-02 | Parameterize queries and commands | AP-02 | safe |
| RP-03 | Split a God Module by responsibility | AP-03 | safe |
| RP-04 | Extract authorization into a policy and a guard | AP-04 | legitimate-use test — see entry |
| RP-05 | Extract a use case from a handler | AP-05 | safe |
| RP-06 | Introduce dependency injection and a composition root | AP-06 | safe |
| RP-07 | Replace global mutable state with scoped context | AP-07 | safe |
| RP-08 | One-way credential storage and output redaction | AP-08 | mixed — see entry |
| RP-09 | Centralize error handling behind a domain taxonomy | AP-09 | mixed — see entry |
| RP-10 | Collapse N+1 into a set-based query | AP-10 | safe |
| RP-11 | Introduce a boundary schema | AP-11 | mixed — see entry |
| RP-12 | Extract a shared policy from duplicated logic | AP-12 | safe |
| RP-13 | Bind resources to scope and bound the work | AP-13 | mixed — see entry |
| RP-14 | Replace a verified-deprecated API with its successor | AP-14 | safe when behaviour is equivalent |
| RP-15 | Replace magic values with named constants | AP-15 | safe |
| RP-16 | Rename for intent and delete dead code | AP-16, AP-17 | safe for internals only |
| RP-17 | Make runtime configuration safe by default | AP-18 | mixed — see entry |
| RP-18 | Upgrade a vulnerable dependency to its fixed version | AP-19 | safe within a major — see entry |

---

## RP-01 — Externalize configuration and secrets

**Fixes AP-01** · **Contract: safe** — a client cannot observe where a secret is read from.

Move every secret and every environment-specific value out of source and into a single configuration
module that reads the environment once, fails loudly when a required value is missing, and exposes an
immutable object.

**Before** (Python)

```python
# ingest.py
SECRET_SIGNING_KEY = "s3cr3t-signing-key-do-not-share"
DB_URL = "postgresql://telemetry_app:hunter2@db.internal:5432/telemetry"
MAX_BATCH = 500

def store_reading(reading):
    conn = psycopg2.connect(DB_URL)
    ...
```

**After**

```python
# config/settings.py
import os
from dataclasses import dataclass

class ConfigError(RuntimeError):
    """Raised at startup when required configuration is absent."""

def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        # Fail at startup, loudly — not lazily at first use.
        raise ConfigError(f"missing required environment variable: {name}")
    return value

@dataclass(frozen=True)          # frozen: configuration is read, never mutated
class Settings:
    signing_key: str
    database_url: str
    max_batch: int

def load_settings() -> Settings:
    return Settings(
        signing_key=_required("SIGNING_KEY"),
        database_url=_required("DATABASE_URL"),
        max_batch=int(os.environ.get("MAX_BATCH", "500")),   # optional: default is fine
    )
```

```python
# ingest.py — receives configuration, never reads the environment itself
class ReadingStore:
    def __init__(self, connection):
        self._connection = connection
```

Also: add `.env.example` listing every key with placeholder values; add the real `.env` and any key
files to the ignore file; and **rotate every secret that was committed** — it is in the history
forever, and deleting the line does not remove it. Say that in the report; it is an action only the
owner can take.

---

## RP-02 — Parameterize queries and commands

**Fixes AP-02** · **Contract: safe** — the observable result is identical for legitimate input.

Never build a statement by string construction. Pass the statement with placeholders and the values
separately, so the driver — not the string — decides what is data.

**Before** (PHP)

```php
$shelf = $_GET['shelf'];
$sql = "SELECT * FROM stock_items WHERE shelf = '" . $shelf . "' ORDER BY " . $_GET['sort'];
$rows = $pdo->query($sql)->fetchAll();
```

**After**

```php
// Values are bound. Identifiers cannot be bound, so they go through an allow-list.
const SORTABLE = ['label' => 'label', 'quantity' => 'quantity', 'updated' => 'updated_at'];

$sortKey = SORTABLE[$_GET['sort'] ?? 'label'] ?? 'label';   // closed set, never input

$stmt = $pdo->prepare(
    "SELECT * FROM stock_items WHERE shelf = :shelf ORDER BY {$sortKey}"
);
$stmt->execute([':shelf' => $_GET['shelf'] ?? '']);
$rows = $stmt->fetchAll();
```

The same shape in Python — note that the substitution happens **inside** the driver call:

```python
# Before — the string is complete before the driver sees it
cursor.execute(f"SELECT * FROM stock_items WHERE shelf = '{shelf}'")

# After — the driver receives a template and a parameter sequence
cursor.execute("SELECT * FROM stock_items WHERE shelf = %s", (shelf,))
```

For process execution: pass an argument vector, never a command string, and never through a shell.

```python
# Before
os.system("archive-tool --input " + path)
# After
subprocess.run(["archive-tool", "--input", path], shell=False, check=True, timeout=30)
```

For filesystem paths: resolve, then verify containment inside the intended root before opening.

---

## RP-03 — Split a God Module by responsibility

**Fixes AP-03** · **Contract: safe** — internal module boundaries are not observable. Keep the
registered routes and their handlers' behaviour identical.

Cut along responsibility seams, not along line counts. Move code; do not rewrite it in the same step.

**Before** (JavaScript — one module holding routing, rules and persistence)

```js
// bookings.js  (400+ lines)
const db = require('./db');
const app = require('./server');

app.post('/bookings', async (req, res) => {
  const { roomId, start, end, guests } = req.body;
  const room = await db.query(`SELECT * FROM rooms WHERE id = ${roomId}`);
  if (guests > room.capacity) return res.status(400).json({ error: 'too many guests' });
  const overlapping = await db.query(
    `SELECT count(*) FROM bookings WHERE room_id = ${roomId} AND start < '${end}' AND end > '${start}'`
  );
  if (overlapping > 0) return res.status(409).json({ error: 'room busy' });
  const nights = Math.ceil((new Date(end) - new Date(start)) / 86400000);
  const total = nights * room.nightly_rate * (nights >= 7 ? 0.9 : 1);
  const saved = await db.query(`INSERT INTO bookings ... RETURNING *`);
  res.status(201).json({ id: saved.id, total });
});
// ... eight more handlers, all in this file
```

**After** — four files, each with one reason to change.

```js
// models/roomRepository.js — persistence only
class RoomRepository {
  constructor(db) { this.db = db; }
  findById(id) {
    return this.db.query('SELECT * FROM rooms WHERE id = $1', [id]);
  }
  countOverlapping(roomId, start, end) {
    return this.db.query(
      'SELECT count(*) AS n FROM bookings WHERE room_id = $1 AND start < $2 AND "end" > $3',
      [roomId, end, start],
    );
  }
}
module.exports = { RoomRepository };
```

```js
// models/booking.js — domain rules, no I/O, no framework
const LONG_STAY_NIGHTS = 7;
const LONG_STAY_DISCOUNT = 0.9;
const MS_PER_NIGHT = 24 * 60 * 60 * 1000;

function nightsBetween(start, end) {
  return Math.ceil((new Date(end) - new Date(start)) / MS_PER_NIGHT);
}

function quote(room, start, end) {
  const nights = nightsBetween(start, end);
  const discount = nights >= LONG_STAY_NIGHTS ? LONG_STAY_DISCOUNT : 1;
  return { nights, total: nights * room.nightly_rate * discount };
}

module.exports = { quote, nightsBetween };
```

```js
// controllers/bookingController.js — one use case, plain values in and out
const { quote } = require('../models/booking');
const { ConflictError, ValidationError } = require('../errors');

class BookingController {
  constructor(rooms, bookings) { this.rooms = rooms; this.bookings = bookings; }

  async create({ roomId, start, end, guests }) {
    const room = await this.rooms.findById(roomId);
    if (!room) throw new ValidationError('unknown room');
    if (guests > room.capacity) throw new ValidationError('too many guests');
    if (await this.rooms.countOverlapping(roomId, start, end) > 0) {
      throw new ConflictError('room busy');
    }
    const { total } = quote(room, start, end);
    return this.bookings.insert({ roomId, start, end, guests, total });
  }
}
module.exports = { BookingController };
```

```js
// views/bookingRoutes.js — protocol only: parse, call, render
module.exports = (router, controller) => {
  router.post('/bookings', async (req, res, next) => {
    try {
      const saved = await controller.create(req.body);
      res.status(201).json({ id: saved.id, total: saved.total });   // shape preserved
    } catch (err) { next(err); }                                     // boundary handles it
  });
  return router;
};
```

Order of moves: extract persistence first (it has the clearest seam), then the pure rules, then the
orchestration; the handler is whatever remains. Run the harness after each extraction.

---

## RP-04 — Extract authorization into a policy and a guard

**Fixes AP-04** · **Contract: decided by the legitimate-use test**
(`04-architecture-guidelines.md` §6). When the application **already identifies callers** and the
fix only stops one principal from acting on another's resource, it is safe — it changes what an
*illegitimate* caller observes — and it is applied, as below. When the application has **no identity
model**, adding authentication rejects every current client, legitimate ones included: that is
contract-changing, and the transformation is proposed — the identity model, the principals and the
policy — not applied. Never invent a policy to make the fix applicable.

Two moves: put the decision in one policy function, and move the enforcement onto the *operation*
rather than onto one of its doors.

**Before** (Go — trusts an input field, and filters only by the supplied id)

```go
func GetMaintenanceRequest(w http.ResponseWriter, r *http.Request) {
    id := r.URL.Query().Get("id")
    role := r.Header.Get("X-Role")           // caller-supplied: not trustworthy
    if role == "admin" {
        req, _ := db.Query("SELECT * FROM maintenance_requests WHERE id = $1", id)
        json.NewEncoder(w).Encode(req)       // any id, from any caller claiming admin
        return
    }
    req, _ := db.Query("SELECT * FROM maintenance_requests WHERE id = $1", id)
    json.NewEncoder(w).Encode(req)           // ...and the non-admin path is identical
}
```

**After**

```go
// models/policy.go — the decision, in one place, testable with no server
type Principal struct {
    ID      string
    Depot   string
    IsAdmin bool
}

func CanViewRequest(p Principal, req MaintenanceRequest) bool {
    return p.IsAdmin || req.DepotID == p.Depot
}
```

```go
// controllers/maintenance.go — enforcement on the operation, not on the route
func (c *MaintenanceController) View(p Principal, id string) (MaintenanceRequest, error) {
    // The query is scoped by the principal: unambiguous, and safe to apply automatically.
    req, err := c.repo.FindByID(id)
    if err != nil {
        return MaintenanceRequest{}, err
    }
    if !CanViewRequest(p, req) {
        return MaintenanceRequest{}, ErrNotAuthorized
    }
    return req, nil
}
```

```go
// views/routes.go — the principal comes from the verified session, never from the request body
func handleView(c *MaintenanceController) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        p, ok := PrincipalFromContext(r.Context())   // set by the authentication middleware
        if !ok {
            writeError(w, ErrNotAuthenticated)
            return
        }
        req, err := c.View(p, r.URL.Query().Get("id"))
        if err != nil {
            writeError(w, err)
            return
        }
        json.NewEncoder(w).Encode(toResponse(req))
    }
}
```

Because the check is in the controller, a second entry point — a CLI, a scheduled job — cannot
bypass it. Prefer scoping the query itself (`WHERE id = $1 AND depot_id = $2`) where the policy
permits: a record the principal may not see is then never loaded at all.

---

## RP-05 — Extract a use case from a handler

**Fixes AP-05** · **Contract: safe** — the handler keeps its route, status codes and body shape.

The handler should read as *parse → call → render*. Everything else moves to a controller method.

**Before** (JavaScript)

```js
router.post('/loans', async (req, res) => {
  const memberId = req.body.memberId;
  const open = await db.query('SELECT count(*) AS n FROM loans WHERE member_id = $1 AND returned_at IS NULL', [memberId]);
  const member = await db.query('SELECT * FROM members WHERE id = $1', [memberId]);
  const cap = member.tier === 'staff' ? 20 : 5;              // business rule, in the handler
  if (open.n >= cap) return res.status(422).json({ error: 'loan limit reached' });
  const due = new Date(Date.now() + (member.tier === 'staff' ? 42 : 21) * 86400000);
  const loan = await db.query('INSERT INTO loans (member_id, due_at) VALUES ($1, $2) RETURNING *', [memberId, due]);
  res.status(201).json({ id: loan.id, dueAt: loan.due_at });
});
```

**After**

```js
// models/loanPolicy.js — pure rules, no I/O, no framework
const LIMITS = { staff: { openLoans: 20, loanDays: 42 },
                 member: { openLoans: 5,  loanDays: 21 } };

const limitsFor = (tier) => LIMITS[tier] ?? LIMITS.member;

function dueDate(tier, from = new Date()) {
  const days = limitsFor(tier).loanDays;
  return new Date(from.getTime() + days * 24 * 60 * 60 * 1000);
}

function mayBorrow(tier, openLoanCount) {
  return openLoanCount < limitsFor(tier).openLoans;
}

module.exports = { limitsFor, dueDate, mayBorrow };
```

```js
// controllers/loanController.js
const { dueDate, mayBorrow } = require('../models/loanPolicy');
const { BusinessRuleError } = require('../errors');

class LoanController {
  constructor(members, loans, clock = () => new Date()) {
    this.members = members; this.loans = loans; this.clock = clock;   // clock injected: testable
  }
  async open(memberId) {
    const member = await this.members.findById(memberId);
    const openCount = await this.loans.countOpenFor(memberId);
    if (!mayBorrow(member.tier, openCount)) throw new BusinessRuleError('loan limit reached');
    return this.loans.insert({ memberId, dueAt: dueDate(member.tier, this.clock()) });
  }
}
```

```js
// views/loanRoutes.js — parse, call, render. Status code and body shape unchanged.
router.post('/loans', async (req, res, next) => {
  try {
    const loan = await controller.open(req.body.memberId);
    res.status(201).json({ id: loan.id, dueAt: loan.due_at });
  } catch (err) { next(err); }
});
```

Note the injected clock: a rule that reads the current time directly cannot be tested at a boundary
date, and that is AP-06 hiding inside AP-05.

---

## RP-06 — Introduce dependency injection and a composition root

**Fixes AP-06** · **Contract: safe** — wiring is not observable.

Collaborators are received, not constructed. One file assembles the graph. No module has side effects
at import time.

**Before** (Python — connects on import, so importing the module requires a live database)

```python
# stock.py
import psycopg2, os

connection = psycopg2.connect(os.environ["DATABASE_URL"])   # runs at import time

def adjust_stock(item_id, delta):
    with connection.cursor() as cur:
        cur.execute("UPDATE stock_items SET quantity = quantity + %s WHERE id = %s", (delta, item_id))
```

**After**

```python
# models/stock_repository.py — receives a connection; imports cause no effects
class StockRepository:
    def __init__(self, connection):
        self._connection = connection

    def adjust(self, item_id: int, delta: int) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                "UPDATE stock_items SET quantity = quantity + %s WHERE id = %s",
                (delta, item_id),
            )
```

```python
# controllers/stock_controller.py — depends on the repository, not on a driver
class StockController:
    def __init__(self, stock_repository):
        self._stock = stock_repository

    def adjust(self, item_id: int, delta: int) -> None:
        if delta == 0:
            return
        self._stock.adjust(item_id, delta)
```

```python
# main.py — the composition root: the only place that names concrete implementations
import psycopg2
from config.settings import load_settings
from models.stock_repository import StockRepository
from controllers.stock_controller import StockController
from views.routes import register_routes

def create_app():
    settings = load_settings()
    connection = psycopg2.connect(settings.database_url)
    controller = StockController(StockRepository(connection))
    app = Framework()
    register_routes(app, controller)
    register_error_handler(app)
    return app

if __name__ == "__main__":
    create_app().run()
```

`create_app()` as a factory — rather than a module-level `app` — is what makes the application
constructible twice in one process, which is what a test needs.

When the dependency is an external effect the domain needs (mail, a third party, the clock), declare
the interface in the domain and implement it outside:

```python
# models/ports.py
from typing import Protocol

class Clock(Protocol):
    def now(self): ...

# adapters/system_clock.py
from datetime import datetime, timezone

class SystemClock:
    def now(self):
        return datetime.now(timezone.utc)
```

---

## RP-07 — Replace global mutable state with scoped context

**Fixes AP-07** · **Contract: safe** — provided the observable behaviour per call is unchanged.
In a concurrent runtime this transformation usually *fixes* a correctness bug, which is the point.

**Before** (JavaScript — per-request data in a module-level slot, and an in-memory store of record)

```js
// state.js
let currentDepot = null;              // clobbered by every concurrent request
const pendingChecks = [];             // grows forever; lost on restart
let nextTicketNumber = 1;             // correct only while exactly one process exists

module.exports = { currentDepot, pendingChecks, nextTicketNumber };
```

**After**

```js
// middlewares/requestContext.js — per-invocation scope, carried on the request
function requestContext(req, _res, next) {
  req.context = {
    depot: req.principal.depot,                 // derived from the verified session
    correlationId: crypto.randomUUID(),
  };
  next();
}
```

```js
// controllers/inspectionController.js — context is a parameter, never a global
class InspectionController {
  constructor(checks, sequence) { this.checks = checks; this.sequence = sequence; }

  async schedule(context, vehicleId) {
    const ticket = await this.sequence.next();  // the datastore owns the sequence
    return this.checks.insert({                 // the datastore owns the pending set
      ticket, vehicleId, depot: context.depot, correlationId: context.correlationId,
    });
  }
}
```

Rules of thumb:

- invocation-scoped data travels as a parameter or on the invocation's own context object;
- state of record lives in the datastore, never in a process variable;
- identifier sequences come from the datastore or a UUID, never from a process counter;
- what is genuinely process-wide — a logger, a frozen settings object, a connection pool — is
  constructed once in the composition root and injected, and is immutable after construction;
- if a cache must exist, give it a bound and an eviction policy, and say why in-process is acceptable.

---

## RP-08 — One-way credential storage and output redaction

**Fixes AP-08** · **Contract: mixed.** Switching to a password KDF is **safe** when done with a
transparent upgrade-on-login path; removing a field that was being leaked in a response is
**contract-changing** — propose it, since a client may be reading it.

**Before** (Ruby)

```ruby
class MemberRepository
  def create(email:, password:)
    digest = Digest::SHA256.hexdigest(password)     # fast digest, no salt, no work factor
    DB[:members].insert(email: email, password_digest: digest)
  end

  def authenticate(email:, password:)
    row = DB[:members].where(email: email).first
    row && row[:password_digest] == Digest::SHA256.hexdigest(password)   # not constant-time
  end
end

# and, at the boundary:
logger.info("sign-in attempt: #{params.inspect}")   # writes the password to the log
render json: row                                    # serializes the whole record, digest included
```

**After**

```ruby
require 'bcrypt'   # or the ecosystem's purpose-built password KDF

class MemberRepository
  def create(email:, password:)
    # A password KDF: per-credential salt and a tunable work factor, both built in.
    DB[:members].insert(email: email, password_digest: BCrypt::Password.create(password))
  end

  def authenticate(email:, password:)
    row = DB[:members].where(email: email).first
    return nil unless row
    # The KDF's comparison is constant-time and re-derives with the stored parameters.
    BCrypt::Password.new(row[:password_digest]) == password ? row : nil
  end
end
```

```ruby
# views/member_presenter.rb — explicit allow-list: adding a column never leaks it
class MemberPresenter
  PUBLIC_FIELDS = %i[id email display_name joined_at].freeze

  def self.call(row)
    row.slice(*PUBLIC_FIELDS)
  end
end

# middlewares/log_redaction.rb
REDACTED = %w[password token secret authorization api_key].freeze

def redact(params)
  params.transform_values.with_index { |v, _| v }        # structure preserved
        .each_with_object({}) { |(k, v), out|
          out[k] = REDACTED.any? { |r| k.to_s.downcase.include?(r) } ? '[REDACTED]' : v
        }
end

logger.info("sign-in attempt: #{redact(params)}")
```

Migration without a flag day: keep verifying old digests, and on a successful login re-hash with the
new KDF and replace the stored value. After a defined window, force a reset for whoever has not
logged in. State this plan in the report — it is an operational decision, not just a code change.

---

## RP-09 — Centralize error handling behind a domain taxonomy

**Fixes AP-09** · **Contract: mixed.** Centralizing while **preserving** the observed status codes
and body shapes is safe. Changing the error body shape, or changing a status code, is
contract-changing — propose it, and record the current shape in the baseline first so you can prove
which is which.

**Before** (JavaScript — the same block copied into every handler, and a swallow)

```js
router.get('/loans/:id', async (req, res) => {
  try {
    const loan = await db.query(`SELECT * FROM loans WHERE id = ${req.params.id}`);
    if (!loan) return res.status(404).json({ error: 'not found' });
    res.json(loan);
  } catch (e) {
    console.log(e);
    res.status(500).json({ error: e.message });   // leaks the driver message to the client
  }
});

// elsewhere
try { await ledger.record(entry); } catch (e) { /* ignore */ }   // a lost write, silently
```

**After**

```js
// errors.js — a small taxonomy owned by the domain
class AppError extends Error {
  constructor(message, { code, status }) { super(message); this.code = code; this.status = status; }
}
class NotFoundError     extends AppError { constructor(m = 'not found')     { super(m, { code: 'not_found',     status: 404 }); } }
class ValidationError   extends AppError { constructor(m = 'invalid input') { super(m, { code: 'invalid_input', status: 400 }); } }
class ConflictError     extends AppError { constructor(m = 'conflict')      { super(m, { code: 'conflict',      status: 409 }); } }
class BusinessRuleError extends AppError { constructor(m = 'rule violated') { super(m, { code: 'rule_violated', status: 422 }); } }
class NotAuthorized     extends AppError { constructor(m = 'not authorized'){ super(m, { code: 'not_authorized',status: 403 }); } }

module.exports = { AppError, NotFoundError, ValidationError, ConflictError, BusinessRuleError, NotAuthorized };
```

```js
// middlewares/errorBoundary.js — one mapping, registered last
const { AppError } = require('../errors');

module.exports = (logger) => (err, req, res, _next) => {
  const correlationId = req.context?.correlationId ?? 'unknown';
  if (err instanceof AppError) {
    logger.warn({ correlationId, code: err.code, message: err.message });
    return res.status(err.status).json({ error: err.message, correlationId });
  }
  // Unexpected: log everything internally, disclose nothing externally.
  logger.error({ correlationId, message: err.message, stack: err.stack });
  res.status(500).json({ error: 'internal error', correlationId });
};
```

```js
// views/loanRoutes.js — handlers stop shaping errors
router.get('/loans/:id', async (req, res, next) => {
  try {
    res.json(await controller.find(req.params.id));   // controller throws NotFoundError
  } catch (err) { next(err); }
});
```

And the swallow becomes explicit — either it matters and must propagate, or it does not and the
decision is written down:

```js
// Deliberate, narrow, and documented. Anything else propagates to the boundary.
try {
  await metrics.increment('loan.opened');
} catch (err) {
  logger.warn({ msg: 'metrics unavailable; continuing', err: err.message });
}
```

The same taxonomy in Python, registered once at the boundary:

```python
# errors.py
class AppError(Exception):
    code, status = "internal_error", 500

class NotFoundError(AppError):
    code, status = "not_found", 404

# middlewares/error_handler.py
def register_error_handler(app, logger):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        logger.warning("%s: %s", err.code, err)
        return {"error": str(err), "code": err.code}, err.status
```

---

## RP-10 — Collapse N+1 into a set-based query

**Fixes AP-10** · **Contract: safe** — same result, fewer round trips. Preserve ordering explicitly:
a set-based query may return rows in a different order, and ordering can be observable.

**Before** (Python — one query per element, plus a second per element inside the loop)

```python
def overdue_report(cursor, depot_id):
    cursor.execute("SELECT id, member_id, due_at FROM loans WHERE depot_id = %s", (depot_id,))
    loans = cursor.fetchall()

    rows = []
    for loan in loans:                                     # N iterations
        cursor.execute("SELECT display_name FROM members WHERE id = %s", (loan.member_id,))
        member = cursor.fetchone()                         # N more round trips
        rows.append({"loan": loan.id, "member": member.display_name, "due": loan.due_at})
    return rows
```

**After** — one round trip, ordering stated explicitly:

```python
def overdue_report(cursor, depot_id):
    cursor.execute(
        """
        SELECT l.id, l.due_at, m.display_name
          FROM loans l
          JOIN members m ON m.id = l.member_id
         WHERE l.depot_id = %s
         ORDER BY l.due_at, l.id          -- deterministic, and matches the previous order
        """,
        (depot_id,),
    )
    return [
        {"loan": r.id, "member": r.display_name, "due": r.due_at}
        for r in cursor.fetchall()
    ]
```

When a join is not appropriate, batch by key — two queries regardless of N:

```python
loans = repo.loans_for_depot(depot_id)
member_ids = {loan.member_id for loan in loans}
members = repo.members_by_ids(member_ids)          # one query: ... WHERE id = ANY(%s)
by_id = {m.id: m for m in members}
rows = [{"loan": l.id, "member": by_id[l.member_id].display_name} for l in loans]
```

Variants of the same move: use the ORM's eager-loading directive instead of a lazy relation inside a
loop; aggregate in the datastore (`count`, `sum`, `group by`) rather than reading the table to count
in memory; batch remote calls, or issue them concurrently with a bounded concurrency limit.

---

## RP-11 — Introduce a boundary schema

**Fixes AP-11** · **Contract: mixed.** Rejecting input that is *unambiguously* invalid (a
non-numeric quantity where a number is required) is safe. Tightening rules so that previously
accepted requests now fail is contract-changing — propose it.

Validate once, at the boundary, declaratively; the layers behind it receive values already known to
be well-formed.

**Before** (TypeScript)

```ts
router.post('/shipments', async (req, res) => {
  const qty = req.body.quantity;                        // could be anything, or absent
  const shelf = req.body.shelf;
  const page = parseInt(req.query.limit as string);     // NaN on garbage, unbounded otherwise
  await repo.insert({ shelf, quantity: qty, limit: page });
  res.status(201).json({ ok: true });
});
```

**After** — a schema object at the boundary, and domain invariants in the domain:

```ts
// views/schemas.ts — shape, type, presence, range, at the boundary
type Parsed<T> = { ok: true; value: T } | { ok: false; errors: string[] };

const MAX_PAGE = 200;

export function parseShipment(body: unknown): Parsed<{ shelf: string; quantity: number }> {
  const errors: string[] = [];
  const b = (body ?? {}) as Record<string, unknown>;

  const shelf = typeof b.shelf === 'string' ? b.shelf.trim() : '';
  if (!shelf) errors.push('shelf is required');
  if (shelf.length > 32) errors.push('shelf must be at most 32 characters');

  const quantity = Number(b.quantity);
  if (!Number.isInteger(quantity)) errors.push('quantity must be an integer');
  else if (quantity <= 0) errors.push('quantity must be greater than zero');

  return errors.length ? { ok: false, errors } : { ok: true, value: { shelf, quantity } };
}

export const parseLimit = (raw: unknown): number => {
  const n = Number(raw);
  return Number.isInteger(n) && n > 0 ? Math.min(n, MAX_PAGE) : 50;   // always bounded
};
```

```ts
// views/shipmentRoutes.ts
router.post('/shipments', async (req, res, next) => {
  const parsed = parseShipment(req.body);
  if (!parsed.ok) return next(new ValidationError(parsed.errors.join('; ')));
  try {
    const created = await controller.receive(parsed.value, parseLimit(req.query.limit));
    res.status(201).json({ ok: true, id: created.id });
  } catch (err) { next(err); }
});
```

Boundary validation is not domain validation. The boundary answers *is this a well-formed request*;
the domain answers *is this a legal state change*. Keep the second one in the model, where every
entry point gets it:

```go
// models/shipment.go — an invariant no boundary can be trusted to enforce
func (s *Shipment) Receive(qty int) error {
    if qty <= 0 {
        return ErrInvalidQuantity
    }
    if s.Received+qty > s.Expected {
        return ErrOverDelivery        // a rule, not a format check
    }
    s.Received += qty
    return nil
}
```

A schema/validation library is preferable to hand-written checks when the project already has one.
Do not add a dependency solely to satisfy this transformation; if there is none, hand-written checks
at a single boundary are the correct answer.

---

## RP-12 — Extract a shared policy from duplicated logic

**Fixes AP-12** · **Contract: safe** — provided the copies agreed. If they had **diverged**, unifying
them changes behaviour on at least one path: determine which copy is correct, say so in the report,
and treat the change as contract-affecting if the divergence was observable.

**Before** (Go — the same eligibility rule in two entry points, already diverged)

```go
// views/web.go
if vehicle.OdometerKM > 15000 || vehicle.MonthsSinceService >= 12 {
    scheduleService(vehicle)
}

// views/batch.go
if vehicle.OdometerKM > 15000 {                      // the months rule was never added here
    scheduleService(vehicle)
}
```

**After**

```go
// models/service_policy.go — one rule, one place, testable on its own
const (
    ServiceIntervalKM     = 15000
    ServiceIntervalMonths = 12
)

// NeedsService reports whether a vehicle is due, by either threshold.
func NeedsService(odometerKM int, monthsSinceService int) bool {
    return odometerKM > ServiceIntervalKM || monthsSinceService >= ServiceIntervalMonths
}
```

```go
// both call sites
if models.NeedsService(v.OdometerKM, v.MonthsSinceService) {
    scheduleService(v)
}
```

Procedure: prove the copies are the same rule (same reason to change, not merely similar code);
choose the correct behaviour and record the choice; extract to one place; redirect every call site;
delete the copies; re-run the harness, expecting a difference on exactly the path that was wrong.

**Do not unify by reflex.** Two blocks that look alike but answer to different reasons for change
should stay apart — a premature abstraction couples them, and the next change forces a parameter,
then a flag, then a branch. Duplication is cheaper than the wrong abstraction; when you decline to
unify, say why in the finding.

---

## RP-13 — Bind resources to scope and bound the work

**Fixes AP-13** · **Contract: mixed.** Adding timeouts and closing handles is safe. Introducing
pagination where a client previously received the entire collection is contract-changing — propose it
(offering a default limit with an opt-out is often the acceptable middle, but it is still a decision
for the owner).

**Before** (Python)

```python
def export_readings(station_id):
    conn = open_connection()                       # never closed on the error path
    cur = conn.cursor()
    cur.execute("SELECT * FROM readings WHERE station_id = %s", (station_id,))
    rows = cur.fetchall()                          # the whole table, into memory
    payload = requests.post(ARCHIVE_URL, json=rows)   # no timeout: can block forever
    conn.close()
    return payload
```

**After**

```python
BATCH_SIZE = 1_000
ARCHIVE_TIMEOUT_SECONDS = 10

def export_readings(pool, http, station_id):
    # Scope-bound acquisition: released on every path, including exceptions.
    with pool.connection() as conn, conn.cursor(name="readings_stream") as cur:
        cur.itersize = BATCH_SIZE
        cur.execute("SELECT * FROM readings WHERE station_id = %s", (station_id,))
        for batch in _chunks(cur, BATCH_SIZE):     # streamed, never fully materialized
            http.post(ARCHIVE_URL, json=batch, timeout=ARCHIVE_TIMEOUT_SECONDS)


def _chunks(cursor, size):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            return
        yield rows
```

The same two moves in Go — scope binding and an explicit deadline:

```go
func ExportReadings(ctx context.Context, db *sql.DB, stationID string) error {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)   // every call has a deadline
    defer cancel()

    rows, err := db.QueryContext(ctx,
        "SELECT id, taken_at, value FROM readings WHERE station_id = $1 LIMIT $2",
        stationID, maxExportRows)
    if err != nil {
        return err
    }
    defer rows.Close()          // released regardless of how the function exits
    ...
}
```

Checklist for this transformation: every acquisition scope-bound; every outbound call with an
explicit timeout; every retry bounded with backoff; every unbounded read paginated or streamed;
every cache bounded and evicting; every background task with a shutdown path.

---

## RP-14 — Replace a verified-deprecated API with its successor

**Fixes AP-14** · **Contract: safe when the successor is behaviourally equivalent.** If the successor
changes observable behaviour — different error semantics, different defaults, a different return
shape — that is contract-changing: propose it.

**Precondition, without exception:** the deprecation is established at evidence tier A, B or C
(`02-antipattern-catalog.md`, AP-14). Never perform this transformation from memory. The example
below shows the *shape* of the move, not a claim about any particular API.

```bash
# 1. Force the detector on and capture the warning with its stack trace (tier A)
node --pending-deprecation --trace-deprecation ./entry.js 2>&1 | tee reports/deprecations.log
#    → gives "DeprecationWarning: ... at <file>:<line>" — the report's File: field, for free

# 2. Confirm the successor from the upstream source, and record the date (tier B/C)
npm view <package>@<resolved-version> deprecated
curl -s -X POST https://api.osv.dev/v1/query \
  -d '{"package":{"name":"<package>","ecosystem":"npm"},"version":"<resolved-version>"}'
```

**Before** — the call site the warning pointed at:

```js
// The warning's stack trace named exactly this line — that is where File:<line> comes from.
const handle = legacyApi(argument);          // <api> as reported deprecated by <source>
```

**After** — the successor named by the cited source, plus the citation carried into the report:

```js
// Replaced per <source>, consulted <YYYY-MM-DD>. Semantics checked against that source:
// same return type, same failure mode, no behavioural difference observable by a caller.
const handle = documentedSuccessor(argument);
```

The placeholders are deliberate. This playbook cannot name a real successor, because by the time you
read it the answer may have changed — and an unverified replacement is a fabricated finding with a
code change attached. The names are filled in from the source you actually consulted, in this run.

Procedure:

1. Force detectors on, run, and collect warnings with their stack traces.
2. For each, confirm the successor from an upstream source and record source + date.
3. Replace one call site at a time; re-run the harness after each.
4. If the successor is not behaviourally identical, do not apply it — propose it with the difference
   named.
5. If a package is deprecated with no successor, the finding is the dependency itself; propose a
   maintained replacement or removal, with the migration cost stated.
6. Record every replacement in the report's Dependency and Deprecated API Verification table, with
   its evidence tier.

If no live lookup was possible (`--offline`, no network), **this transformation does not run.** Say
so in the degraded-verification block. A guessed replacement is a fabricated finding with a code
change attached, which is strictly worse than leaving the deprecated call in place.

---

## RP-15 — Replace magic values with named constants

**Fixes AP-15** · **Contract: safe** — a name is not observable.

**Before** (Ruby)

```ruby
def reservation_fee(nights, guests)
  fee = nights * 45.0
  fee *= 0.9 if nights >= 7
  fee += 25.0 if guests > 4
  fee += fee * 0.07
  fee
end

sleep 300 if attempts > 3
```

**After**

```ruby
module BookingRates
  NIGHTLY_RATE          = 45.0
  LONG_STAY_NIGHTS      = 7
  LONG_STAY_MULTIPLIER  = 0.9
  LARGE_PARTY_GUESTS    = 4
  LARGE_PARTY_SURCHARGE = 25.0
  CITY_LEVY_RATE        = 0.07     # set by the municipality; changes outside our release cycle
end

MAX_ATTEMPTS           = 3
RETRY_BACKOFF_SECONDS  = 300       # the unit is in the name, so the reader cannot guess wrong

def reservation_fee(nights, guests)
  fee  = nights * BookingRates::NIGHTLY_RATE
  fee *= BookingRates::LONG_STAY_MULTIPLIER if nights >= BookingRates::LONG_STAY_NIGHTS
  fee += BookingRates::LARGE_PARTY_SURCHARGE if guests > BookingRates::LARGE_PARTY_GUESTS
  fee * (1 + BookingRates::CITY_LEVY_RATE)
end
```

Where the values are owned by someone outside engineering — rates, legal periods, regulatory limits —
they belong in configuration rather than in code; name them first, then decide where they live.

For string-keyed enumerations, replace repeated literals with a single closed definition so a typo
fails instead of silently creating a new state:

```php
final class LoanStatus {
    public const OPEN     = 'open';
    public const RETURNED = 'returned';
    public const OVERDUE  = 'overdue';

    public const ALL = [self::OPEN, self::RETURNED, self::OVERDUE];
}
```

---

## RP-16 — Rename for intent and delete dead code

**Fixes AP-16 and AP-17** · **Contract: safe for internals only.** Renaming an exported symbol, a
route, a command or a response field is contract-changing — propose it. Deleting code that is
genuinely unreachable is safe; deleting code you have not proven unreachable is not.

**Before** (PHP)

```php
// checks whether the item is ok  <- the comment is stale: it also writes
function getData($d, $f = false) {
    $x = query("SELECT * FROM stock_items WHERE id = " . $d);
    // if ($f) { legacy_sync($x); }        // disabled 2019-03 - keep just in case
    if ($f) { audit_log($x); }
    return $x;
}
```

**After**

```php
/**
 * Loads a stock item and, optionally, records an audit entry.
 * The name now says what it does; the caller no longer needs a boolean it cannot read.
 */
function loadStockItem(int $itemId): ?StockItem { ... }

function loadStockItemWithAudit(int $itemId): ?StockItem { ... }
```

Rules:

- rename to what the unit *does*, not how it does it;
- if a name cannot be chosen because the unit does several things, that is AP-03 — split first, then
  name;
- replace a boolean parameter with two named functions, or an enumerated value, when the call site is
  unreadable without opening the definition;
- delete commented-out code outright. Version control is the archive, and "keep just in case" is the
  finding, not a defence;
- before deleting an apparently unused unit, rule out reflection, dynamic import, string-keyed
  dispatch and plugin registration. If you cannot rule them out, report it with lowered confidence
  and leave it in place;
- delete any parallel copy of a file (`*_old`, `*.bak`, `*_v2`, a duplicated directory) as part of
  the in-place rewrite — leaving it is a second implementation of live behaviour, carrying every
  anti-pattern the refactoring just removed;
- do not reformat files you did not otherwise change: a diff full of whitespace hides the real
  change and defeats review and bisect.

---

## RP-17 — Make runtime configuration safe by default

**Fixes AP-18** · **Contract: mixed.**
- **Safe:** reading the debug flag, the bind address and the cross-origin policy from configuration
  **with the same values the application used before** as explicit settings; switching debug off
  on the production path; replacing a framework's default error output with the centralized
  handler of RP-09, keeping status codes. Internals in an error body are not something a
  legitimate client relies on, and the status code — the contract — does not change.
- **Contract-changing:** narrowing the cross-origin policy, restricting the bind address, or
  removing a diagnostic route that clients may call. These change who can reach the application.
  Propose them, with the exact configuration value that would apply them.

The move is the same in every framework: take each runtime setting out of the code, give it a safe
default in the configuration module (RP-01), and let the environment opt **in** to the unsafe
value — never opt out of it.

**Before** (Ruby, a small web service for fleet maintenance)

```ruby
# app.rb
require 'sinatra'

set :bind, '0.0.0.0'
set :show_exceptions, true        # stack traces and an interactive page, on every error
set :dump_errors, true

before do
  headers 'Access-Control-Allow-Origin'      => request.env['HTTP_ORIGIN'].to_s,   # reflected
          'Access-Control-Allow-Credentials' => 'true'
end

get '/vehicles/:id/work-orders' do
  WorkOrders.for_vehicle(params[:id]).to_json
end
```

**After**

```ruby
# config/settings.rb — the only place runtime behaviour is decided; unsafe values are opt-in
module Settings
  DEBUG           = ENV.fetch('APP_DEBUG', 'false') == 'true'
  BIND_ADDRESS    = ENV.fetch('APP_BIND', '0.0.0.0')          # same value as before, now visible
  ALLOWED_ORIGINS = ENV.fetch('APP_ALLOWED_ORIGINS', '').split(',').map(&:strip)
end
```

```ruby
# app.rb — the composition root applies configuration; it does not invent it
require 'sinatra'
require_relative 'config/settings'
require_relative 'middlewares/error_boundary'

set :bind, Settings::BIND_ADDRESS
set :show_exceptions, Settings::DEBUG
set :dump_errors, Settings::DEBUG
use ErrorBoundary                  # RP-09: generic body outside, full detail in the log

before do
  origin = request.env['HTTP_ORIGIN']
  if origin && Settings::ALLOWED_ORIGINS.include?(origin)
    headers 'Access-Control-Allow-Origin'      => origin,
            'Access-Control-Allow-Credentials' => 'true'
  end
end
```

Here the cross-origin change **is** contract-changing: a browser client on an origin that is not
listed stops working. In Phase 3 the safe half is applied — debug off by default, error boundary,
settings externalized — and the origin allow-list is proposed with its default value left to the
team. Record the proposal with the list of origins the team must supply. Cover the change in the
surface inventory with an entry carrying an `Origin` header (`06-validation-protocol.md` §5.3), so
the replay shows exactly which cross-origin headers changed.

---

## RP-18 — Upgrade a vulnerable dependency to its fixed version

**Fixes AP-19** · **Contract: safe within the same major version** when the replay passes.
Across a major version, or when the changelog between the two versions announces a behaviour
change, it is safe **only** if the replay exercises the behaviour that changes — contract headers
included. Otherwise propose it (`04-architecture-guidelines.md` §6, dependency upgrades).

**Precondition, without exception:** the advisory is established at evidence tier B or C, with its
identifier, source and lookup date (`02-antipattern-catalog.md`, AP-19). Like RP-14, the example
shows the shape of the move with placeholders, because the answer changes over time.

```bash
# 1. Confirm the advisory and the first fixed version for the RESOLVED version in use
curl -s -X POST https://api.osv.dev/v1/query \
  -d '{"package":{"name":"<package>","ecosystem":"Go"},"version":"<resolved-version>"}'
#    → affected ranges and "fixed" events: pick the lowest fixed version on the same major line
```

**Before** (Go module manifest)

```go
// go.mod
require (
    example.org/<package> v1.4.2   // <advisory-id>: fixed in v1.4.7 (per <source>, <YYYY-MM-DD>)
)
```

**After**

```go
// go.mod — the smallest move that closes the advisory: same major, lowest fixed version
require (
    example.org/<package> v1.4.7
)
```

The lockfile moves with the manifest (`go.sum` here; the ecosystem's own lockfile elsewhere),
regenerated by the ecosystem's tool, never edited by hand.

Procedure:

1. Choose the **lowest** fixed version on the **same major line**. The smallest change that closes
   the advisory is the one with the least behaviour to verify.
2. Update the manifest and regenerate the lockfile with the ecosystem's own tool.
3. Read the changelog between the two versions. If it announces a behaviour change, check that the
   replay exercises it; if not, add a surface entry **captured against the original** first
   (`06-validation-protocol.md` §4.3), or propose the upgrade.
4. Replay. A `REGRESSION` means the upgrade is not behaviour-preserving: revert it and propose it,
   naming what changed.
5. If the only fix is on a new major line, or the package has no fix, propose the upgrade or a
   replacement, with the migration cost and the interim mitigation (disable the vulnerable feature,
   validate the input that reaches it).
6. Record the advisory, the version change and its evidence in the report's dependency verification
   table.

If the vulnerable package is transitive, move the **direct** dependency that pulls it in, or use the
ecosystem's override mechanism, and say which. An override that pins a transitive package outside
the range its parent declares runs the parent with a version it was never tested against: treat it
like a major upgrade (step 3).
